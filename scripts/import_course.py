#!/usr/bin/env python3
"""Create a starter course pack from a folder of local videos.

This importer deliberately does not invent note content. It creates valid
knowledge-note skeletons and accurate media timestamps; run your own
transcript/vision pipeline to fill the teaching fields.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}


def natural_key(path: Path):
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", str(path))]


def probe_duration(path: Path, ffprobe: str) -> float:
    proc = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    try:
        return round(float(proc.stdout.strip()), 3)
    except ValueError:
        return 0.0


def safe_id(value: str, fallback="course"):
    value = re.sub(r"[^0-9A-Za-z_-]+", "-", value).strip("-").lower()
    return value[:50] or fallback


def skeleton_episode(title: str, duration: float):
    end = int(duration)
    clock = lambda value: f"{value // 60:02d}:{value % 60:02d}"
    return {
        "title": title,
        "thesis": "待补充：用一句话写出本讲的中心问题、核心机制和结论。",
        "objectives": [
            "待补充：学完本讲后能够独立解释什么。",
            "待补充：能够完成哪一个最小练习。",
        ],
        "terms": [],
        "timeline": [
            {
                "time": f"00:00-{clock(end)}",
                "topic": "待整理",
                "must": "根据完整字幕和关键画面拆分语义段，不要只按固定时长切分。",
            }
        ],
        "core": [],
        "formula": "",
        "visuals": [],
        "visualThesis": "",
        "visualRead": [],
        "trap": "",
        "recall": [],
        "bridges": [],
        "memoryHook": "",
        "transcript": [],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="folder that will become the course pack")
    parser.add_argument("--title", required=True)
    parser.add_argument("--id", default="")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    root = args.input.resolve()
    if not root.is_dir():
        raise SystemExit(f"not a directory: {root}")
    manifest = root / "course.json"
    if manifest.exists() and not args.force:
        raise SystemExit("course.json already exists; pass --force to rebuild")
    ffprobe = shutil.which("ffprobe")
    videos = sorted(
        (p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS),
        key=natural_key,
    )
    if not videos:
        raise SystemExit("no video files found")

    course_id = safe_id(args.id or root.name, "course")
    chapters = []
    chapter_ids = {}
    episodes = []
    knowledge_dir = root / "knowledge"
    knowledge_dir.mkdir(exist_ok=True)

    for number, video in enumerate(videos, 1):
        relative = video.relative_to(root)
        chapter_title = str(relative.parent) if str(relative.parent) != "." else "未分章"
        cid = safe_id(chapter_title, "chapter")
        if cid not in chapter_ids:
            chapter_ids[cid] = chapter_title
            chapters.append({"id": cid, "title": chapter_title, "episodeIds": []})
        episode_id = f"{course_id}-e{number:03d}"
        chapter_next = next(x for x in chapters if x["id"] == cid)
        chapter_next["episodeIds"].append(episode_id)
        duration = probe_duration(video, ffprobe) if ffprobe else 0.0
        title = video.stem
        note_rel = Path("knowledge") / f"e{number:03d}.json"
        (root / note_rel).write_text(
            json.dumps(skeleton_episode(title, duration), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        episodes.append({
            "id": episode_id,
            "number": number,
            "title": title,
            "chapterId": cid,
            "duration": duration,
            "video": relative.as_posix(),
            "knowledge": note_rel.as_posix(),
        })

    data = {
        "schemaVersion": 1,
        "id": course_id,
        "title": args.title,
        "description": "Imported course skeleton. Complete transcripts, visual evidence and synthesis before publishing.",
        "license": "Unknown",
        "chapters": chapters,
        "episodes": episodes,
        "network": {
            "title": args.title + "知识网",
            "nodes": [
                {
                    "id": chapter["id"],
                    "label": chapter["title"],
                    "subtitle": "待补充依赖关系",
                    "episodeIds": chapter["episodeIds"],
                }
                for chapter in chapters
            ],
            "edges": [],
        },
    }
    if not data["network"]["nodes"]:
        data["network"]["nodes"] = [
            {"id": "course", "label": args.title, "subtitle": "待补充",
             "episodeIds": [x["id"] for x in episodes]}
        ]
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "pack": str(root), "episodes": len(episodes)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
