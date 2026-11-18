from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vks.state import StateStore


class StateStoreTests(unittest.TestCase):
    def test_revision_replaces_only_selected_fragment_and_undoes(self):
        with tempfile.TemporaryDirectory() as td:
            store = StateStore(Path(td))
            before = "前文。要修正的局部句子。后文。"
            applied = store.revision("course", "episode", {
                "act": "apply",
                "draft": {
                    "kid": "E01:core:0",
                    "before": before,
                    "original": "要修正的局部句子",
                    "replacement": "更准确的新句子",
                    "reason": "test",
                },
            })
            self.assertEqual(applied["overrides"]["E01:core:0"], "前文。更准确的新句子。后文。")
            revision_id = applied["revisions"][-1]["id"]
            undone = store.revision("course", "episode", {
                "act": "undo", "revisionId": revision_id,
            })
            self.assertEqual(undone["overrides"]["E01:core:0"], before)

    def test_annotation_add_and_delete(self):
        with tempfile.TemporaryDirectory() as td:
            store = StateStore(Path(td))
            state = store.annotation("course", "episode", {
                "text": "side note", "kid": "E01:core:0", "time": 12,
            })
            self.assertEqual(len(state["annotations"]), 1)
            aid = state["annotations"][0]["id"]
            state = store.annotation("course", "episode", {
                "act": "del", "annotationId": aid,
            })
            self.assertEqual(state["annotations"], [])


if __name__ == "__main__":
    unittest.main()
