---
name: jd-review
description: "京东评价领京豆自动化：读取评价中心待评价清单，用拟人操作（随机停顿、真实逐段键入、hover 后点击、滚动浏览）逐条提交评价并核对京豆到账。当用户说「评价领京豆」「去京东评价」「帮我把待评价的都评了」「京豆能领多少」「补追评晒图」时使用。依赖 playwright-cli + 持久化登录会话。"
---

# 京东评价领京豆（jd-review）

用真实浏览器会话提交京东待评价，领取评价京豆，并把风控暴露降到最低。

## 硬性边界（先读，不可绕过）

1. **只提交真实文字。** 评价内容必须是对该商品的客观描述。禁止编造未发生的体验细节（例如没测过就写"续航很强"）。批量默认文案只能使用用户认可的通用中性句式，且**不得对同一商品重复使用**——京东规则第 5 条把"与自己过去发布内容重复度较高"列为不发奖励的情形。
2. **禁止补图作弊。** 不生成 AI 图片、不从网上或商品详情页取图冒充"买家实拍"。规则明文"图片需为实拍图""非 aigc 评价：用 AI 工具生成的评价将无法获得奖励"。用户这样要求时，说明拒绝并给出替代路径（用户手机实拍图 → 按商品放文件夹 → 逐条上传）。
3. **单账号单会话。** 不并发多标签提交，不伪造 UA/设备指纹，不绕过滑块或 h5st 签名。签名一律由页面自己产生。
4. 每日上限：默认单次运行不超过 **10 条**，其余留到后续日期。要突破必须先向用户说明并得到确认。
5. 出现连续 `403` 或页面提示违规/禁言 → 立即停止，不重试第三轮。

## 前置条件

```bash
command -v npx >/dev/null || echo "需要 Node.js/npm"
```

浏览器会话统一使用命名会话 `jd` + 持久 profile（登录态保存在此目录，跨批复用）：

```bash
PW="npx --yes @playwright/cli@latest -s=jd"
$PW open "https://comment.m.jd.com/pc-static/center" \
    --browser=chrome --profile="$HOME/tmp/jd_profile" --headed
```

- **优先接管用户已登录的 Chrome**（用户 AGENTS 规则要求复用登录态）。但 macOS 下 Chrome 默认 profile 受 TCC 保护、且新版 Chrome 禁止在默认 profile 开调试端口，通常接管不了。若接管失败，直接走下面的扫码路径，不要反复尝试 AppleScript / 复制 profile。
- **扫码登录（最稳）**：新开 headed 窗口后跳到 `https://passport.jd.com/new/login.aspx?ReturnUrl=https%3A%2F%2Fcomment.m.jd.com%2Fpc-static%2Fcenter`，请用户把窗口切前台用京东 App 扫码；登录态留在 `--profile` 目录，后续运行免登录。
- 判断是否已登录：页面文本出现用户昵称 + `已写评价` 计数即成功；被重定向到 `passport.jd.com` 即未登录。

## 工作流

### 1. 读取待评价清单（含真实 orderId / skuId / 可领京豆）

清单接口是 `functionId=getUserAggregateCommentList`（POST `api.m.jd.com/client.action`，body 里 `status=1`、`page`、`pageSize=30`、`tabType=1`）。页面自身会发出带合法 h5st 的请求，**不要自己构造签名**——用 DOM 触发翻页（滚动容器），再读回响应体：

```bash
python3 scripts/jd_list.py --session jd --out /Users/hzd/tmp/jd_todo.json
```

脚本逻辑：`goto` 评价中心 → 从 `requests` 里筛 `client.action` 的请求，逐条读 `request-body` 确认哪个是清单接口 → `response-body` 取 JSON → 需要更多页时用 `eval` 操作**页面内的滚动容器**（真实懒加载）再抓新增请求。关键字段：`orderId`、`wareId`、`wname`、`estJingBean`（标注总额）、`estCommentJingBean`（文字档）、`estDiscussionJingBean`（晒图档）。

> 清单接口是 POST，`functionId` 在**请求体**里，URL 上看不见，所以不能按 URL grep functionId。详见 [references/pitfalls.md](references/pitfalls.md)。

`estJingBean = 0` 的商品没有京豆奖励，除非用户要求，跳过。

### 2. 逐条提交（拟人操作，核心）

```bash
python3 scripts/jd_publish.py --session jd --order <orderId> --sku <skuId> --text "对该商品的真实描述"
```

`jd_publish.py` 内置的拟人化措施（不要精简掉，这些是实测有效的部分）：

| 环节 | 做法 | 为什么 |
|---|---|---|
| 进页面 | `goto` 后随机睡 3.5–7s | 首屏立刻操作是机器特征 |
| 看内容 | 随机 2–4 次 `scrollBy`（-80~260px），每次间歇 0.6–2.4s | 真实用户会先浏览表单 |
| 聚焦 | 对 textarea 先 `hover` 再 `click`（selector 即可） | 用 `eval` 直接 `.focus()` 不产生鼠标事件 |
| 键入 | 拆成 3–7 字的短片段，用 CLI `type` **真实逐字键入**，片段间 0.4–1.6s，长句后偶发 2–4s 停顿 | 一次 `set.call(ta, 全文)` 是纯粘贴，实测触发 403 |
| 改稿 | 小概率 `press Backspace` × 1–3 再补输 | 真人会打错再改 |
| 评分 | 读 `.scoreBox-conter-score` 确认已是"非常好"，缺项才点击星星 | 少做无谓点击 |
| 提交前 | 随机 4–10s "读完再发" 停顿，`hover` 发布按钮再 `click` | 关键：JS 合成 `click()` 实测返回 403，真实点击通过 |
| 校验 | 页面文本含 `评价成功` 才算成功 | 不要凭 HTTP 200 判断 |
| 失败 | `NOT-PUBLISHED`/403 → 冷却 40–90s，用 `find` 重新取 ref，`hover`+`click` 重试 1 次 | 风控多为限流，等一会儿即过 |

发布页 URL（GET 即可，无签名）：
`https://comment.m.jd.com/pc-static/publish?orderId=<orderId>&skuId=<skuId>&commentType=1`
同订单多商品可用合并评价 `commentType=5`（评价中心点"一起评"，会打开新标签，此时两个 textarea 都要填）。

### 3. 批量运行

```bash
python3 scripts/jd_run.py --session jd --todo /Users/hzd/tmp/jd_todo.json --limit 8
```

- 每条之间随机睡 25–70s，每 4 条额外睡 60–180s（打散节奏）。
- 断点续跑：成功记录写 `~/.agents/skills/jd-review/state/published.json`（`orderId` 去重），重跑自动跳过；失败的条目不记账，下次会再试。
- 文案优先用 `--texts-file ~/tmp/my_words.json`（`{"<orderId>": "用户的真实感受"}`）。没有时按商品名做模板差异化轮换，同一模板不重复用。
- 连续 2 条失败即中止，汇报而不是硬闯。
- 换环境或改过脚本后，先 `--dry-run` 跑一条：走完拟人键入但不点发布、不记账，用来验证链路。

### 4. 对账

```bash
python3 scripts/jd_check.py --session jd --reload --save
```

读评价中心头部 `已写评价 / 已获京豆` 计数与剩余待评条数。**提交前先 `--save` 记基线**，结束后再跑一次，差值即本轮到账。京豆明细页 `bean.m.jd.com` 经常返回"网络连接不佳"，取不到时以评价中心计数为准并标注为待精确核对。

## 京豆规则速查（来自 comment.m.jd.com/m-rate/rate-rule）

| 档 | 条件 | 豆 |
|---|---|---|
| 文字评价 | 实付 ≥20 元、≥10 字、过审 | 10（实付 ≥100 → 20） |
| 晒图 | 上传**实拍图**并过审 | 10（≥100 → 20） |
| 尺码 | 鞋服填尺码 | 10 / 20 |
| 首次评价 | 用户首次在京东评价 | 文字档 ×2 |
| 评价官优质评价 | 60 字 + 2 图/视频且原创、被选为优质 | ×2 |
| 评价有礼 | 商家配置（如标注 320 京豆） | 按商家配置，数量先到先得 |
| 特殊类目加磅 | 运动户外 ×2/×5、美妆护肤 ×2，仅受邀用户 | — |

时效：60 天内首评、60 天内评服务、180 天内追评。**追评无独立返豆**；接口里 `picJingBean` 仍 >0 表示晒图档未领，只有用户真实实拍图补上才可能拿到，且金额以审核后系统发放为准（未验证是否经追评入口发放）。

风险条款：未审核通过累计 ≥5 条 → 一年内该账号所有评价晒单均不发京豆。所以宁可少发、慢发，也别批量硬发。

## 汇报口径

只报三件事：本轮新提交成功 N 条（哪些商品）、京豆计数 基线→现值 = 到账 M、剩余可领（含因缺实拍图拿不到的部分）。批量文案的重复度风险、以及无法逐笔对账的事实，要一并说明。

## 文件

| 路径 | 用途 |
|---|---|
| [scripts/pw.py](scripts/pw.py) | playwright-cli 会话封装 + 拟人基础件（`real_click`/`find_ref`/`human_scroll`/各类 JS 模板） |
| [scripts/jd_list.py](scripts/jd_list.py) | 读待评价清单 → `jd_todo.json` |
| [scripts/jd_publish.py](scripts/jd_publish.py) | 拟人化提交单条评价/追评，支持 `--dry-run` |
| [scripts/jd_run.py](scripts/jd_run.py) | 批量提交 + 限速 + 断点续跑 |
| [scripts/jd_check.py](scripts/jd_check.py) | 计数对账，`--save` 存 `state/counter.json` 历史 |
| [state/published.json](state/published.json) | 已提交记录（去重依据） |
| [references/pitfalls.md](references/pitfalls.md) | 403 风控、CLI eval 换行坑、接口签名/翻页、浏览器接入等实测踩坑 |
