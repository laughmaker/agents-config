#!/usr/bin/env python3
"""拟人化提交一条京东评价（或追评），并校验是否真正发布成功。

反风控要点（都是实测出来的，不要精简）：
  1) 进页面后先随机停顿 + 随机滚动，模拟先看再动。
  2) 正文用 CLI `type` 真实逐字键入，按 3-7 字片段切分，片段间随机间隔；
     直接把整段字符串 set 进 textarea（等效粘贴）实测会触发 403。
  3) 小概率按 Backspace 再补输，模拟打错改稿。
  4) 提交用 hover + click 真实点击；JS 里 el.click() 合成事件实测 403。
  5) 成功判定读页面文本「评价成功」，不看 HTTP 状态。
  6) 失败冷却 40-90s 后重试 1 次；仍失败就交给上层停止。

用法:
  python3 jd_publish.py --session jd --order <订单号> --sku <商品ID> \
      --text "评价正文"
  追评加 --type 2（同订单多商品合并评价用 --type 5，sku 用逗号连接）
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pw  # noqa: E402

PUBLISH_URL = ("https://comment.m.jd.com/pc-static/publish"
               "?orderId={order}&skuId={sku}&commentType={ctype}")
TA = "textarea.rate-comment-content-textarea"


def type_human(session: str, text: str) -> tuple[bool, int]:
    """真实逐字键入。返回 (textarea 是否存在, 最终字数)。"""
    probe = pw.ev(session, pw.TA_LEN_JS)
    if "NO-TEXTAREA" in str(probe):
        return False, 0
    pw.real_click(session, TA)               # 聚焦：hover + click 真实事件
    pw.sleep(0.8, 2.0)

    chunks: list[str] = []
    i = 0
    while i < len(text):
        n = random.randint(3, 7)
        chunks.append(text[i:i + n])
        i += n
    for c in chunks:
        pw.cli(session, "type", c, timeout=60)
        pw.sleep(0.35, 1.5)
        if random.random() < 0.10:           # 打错再改
            pw.cli(session, "press", "Backspace", timeout=60)
            pw.sleep(0.3, 0.9)
            pw.cli(session, "type", c[-1:], timeout=60)
        if random.random() < 0.18:           # 停顿想措辞
            pw.sleep(1.8, 4.0)
    got = str(pw.ev(session, pw.TA_LEN_JS)).replace("LEN", "")
    try:
        return True, int(got or 0)
    except ValueError:
        return True, 0


def publish_once(session: str, ctype: str, text: str, dry_run: bool = False) -> tuple[str, str]:
    ok, n = type_human(session, text)
    if not ok:
        return "NO-TEXTAREA", "form 未加载"
    if n == 0:
        return "EMPTY", "键入后正文为空"
    pw.human_scroll(session)                 # 写完再看一眼页面
    pw.ev(session, pw.STARS_JS)              # 读评分项（默认已是"非常好"）
    if dry_run:
        return "DRY-RUN", f"chars={n},未点击发布"
    pw.sleep(4.0, 10.0)                      # 「读完再发」的停顿
    ref = pw.find_ref(session, "发布追评" if ctype == "2" else "发布")
    res = pw.real_click(session, ref or ".rate-publish-submit-button")
    pw.sleep(4.5, 8.0)
    return str(pw.ev(session, pw.DONE_JS)), f"chars={n},click={res}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="jd")
    ap.add_argument("--order", required=True)
    ap.add_argument("--sku", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--type", dest="ctype", default="1", choices=["1", "2", "5"])
    ap.add_argument("--tries", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true",
                    help="走完拟人键入流程但不点发布，用于验证链路")
    a = ap.parse_args()

    if len(a.text) < 10:
        print("正文不足 10 字，按规则不会发豆，跳过", file=sys.stderr)
        return 3

    for attempt in range(1, a.tries + 1):
        pw.cli(a.session, "goto",
               PUBLISH_URL.format(order=a.order, sku=a.sku, ctype=a.ctype), timeout=120)
        pw.sleep(3.5, 7.0)
        status, note = publish_once(a.session, a.ctype, a.text, a.dry_run)
        if a.dry_run:
            print(f"[dry] {a.order} -> {status} ({note})")
            return 0 if status == "DRY-RUN" else 1
        print(f"[try {attempt}] {a.order} {a.sku} -> {status} ({note})", flush=True)
        if status == "OK":
            print(f"RESULT=OK {a.order} {a.sku}")
            return 0
        if attempt < a.tries:
            w = pw.sleep(40.0, 90.0)         # 多为限流，等一会再试
            print(f"  冷却 {w:.0f}s 后重试", flush=True)

    print("RESULT=FAIL", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
