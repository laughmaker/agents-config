#!/usr/bin/env python3
"""清理照片背景，人物像素零改动。

思路：用 matting 得到的人物 alpha 当权重，只在人物之外重建背景。
   1) 先用局部克隆清掉会污染参考采样列的杂物
   2) 整行用左右两侧真实墙色线性插值铺满
   3) 人物保护用形态学闭运算填蒙版孔洞（不外扩轮廓）
   4) 兜底：残余偏色且不在保护区的像素强制换成背景层

用法:
    python clean_photo_background.py --image src.jpg --matte matte.png --out out.png \
        --clean "44,788,216,902:44,660,216,774" \
        --clean "0,726,64,1062:0,500,64,836" \
        --rebuild-ymax 1002

验收: 脚本打印的 "alpha>250 区域最大改动" 必须 == 0。
"""
from pathlib import Path
import argparse

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

parser = argparse.ArgumentParser()
parser.add_argument("--image", required=True, help="原图")
parser.add_argument("--matte", required=True, help="matting 输出的 RGBA PNG")
parser.add_argument("--out", required=True, help="输出路径")
parser.add_argument("--clean", action="append", default=[],
                    help="克隆清理，一组四个坐标 dst_x1,dst_y1,dst_x2,dst_y2:src_x1,src_y1,src_x2,src_y2，可重复")
parser.add_argument("--rebuild-ymax", type=int, default=0,
                    help="重建背景的纵向上限，默认整图高度")
parser.add_argument("--ref-left", default="", help="左参考列，如 6:22，默认按宽度比例推算")
parser.add_argument("--ref-right", default="", help="右参考列，如 938:954")
parser.add_argument("--feather", type=int, default=12, help="局布克隆羽化半径")
args = parser.parse_args()

orig = np.asarray(Image.open(args.image).convert("RGB")).astype(np.float32)
alpha = np.asarray(Image.open(args.matte).convert("RGBA"))[:, :, 3].astype(np.float32)
H, W = alpha.shape
if orig.shape[:2] != (H, W):
    raise SystemExit(f"尺寸不一致: 原图 {orig.shape[1]}x{orig.shape[0]} vs 蒙版 {W}x{H}")

# ---------- 参考列 ----------
if args.ref_left:
    lx1, lx2 = (int(v) for v in args.ref_left.split(":"))
else:
    lx1, lx2 = int(W * 0.006), int(W * 0.023)
if args.ref_right:
    rx1, rx2 = (int(v) for v in args.ref_right.split(":"))
else:
    rx1, rx2 = int(W * 0.977), int(W * 0.994)
print(f"参考列 left={lx1}:{lx2}  right={rx1}:{rx2}")

Y_MAX = args.rebuild_ymax or H


def rect_mask(box, feather):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rectangle(box, fill=255)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(feather))).astype(np.float32) / 255.0


# ---------- 阶段 1: 局部克隆，清掉污染参考列的杂物 ----------
cleaned = orig.copy()
for spec in args.clean:
    try:
        dst_s, src_s = spec.split(":")
        dst = tuple(int(v) for v in dst_s.split(","))
        src = tuple(int(v) for v in src_s.split(","))
        assert len(dst) == 4 and len(src) == 4
    except Exception:
        raise SystemExit(f"--clean 格式错误: {spec}（应为 x1,y1,x2,y2:x1,y1,x2,y2）")
    x1, y1, x2, y2 = dst
    sx1, sy1, sx2, sy2 = src
    if (x2 - x1) != (sx2 - sx1) or (y2 - y1) != (sy2 - sy1):
        raise SystemExit(f"克隆源与目标尺寸不一致: {spec}")
    patch = cleaned.copy()
    patch[y1:y2, x1:x2] = cleaned[sy1:sy2, sx1:sx2]
    m = rect_mask(dst, args.feather)[:, :, None]
    cleaned = cleaned * (1 - m) + patch * m
    print(f"克隆 {dst} <- {src}")

# ---------- 阶段 2: 逐行左右墙色插值重建背景 ----------
left = np.zeros((Y_MAX, 3), np.float32)
right = np.zeros((Y_MAX, 3), np.float32)
for y in range(Y_MAX):
    left[y] = np.median(cleaned[y, lx1:lx2], axis=0)
    right[y] = np.median(cleaned[y, rx1:rx2], axis=0)


def smooth(ref, k=15):
    pad = np.pad(ref, ((k, k), (0, 0)), mode="edge")
    out = np.zeros_like(ref)
    for c in range(3):
        out[:, c] = np.convolve(pad[:, c], np.ones(2 * k + 1) / (2 * k + 1), mode="valid")[:len(ref)]
    return out


left, right = smooth(left), smooth(right)

bg = cleaned.copy()
t = (np.arange(W) / (W - 1))[:, None]
for y in range(Y_MAX):
    bg[y, :] = left[y][None, :] * (1 - t) + right[y][None, :] * t

bg_mask = np.zeros((H, W), np.float32)
bg_mask[:Y_MAX, :] = 1.0
bg_mask = np.asarray(
    Image.fromarray((bg_mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))
).astype(np.float32) / 255.0

# ---------- 人物保护: 形态学闭运算填孔洞，不外扩轮廓 ----------
raw = Image.fromarray(((alpha > 120) * 255).astype(np.uint8))
closed = raw.filter(ImageFilter.MaxFilter(17)).filter(ImageFilter.MinFilter(17))
closed = np.asarray(closed.filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255.0
a_eff = np.clip(np.maximum(alpha / 255.0, closed), 0, 1)
print(f"人物保护面积占比: {float((a_eff > 0.9).mean()):.3f}")

# ---------- 合成 ----------
w = (bg_mask * (1.0 - a_eff))[:, :, None]
out = orig * (1.0 - w) + bg * w

# ---------- 兜底: 残余偏色像素强制替换 ----------
is_bg = np.abs(out - bg).max(axis=2) < 3.0
bad = ((out[:, :, 0] - out[:, :, 1] > 14) | (out[:, :, 1] - out[:, :, 0] > 14)) & ~is_bg
force = bad & (closed < 0.85)
print(f"兜底强制替换的偏色像素: {int(force.sum())}")
fw = (bg_mask * force.astype(np.float32))[:, :, None]
out = out * (1.0 - fw) + bg * fw

if Path(args.out).suffix.lower() != ".png":
    raise SystemExit("人物像素零改动要求输出 PNG，避免有损编码")
protected = alpha > 250
encoded = np.clip(out, 0, 255).astype(np.uint8)
encoded[protected] = orig.astype(np.uint8)[protected]
Image.fromarray(encoded).save(args.out)

d = np.abs(encoded.astype(np.float32) - orig).max(axis=2)
worst = float(d[alpha > 250].max()) if (alpha > 250).any() else 0.0
print(f"alpha>250 区域最大改动: {worst:.3f}  (验收要求 == 0)")
print(f"saved {args.out}")
