from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class CourseError(ValueError):
    pass


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def safe_child(root: Path, relative: str) -> Path:
    root = root.resolve()
    path = (root / relative).resolve()
    if path != root and root not in path.parents:
        raise CourseError("path escapes its course pack")
    return path


def clock_seconds(value) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip()
    try:
        parts = [float(x) for x in text.split(":")]
    except ValueError:
        return None
    if len(parts) == 2:
        return round(parts[0] * 60 + parts[1], 3)
    if len(parts) == 3:
        return round(parts[0] * 3600 + parts[1] * 60 + parts[2], 3)
    return None


def normalize_note_times(note: dict[str, Any], duration: float) -> None:
    def clip(value):
        if value is None:
            return None
        return max(0.0, min(float(value), duration))

    for row in note.get("timeline", []):
        if not isinstance(row, dict):
            continue
        start, end = row.get("start"), row.get("end")
        text = str(row.get("time") or "")
        if (start is None or end is None) and "-" in text:
            left, right = text.split("-", 1)
            start = clock_seconds(left) if start is None else start
            end = clock_seconds(right) if end is None else end
        row["start"], row["end"] = clip(start), clip(end)
    for row in note.get("core", []):
        if isinstance(row, dict) and row.get("start") is None:
            row["start"] = clip(clock_seconds(row.get("time")))
    for row in note.get("visuals", []):
        if not isinstance(row, dict):
            continue
        value = row.get("start", row.get("at"))
        if value is None:
            value = clock_seconds(row.get("time"))
        row["start"] = clip(value)


class CourseStore:
    """Load self-contained course packs from disk."""

    def __init__(self, packs_dir: Path):
        self.packs_dir = packs_dir.resolve()
        self.courses: dict[str, dict[str, Any]] = {}
        self.episodes: dict[str, dict[str, Any]] = {}
        self.reload()

    def reload(self) -> None:
        self.courses.clear()
        self.episodes.clear()
        if not self.packs_dir.is_dir():
            return
        if (self.packs_dir / "course.json").is_file():
            pack_dirs = [self.packs_dir]
        else:
            pack_dirs = sorted(self.packs_dir.iterdir(), key=lambda p: p.name.lower())
        for pack_dir in pack_dirs:
            manifest = pack_dir / "course.json"
            if not pack_dir.is_dir() or not manifest.is_file():
                continue
            raw = load_json(manifest)
            if not isinstance(raw, dict):
                continue
            try:
                course = self._normalize_course(pack_dir, raw)
            except (KeyError, TypeError, CourseError) as exc:
                raise CourseError(f"{manifest}: {exc}") from exc
            if course["id"] in self.courses:
                raise CourseError(f"duplicate course id: {course['id']}")
            self.courses[course["id"]] = course
            for ep in course["episodes"]:
                if ep["id"] in self.episodes:
                    raise CourseError(f"duplicate episode id: {ep['id']}")
                self.episodes[ep["id"]] = ep

    def _normalize_course(self, pack_dir: Path, raw: dict[str, Any]) -> dict[str, Any]:
        course_id = str(raw["id"]).strip()
        if not course_id:
            raise CourseError("course id is empty")
        chapters = []
        chapter_titles = {}
        for chapter in raw.get("chapters", []):
            cid = str(chapter["id"]).strip()
            title = str(chapter["title"]).strip()
            ids = [str(x) for x in chapter.get("episodeIds", [])]
            chapters.append({"id": cid, "title": title, "episodeIds": ids})
            chapter_titles[cid] = title

        episodes = []
        for item in raw.get("episodes", []):
            number = int(item["number"])
            episode_id = str(item["id"]).strip()
            chapter_id = str(item.get("chapterId", "")).strip()
            knowledge_path = safe_child(pack_dir, str(item["knowledge"]))
            video_path = safe_child(pack_dir, str(item["video"]))
            if not knowledge_path.is_file():
                raise CourseError(f"missing knowledge file: {knowledge_path}")
            if not video_path.is_file():
                raise CourseError(f"missing video file: {video_path}")
            knowledge = load_json(knowledge_path)
            if not isinstance(knowledge, dict):
                raise CourseError(f"invalid knowledge JSON: {knowledge_path}")
            normalize_note_times(knowledge, float(item.get("duration") or knowledge.get("duration") or 0))
            episode = {
                "id": episode_id,
                "number": number,
                "title": str(item.get("title") or knowledge.get("title") or episode_id),
                "chapterId": chapter_id,
                "chapter": chapter_titles.get(chapter_id, str(item.get("chapter") or "")),
                "duration": float(item.get("duration") or knowledge.get("duration") or 0),
                "courseId": course_id,
                "courseTitle": str(raw.get("title") or course_id),
                "packDir": pack_dir,
                "videoPath": video_path,
                "knowledgePath": knowledge_path,
                "knowledge": knowledge,
                "mtime": int(video_path.stat().st_mtime),
            }
            episodes.append(episode)

        known = {x["id"] for x in episodes}
        for chapter in chapters:
            unknown = sorted(set(chapter["episodeIds"]) - known)
            if unknown:
                raise CourseError(f"chapter {chapter['id']} references unknown episodes: {unknown}")

        return {
            "id": course_id,
            "title": str(raw.get("title") or course_id),
            "description": str(raw.get("description") or ""),
            "license": str(raw.get("license") or ""),
            "chapters": chapters,
            "episodes": episodes,
            "network": raw.get("network") or {"title": "知识网", "nodes": [], "edges": []},
            "packDir": pack_dir,
        }

    def projects(self) -> list[dict[str, Any]]:
        rows = []
        for course in self.courses.values():
            chapter_order = {x["id"]: i for i, x in enumerate(course["chapters"])}
            for ep in course["episodes"]:
                blocks = (
                    len(ep["knowledge"].get("timeline", []))
                    + len(ep["knowledge"].get("core", []))
                    + len(ep["knowledge"].get("visuals", []))
                )
                rows.append({
                    "id": ep["id"],
                    "title": f"{ep['number']:02d} · {ep['title']}",
                    "minutes": round(ep["duration"] / 60, 2),
                    "pages": blocks,
                    "segments": [],
                    "dir": f"{course['id']}/{ep['id']}",
                    "mtime": ep["mtime"],
                    "seq": ep["number"],
                    "qualities": {},
                    "kind": "course-video",
                    "knowledge": course["id"],
                    "courseTitle": course["title"],
                    "chapter": ep["chapter"],
                    "chapterOrder": chapter_order.get(ep["chapterId"], 999),
                })
        rows.sort(key=lambda x: (x["courseTitle"], x["chapterOrder"], x["seq"]))
        return rows

    def get(self, episode_id: str) -> dict[str, Any] | None:
        return self.episodes.get(episode_id)

    def knowledge_payload(self, episode_id: str) -> dict[str, Any] | None:
        ep = self.get(episode_id)
        if not ep:
            return None
        course = self.courses[ep["courseId"]]
        public_lesson = {k: v for k, v in ep["knowledge"].items() if k != "sourceVideo"}
        public_lesson.update({
            "id": ep["id"],
            "episode": ep["number"],
            "title": ep["title"],
            "chapter": ep["chapter"],
            "duration": ep["duration"],
        })
        summaries = []
        for other in course["episodes"]:
            summaries.append({
                "id": other["id"],
                "episode": other["number"],
                "title": other["title"],
                "chapter": other["chapter"],
                "duration": other["duration"],
                "thesis": other["knowledge"].get("thesis", ""),
            })
        return {
            "episode": public_lesson,
            "index": {
                "course": course["title"],
                "description": course["description"],
                "license": course["license"],
                "chapters": course["chapters"],
                "network": course["network"],
                "episodes": summaries,
            },
        }
