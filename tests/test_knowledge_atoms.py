from __future__ import annotations

import unittest

from vks import knowledge_atoms


def note():
    return {
        "schemaVersion": 2,
        "episode": 9,
        "concepts": [
            {"title": "锚点 A", "oneLine": "A 的定义。", "evidence": [{"start": 10}]},
            {"title": "锚点 B", "oneLine": "B 的定义。", "evidence": [{"start": 70}]},
        ],
        "coverage": [
            {
                "blockId": "B01",
                "start": "00:00",
                "startSeconds": 0,
                "end": "00:30",
                "endSeconds": 30,
                "status": "knowledge",
                "topic": "A",
                "keyPoints": ["A 是指一种状态。", "A 通过两个步骤转换。"],
                "conceptTitles": ["锚点 A"],
            },
            {
                "blockId": "B02",
                "start": "01:00",
                "startSeconds": 60,
                "end": "01:30",
                "endSeconds": 90,
                "status": "knowledge",
                "topic": "B",
                "keyPoints": ["B 是结果。"],
                "conceptTitles": ["锚点 B"],
            },
            {
                "blockId": "B03",
                "start": "02:00",
                "startSeconds": 120,
                "end": "02:05",
                "endSeconds": 125,
                "status": "housekeeping",
                "topic": "收尾",
                "keyPoints": ["课程结束。"],
                "conceptTitles": [],
            },
        ],
        "visualEvidence": [{"candidateId": "F01", "start": 12}],
        "conceptGraph": {
            "nodes": [{"conceptTitle": "锚点 A"}, {"conceptTitle": "锚点 B"}],
            "edges": [{
                "from": "锚点 A",
                "to": "锚点 B",
                "type": "mechanism",
                "time": "01:00",
                "explain": "A 产生 B。",
            }],
        },
        "quality": {},
    }


class KnowledgeAtomTests(unittest.TestCase):
    def test_every_key_point_becomes_one_anchored_atom(self):
        value = note()
        atoms = knowledge_atoms.attach_knowledge_atoms(value)
        self.assertEqual(value["schemaVersion"], 3)
        self.assertEqual(len(atoms), 3)
        self.assertEqual(sum(len(row["knowledgeAtomIds"]) for row in value["coverage"]), 3)
        self.assertEqual(atoms[0]["visualEvidenceIds"], ["F01"])
        self.assertEqual(knowledge_atoms.validate_knowledge_atoms(value), [])

    def test_changed_claim_is_rejected(self):
        value = note()
        knowledge_atoms.attach_knowledge_atoms(value)
        value["knowledgeAtoms"][0]["claim"] = "被改写的知识。"
        errors = knowledge_atoms.validate_knowledge_atoms(value)
        self.assertTrue(any("keyPoint 不一致" in row for row in errors))


if __name__ == "__main__":
    unittest.main()
