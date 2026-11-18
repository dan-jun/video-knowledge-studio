# -*- coding: utf-8 -*-
"""polyphone.py —— 配音前的多音字守门员

背景：工坊配音走 edge-tts / MiniMax，**都不支持拼音标注或 SSML 音素标签**，
没法指定读第几声。所以只能：① 把正确读音写清楚（`polyphone.txt`）；
② 配音前扫口播稿，把「同形不同音、两种读法都常见」的词按风险挑出来；
③ 需要时改文案（唯一能真正影响 TTS 的手段）。

用法：
    python tools/polyphone.py check <storyboard.json | 目录 | 文本文件 | "一段文本">
    python tools/polyphone.py check <storyboard.json> --strict     # 有高风险就返回非零（门禁用）
    python tools/polyphone.py fix <storyboard.json> --replace "长序列=很长的序列" [--dry-run]

note: fix 只做你显式给出的替换（不搞自动建议——机械替换会长出「模型模型权重」这种东西）。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
TABLE = os.environ.get("POLYPHONE_TABLE") or os.path.join(HERE, "polyphone.txt")
RISK_ORDER = {"高": 0, "中": 1, "低": 2}


def load_table(path: str = TABLE) -> list[dict]:
    rows: list[dict] = []
    if not os.path.isfile(path):
        return rows
    for raw in open(path, encoding="utf-8"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3 or not parts[0]:
            continue
        rows.append({
            "word": parts[0],
            "pinyin": parts[1],
            "note": parts[2],
            "risk": parts[3] if len(parts) > 3 and parts[3] in RISK_ORDER else "低",
        })
    return rows


def _context(text: str, word: str, width: int = 12) -> str:
    i = text.find(word)
    if i < 0:
        return ""
    a, b = max(0, i - width), min(len(text), i + len(word) + width)
    return ("…" if a > 0 else "") + text[a:b].replace("\n", " ") + ("…" if b < len(text) else "")


def scan_text(text: str, table: list[dict]) -> list[dict]:
    hits = []
    for r in table:
        n = text.count(r["word"])
        if n:
            hits.append({**r, "count": n, "context": _context(text, r["word"])})
    # 长词命中就把被它包含的短词去掉（卷积核 已报，就不再单独报 卷积）
    return [h for h in hits
            if not any(o is not h and h["word"] in o["word"] and o["count"] >= h["count"] for o in hits)]


def _iter_texts(target: str):
    """(标签, 文本)：支持 storyboard / 目录 / 文本文件 / 直接给一段话。"""
    if os.path.isdir(target):
        for dp, _dn, fn in os.walk(target):
            for f in fn:
                if f.lower().endswith((".json", ".txt", ".md")):
                    p = os.path.join(dp, f)
                    yield p, open(p, encoding="utf-8", errors="replace").read()
        return
    if os.path.isfile(target):
        raw = open(target, encoding="utf-8", errors="replace").read()
        if target.lower().endswith(".json"):
            try:
                data = json.loads(raw)
            except Exception:  # noqa: BLE001
                yield target, raw
                return
            found = False
            for part in data.get("parts") or []:
                for page in part.get("pages") or []:
                    nar = page.get("narration")
                    if isinstance(nar, str) and nar:
                        found = True
                        yield f"{(page.get('id') or part.get('part') or '?')}", nar
            if not found:
                yield target, raw
            return
        yield target, raw
        return
    yield "<文本>", target


def cmd_check(a) -> int:
    table = load_table()
    if not table:
        print(json.dumps({"ok": False, "reason": f"读音表为空或不存在：{TABLE}"}, ensure_ascii=False))
        return 2
    hits = []
    for label, text in _iter_texts(a.target):
        for h in scan_text(text, table):
            hits.append({"where": label, **h})
    hits.sort(key=lambda x: (RISK_ORDER.get(x["risk"], 3), x["word"]))
    high = [h for h in hits if h["risk"] == "高"]
    print(json.dumps({
        "ok": True,
        "table": os.path.basename(TABLE),
        "hits": len(hits),
        "high_risk": len(high),
        "items": hits,
        "hint": "风险=高 的优先处理：要么改文案，要么配音后人工听一遍这几个词",
    }, ensure_ascii=False, indent=2))
    if a.strict and high:
        return 1
    return 0


def cmd_fix(a) -> int:
    if not os.path.isfile(a.storyboard):
        print(json.dumps({"ok": False, "reason": "需要 storyboard.json 路径"}, ensure_ascii=False))
        return 2
    pairs = []
    for item in a.replace or []:
        if "=" in item:
            src, dst = item.split("=", 1)
            if src.strip():
                pairs.append((src.strip(), dst.strip()))
    if not pairs:
        print(json.dumps({"ok": False, "reason": "没有给 --replace，拒绝改动（本命令不做自动建议）"},
                         ensure_ascii=False))
        return 2
    data = json.load(open(a.storyboard, encoding="utf-8"))
    changed = []
    for part in data.get("parts") or []:
        for page in part.get("pages") or []:
            nar = page.get("narration")
            if not isinstance(nar, str) or not nar:
                continue
            new = nar
            for src, dst in pairs:
                if src in new:
                    new = new.replace(src, dst)
                    changed.append({"page": page.get("id"), "from": src, "to": dst})
            page["narration"] = new
    if not changed:
        print(json.dumps({"ok": True, "changed": 0}, ensure_ascii=False))
        return 0
    if a.dry_run:
        print(json.dumps({"ok": True, "dry_run": True, "changed": len(changed), "items": changed},
                         ensure_ascii=False, indent=2))
        return 0
    shutil.copy2(a.storyboard, a.storyboard + ".bak")
    open(a.storyboard, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2))
    print(json.dumps({"ok": True, "changed": len(changed), "items": changed,
                      "backup": a.storyboard + ".bak"}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="配音前的多音字检查 / 显式改写")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="扫口播稿，列出多音词、读音与风险")
    c.add_argument("target")
    c.add_argument("--strict", action="store_true", help="有高风险就返回非零（供门禁使用）")
    f = sub.add_parser("fix", help="按显式 --replace 改写（改前备份）")
    f.add_argument("storyboard")
    f.add_argument("--replace", action="append", help="形如 长序列=很长的序列，可多次")
    f.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    return {"check": cmd_check, "fix": cmd_fix}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
