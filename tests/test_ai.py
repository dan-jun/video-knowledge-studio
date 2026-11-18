from __future__ import annotations

import dataclasses
import unittest

from vks.ai import TutorService
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


if __name__ == "__main__":
    unittest.main()
