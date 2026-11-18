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
        for name in ("workflow-overview.svg", "demand-driven-flow.svg"):
            path = ROOT / "docs" / "images" / name
            self.assertLess(path.stat().st_size, 2_000_000)
            root = ET.parse(path).getroot()
            self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")

    def test_demo_media_are_present_and_bounded(self):
        for name in ("demo.png", "production-workspace.png", "production-demo.gif"):
            path = ROOT / "docs" / "images" / name
            self.assertGreater(path.stat().st_size, 10_000)
            self.assertLess(path.stat().st_size, 2_000_000)


if __name__ == "__main__":
    unittest.main()
