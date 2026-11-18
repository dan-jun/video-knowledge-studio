#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""course 长教学 = 多源整合。把 N 支已转写的涅槃项目合并成一门课的项目骨架。

用法：
    python tools/course_merge.py --into <新课程项目目录> \
        --source <已转写项目1> --source <已转写项目2> [...]

做什么：
  1. 校验每个来源都有 src/transcript.txt（没转写就先跑 video_agent remix）
  2. 从各来源的 agent.json 解析 BV 号 / 标题
  3. 把转录稿汇总到 <新项目>/src/source-<n>.txt
  4. 写 agent.json（mode=course）+ storyboard.json（含 sources 数组 + 章节草稿目录）
  5. 生成 course-outline.md：按来源分块 + 每块的关键句，供人工/模型编排章节

⚠️ 这一步只负责「合并素材 + 登记来源」，讲解稿仍由 agent 撰写。
"""
import argparse
import json
import os
import pathlib
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runtime import OUT_ROOT


def bv_of(url):
    m = re.search(r"(BV[0-9A-Za-z]{10})", url or "")
    return m.group(1) if m else ""


def read_source(proj):
    tr = proj / "src" / "transcript.txt"
    if not tr.exists():
        return None
    return tr.read_text(encoding="utf-8", errors="replace")


def key_sentences(text, k=8):
    """粗提关键句：按标点切句，取中长句里含术语/数字的。"""
    sents = [s.strip() for s in re.split(r"[。！？\n]", text) if 12 <= len(s.strip()) <= 80]
    scored = []
    for s in sents:
        score = 0
        if re.search(r"\d", s):
            score += 2
        if re.search(r"[A-Za-z]{3,}", s):
            score += 1
        score += min(len(s), 60) / 60
        scored.append((score, s))
    scored.sort(key=lambda x: -x[0])
    picked, seen = [], set()
    for _, s in scored:
        if s in seen:
            continue
        seen.add(s)
        picked.append(s)
        if len(picked) >= k:
            break
    return picked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--into", required=True, help="新课程项目目录（相对路径落到输出根）")
    ap.add_argument("--source", action="append", required=True, help="已转写的涅槃项目目录")
    ap.add_argument("--title", default="")
    a = ap.parse_args()

    into = pathlib.Path(a.into)
    if not into.is_absolute():
        into = OUT_ROOT / into
    sources = []
    for sp in a.source:
        p = pathlib.Path(sp)
        if not p.is_absolute():
            p = OUT_ROOT / p
        txt = read_source(p)
        if txt is None:
            print(f"  ✗ {p.name} 没有 src/transcript.txt，先跑 remix 转写")
            continue
        aj = {}
        try:
            aj = json.loads((p / "agent.json").read_text(encoding="utf-8"))
        except Exception:
            pass
        url = str((aj.get("source") or {}).get("local") or "")
        sources.append({"dir": p, "name": p.name, "text": txt,
                        "bvid": bv_of(url), "url": url})

    if len(sources) < 2:
        print(f"✗ 只找到 {len(sources)} 个可用来源；course 至少需要 2 个（这就是「多源涅槃」）")
        return 1

    (into / "src").mkdir(parents=True, exist_ok=True)
    lines = [f"# course 多源整合：{a.title or into.name}", ""]
    sb_sources = []
    for i, s in enumerate(sources, 1):
        (into / "src" / f"source-{i}.txt").write_text(s["text"], encoding="utf-8")
        title = s["name"]
        sb_sources.append({"bvid": s["bvid"], "title": title, "url": s["url"],
                           "file": f"src/source-{i}.txt",
                           "chars": len(s["text"])})
        lines.append(f"## 来源 {i}：{title}"
                     + (f"（{s['bvid']}）" if s["bvid"] else ""))
        lines.append("")
        lines.append(f"- 转写字数：{len(s['text'])}")
        lines.append("- 候选关键句：")
        for k in key_sentences(s["text"]):
            lines.append(f"  - {k}")
        lines.append("")

    outline = "\n".join(lines)
    (into / "course-outline.md").write_text(outline, encoding="utf-8")

    agent = {"mode": "course", "stage": "merged",
             "sources": [{"bvid": s["bvid"], "url": s["url"]} for s in sb_sources]}
    (into / "agent.json").write_text(json.dumps(agent, ensure_ascii=False, indent=2),
                                     encoding="utf-8")

    sb_path = into / "storyboard.json"
    if sb_path.exists():
        print(f"  ! {sb_path.name} 已存在，只更新 sources")
        sb = json.loads(sb_path.read_text(encoding="utf-8"))
        sb["sources"] = sb_sources
    else:
        sb = {"title": a.title or into.name, "style": "M1", "sources": sb_sources,
              "parts": [{"part": f"第{i}章 待定", "pages": []} for i in range(1, 2)]}
    sb_path.write_text(json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")

    total = sum(s["chars"] for s in sb_sources)
    print(f"✓ 合并 {len(sb_sources)} 个来源 → {into}")
    print(f"  总转写 {total} 字；按 270 字/分可支撑约 {total/270:.0f} 分钟")
    print(f"  来源清单已写入 storyboard.sources（multi_source 门禁可过）")
    print(f"  大纲草稿：{into / 'course-outline.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
