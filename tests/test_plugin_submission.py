from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts import package_plugin


ROOT = Path(__file__).resolve().parents[1]


class PluginSubmissionTests(unittest.TestCase):
    def test_public_submission_manifest_passes(self):
        result = package_plugin.validate()
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(
            result["skills"],
            ["demand-driven-video-learning", "video-knowledge-studio"],
        )

    def test_manifest_uses_final_directory_lengths(self):
        manifest = json.loads(
            (
                ROOT / "plugins" / "video-knowledge-studio" / "plugin.json"
            ).read_text(encoding="utf-8")
        )
        interface = manifest["extensions"]["com.openai"]["interface"]
        self.assertLessEqual(len(interface["displayName"]), 30)
        self.assertLessEqual(len(interface["shortDescription"]), 30)
        self.assertLessEqual(len(interface["longDescription"]), 4000)
        self.assertLessEqual(len(interface["defaultPrompt"]), 3)
        for prompt in interface["defaultPrompt"]:
            self.assertLessEqual(len(prompt), 128)

    def test_manifest_has_submission_assets_and_legal_links(self):
        manifest = json.loads(
            (
                ROOT / "plugins" / "video-knowledge-studio" / "plugin.json"
            ).read_text(encoding="utf-8")
        )
        interface = manifest["extensions"]["com.openai"]["interface"]
        for field in (
            "websiteURL",
            "supportURL",
            "privacyPolicyURL",
            "termsOfServiceURL",
            "logo",
            "composerIcon",
        ):
            self.assertIn(field, interface)
            self.assertTrue(interface[field])
        self.assertTrue((ROOT / "docs" / "plugin-privacy.md").is_file())
        self.assertTrue((ROOT / "docs" / "plugin-terms.md").is_file())

    def test_package_has_one_root_and_no_generated_files(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "plugin.zip"
            result = package_plugin.package(output=output)
            self.assertTrue(result["ok"], result["errors"])
            self.assertEqual(len(result["sha256"]), 64)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                self.assertIsNone(archive.testzip())
            self.assertIn("video-knowledge-studio/plugin.json", names)
            self.assertIn("video-knowledge-studio/assets/icon.svg", names)
            self.assertIn(
                "video-knowledge-studio/skills/video-knowledge-studio/SKILL.md",
                names,
            )
            self.assertIn(
                "video-knowledge-studio/skills/demand-driven-video-learning/SKILL.md",
                names,
            )
            self.assertTrue(
                all(name.startswith("video-knowledge-studio/") for name in names)
            )
            self.assertFalse(any("__pycache__" in name or name.endswith(".pyc") for name in names))


if __name__ == "__main__":
    unittest.main()
