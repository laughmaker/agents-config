#!/usr/bin/env python3
"""批量拟人化提交京东待评价，带断点续跑和风控节奏控制。

安全默认值（可在调用时放宽，但要先跟用户确认）：
  --limit 8            单次运行最多提交条数
  每条之间 25-70s，每 4 条额外 60-180s 长停顿
  连续 2 条失败即中止，不硬闯

文案：优先用 --texts-file（用户提供的真实感受，JSON {orderId: "文案"}）。
没有时从模板池按商品名做差异化轮换，**同一模板对同一商品不重复使用**——
京东规则把"与自己过去内容重复度较高"列为不发奖励的情形。

用法:
  python3 jd_run.py --session jd --todo ~/tmp/jd_todo.json --limit 8
  python3 jd_run.py --session jd --texts-file ~/tmp/my_words.json
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import time  # noqa: E402
import pw  # noqa: E402
from jd_publish import publish_once  # noqa: E402
import time  # noqa: E402

PUBLISH_URL = ("https://comment.m.jd.com/pc-static/publish"
               "?orderId={order}&skuId={sku}&commentType=1")
STATE = Path(__file__).resolve().parent.parent / "state" / "published.json"

# 中性、可通用的观察句式；调用方有更具体的真实体验时应覆盖。
TEMPLATES = [
    "收到了，{k}和页面描述一致，包装完好没有破损。",
    "{k}没问题，日常使用够用，发货和到货都正常。",
    "东西收到了，{k}正常，先给个基础评价，用一段时间再补充。",
    "按页面说明买的，{k}对得上，物流时效正常，暂时没发现问题。",
    "已收货，{k}与预期一致，做工正常，后续有情况再来追评。",
    "{k}都符合描述，家里够用，包装没有挤压痕迹。",
]
STOPWORDS = {"（", "）", "【", "】", "/", "，", "。"}


def keyword(name: str) -> str:
    """从商品名里挑一个短词做差异化，避免整批同一句。"""
    toks = [t for t in (name or "").replace("  ", " ").split(" ") if len(t) > 1]
    cand = [t for t in toks if not any(c in STOPWORDS for c in t)]
    pick = (cand or toks or [name or "商品"])[0][:10]
    return pick


def build_text(name: str, used: set[str]) -> str:
    pool = list(TEMPLATES)
    random.shuffle(pool)
    for tpl in pool:
        t = tpl.format(k=keyword(name))
        if len(t) >= 14 and t not in used:
            used.add(t)
            return t
    t = random.choice(TEMPLATES).format(k=keyword(name))
    used.add(t)
    return t


def load_state() -> list[dict]:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_state(rec: list[dict]) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="jd")
    ap.add_argument("--todo", default=str(Path.home() / "tmp/jd_todo.json"))
    ap.add_argument("--texts-file", default="", help="JSON {orderId: 真实评价文案}")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true", help="只验证链路，不发布不记账")
    ap.add_argument("--include-no-reward", action="store_true",
                    help="连 est=0 的商品也评（默认跳过，不发京豆）")
    a = ap.parse_args()

    todo = json.loads(Path(a.todo).expanduser().read_text(encoding="utf-8"))
    custom = {}
    if a.texts_file:
        custom = json.loads(Path(a.texts_file).expanduser().read_text(encoding="utf-8"))
    rec = load_state()
    done = set()
    for r in rec:  # 兼容旧格式 [orderId, wareId, est, name]
        done.add(r[0] if isinstance(r, list) else r.get("orderId"))

    items = [t for t in todo
             if t["orderId"] not in done
             and (a.include_no_reward or int(t.get("est") or 0) > 0)
             and t.get("orderId") and t.get("wareId")]
    if a.limit > 8:
        print(f"注意：--limit {a.limit} 超过默认安全值 8，风控与文案重复风险上升", flush=True)
    items = items[:a.limit]
    if not items:
        print("没有待提交条目（可能都已记录在 state/published.json）")
        return 0
    print(f"本轮计划提交 {len(items)} 条，标注额度合计 {sum(int(i['est']) for i in items)} 京豆",
          flush=True)

    before = str(pw.ev(a.session, pw.COUNTER_JS))
    print(f"基线 {before}", flush=True)

    used_texts: set[str] = set()
    fails = 0
    for i, it in enumerate(items, 1):
        text = custom.get(it["orderId"]) or build_text(it["name"], used_texts)
        pw.cli(a.session, "goto",
               PUBLISH_URL.format(order=it["orderId"], sku=it["wareId"]), timeout=120)
        pw.sleep(3.5, 7.0)
        pw.human_scroll(a.session)
        status, note = publish_once(a.session, "1", text, a.dry_run)
        if a.dry_run:
            print(f"  [dry] {it['orderId']} -> {status} ({note})")
            pw.cli(a.session, "goto", "https://comment.m.jd.com/pc-static/center", timeout=120)
            continue
        print(f"[{i}/{len(items)}] {it['orderId']} {(it['name'] or '')[:20]} "
              f"est={it['est']} -> {status} ({note})", flush=True)
        if status == "OK":
            rec.append({"orderId": it["orderId"], "wareId": it["wareId"],
                        "est": int(it["est"]), "name": it["name"], "text": text})
            save_state(rec)
            fails = 0
        else:
            fails += 1
            if fails >= 2:
                print("连续失败 2 条，疑似风控介入，本轮中止。请隔几小时再跑，"
                      "或让用户在 App 里手动评几条。", file=sys.stderr)
                break
        if i < len(items):
            w = pw.sleep(25.0, 70.0)
            if i % 4 == 0:
                w += pw.sleep(60.0, 180.0)
            print(f"  休息 {w:.0f}s", flush=True)

    pw.cli(a.session, "goto", "https://comment.m.jd.com/pc-static/center", timeout=120)
    time.sleep(6)
    after = str(pw.ev(a.session, pw.COUNTER_JS))
    print(f"计数 前 {before} -> 后 {after}（京豆为累计值，审核有延迟，以页面为准）", flush=True)
    print(f"state 已写入 {STATE}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
