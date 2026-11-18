from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProductionMetadataTests(unittest.TestCase):
    def test_anim_gen_records_selected_mode_parameters(self):
        spec = {
            "topic": "metadata-smoke",
            "title": "Metadata smoke",
            "style": "SOLARA",
            "pages": [
                {
                    "id": "c01",
                    "type": "title",
                    "title": "Metadata smoke",
                    "narration": "A short metadata check.",
                },
                {
                    "id": "c02",
                    "type": "recap",
                    "title": "Recap",
                    "narration": "我们回顾一下。这是一次测试。",
                    "items": ["one", "two"],
                },
            ],
        }
        generated_scene = ROOT / "production" / "scenes" / "gen_metadata-smoke.py"
        try:
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                spec_path = root / "spec.json"
                project = root / "project"
                spec_path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
                subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "production" / "tools" / "anim_gen.py"),
                        str(spec_path),
                        "--mode",
                        "scipop",
                        "--project",
                        str(project),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env={
                        **os.environ,
                        "PYTHONUTF8": "1",
                        "PYTHONIOENCODING": "utf-8",
                    },
                )
                agent = json.loads((project / "agent.json").read_text(encoding="utf-8"))
                self.assertEqual(agent["mode"], "scipop")
                self.assertEqual(agent["label"], "科普短片（精品手工路线）")
                self.assertEqual(agent["params"]["target_min"], [2.0, 6.0])
                self.assertEqual(agent["params"]["mm_speed"], 1.08)
                self.assertFalse(agent["params"]["quiz"])
        finally:
            generated_scene.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
