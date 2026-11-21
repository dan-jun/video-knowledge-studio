from __future__ import annotations

import dataclasses
import json
import tempfile
import time
import unittest
from pathlib import Path

from vks.config import load_settings
from vks.deep_notes import (
    DeepNoteService,
    DeepNoteUnavailable,
    cluster_visual_candidates,
    coverage_ratio,
    split_transcript_blocks,
)


def make_episode(root: Path) -> dict:
    visuals = []
    for index in range(3):
        path = root / "media" / f"frame-{index}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"image")
        visuals.append({
            "file": f"media/frame-{index}.png",
            "time": f"0{index}:00",
            "start": index * 180,
            "caption": f"关键画面 {index + 1}",
            "whatItAdds": "图中给出机制关系。",
        })
    transcript = [
        {
            "start": index * 60,
            "end": (index + 1) * 60,
            "text": f"第 {index + 1} 段解释条件、机制和结果的因果关系。",
        }
        for index in range(10)
    ]
    return {
        "id": "deep-e01",
        "number": 1,
        "title": "深度知识测试",
        "chapter": "测试章",
        "duration": 600,
        "packDir": root,
        "knowledge": {
            "title": "深度知识测试",
            "thesis": "结论必须保留条件和证据。",
            "objectives": ["能解释机制"],
            "timeline": [{"time": "00:00-10:00", "topic": "完整机制"}],
            "core": [{"title": "核心机制"}],
            "visuals": visuals,
            "transcript": transcript,
        },
    }


def quality_payload(packet: dict, concepts: int = 5) -> dict:
    titles = [f"概念 {index + 1}" for index in range(concepts)]
    rows = []
    for index, title in enumerate(titles):
        rows.append({
            "title": title,
            "oneLine": f"{title} 的一句话定义。",
            "explain": f"{title} 的完整解释包含条件、执行机制和结果；需要说明为什么成立，以及哪些证据支持这个结论。",
            "mechanism": ["先识别条件。", "再执行机制并检查结果。"],
            "example": f"{title} 的最小例子。",
            "boundary": f"{title} 的适用边界。",
            "misconception": f"{title} 的常见误区。",
            "evidence": [{"time": f"{index:02d}:10", "reason": "原片支持该概念。"}],
        })
    coverage = []
    for index, block in enumerate(packet["transcriptBlocks"]):
        coverage.append({
            "blockId": block["blockId"],
            "start": block["startClock"],
            "end": block["endClock"],
            "status": "knowledge",
            "topic": f"知识块 {index + 1}",
            "keyPoints": [f"第 {index + 1} 块的关键主张。"],
            "conceptTitles": [titles[index % len(titles)]],
            "exclusionReason": "",
        })
    visual_decisions = [
        {
            "candidateId": row["candidateId"],
            "decision": "include",
            "importance": "critical" if index == 0 else "supporting",
            "reason": "该画面包含文字之外的关系。",
            "caption": f"关键画面 {index + 1}",
            "whatItAdds": "展示机制或状态关系。",
            "conceptTitles": [titles[index % len(titles)]],
        }
        for index, row in enumerate(packet["visualCandidates"])
    ]
    graph_edges = [
        {
            "from": titles[index],
            "to": titles[index + 1],
            "type": "prerequisite",
            "explain": "前一个概念为后一个概念提供基础。",
            "time": f"0{index + 1}:00",
        }
        for index in range(len(titles) - 1)
    ]
    graph_edges.append({
        "from": titles[0],
        "to": titles[2],
        "type": "example",
        "explain": "用后一个概念的具体场景说明前一个概念。",
        "time": "03:30",
    })
    return {
        "centralQuestion": "条件如何通过机制产生结果？",
        "bigIdea": "先追踪条件，再按机制推导结果。",
        "learningGoals": ["解释条件", "复述机制", "判断边界"],
        "mentalModel": [
            {"label": "识别条件", "explain": "找到成立前提。", "time": "00:10"},
            {"label": "执行机制", "explain": "按步骤产生变化。", "time": "03:10"},
            {"label": "检查结果", "explain": "回到证据验证结果。", "time": "08:10"},
        ],
        "concepts": rows,
        "comparisons": [{
            "dimension": "是否保留条件",
            "left": "证据化总结",
            "right": "字幕压缩",
            "difference": "前者可复核，后者丢失边界。",
        }],
        "formulas": [],
        "examPoints": [{
            "point": "条件不能省略",
            "reason": "省略后无法判断结论是否成立。",
            "time": "05:10",
        }],
        "recall": [
            {"question": "为什么先看条件？", "answer": "它决定机制是否成立。", "time": "01:10"},
            {"question": "怎样验证结果？", "answer": "回到原片证据。", "time": "06:10"},
            {"question": "什么情况超出边界？", "answer": "前提条件不再满足时。", "time": "09:10"},
        ],
        "glossary": [
            {"term": "条件", "plain": "成立前提。", "example": "先有输入。", "time": "00:10"},
            {"term": "机制", "plain": "产生变化的步骤。", "example": "按序执行。", "time": "03:10"},
            {"term": "证据", "plain": "可回查的材料。", "example": "原片与画面。", "time": "08:10"},
        ],
        "coverage": coverage,
        "visualDecisions": visual_decisions,
        "conceptGraph": {
            "nodes": [
                {
                    "conceptTitle": title,
                    "role": "core" if index == 0 else "mechanism",
                    "summary": f"{title} 在知识体系中的作用。",
                }
                for index, title in enumerate(titles)
            ],
            "edges": graph_edges,
        },
        "uncertainties": [],
    }


def wait_for_job(service: DeepNoteService, job_id: str) -> dict:
    for _ in range(100):
        row = service.job(job_id)
        if row and row.get("status") in {"done", "failed"}:
            return row
        time.sleep(0.02)
    raise AssertionError("deep-note job did not finish")


class DeepNoteServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.episode = make_episode(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def settings(self, provider: str = "auto"):
        return dataclasses.replace(
            load_settings(),
            data_dir=self.root / "data",
            ai_provider=provider,
        )

    def test_generates_caches_and_reuses_quality_note(self):
        captured = {}

        def generator(packet, images, progress):
            captured["packet"] = packet
            captured["images"] = images
            progress("生成中")
            return quality_payload(packet), "test-provider"

        service = DeepNoteService(self.settings(), generator=generator)
        started = service.start(self.episode)
        self.assertTrue(started["ok"])
        row = wait_for_job(service, started["job"])
        self.assertEqual(row["status"], "done", row.get("error"))
        note = row["note"]
        self.assertEqual(note["quality"]["coverage"], 1.0)
        self.assertEqual(note["quality"]["conceptCount"], 5)
        self.assertEqual(note["model"], "test-provider")
        self.assertEqual(len(captured["packet"]["transcript"]), 10)
        self.assertGreaterEqual(len(captured["packet"]["transcriptBlocks"]), 2)
        self.assertEqual(len(captured["images"]), 3)
        self.assertEqual(note["quality"]["visualClusters"], 3)
        self.assertEqual(note["quality"]["includedVisualClusters"], 3)
        self.assertEqual(note["quality"]["graphNodeCount"], 5)
        self.assertTrue(service.cache_path("deep-e01").is_file())
        cached = service.cached(self.episode)
        self.assertEqual(cached["inputHash"], note["inputHash"])
        again = service.start(self.episode)
        self.assertTrue(again.get("cached"))

    def test_source_change_invalidates_old_cache(self):
        service = DeepNoteService(
            self.settings(),
            generator=lambda packet, images, progress: (quality_payload(packet), "test-provider"),
        )
        started = service.start(self.episode)
        wait_for_job(service, started["job"])
        self.assertIsNotNone(service.cached(self.episode))
        cache_path = service.cache_path("deep-e01")
        old = json.loads(cache_path.read_text(encoding="utf-8"))
        old["schemaVersion"] = 1
        cache_path.write_text(json.dumps(old), encoding="utf-8")
        self.assertIsNone(service.cached(self.episode))
        old["schemaVersion"] = 2
        cache_path.write_text(json.dumps(old), encoding="utf-8")
        self.episode["knowledge"]["transcript"][0]["text"] += " 新修订。"
        self.assertIsNone(service.cached(self.episode))

    def test_rejects_too_few_concepts(self):
        service = DeepNoteService(
            self.settings(),
            generator=lambda packet, images, progress: (quality_payload(packet, 3), "test-provider"),
        )
        started = service.start(self.episode)
        row = wait_for_job(service, started["job"])
        self.assertEqual(row["status"], "failed")
        self.assertIn("核心概念应为 5–9 个", row["error"])

    def test_rejects_coverage_links_to_unknown_concepts(self):
        def generator(packet, images, progress):
            raw = quality_payload(packet)
            raw["coverage"][0]["conceptTitles"] = ["不存在的概念"]
            return raw, "test-provider"

        service = DeepNoteService(
            self.settings(),
            generator=generator,
        )
        started = service.start(self.episode)
        row = wait_for_job(service, started["job"])
        self.assertEqual(row["status"], "failed")
        self.assertIn("引用了未知概念", row["error"])

    def test_rejects_missing_visual_decision(self):
        def generator(packet, images, progress):
            raw = quality_payload(packet)
            raw["visualDecisions"].pop()
            return raw, "test-provider"

        service = DeepNoteService(self.settings(), generator=generator)
        started = service.start(self.episode)
        row = wait_for_job(service, started["job"])
        self.assertEqual(row["status"], "failed")
        self.assertIn("画面审核账本不完整", row["error"])

    def test_rejects_disconnected_concept_graph(self):
        def generator(packet, images, progress):
            raw = quality_payload(packet)
            raw["conceptGraph"]["edges"] = []
            return raw, "test-provider"

        service = DeepNoteService(self.settings(), generator=generator)
        started = service.start(self.episode)
        row = wait_for_job(service, started["job"])
        self.assertEqual(row["status"], "failed")
        self.assertIn("孤立节点", row["error"])

    def test_offline_provider_does_not_fabricate_note(self):
        service = DeepNoteService(self.settings("mock"))
        with self.assertRaises(DeepNoteUnavailable):
            service.start(self.episode)
        self.assertFalse(service.cache_path("deep-e01").exists())

    def test_coverage_uses_union_of_timed_blocks(self):
        rows = [
            {"startSeconds": 0, "endSeconds": 300},
            {"startSeconds": 250, "endSeconds": 540},
        ]
        self.assertAlmostEqual(coverage_ratio(rows, 600), 0.9)
        self.assertAlmostEqual(coverage_ratio(rows, 300), 1.0)

    def test_deterministic_blocks_cover_exact_duration_once(self):
        transcript = self.episode["knowledge"]["transcript"]
        blocks = split_transcript_blocks(transcript, 600, target_seconds=180, max_seconds=300)
        self.assertEqual(blocks[0]["start"], 0.0)
        self.assertEqual(blocks[-1]["end"], 600.0)
        for left, right in zip(blocks, blocks[1:]):
            self.assertEqual(left["end"], right["start"])
        self.assertEqual(sum(row["segmentCount"] for row in blocks), len(transcript))

    def test_visual_candidates_cluster_duplicates_but_audit_all(self):
        rows = [
            {"file": "a.jpg", "start": 0, "time": "00:00", "ocr": ["状态图", "就绪态"]},
            {"file": "b.jpg", "start": 1, "time": "00:01", "ocr": ["状态图", "就绪态"]},
            {"file": "c.jpg", "start": 40, "time": "00:40", "ocr": ["阻塞队列"]},
        ]
        candidates = cluster_visual_candidates(rows)
        self.assertEqual(len(candidates), 3)
        self.assertEqual(len({row["clusterId"] for row in candidates}), 2)
        self.assertEqual(candidates[0]["clusterId"], candidates[1]["clusterId"])

    def test_cache_names_cannot_collide_after_sanitizing(self):
        service = DeepNoteService(
            self.settings(),
            generator=lambda packet, images, progress: (quality_payload(), "test-provider"),
        )
        self.assertNotEqual(
            service.cache_path("course/a"),
            service.cache_path("course-a"),
        )


if __name__ == "__main__":
    unittest.main()
