#!/usr/bin/env python3
"""核对评价京豆：读评价中心头部「已写评价 / 已获京豆」计数。

用法:
  python3 jd_check.py --session jd            # 读当前值
  python3 jd_check.py --session jd --save     # 并存到 state/counter.json，供下次比对基线

说明：京豆明细页 bean.m.jd.com 经常返回"网络连接不佳"，取不到就以本页计数为准，
并在汇报里标注为待精确核对。评价审核存在延迟，数字可能滞后上涨。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pw  # noqa: E402

CENTER = "https://comment.m.jd.com/pc-static/center"
STATE = Path(__file__).resolve().parent.parent / "state" / "counter.json"


def read(session: str) -> dict:
    raw = str(pw.ev(session, pw.COUNTER_JS))
    try:
        return json.loads(raw)
    except Exception:
        return {"_raw": raw}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="jd")
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--reload", action="store_true", help="先 goto 评价中心再读")
    a = ap.parse_args()

    if a.reload:
        pw.cli(a.session, "goto", CENTER, timeout=120)
        time.sleep(6)
    cur = read(a.session)
    if "_raw" in cur or not cur.get("beans"):
        print(f"读不到计数：{cur}\n请先确认已登录且页面在评价中心（见 SKILL.md 前置条件）",
              file=sys.stderr)
        return 2

    prev = {}
    if STATE.exists():
        try:
            prev = json.loads(STATE.read_text(encoding="utf-8"))[-1]
        except Exception:
            prev = {}
    hist = []
    if STATE.exists():
        try:
            hist = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            hist = []
    if a.save:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        hist.append(cur)
        STATE.write_text(json.dumps(hist, ensure_ascii=False, indent=1), encoding="utf-8")

    print(json.dumps(cur, ensure_ascii=False))
    if prev.get("beans"):
        print(f"较上次记录：评价 {prev['wrote']} -> {cur['wrote']} (+{int(cur['wrote']) - int(prev['wrote'])})，"
              f"京豆 {prev['beans']} -> {cur['beans']} (+{int(cur['beans']) - int(prev['beans'])})")
    print(f"剩余：可领京豆 {cur['pendingWithBeans']} 条，无京豆奖励 {cur['pendingNoBeans']} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
