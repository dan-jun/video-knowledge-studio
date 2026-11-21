from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "Node.js is required for the knowledge contract test")
class LearningDepthTests(unittest.TestCase):
    def test_transcript_grouping_covers_every_segment_once(self):
        script = r"""
const K = require(process.argv[1]);
const rows = Array.from({ length: 24 }, (_, i) => ({
  start: i * 6,
  end: i * 6 + 6,
  text: `第${i + 1}项功能说明：这一段必须进入知识卡并且不能丢失。`,
}));
const units = K.groupTranscript(rows, { targetChars: 240, maxSeconds: 60 });
const flat = units.flatMap((unit) => unit.rows.map((row) => row.text));
if (JSON.stringify(flat) !== JSON.stringify(rows.map((row) => row.text))) process.exit(2);
if (units.length < 2 || units.some((unit) => !unit.heading || !unit.preview || !unit.rows.length)) process.exit(3);
if (K.groupTranscript([]).length !== 0) process.exit(4);
process.stdout.write(JSON.stringify({ units: units.length, segments: flat.length }));
"""
        result = subprocess.run(
            ["node", "-e", script, str(ROOT / "web" / "knowledge.js")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        self.assertIn('"segments":24', result.stdout)

    def test_ui_renders_expandable_timed_transcript_and_menu_toggles(self):
        knowledge = (ROOT / "web" / "knowledge.js").read_text(encoding="utf-8")
        player = (ROOT / "web" / "player.js").read_text(encoding="utf-8")
        self.assertIn("const transcriptUnits = groupTranscript", knowledge)
        self.assertIn("逐段知识卡", knowledge)
        self.assertIn("dataset.vksTranscriptUnit", knowledge)
        self.assertIn("line.onclick = () => seek(row.start)", knowledge)
        self.assertIn("展开全部", knowledge)
        self.assertIn("case 'gear': this.toggleMenu('settings')", player)
        self.assertIn("toggleMenu(view)", player)
        self.assertIn("if (k === 'Escape' && this.el.menu.classList.contains('open'))", player)
        self.assertIn("a.startsWith('rate:')", player)


if __name__ == "__main__":
    unittest.main()
