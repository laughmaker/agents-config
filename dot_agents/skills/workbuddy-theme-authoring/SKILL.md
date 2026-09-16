---
name: workbuddy-theme-authoring
description: 设计、逆向或排查 WorkBuddy 客户端主题（皮肤）。当用户要「给 WorkBuddy 做一套主题/皮肤」、想换肤、问皮肤为什么没生效、或需要从 app.asar 里挖 WorkBuddy 内部机制与界面文案时使用。
agent_created: true
---

# WorkBuddy 主题（皮肤）设计与逆向

主题**不是**换背景图，而是一份覆盖约 670+ 个 CSS 变量的 `skin.css` + 可选素材，打包成 ZIP 由服务端下发。

## 一、加载链路（两套并存，都有代码依据）

**主进程侧**（`DesktopAppearanceRepo`，负责落盘与 `local-file://` 供给）：
```
listResources()  →  云端 API 取资源列表（resourceKey / zipUrl / updatedAt / vipLevel / series / validTo）
        ↓
getLocalResource(theme)  →  dirName = `${resourceKey}-${updatedAt}`
        ↓
tryReadCachedCss()  命中 <dir>/skin.css 就直接返回，★不校验归属★
        ↓  未命中
downloadZip → extractZip → rewriteCssUrls（相对 url() → local-file:// 绝对路径）→ tmp+rename 原子写
        ↓
enforceLru()  →  只保留最新 8 个目录，其余 rm -rf
```

**渲染进程侧**（`ResourceLoader` / `SkinManager`）：
```
fetch(zipUrl) → JSZip.loadAsync → validateArchive → readManifest → rewriteCssUrls（→ Blob URL）
        ↓
sanitizeThemeCss（仅长度校验 + trim）
        ↓
SkinManager.applyTheme → adoptedStyleSheets（优先）或 <style data-skin-sheet="skin">
```
冷启动首帧走 localStorage 快照（`APPEARANCE_CSS_CACHE_KEY`）同步注入以避免闪色。

## 二、硬约束（照抄，别踩）

| 项 | 值 |
|---|---|
| CSS 上限 | 1 MB（`MAX_THEME_CSS_BYTES`）；localStorage 快照 512 KB |
| ZIP 包 | ≤20 MB；解压后 ≤50 MB；单条目 ≤10 MB；条目 ≤500 |
| 下载域名白名单 | `.codebuddy.cn` / `.myqcloud.com` / `.tencentcos.cn` |
| resourceKey 命名 | `/^[a-z0-9][a-z0-9_-]{0,63}$/` |
| 素材 MIME | png jpg webp gif avif / mp4 webm mov m4v ogv / mp3 m4a wav ogg |
| 内存缓存 | 最多 8 套（`MAX_MEMORY_SKINS`） |
| 磁盘缓存 | `appearance-resources/` 只留最新 8 个目录（`enforceLru`） |
| 路径安全 | 禁止绝对路径 / `..` / 盘符 / 反斜杠；`__MACOSX` 等噪声条目自动跳过 |

**包结构**：
```
<name>.zip
├── manifest.json          # {"css": "skin.css"}，可省（省则取包内第一个 .css）
└── skin.css + assets/     # CSS 内用相对路径 url("assets/x.png")
```
顶层 `skin.css` 会被「重写后另写一份」到 `<dir>/skin.css`，不原样落盘。

## 三、四条最容易搞错的设计约束

1. **只做浅色一套。** `applyTheme` 会 `overrideThemeForSkin("light")` 并移除
   `.dark` / `cb-dark` / `vscode-dark`。写 dark 变量是冗代码。
2. **圆角是参数化的。** `--radius-N = calc(Npx * var(--scaling) * var(--radius-factor))`。
   改 `--radius-factor`（取值通常 0/0.75/1/1.5，可填 0.4 之类）即可全局收窄，
   **不必逐组件写选择器**。但 `--td-radius-*`（TDesign）与 `--cb-border-radius-*`、
   `--card-border-radius`、`--inset-border-radius`、`--cb-*-bubble-radius` 是固定 px，要单独覆盖。
3. **官方外观页是商城模式。** 设置→外观（`elementId: appearance_setting_page_show`）只有
   「基础/个性」两个系列 + 「体验/标准/高级/旗舰」档位，**没有**自定义皮肤导入入口
   （全库搜「导入皮肤 / 自定义皮肤 / 上传皮肤」命中数为 0）。
4. **皮肤列表 100% 来自服务端。** 本地放 zip 或目录**不会**出现在外观页。
   可行的本地生效手段只有：覆盖某个**已存在**皮肤目录的 `skin.css`（靠 `tryReadCachedCss`
   命中即用、不校验归属）。代价是顶掉那个皮肤，且可能被 LRU 清理。
   想长期可用必须走官方上架。

## 四、变量分层（写 skin.css 时按这个顺序组织）

| 层 | 变量族 | 说明 |
|---|---|---|
| 1 品牌 | `--wb-brand-primary` / `-deep` / `-accent` / `-soft` | 主色锚点，先定这几个 |
| 2 背景 | `--wb-bg-primary` `-secondary` `-tertiary` `-card` `-hover` `-elevated` `-modal` `-popover` | 层级由浅到深，**必须单调** |
| 3 文字 | `--wb-color-text-primary` `-secondary` `-tertiary` `-hint` `-link-*` | 用 alpha 后缀保层次 |
| 4 描边 | `--wb-border-default` `-subtle` `-strong` `-control` `-focus` | 复古 / 厚重风格在这里加深 |
| 5 状态 | `--wb-status-*` / `--wb-accent-*` | 语义色，**不可被主色吞掉** |
| 6 按钮 | `--wb-button-{primary,secondary,ghost,grey,danger,link}-bg(-hover/-active/-disabled)` + `-fg` | 四态齐全 |
| 7 色阶 | `--wb-palette-{brand,blue,gray,green,red,orange,purple,cyan,black,white}-N` | 组件通用色阶 |
| 8 桥接 | `--cb-*`(50) / `--cr-*`(48) / `--vscode-*`(8) | VS Code / CBChat / 另一组件套 token |
| 9 结构 | 具体选择器补丁，如 `:root .wb-home-composer .quick-actions__list` 的 mask | 变量改不动时用 |

变量总数：约 670+。**注意前缀不止 `cb`/`wb`** —— 还有 `--cr-*`（48 个）、
`--quick-*`、`--ic-*`、`--artifact-*`，按 `--(cb|wb|vscode)-` 匹配会漏。

## 五、制作皮肤的四类坑（实战踩过）

1. **描边 alpha 继承陷阱（最容易翻车）**
   很多底版皮肤把描边写成「深色 + 低不透明度」，如 `--wb-border-default: #001f4f14`。
   如果换色时**保留原 alpha**，新描边依然 8% 透明 → 视觉上比原来更淡。
   正确做法：按原 alpha / 亮度反推应有层级，输出**不透明色**。
   参考阈值：alpha ≤0x1F → 最浅分割线；≤0x4D → 常规描边；更高 → 强描边。

2. **底版可能是「单色化」主题**
   已有皮肤常把 `palette` 的 gray/green/purple/cyan 全做成主色调。
   若你恢复了 `--wb-status-success` 为绿色，必须**同步修 `--wb-palette-green-*`**，
   否则出现「success 是绿的、palette-green 是蓝的」自相矛盾。gray 阶务必中性。

3. **多色值行不要做单色覆盖**
   渐变 / 多层阴影一行含多个 hex。按变量名映射成单一色会把色标压成同色、渐变塌陷。
   检测到一行 >1 个 hex 时，应逐色走色值表/算法，保留结构。

4. **非 hex 写法要归一化**
   `rgb(248 253 255 / 100%)`（空格 + 斜杠百分比）和 `rgba(0, 31, 79, 0.12)` 都出现过；
   直接处理 `#hex` 会漏。先统一转成 hex+alpha 再走同一套映射。

## 六、推荐做法：以最全的已有皮肤为底版做 remap

不要从零写 670 个变量。选**变量覆盖最全**的已有皮肤当底版（统计方法见第八节），然后：

1. **显式覆盖表**（BY_NAME）—— 约 150–200 条关键语义变量，精确指定
2. **色值表**（BY_VALUE）—— 高频色值统一改写
3. **HSL 保形变换兜底** —— 保留明度 L 与 alpha，只改色相/饱和度。
   这样层级关系不会崩坏。参考规则：
   - S < 10（中性）→ 冷灰化，S 压到 ≤6
   - 品牌蓝带 → 主色相，按比例对齐目标饱和度；极浅/极深（L>88 或 <22）视为着色中性
   - 绿 / 青 / 紫 → 保留色相
   - 红 → 略降饱和（更沉的复古红）
   - 金黄 → 目标橙黄色相
4. **形状层** —— `--radius-factor` + 各固定圆角变量 + 滚动条 / 投影 / 焦点态

## 七、从 app.asar 挖 WorkBuddy 内部机制（复用手法）

```python
import json, struct
f = open("/Applications/WorkBuddy.app/Contents/Resources/app.asar", "rb")
# 头部布局：offset 0/4/8/12 = 四个 uint32；JSON 从 offset 16 开始
f.seek(12); jlen = struct.unpack("<I", f.read(4))[0]
j = json.loads(f.read(jlen).decode("utf-8", errors="ignore"))
# 递归 j["files"] 拿文件列表；条目的 offset/size 是 ★字符串★，要 int()
```

- 源码定位：**不要**用 `grep -aoE '.{200}xxx.{200}'`（大回溯正则会超时被 SIGTERM）。
  改用 `data.find(b"标识符")` 然后切 ±2KB 片段。
- 中文界面文案：按 UTF-8 字节 `find`（如 `"皮肤".encode()`），读上下文再筛是否含 `skin|theme`。
- i18n 文案批量提取：`re.findall(r'"settings\.appearance\.[A-Za-z0-9_.]+"\s*:\s*"[^"]{0,60}"', txt)`
  （appearance 面共 129 条，覆盖全部语言）。
- 93 个 `.css` 都在 asar 里可直接读：定位 `renderer/assets/*.css` 里的
  foundation 与组件样式（`esm-*`、`main-content-core-*`、`lib-chat-ui-*` 最大）。
- renderer 是打包的 vite chunk，`node_modules` 下的 `simpleTask*` 命中是噪声，忽略。

## 八、统计与校验（做主题时必跑）

```bash
# 已有皮肤的变量覆盖排名 —— 选底版
for f in $(find ~/.workbuddy/appearance-resources -name skin.css); do
  n=$(grep -oE '\-\-[a-zA-Z0-9-]+:' "$f" | sort -u | wc -l)
  printf "%4s vars | %s\n" "$n" "$f"
done | sort -rn
```
产出后校验：花括号配平、变量数不减少（`set(底版) - set(新版)` 应为空）、
CSS ≤1MB、无 `local-file://` 或底版素材残留。

**视觉校验**：把 `skin.css` 与一份模拟界面 HTML 同放 `tmp/<slug>/`，
用 headless Chrome 截图（**必须 `dangerouslyDisableSandbox`**）：
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --no-sandbox --hide-scrollbars --virtual-time-budget=3000 --screenshot=preview.png \
  --window-size=1040,700 "<file uri>"
```
文件 URI 用 Python `pathlib.Path(...).resolve().as_uri()` 生成（手写百分号编码会在 CJK 路径出错）。
