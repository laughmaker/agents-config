"""playwright-cli 会话封装：所有脚本共用。

设计要点（实测踩坑）：
- 参数用 list 传给 subprocess，绝不过 shell，中文无需转义。
- `--raw eval` 的返回值是被 JSON 引号包裹的一行；解析函数负责剥壳。
- 传给 eval 的 JS 里**不能含真实换行**，中文字面量在模板里用 \\uXXXX，
  否则 CLI 会把 JS 截断成 `at UtilityScript.<anonymous> (<anonymous>:1:44)` 这类报错。
- 交互一律走真实命令（click/hover/type），不要用 eval 里的 el.click()：
  合成 click 不产生鼠标事件，实测触发京东风控 403。
"""
from __future__ import annotations

import json
import random
import re
import subprocess
import time

BIN = ["npx", "--yes", "@playwright/cli@latest"]


def cli(session: str, *args: str, timeout: int = 120) -> str:
    cmd = BIN + ["-s=" + session] + list(args)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "__TIMEOUT__"
    return p.stdout or ""


def raw(session: str, *args: str, timeout: int = 120) -> str:
    """`--raw` 输出解析：返回最后一行，剥掉 JSON 双引号。"""
    out = cli(session, "--raw", *args, timeout=timeout).strip()
    if not out:
        return ""
    for line in reversed(out.splitlines()):
        line = line.strip()
        if line and not line.startswith("```"):
            try:
                return json.loads(line)
            except Exception:
                return line.strip('"')
    return ""


def ev(session: str, js: str, timeout: int = 60) -> str:
    return raw(session, "eval", " ".join(js.split("\n")), timeout=timeout)


def sleep(a: float, b: float) -> float:
    d = random.uniform(a, b)
    time.sleep(d)
    return d


def human_scroll(session: str, times: int | None = None) -> None:
    """随机上下滚动，模拟先看页面再操作。"""
    n = times if times is not None else random.randint(2, 4)
    for _ in range(n):
        dy = random.randint(-80, 260)
        ev(session, "(() => { window.scrollBy(0, %d); return 1; })()" % dy)
        sleep(0.6, 2.4)


STARS_JS = (
    "(() => { const rows=[...document.querySelectorAll('.scoreBox-conter-score')];"
    "return JSON.stringify(rows.map(r=>r.innerText.replace(/[\\r\\n]+/g,'|'))); })()"
)

TA_LEN_JS = (
    "(() => { const ta=document.querySelector('textarea.rate-comment-content-textarea');"
    "if(!ta) return 'NO-TEXTAREA'; return 'LEN'+ta.value.length; })()"
)

DONE_JS = (
    "(() => { const t=document.body.innerText;"
    "if(t.indexOf('\\u8bc4\\u4ef7\\u6210\\u529f')>=0) return 'OK';"
    "if(t.indexOf('\\u53d1\\u5e03\\u8ffd\\u8bc4')>=0) return 'APPEND-FORM';"
    "return 'NOT-PUBLISHED'; })()"
)

COUNTER_JS = (
    "(() => { const t=document.body.innerText.replace(/[\\r\\n]+/g,'|');"
    "const m=t.match(/(\\d+)\\|\\u5df2\\u5199\\u8bc4\\u4ef7\\|(\\d+)\\|\\u5df2\\u83b7\\u4eac\\u8c46/);"
    "const go=(t.match(/\\u53bb\\u8bc4\\u4ef7/g)||[]).length;"
    "const goB=(t.match(/\\u53bb\\u8bc4\\u4ef7\\|\\d+\\u4eac\\u8c46/g)||[]).length;"
    "return JSON.stringify({wrote:m&&+m[1], beans:m&&+m[2], logged:!!m,"
    "pendingTotal:go, pendingWithBeans:goB, pendingNoBeans:Math.max(0, go-goB)}); })()"
)


def find_ref(session: str, text: str, last: bool = True) -> str | None:
    """用 CLI `find <文本>` 在实时快照里取文本节点 ref，避免引用过期。"""
    out = cli(session, "find", text, timeout=90)
    refs = re.findall(r"\[ref=([A-Za-z0-9]+)\](?: \[cursor=pointer\])?: %s\s*$" % re.escape(text),
                      out, flags=re.M)
    if not refs:
        refs = re.findall(r"\[ref=([A-Za-z0-9]+)\][^\n:]*: %s" % re.escape(text), out)
    if not refs:
        return None
    return refs[-1] if last else refs[0]


def real_click(session: str, target: str) -> str:
    """hover 再 click，产生真实鼠标轨迹事件。"""
    raw(session, "hover", target)
    sleep(0.5, 1.6)
    out = cli(session, "click", target, timeout=90)
    return "ERR" if "__TIMEOUT__" in out or "Error" in out else "OK"
