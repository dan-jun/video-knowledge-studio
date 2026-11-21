from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "semantic_review_deep_notes.py"
SPEC = importlib.util.spec_from_file_location("semantic_review_deep_notes", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def checks():
    return {
        key: True
        for key in MODULE.review_schema()["properties"]["checks"]["required"]
    }


class SemanticReviewTests(unittest.TestCase):
    def test_downgrades_inconsistent_pass(self):
        review = {
            "decision": "pass",
            "coverage": 0.95,
            "summary": "looks complete",
            "checks": {**checks(), "visual_evidence": False},
            "omissions": [],
            "uncertainties": [],
        }
        result = MODULE.validate_review(review)
        self.assertEqual(result["decision"], "fail")
        self.assertIn("visual_evidence", result["validationWarnings"][-1])

    def test_blocking_omission_cannot_pass(self):
        review = {
            "decision": "pass",
            "coverage": 0.95,
            "summary": "looks complete",
            "checks": checks(),
            "omissions": [{
                "severity": "high",
                "kind": "mechanism",
                "time": "03:20",
                "sourceEvidence": "原片给出完整机制",
                "issue": "笔记只写了结论",
                "suggestedRepair": "补入机制步骤",
            }],
            "uncertainties": [],
        }
        self.assertEqual(MODULE.validate_review(review)["decision"], "fail")

    def test_canonical_hash_changes_with_content(self):
        self.assertNotEqual(
            MODULE.canonical_hash({"note": "A"}),
            MODULE.canonical_hash({"note": "B"}),
        )


if __name__ == "__main__":
    unittest.main()
