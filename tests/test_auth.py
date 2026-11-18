from __future__ import annotations

import unittest

from vks.auth import Auth


class AuthTests(unittest.TestCase):
    def test_session_round_trip(self):
        auth = Auth("correct horse", "test-secret")
        self.assertTrue(auth.verify("correct horse"))
        self.assertFalse(auth.verify("wrong"))
        token = auth.issue()
        self.assertTrue(auth.check(token))

    def test_tampered_session_is_rejected(self):
        auth = Auth("pw", "test-secret")
        token = auth.issue()
        self.assertFalse(auth.check(token[:-1] + ("0" if token[-1] != "0" else "1")))


if __name__ == "__main__":
    unittest.main()
