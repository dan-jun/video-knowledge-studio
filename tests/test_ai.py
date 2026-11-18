from __future__ import annotations

import dataclasses
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from vks.ai import CodexProvider, TutorService
from vks.config import load_settings


class FailingProvider:
    name = "failing"

    def available(self):
        return True

    def answer(self, prompt, image_path):
        raise RuntimeError("provider failed")


class GoodProvider:
    name = "fallback"

    def available(self):
        return True

    def answer(self, prompt, image_path):
        return {
            "answer": "fallback answer",
            "annotation": "",
            "evidence": [],
            "proposed_revision": None,
            "confidence": "low",
            "uncertain": True,
            "provider": self.name,
        }


class TutorFallbackTests(unittest.TestCase):
    def test_auto_mode_falls_back_after_runtime_failure(self):
        settings = dataclasses.replace(load_settings(), ai_provider="auto")
        service = TutorService(settings)
        service.providers = {
            "codex": FailingProvider(),
            "openai": FailingProvider(),
            "mock": GoodProvider(),
        }
        result = service.answer({}, None)
        self.assertEqual(result["provider"], "fallback")


class CodexWorkspaceTempTests(unittest.TestCase):
    def test_codex_scratch_directory_stays_in_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = dataclasses.replace(
                load_settings(),
                data_dir=Path(directory),
                ai_timeout=5,
                codex_exe="codex",
            )
            provider = CodexProvider(settings)
            captured = {}

            def fake_run(command, **kwargs):
                captured.update(kwargs)
                answer_path = Path(command[command.index("--output-last-message") + 1])
                answer_path.write_text(
                    json.dumps({
                        "answer": "ok",
                        "annotation": "",
                        "evidence": [],
                        "proposed_revision": None,
                        "confidence": "high",
                        "uncertain": False,
                    }),
                    encoding="utf-8",
                )
                kwargs["stdout"].write(b"ok")
                kwargs["stderr"].write(b"")
                return SimpleNamespace(returncode=0)

            with patch("vks.ai.subprocess.run", side_effect=fake_run):
                result = provider.answer("{}", None)

            self.assertEqual(result["answer"], "ok")
            temp_root = Path(captured["env"]["TEMP"])
            self.assertTrue(temp_root.is_relative_to(Path(directory)))


if __name__ == "__main__":
    unittest.main()
