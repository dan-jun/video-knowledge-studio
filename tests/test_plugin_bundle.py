from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import bootstrap, sync_plugin


ROOT = Path(__file__).resolve().parents[1]


class PluginBundleTests(unittest.TestCase):
    def test_bundle_is_synchronized(self):
        result = sync_plugin.check()
        self.assertTrue(result["ok"], result)

    def test_manifest_and_marketplace_are_valid(self):
        plugin = json.loads(
            (ROOT / "plugins" / "video-knowledge-studio" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(plugin["name"], "video-knowledge-studio")
        self.assertEqual(
            plugin["extensions"]["com.openai"]["interface"]["category"],
            "Education & Research",
        )
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        version = pyproject.split('version = "', 1)[1].split('"', 1)[0]
        self.assertEqual(plugin["version"], version)
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
        )
        self.assertEqual(marketplace["name"], "video-knowledge-studio-local")
        source = marketplace["plugins"][0]["source"]["path"]
        self.assertTrue((ROOT / source / "plugin.json").is_file())

    def test_bundled_skills_have_valid_identity(self):
        for source in sync_plugin.skill_dirs():
            text = (source / "SKILL.md").read_text(encoding="utf-8")
            frontmatter = text.split("---", 2)[1]
            self.assertIn(f"name: {source.name}", frontmatter)
            self.assertIn("description:", frontmatter)
            self.assertNotIn("TODO", frontmatter)

    def test_direct_skill_fallback_installs_both_skills(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.dict(os.environ, {"VKS_AGENT_SKILLS_ROOT": temp}):
                result = bootstrap.install_agent_bundle(no_plugin=True)
            self.assertEqual(result["method"], "skills")
            self.assertTrue((Path(temp) / "demand-driven-video-learning" / "SKILL.md").is_file())
            self.assertTrue((Path(temp) / "video-knowledge-studio" / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
