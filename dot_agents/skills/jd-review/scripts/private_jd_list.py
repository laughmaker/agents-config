#!/usr/bin/env python3
"""读取京东评价中心待评价清单（含真实 orderId / skuId / 可领京豆）。

不自己构造 h5st 签名：让页面自己发 getUserAggregateCommentList，再从 playwright-cli
的网络日志里把响应体捞回来。翻页也靠真实滚动页面容器触发。

用法:
  python3 jd_list.py --session jd --out ~/tmp/jd_todo.json [--pages 3]
输出 JSON: [{orderId, wareId, name, est, comment, discuss, status}]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pw  # noqa: E402

CENTER = "https://comment.m.jd.com/pc-static/center"
FN = "getUserAggregateCommentList"

# 让页面自己请求第 N 页：真实滚动滚动容器到底部，触发懒加载。
SCROLL_BOTTOM_JS = (
    "(() => { const els=[...document.querySelectorAll('*')]"
    ".filter(e=>e.scrollHeight>e.clientHeight+200&&e.clientHeight>300); els.forEach(e=>{"
    "for(let i=0;i<3;i++){ e.scrollTop=e.scrollHeight; } });"
    "window.scrollTo(0, document.body.scrollHeight); return els.length; })()"
)

def req_ids(session: str) -> list[int]:
    """返回可能调用过清单接口的请求序号。

    清单接口是 POST https://api.m.jd.com/client.action，functionId 在 **请求体** 里，
    `requests` 输出的 URL 上没有，所以只能先按 client.action 收窄，再逐条读 body 确认。
    """
    out = pw.cli(session, "requests", timeout=90)
    ids: list[int] = []
    cur = None
    for line in out.splitlines():
        m = re.match(r"^\s*(\d+)\.\s*\[(GET|POST)\]", line)
        if m:
            cur = int(m.group(1))
        if cur is not None and "client.action" in line and cur not in ids:
            ids.append(cur)
    return ids


def is_list_request(session: str, idx: int) -> bool:
    body = str(pw.raw(session, "request-body", str(idx), timeout=60))
    return FN in body


def fetch(session: str, idx: int) -> dict | None:
    body = pw.raw(session, "response-body", str(idx), timeout=90)
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except Exception:
            return None
    return body if isinstance(body, dict) else None


def parse(resp: dict) -> tuple[list[dict], dict]:
    res = resp.get("result") or {}
    info = res.get("userCommentListInfo") or {}
    rows: list[dict] = []
    for o in info.get("userCommentList") or []:
        for it in o.get("userAggregateCommentList") or []:
            rows.append({
                "orderId": it.get("orderId"),
                "wareId": it.get("wareId"),
                "name": it.get("wname"),
                "est": int(it.get("estJingBean") or 0),
                "comment": int(it.get("estCommentJingBean") or 0),
                "discuss": int(it.get("estDiscussionJingBean") or 0),
                "status": it.get("jingBeanOrAuditStatus") or "",
                "hasReward": bool(it.get("rewardList")),
            })
    meta = {
        "tabs": res.get("tabList"),
        "countInfo": info.get("commentCountInfo"),
        "header": (res.get("commentOfficerInfo") or {}).get("officerLevelInfo") or {},
    }
    return rows, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="jd")
    ap.add_argument("--out", default=str(Path.home() / "tmp/jd_todo.json"))
    ap.add_argument("--pages", type=int, default=2, help="最多翻几页（真实滚动触发）")
    a = ap.parse_args()

    seen = pw.cli(a.session, "--raw", "eval", "1+1", timeout=60)
    if not seen.strip():
        print("会话不可用：先 open/goto 评价中心（见 SKILL.md 前置条件）", file=sys.stderr)
        return 2

    print(f"打开 {CENTER}", flush=True)
    pw.cli(a.session, "goto", CENTER, timeout=120)
    time.sleep(6)

    rows: dict[tuple, dict] = {}
    meta = {}
    seen: set[int] = set()   # 首轮扫描全部 client.action，之后只看本轮新增
    found = 0
    for attempt in range(1, a.pages + 2):
        new = [i for i in req_ids(a.session) if i not in seen]
        seen.update(new)
        hit = False
        for i in new:
            if not is_list_request(a.session, i):
                continue
            hit = True
            resp = fetch(a.session, i)
            if not resp:
                continue
            r, m = parse(resp)
            meta = m or meta
            for x in r:
                rows[(x["orderId"], x["wareId"])] = x
            found += 1
        print(f"  第 {attempt} 轮：抓到清单响应 {found} 个，累计 {len(rows)} 条", flush=True)
        if not hit and attempt > 1:
            break
        if attempt <= a.pages:
            pw.ev(a.session, SCROLL_BOTTOM_JS)
            time.sleep(4)
            pw.human_scroll(a.session, times=1)
            pw.ev(a.session, SCROLL_BOTTOM_JS)
            time.sleep(4)

    items = list(rows.values())
    out = Path(a.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")

    with_b = [x for x in items if x["est"] > 0]
    print(json.dumps(meta.get("tabs"), ensure_ascii=False))
    print(f"待评价 {len(items)} 条，其中可领京豆 {len(with_b)} 条，"
          f"标注额度合计 {sum(x['est'] for x in with_b)} 京豆 -> {out}")
    for x in with_b:
        print(f"  {x['orderId']} {x['wareId']} est={x['est']} 文字={x['comment']} 晒图={x['discuss']} {(x['name'] or '')[:26]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
