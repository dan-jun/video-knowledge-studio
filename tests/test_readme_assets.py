from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]


class ReadmeAssetTests(unittest.TestCase):
    def test_local_readme_links_exist(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        missing = []
        for target in re.findall(r"\]\(([^)]+)\)", text):
            target = target.strip()
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path = unquote(target.split("#", 1)[0])
            if path and not (ROOT / path).exists():
                missing.append(path)
        self.assertEqual(missing, [])

    def test_readme_diagrams_are_valid_svg(self):
        for name in (
            "workflow-overview.svg",
            "demand-driven-flow.svg",
            "before-after.svg",
            "social-preview.svg",
        ):
            path = ROOT / "docs" / "images" / name
            self.assertLess(path.stat().st_size, 2_000_000)
            root = ET.parse(path).getroot()
            self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")

    def test_english_release_copy_contains_no_cjk(self):
        paths = [
            ROOT / "README.md",
            ROOT / "docs" / "images" / "workflow-overview-en.svg",
            ROOT / "docs" / "images" / "demand-driven-flow-en.svg",
            ROOT / "docs" / "images" / "before-after-en.svg",
            ROOT / "docs" / "images" / "social-preview-en.svg",
        ]
        pattern = re.compile(r"[\u3400-\u9fff]")
        for path in paths:
            self.assertIsNone(
                pattern.search(path.read_text(encoding="utf-8")),
                f"public English copy contains CJK text: {path}",
            )

    def test_demo_media_are_present_and_bounded(self):
        for name in (
            "demo.png",
            "ai-tutor-demo.png",
            "production-workspace.png",
            "production-demo.gif",
            "social-preview.png",
            "product-demo-poster.png",
            "learning-workspace-en.png",
            "ai-tutor-demo-en.png",
            "production-workspace-en.png",
            "production-demo-en-raft.gif",
            "social-preview-en.png",
            "product-demo-poster-en.png",
        ):
            path = ROOT / "docs" / "images" / name
            self.assertGreater(path.stat().st_size, 10_000)
            self.assertLess(path.stat().st_size, 2_000_000)
        video = ROOT / "docs" / "media" / "product-demo.mp4"
        self.assertGreater(video.stat().st_size, 1_000_000)
        self.assertLess(video.stat().st_size, 10_000_000)
        english_video = ROOT / "docs" / "media" / "product-demo-en.mp4"
        self.assertGreater(english_video.stat().st_size, 1_000_000)
        self.assertLess(english_video.stat().st_size, 10_000_000)


if __name__ == "__main__":
    unittest.main()
