from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "Node.js is required for the player contract test")
class PlayerSubtitleTests(unittest.TestCase):
    def test_transcript_builds_webvtt_and_wires_player_controls(self):
        script = r"""
const VP = require('./web/player.js');
const vtt = VP.cuesToVtt([
  { start: 0, end: 1.2, text: 'First <caption> & test' },
  { start: 1.2, end: 3.2, text: 'Second line' },
]);
process.stdout.write(JSON.stringify({ vtt }));
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
        vtt = payload["vtt"]
        self.assertTrue(vtt.startswith("WEBVTT\n"))
        self.assertIn("00:00:00.000 --> 00:00:01.199", vtt)
        self.assertIn("First &lt;caption&gt; &amp; test", vtt)
        self.assertIn("00:00:01.200 --> 00:00:03.200", vtt)

        player = (ROOT / "web" / "player.js").read_text(encoding="utf-8")
        knowledge = (ROOT / "web" / "knowledge.js").read_text(encoding="utf-8")
        self.assertIn("setSubtitles(cues)", player)
        self.assertIn("track.kind = 'subtitles'", player)
        self.assertIn("track.mode = this.ccOn ? 'showing' : 'disabled'", player)
        self.assertIn("window.__vp.setSubtitles", knowledge)
        self.assertIn("d.episode && d.episode.transcript", knowledge)


if __name__ == "__main__":
    unittest.main()
