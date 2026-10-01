---
name: xhs-kol-info
description: Read Xiaohongshu Pugongying (小红书蒲公英 / pgy.xiaohongshu.com) invite-list KOL details from the logged-in Chrome browser, especially 感兴趣 + 未跟进 rows. Use when the user asks to read the first N bloggers/KOLs, filter 感兴趣 and 跟进状态=未跟进, open 查看详情, reveal 手机号 or 微信号 via the eye icon, export or append them to Excel, and optionally mark processed KOLs as 已跟进 when explicitly requested.
---

# xhs-kol-info
Use this skill to read contact fields from Xiaohongshu Pugongying invite-list rows, export or append them to `.xlsx`, and optionally mark processed KOLs as followed.

## Core workflow
1. Prefer the user's existing Chrome login state. Use the existing Chrome tab at `https://pgy.xiaohongshu.com/solar/pre-trade/brand/invite-list/note` when available.
2. The script first selects the `感兴趣` tab, sets `跟进状态` to `未跟进`, then clicks `查询`.
3. If Chrome exposes a local CDP port, run the bundled script instead of rewriting browser automation code:
```bash
python3 /Users/hzd/.agents/skills/xhs-kol-info/scripts/export_xhs_kol_info.py --count <N>
```
4. If the user gives an output path, pass `--out <xlsx-path>`. Otherwise the script writes to `./artifacts/xhs-kol-info-YYYYMMDD-HHMMSS.xlsx` under the current workspace.
5. By default the script uses `--browser chrome` and auto-checks common local CDP ports. If the Chrome DevTools port is known, pass `--port <port>`.
6. By default the script does NOT mark rows as `已跟进`. Only pass `--mark-followed` when the user explicitly requests it.
7. After each KOL is read and recorded in memory, the script closes the detail drawer. When `--mark-followed` is NOT used, the script tracks already-read visible rows and moves down the list instead of repeatedly reading the first row.
8. Report the created Excel path and a short preview table.

## Chrome extension path
Use this path when the user says the page is already open in Chrome, or when `curl http://127.0.0.1:<port>/json/list` cannot find a local CDP port but Chrome is connected through Codex Computer Use / Chrome extension.

### Setup and connection management
1. Load and follow `chrome:control-chrome`.
2. Initialize the browser runtime once per fresh Node session:
```js
const { setupBrowserRuntime } = await import("/Users/hzd/.codex/plugins/cache/openai-bundled/chrome/26.623.141536/scripts/browser-client.mjs");
await setupBrowserRuntime({ globals: globalThis });
```
3. `setupBrowserRuntime` is fast (< 300ms). `openTabs()` and `claimTab()` can take 5–70s. Do them in the same call right after setup to reduce timeout risk.
4. **Connection health check**: before a batch of operations, verify the browser is alive with `document.title`. If you get "browser is not defined" or "Browser is not available", re-run `setupBrowserRuntime` and re-claim the tab.
5. **Node REPL variable scoping**: Node REPL top-level `let`/`const` bindings persist across calls and silently shadow later declarations. Always wrap multi-statement browser interactions in `{ }` blocks to avoid redeclaration errors, or use unique variable names per call.
6. **kernel reset recovery**: if the JS kernel resets (timeout or crash), all globals are lost. Re-import and re-setup in a single call, then re-claim the tab from fresh `openTabs()`.

### Reading data from the page
1. Use `browser.user.openTabs()` to find the tab titled `我的邀约 - 小红书蒲公英` or URL `https://pgy.xiaohongshu.com/solar/pre-trade/brand/invite-list/note`. Claim it with `browser.user.claimTab(tab)`.
2. Use the tab `cdp` capability: `const cdp = await tab.capabilities.get('cdp')`, then `await cdp.send('Runtime.evaluate', { expression: '...', returnByValue: true })`.
3. **Clicking buttons**: prefer Playwright (`tab.playwright.getByText('查看详情').nth(i).click()`) for button clicks — it auto-waits for the element. CDP `Runtime.evaluate` with `.click()` does NOT wait.
4. **Reading data**: prefer CDP `Runtime.evaluate` with `returnByValue: true` for reading DOM state and text content.

### Row-by-row extraction pattern
Read rows serially. For each row:
1. **Close the drawer**: `document.querySelector('.d-drawer-close')?.click()`, then wait 400ms.
2. **Click 查看详情**: use Playwright `tab.playwright.getByText('查看详情').nth(i).click()`, wait 800ms for the drawer to load.
3. **Reveal contacts (separate calls)**: eye icons update the DOM asynchronously. Split into TWO calls:
   - Call 1: click all `document.querySelectorAll('.invite-detail-drawer span.d-icon.cursor-animation')` that contain an `<svg>`.
   - Wait 600–800ms (`await new Promise(r => setTimeout(r, 700))`).
   - Call 2: read the now-revealed `.item-right` text content.
   Do NOT click and read in the same JS execution — you will read stale (masked) values.
4. **Read fields**: extract only blogger contact fields from the drawer:
```js
(function() {
  let d = document.querySelector('.invite-detail-drawer');
  let name = d.querySelector('.kol-info a')?.textContent?.trim() || '';
  let link = d.querySelector('.kol-info a')?.getAttribute('href') || '';
  let fields = d.querySelectorAll('.flex.gap-16');
  let vals = {};
  for (let f of fields) {
    let l = f.querySelector('.item-left')?.textContent?.trim() || '';
    let v = f.querySelector('.item-right')?.textContent?.trim() || '';
    v = v.replace(/ 联系方式属于博主的重要个人信息.*$/, '').trim();
    if (l.includes('博主')) vals[l] = v;
  }
  return JSON.stringify({ name: name, pgy: 'https://pgy.xiaohongshu.com' + link, vals: vals });
})()
```
5. **Close the drawer** before moving to the next row.

### What to extract and what NOT to extract

**Extract** (博主信息 only):
- `达人昵称` — from `.kol-info a` text
- `达人蒲公英地址` — `https://pgy.xiaohongshu.com` + `.kol-info a` href
- `手机号` — the `博主手机号` field value (may be empty)
- `微信号` — the `博主微信` field value (may be empty)
- `博主意向` — e.g. 感兴趣
- `邀约发起时间` / `邀约回复时间` — from the detail drawer or the table row

**Do NOT extract** (these are 基本信息, not 博主信息, and the user does not want them):
- 合作类型, 笔记报价, 期望笔记发布时间
- 品牌名, 品牌联系电话
- 产品名称, 合作内容介绍

### Raw JSON format for the append script
The bundled `append_xhs_kol_info.py` expects **Chinese field names** that match the canonical Excel headers. Always save raw extracted data with these exact keys:
```json
{
  "达人昵称": "FANDEAR®",
  "达人蒲公英地址": "https://pgy.xiaohongshu.com/solar/advertiser/kol/59f3adf64eacab4c4f1384cf",
  "手机号": "15113512769",
  "微信号": "Fc56812",
  "博主意向": "感兴趣",
  "邀约发起时间": "2026-07-07 16:32:15",
  "邀约回复时间": "2026-07-08 00:01:40",
  "原跟进状态": "未跟进"
}
```
Do NOT use English keys like `name`, `phone`, `wechat`, `pgy` — the append script will silently misinterpret them.

8. Save raw extracted rows to timestamped JSON under `./artifacts/` before writing Excel.
9. Call `browser.tabs.finalize({})` after the read is complete.

## Append workflow
Use this path when the user asks to append to an existing workbook such as `artifacts/xhs-kol-info-unfollowed.xlsx`.
1. Never overwrite blindly. The bundled append script creates a timestamped backup automatically.
2. Read the canonical headers from the existing workbook to understand its current structure.
3. Find the last real data row by the `达人昵称` column, not by `max_row`.
4. Deduplicate invite records by `达人昵称 + 达人蒲公英地址 + 邀约发起时间 + 邀约回复时间`. Preserve duplicate nicknames when the invite timestamps differ.
5. Renumber `序号` continuously from existing real rows.
6. Run the bundled append helper with Chinese-field raw JSON:
```bash
python3 /Users/hzd/.agents/skills/xhs-kol-info/scripts/append_xhs_kol_info.py --input <raw-json> --workbook artifacts/xhs-kol-info-unfollowed.xlsx
```
7. Verify with `openpyxl.load_workbook`: sheet name, headers, data row count, non-empty names, and unique names.

## Safety and anti-control behavior
- Process rows serially. Do not parallelize requests or open many detail drawers at once.
- Keep human-like pacing: randomized waits, scroll selected rows into view, click by visible coordinates, and close each drawer before opening the next.
- Only mark rows as `已跟进` when `--mark-followed` is passed. When marking, only click the follow-status dropdown mutation needed. Do not click 发起合作, 添加至已选博主, submit buttons, or unrelated mutations.
- If the page shows captcha, login wall, risk-control, abnormal behavior, or network/auth errors, stop immediately and ask the user to handle it manually in Chrome.
- Treat phone and WeChat values as sensitive personal information. Only return/export the fields the user asked for.

## Expected output fields
The Excel should include at least:
- `序号`
- `达人昵称`
- `达人蒲公英地址`
- `手机号`
- `微信号`
- `博主意向`
- `邀约发起时间`
- `邀约回复时间`
- `原跟进状态`
- `跟进状态更新`
- `读取状态`
- `读取时间`

## Troubleshooting
- Check Chrome CDP availability with `curl http://127.0.0.1:<port>/json/list`. If no port is open, Computer Use/Chrome being connected is not enough for this script; the script needs Chrome to expose a remote debugging port. Use the known port with `--port <port>` or launch a Chrome debugging session before running the export.
- If the user has Chrome open but no local CDP port exists, do not stop immediately. Use the Chrome extension path above; it can read the already-open tab through the tab `cdp` capability without `127.0.0.1:9222`.
- If WebSocket is rejected with Origin 403, the script uses `suppress_origin=True`; do not add a browser restart unless this stops working.
- If the first page count changes while reading, trust the drawer detail text for contact fields and the row text for list ordering.
- When `--mark-followed` is used, the script processes the first visible `未跟进 + 感兴趣` row repeatedly instead of caching row indexes. This is intentional: after marking one KOL as `已跟进`, the filtered list may remove it and shift the next KOL upward. When `--mark-followed` is NOT used (default), the script reads rows in order from the list without marking them.
- If a workbook appears to have many rows but `达人昵称` is blank, treat them as ghost rows and clean them before appending.
- **Chrome extension randomly disconnects**: `claimTab` and `openTabs` intermittently time out (30–90s). If this happens, ask the user to restart Chrome, then re-do `setupBrowserRuntime` + `openTabs` + `claimTab` in a SINGLE call. The user's page state is preserved across Chrome restarts.
- **Eye icon click didn't reveal the value**: you clicked and read in the same JS execution. Always separate the click and the read into two CDP calls with a 600–800ms delay between them.
- **Drawer shows stale content from previous row**: always close the drawer and wait ≥400ms before clicking the next row's 查看详情. The drawer recycles DOM nodes; without a close+wait you read the previous row's data.
- **`Identifier 'x' has already been declared`**: wrap browser code in `{ }` block scope or reset the JS kernel before continuing.
