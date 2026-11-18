from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vks.courses import CourseError, CourseStore


ROOT = Path(__file__).resolve().parents[1]


class CourseStoreTests(unittest.TestCase):
    def test_sample_pack_loads(self):
        store = CourseStore(ROOT / "packs")
        self.assertGreaterEqual(len(store.courses), 2)
        self.assertGreaterEqual(len(store.episodes), 4)
        projects = store.projects()
        demo = next(row for row in projects if row["id"] == "demo-e01")
        self.assertEqual(demo["chapter"], "第1章 从信息到结构")
        raft = next(row for row in projects if row["id"] == "raft-e01")
        self.assertEqual(raft["courseTitle"], "4 小时读懂 Raft")
        payload = store.knowledge_payload("demo-e01")
        self.assertEqual(payload["lesson"]["id"] if "lesson" in payload else payload["episode"]["id"], "demo-e01")
        self.assertNotIn("sourceVideo", payload["episode"])

    def test_single_pack_root_is_supported(self):
        store = CourseStore(ROOT / "packs" / "demo")
        self.assertEqual(len(store.episodes), 3)

    def test_duplicate_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in ("a", "b"):
                pack = root / name
                pack.mkdir()
                (pack / "video.mp4").write_bytes(b"not-a-real-video")
                note = {
                    "title": name, "thesis": "", "objectives": [], "terms": [],
                    "timeline": [], "core": [], "formula": "", "visuals": [],
                    "visualThesis": "", "visualRead": [], "trap": "",
                    "recall": [], "bridges": [], "memoryHook": "", "transcript": [],
                }
                (pack / "note.json").write_text(json.dumps(note), encoding="utf-8")
                manifest = {
                    "id": "same", "title": name,
                    "chapters": [{"id": "c", "title": "C", "episodeIds": ["same-e1"]}],
                    "episodes": [{
                        "id": "same-e1", "number": 1, "title": name,
                        "chapterId": "c", "duration": 1,
                        "video": "video.mp4", "knowledge": "note.json",
                    }],
                }
                (pack / "course.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(CourseError):
                CourseStore(root)

    def test_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            pack = Path(td) / "bad"
            pack.mkdir()
            manifest = {
                "id": "bad", "title": "Bad",
                "chapters": [],
                "episodes": [{
                    "id": "bad-e1", "number": 1, "title": "Bad",
                    "duration": 1, "video": "../../secret.mp4",
                    "knowledge": "../../secret.json",
                }],
            }
            (pack / "course.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(CourseError):
                CourseStore(Path(td))


if __name__ == "__main__":
    unittest.main()
