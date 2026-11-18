# -*- coding: utf-8 -*-
"""Validate a storyboard against notes/stage2-contract.md (§3 schema + §5 checklist).

Usage: python validate_storyboard.py storyboard.json
Exit code 0 = no errors (warnings allowed), 1 = errors.
"""
import json
import re
import sys

# kit = anim_kit 手法页（anim_gen 负责生成、check_kit_args 负责校验参数）
# 2026-11-16：之前漏了 "kit"，导致所有 anim_kit 项目在这里必红（10/10 页报错）
ALLOWED_TYPES = {"title", "bullets", "code", "diagram", "quiz", "answer", "recap", "kit"}
FORBIDDEN = ["综上所述", "值得注意的是", "众所周知", "显而易见"]
CITE_RE = re.compile(r"^S\d+\s+p\d+\s+(?:\d{1,2}:)?\d{1,2}:\d{2}$")
MARKDOWN_HINTS = ["**", "`", "##", "- [", "]("]


def flatten(sb):
    if "pages" in sb:
        return sb["pages"]
    out = []
    for part in sb.get("parts", []):
        for p in part.get("pages", []):
            p.setdefault("part", part.get("part"))
            out.append(p)
    return out


def strip_ws(s):
    return re.sub(r"\s+", "", s)


def main():
    path = sys.argv[1]
    sb = json.load(open(path, encoding="utf-8"))
    pages = flatten(sb)
    errors, warns = [], []

    if not pages:
        print("ERROR: no pages")
        return 1

    # per-part page count
    by_part = {}
    for p in pages:
        by_part.setdefault(p.get("part") or "-", []).append(p)
    for part, ps in by_part.items():
        if not (4 <= len(ps) <= 8):
            warns.append(f"[页数] 「{part}」有 {len(ps)} 页，契约建议 4–8 页")

    seen_ids = set()
    total_chars = 0
    for i, p in enumerate(pages, 1):
        pid = p.get("id") or f"#{i}"
        if pid in seen_ids:
            errors.append(f"[id] 重复 page id: {pid}")
        seen_ids.add(pid)

        nar = p.get("narration", "")
        n_chars = len(strip_ws(nar))
        total_chars += n_chars
        if not (60 <= n_chars <= 100):
            warns.append(f"[字数] {pid} narration {n_chars} 字（建议 60–100）：{nar[:24]}…")

        for bad in FORBIDDEN:
            if bad in nar:
                errors.append(f"[禁用词] {pid} 出现「{bad}」")
        for mk in MARKDOWN_HINTS:
            if mk in nar:
                errors.append(f"[格式] {pid} narration 含 Markdown 片段「{mk}」")
        if re.search(r"\[S\d+", nar):
            errors.append(f"[格式] {pid} narration 残留来源标记")

        v = p.get("visual") or {}
        vt = v.get("type")
        if vt not in ALLOWED_TYPES:
            errors.append(f"[视觉] {pid} type={vt} 不在 {sorted(ALLOWED_TYPES)}")
        if vt == "kit" and not str(v.get("kit") or "").strip():
            # kit 页必须声明手法名，否则 anim_gen 生成不了场景
            errors.append(f"[视觉] {pid} 是 kit 页，但没写 kit 手法名")
        if vt == "code":
            n_lines = len((v.get("code") or "").split("\n"))
            if n_lines > 14:
                errors.append(f"[视觉] {pid} code {n_lines} 行 > 14")
        if vt == "diagram":
            steps = v.get("steps") or []
            if len(steps) > 5:
                errors.append(f"[视觉] {pid} steps {len(steps)} 个 > 5")
            if len(steps) < 2:
                warns.append(f"[视觉] {pid} diagram 只有 {len(steps)} 个 step")

        cites = p.get("cites") or []
        if not cites:
            errors.append(f"[取证] {pid} 没有 cites")
        for c in cites:
            if not CITE_RE.match(c.strip()):
                warns.append(f"[取证] {pid} cite 格式可疑：「{c}」（应为 `S# pNN mm:ss`）")

        # 练习题：题目与答案分两页，题目页必须口播「暂停三秒」，答案页不得复述题干
        if vt == "quiz":
            if ("暂停" not in nar) or not any(k in nar for k in ("三秒", "3 秒", "3秒")):
                errors.append(f"[练习] {pid} 是题目页，但 narration 没口播「暂停三秒」提示")
            nxt = pages[i] if i < len(pages) else None
            if not nxt or (nxt.get("visual") or {}).get("type") != "answer":
                errors.append(f"[练习] {pid} 题目页后面没有紧跟 answer 页（题目与答案必须分开的两页）")
            if not (v.get("question") or []):
                errors.append(f"[练习] {pid} quiz 页缺少 question 字段")
        if vt == "answer":
            prev = pages[i - 2] if i >= 2 else None
            if prev and (prev.get("visual") or {}).get("type") == "quiz":
                q_key = strip_ws("".join(prev["visual"].get("question") or []))[:8]
                if q_key and q_key in strip_ws(nar):
                    warns.append(f"[练习] {pid} 答案页复述了题干（「{q_key}」），建议直接给解析")
            if not (v.get("items") or []):
                warnings_local = f"[练习] {pid} answer 页没有 items，观众看不到要点"
                warns.append(warnings_local)

        # animated elements must be spoken in the narration (ignore punctuation)
        eles = steps if vt == "diagram" else v.get("items") or []
        if eles and (vt == "diagram" or v.get("animate")):
            nn = re.sub(r"[^\w\u4e00-\u9fff]", "", nar)
            for e in eles:
                ek = re.sub(r"[^\w\u4e00-\u9fff]", "", e)
                key = ek[:6]
                if len(ek) >= 2 and key and key not in nn:
                    warns.append(f"[动画] {pid} 元素「{e}」没在 narration 里被念到，只能均匀铺开")

    last = pages[-1]
    if (last.get("visual") or {}).get("type") != "recap":
        warns.append(f"[复盘] 最后一页 {last.get('id')} 不是 recap 页 —— 片尾应复盘本节要点")
    else:
        if "回顾" not in last.get("narration", "") and "复盘" not in last.get("narration", ""):
            warns.append(f"[复盘] {last.get('id')} 是复盘页，但口播没有说「回顾/复盘」")

    est_min = total_chars / 240
    print(f"pages={len(pages)}  parts={len(by_part)}  总字数={total_chars}  估算时长≈{est_min:.1f} 分钟（240 字/分）")
    if errors:
        print(f"\n[ERR] errors={len(errors)}")
        for e in errors:
            print("  " + e)
    if warns:
        print(f"\n[WARN] warnings={len(warns)}")
        for w in warns:
            print("  " + w)
    if not errors:
        print("\n[OK] no hard errors (warnings are acceptable but read each one)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
