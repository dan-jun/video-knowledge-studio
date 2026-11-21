from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "Node.js is required for the player contract test")
class PlayerSubtitleTests(unittest.TestCase):
    def test_transcript_builds_readable_caption_overlay(self):
        script = r"""
const VP = require('./web/player.js');
const cues = VP.buildCaptionCues([
  { start: 0, end: 8, text: '第一句解释操作系统是什么。第二句说明它有哪些功能，并且为什么需要这些功能。' },
  { start: 8, end: 12, text: '最后用一个简短例子收尾。' },
]);
if (cues.length < 3) process.exit(2);
if (cues.some((cue) => !cue.text || cue.text.length > 24)) process.exit(3);
if (cues[0].start !== 0 || cues[cues.length - 1].end !== 12) process.exit(4);
process.stdout.write(JSON.stringify({ cues }));
"""
        proc = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        payload = json.loads(proc.stdout)
        cues = payload["cues"]
        self.assertGreaterEqual(len(cues), 3)
        self.assertTrue(all(len(cue["text"]) <= 24 for cue in cues))

        player = (ROOT / "web" / "player.js").read_text(encoding="utf-8")
        css = (ROOT / "web" / "player.css").read_text(encoding="utf-8")
        knowledge = (ROOT / "web" / "knowledge.js").read_text(encoding="utf-8")
        self.assertIn("setSubtitles(cues)", player)
        self.assertIn("buildCaptionCues", player)
        self.assertIn("vp-caption-layer", player)
        self.assertNotIn("track.kind = 'subtitles'", player)
        self.assertIn(".vp-caption-layer", css)
        self.assertIn('.vp[data-caption-style="outline"]', css)
        self.assertIn(".vp.autohide:not(:hover):not(:focus-within) .vp-caption-layer", css)
        self.assertIn("captionStyle:outline", player)
        self.assertIn("captionSize:large", player)
        self.assertIn("window.__vp.setSubtitles", knowledge)
        self.assertIn("d.episode && d.episode.transcript", knowledge)


if __name__ == "__main__":
    unittest.main()
