#!/usr/bin/env python3
"""定位照片背景里的杂物，输出坐标供 clean_photo_background.py 使用。

用法:
    python inspect.py --image src.jpg --matte matte.png
"""
import argparse

import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--matte", help="matting 输出的 RGBA PNG，用于打印人物逐行边界")
    args = ap.parse_args()

    im = Image.open(args.image).convert("RGB")
    a = np.asarray(im).astype(np.int16)
    H, W, _ = a.shape
    print(f"size: {W} x {H}")
    print(f"参考列建议: --ref-left {int(W*0.006)}:{int(W*0.023)} "
          f"--ref-right {int(W*0.977)}:{int(W*0.994)}")
    # 各区域按比例换算的提示
    print("坐标换算基准: 下列坐标均为原图像素坐标")

    # 绿色物体（LED 屏、指示灯）
    g = (a[:, :, 1] > 120) & (a[:, :, 1] - a[:, :, 0] > 60) & (a[:, :, 1] - a[:, :, 2] > 60)
    ys, xs = np.where(g)
    if len(xs) > 50:
        print(f"[绿色物体] bbox x {xs.min()}..{xs.max()}  y {ys.min()}..{ys.max()}  ({len(xs)} px)")
        print(f"  建议 --clean 扩边 20~30px: {max(0,xs.min()-28)},{max(0,ys.min()-35)},"
              f"{xs.max()+30},{ys.max()+34}"
              f":{max(0,xs.min()-28)},{max(0,ys.min()-165)},{xs.max()+30},{ys.max()-96}")

    # 红色物体（柜体、消防箱）
    r = (a[:, :, 0] > 55) & (a[:, :, 0] - a[:, :, 1] > 35) & (a[:, :, 0] - a[:, :, 2] > 20)
    ys, xs = np.where(r)
    if len(xs) > 50:
        print(f"[红色物体] bbox x {xs.min()}..{xs.max()}  y {ys.min()}..{ys.max()}  ({len(xs)} px)")

    # 暗色竖直框（门框、隔断边框）：在上部背景带扫描
    L = a.mean(axis=2)
    band = L[int(H * 0.09):int(H * 0.20)]
    dark = (band < 90).mean(axis=0)
    idx = np.where(dark > 0.6)[0]
    if len(idx):
        segs, start = [], idx[0]
        for i in range(1, len(idx)):
            if idx[i] != idx[i - 1] + 1:
                segs.append((int(start), int(idx[i - 1])))
                start = idx[i]
        segs.append((int(start), int(idx[-1])))
        segs = [s for s in segs if s[1] - s[0] > 4]
        print(f"[暗色竖框] 列段 {segs}")

    # 墙面参考色
    pts = {
        "左上": (int(W * 0.08), int(H * 0.25)),
        "左中": (int(W * 0.16), int(H * 0.42)),
        "左小": (int(W * 0.14), int(H * 0.78)),
        "右中": (int(W * 0.92), int(H * 0.35)),
        "右上": (int(W * 0.92), int(H * 0.06)),
    }
    for name, (x, y) in pts.items():
        print(f"[墙面] {name} ({x},{y}) = {tuple(int(v) for v in a[y, x])}")

    if args.matte:
        al = np.asarray(Image.open(args.matte).convert("RGBA"))[:, :, 3]
        print("[人物边界] 抽样（alpha>120 的横向范围）")
        for y in range(0, H, max(1, H // 12)):
            row = np.where(al[y] > 120)[0]
            if len(row):
                print(f"  y={y}: x {row.min()}..{row.max()}")
            else:
                print(f"  y={y}: 无（纯背景行）")


if __name__ == "__main__":
    main()
