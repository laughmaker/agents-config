---
name: photo-background-cleanup
description: "Clean up a messy photo background WITHOUT altering the person — remove clutter (LED panels, cabinets, wall boxes, glass partitions, black door frames) and rebuild a uniform wall, while preserving decoded RGB pixels exactly in the verified protected subject mask. Use when the user says 背景修整/背景太乱/清一下背景/只改背景别改人/把背景弄干净, or when a portrait's background is distracting and the subject must not be re-generated. Also covers the anti-pattern: do NOT use buddy-image-processing `erase` for scene-object removal, and do NOT use ImageGen img2img for background cleanup (both change the person)."
agent_created: true
---

# 照片背景清理（人物像素零改动）

## 何时用

- 用户要「修整背景 / 背景太乱 / 清一下背景 / 只改背景别改人」。
- 肖像照背景里有杂物（LED 屏、柜子、门框、隔断、墙面面板、杂物堆），但人物不能变。

**不适用**（换成这些工具）：
- 要换场景/换风格/重绘 → `ImageGen`（图生图）。
- 要磨皮美白 → `buddy-image-processing` 的 `beauty`。
- 背景里是**文字/水印/logo** → `buddy-image-processing` 的 `erase` 可以用。

## 三条硬约束（违反即返工）

1. **`erase` 不能用来清场景物体。** 实测：明确列出「绿色 LED 屏 / 红柜 / 墙面面板 / 门框竖条」
   后跑 `erase`，返回结果**只做了轻微美化，杂物一个没动**。`erase` 模型只认文字/水印类目标。
2. **`ImageGen` 图生图不做背景清理。** 它会重绘人物（脸型、肤色、五官都会漂移），
   用户对「不像了」零容忍。
3. **已确认的人物保护区域 RGB 像素必须逐像素保持原样。** `alpha>250` 区域最大改动必须为 0；先目视确认蒙版完整覆盖人物，不能仅凭自动蒙版保证整个人物未变。边缘过渡带单独说明。

## 流程

### 1. 备份原图
微信/聊天工具收到的图先复制到`~/tmp/<task>/source.jpg`，temp 目录随时会被清空。

### 2. 取人物蒙版
先使用用户提供的蒙版，或检查可用的抠图工具。`buddy-image-processing` 是可选外部依赖，不在本技能目录内：仅从当前会话技能目录或用户指定路径定位其实际 `scripts/buddy-image-processing.py`，并确认 `connect_cloud_service` 可用；缺失时使用已安装的抠图工具或人工蒙版，不编造工具、不自动安装。只有需要云端工具且已有授权时才获取 token，不能打印或保存 token。

以下仅在已定位该依赖并完成认证时使用：
```bash
python3 "<BUDDY_SKILL_DIR>/scripts/buddy-image-processing.py" image-edit \
  --operation matting --image-file "<src>" \
  --prompt "提取人物的精细前景蒙版，保留头发边缘细节" --token "<clientTempToken>"
```
若使用云端抠图，先按该工具文档认证；完成后检查蒙版，耗时和边缘质量不作保证。

### 3. 定位背景杂物
```bash
python scripts/inspect_photo.py --image <src> --matte <matte.png>
```
（脚本名不要改成 `inspect.py` —— 会遮蔽标准库 `inspect` 模块，导致 numpy 导入直接崩。）
脚本会打印：图片尺寸、绿色/红色物体包围盒、暗色竖直框的列段、墙面参考色、人物逐行左右边界。
**先跑这个再动手**，所有坐标都从这里来，不要靠目测猜。

### 4. 重建背景
```bash
python scripts/clean_photo_background.py \
  --image <src> --matte <matte.png> --out <out.png> \
  --clean "44,788,216,902:44,660,216,774" \
  --clean "0,726,64,1062:0,500,64,836" \
  --rebuild-ymax 1002
```
- `--clean dst:src`：把 `src` 矩形的内容克隆到 `dst` 矩形，用来**先**清掉会污染参考采样的杂物。
  冒号前是目标框，冒号后是源框（都是 `x1,y1,x2,y2`，可重复传多次）。
- 之后整行用左右两侧真实墙色线性插值铺满背景。
- `--rebuild-ymax` 默认等于图片高度；人物铺满底部的图可设成人物顶到边界前的高度。

### 5. 验收（必做）
脚本会打印 `alpha>250 区域最大改动`。**必须为 0**，否则说明人物被动过，回去检查保护逻辑。

## 三个已踩过的坑

1. **参考采样列被杂物污染** → 整行被染色。若参考列（左 `x 6:22`、右 `x 938:954`）
   落在红色柜体/绿色 LED 上，插值会把整行染成淡红/淡绿。
   **顺序必须是：先局部克隆清掉参考列上的杂物，再做整行插值。**

2. **人物保护圈把人物轮廓外的杂物一起保护住.**
   不要用「逐行取 alpha 横向 min-max 实心填充」——那会把肩侧紧邻的红柜边缘也纳入保护。
   改用**形态学闭运算**（`MaxFilter(17)` 再 `MinFilter(17)`）：只填蒙版内部孔洞，不外扩轮廓。

3. **蒙版在人物内部有孔洞** → 会出现灰蓝色斑块。
   实测脸右侧区域有约 16% 的像素 alpha≈0（被误判为背景），被替换成灰背景后形成明显色块。
   闭运算能补掉这些孔洞；再叠一层兜底：结果里仍偏色（`R−G>14` 或 `G−R>14`）且不在保护区的像素，
   强制换成背景层。

## 已知局限

- 背景会被压成**没有深度信息的均匀墙面**（原有的隔断、景深层次都会消失）。
  若用户要保住背景的空间感，只能退回到「只清明显杂物」的保守方案。
- 人物边缘的 alpha 过渡带会保留部分原背景，紧贴人物轮廓的杂物可能留下极淡的痕迹。
- 默认参考列已按图片宽度比例计算，仍需确认采样没有碰到杂物；
  脚本里用 `--ref-left` / `--ref-right` 覆盖。
