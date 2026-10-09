# 踩坑记录（按重要性排序）

这些是实测撞出来的，脚本里已经处理；改动脚本前先看这里。

## 反风控

| 现象 | 原因 | 处理 |
|---|---|---|
| 发布返回 `client.action` **403**，页面停在表单不跳"评价成功" | 用 `eval` 里 `el.click()` 合成点击，或把整段文字一次 `set` 进 textarea（等效粘贴） | 必须真实 `click`（hover→click）+ CLI `type` 分片逐字键入 |
| 连发 10+ 条后开始出现 403 | 提交频率限流 | 冷却 40–90s 再重试，通常即过；连续 2 条失败就中止本轮 |
| 同一条重试时按钮点不到 | 页面重渲染，ref 失效 | 每次提交前用 CLI `find <文本>` 现取 ref，不缓存 ref |
| 评价有字数但没拿到预期豆数 | 缺实拍图，只发文字档；或文案与本人历史评价高度重复被判"无意义" | 不批量刷同一句；晒图档只在用户提供真实实拍图时补 |

## playwright-cli 用法坑

- `--raw eval` 的输出是 JSON 引号包裹的一行，取最后一行并剥壳；别按多行解析。
- 传给 `eval` 的 JS **不能含真实换行**：CLI 是把它塞进 `page.evaluate('...')` 的单引号字符串里，真实换行会把 JS 截断，返回 `at UtilityScript.<anonymous> (<anonymous>:1:44)`。中文字面量在模板里写成 `\\uXXXX`，并 `\" \".join(js.split(\"\\n\"))`（见 `pw.ev`）。
- `type` 命令只接文本、无延迟参数，节奏靠"分片 + 片间 sleep"做出来。
- 会话生命周期：`list` 看会话，`close` 关掉。长时间不用浏览器会被 daemon 回收，profile 里的登录态不丢，重开即可。

## 数据获取坑

- 清单接口 `getUserAggregateCommentList` 是 POST 到 `api.m.jd.com/client.action`，**functionId 在请求体里，URL 上没有**。所以 `requests` 里按 URL grep 是找不到的，必须按 `client.action` 收窄后逐条 `request-body` 确认（`jd_list.py:is_list_request`）。
- 不要自己构造 `h5st` 签名。让页面自己发请求，再从网络日志捞响应体。翻页同理：滚动**页面内的滚动容器**（不是 window）触发懒加载。
- 一条待评价 = 一个 `userAggregateCommentList` 元素；`orderId + wareId` 才唯一，同一订单同商品可能有重复行，落盘时按这对键去重。
- `estJingBean` 是"评完最多可获"总额，`estCommentJingBean` + `estDiscussionJingBean` 才分得清文字档 / 晒图档。
- 已评价清单走另一个接口 `getCommentWareList`（`status=3`），里面 `picJingBean>0` 表示晒图档仍未领。

## 浏览器接入坑（首次登录）

- 想直接接管用户已登录 Chrome：此路通常不通。macOS 下 `~/Library/Application Support/Google/Chrome` 受 TCC 保护（`Operation not permitted`），AppleScript 需要 GUI 批准权限、agent 环境里会卡死；新版 Chrome 还禁止在默认 profile 上开 `--remote-debugging-port`（[说明](https://developer.chrome.com/blog/remote-debugging-port?hl=zh-cn)）。
- `attach --extension=chrome` 需要先在 Chrome 装 Playwright 扩展，扩展 ID `mmlmfjhmonkocbjadbfplnigmagldckm`。用户愿意装时这条路最省事。
- 最稳：`-s=jd open ... --browser=chrome --profile=$HOME/tmp/jd_profile --headed`，请用户扫码一次，登录态留在 profile，之后免登录。
- `bean.m.jd.com` 京豆明细页经常返回"网络连接不佳"，取不到就以评价中心头部计数为准，并注明待精确核对。
