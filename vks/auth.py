from __future__ import annotations

import hashlib
import hmac
import time
from http.cookies import SimpleCookie


class Auth:
    def __init__(self, password: str, secret: str, days: int = 30):
        self.password = password
        self.secret = secret.encode("utf-8")
        self.days = days

    @property
    def enabled(self) -> bool:
        return bool(self.password)

    def verify(self, candidate: str) -> bool:
        return hmac.compare_digest(
            hashlib.sha256(candidate.encode()).digest(),
            hashlib.sha256(self.password.encode()).digest(),
        )

    def issue(self) -> str:
        exp = int(time.time()) + self.days * 86400
        sig = hmac.new(self.secret, f"v1|{exp}".encode(), hashlib.sha256).hexdigest()
        return f"{exp}.{sig}"

    def check(self, token: str) -> bool:
        if not token or "." not in token:
            return False
        exp_s, sig = token.split(".", 1)
        try:
            exp = int(exp_s)
        except ValueError:
            return False
        if exp < time.time():
            return False
        want = hmac.new(self.secret, f"v1|{exp}".encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, want)

    def authorized(self, headers) -> bool:
        if not self.enabled:
            return True
        raw = headers.get("Cookie", "")
        cookie = SimpleCookie()
        try:
            cookie.load(raw)
        except Exception:
            pass
        if cookie.get("vks_session") and self.check(cookie["vks_session"].value):
            return True
        return self.check(headers.get("X-VKS-Token", ""))
