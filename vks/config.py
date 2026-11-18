from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(ROOT / ".env")


def _path(name: str, default: Path) -> Path:
    return Path(os.environ.get(name, str(default))).expanduser().resolve()


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    root: Path
    web_dir: Path
    packs_dir: Path
    data_dir: Path
    host: str
    port: int
    password: str
    session_secret: str
    ai_provider: str
    codex_exe: str
    openai_base_url: str
    openai_api_key: str
    openai_model: str
    request_timeout: int
    ai_timeout: int


def load_settings() -> Settings:
    data_dir = _path("VKS_DATA", ROOT / "data")
    secret = os.environ.get("VKS_SECRET", "").strip()
    if not secret:
        data_dir.mkdir(parents=True, exist_ok=True)
        secret_file = data_dir / ".session_secret"
        if secret_file.is_file():
            secret = secret_file.read_text(encoding="utf-8").strip()
        else:
            import secrets
            secret = secrets.token_urlsafe(48)
            secret_file.write_text(secret, encoding="utf-8")
    return Settings(
        root=ROOT,
        web_dir=ROOT / "web",
        packs_dir=_path("VKS_PACKS", ROOT / "packs"),
        data_dir=data_dir,
        host=os.environ.get("VKS_HOST", "127.0.0.1"),
        port=_int("VKS_PORT", 7870),
        password=os.environ.get("VKS_PASSWORD", ""),
        session_secret=secret,
        ai_provider=os.environ.get("VKS_AI_PROVIDER", "auto").lower(),
        codex_exe=os.environ.get("VKS_CODEX_EXE", "codex"),
        openai_base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        openai_model=os.environ.get("VKS_MODEL", "gpt-4.1-mini"),
        request_timeout=_int("VKS_REQUEST_TIMEOUT", 180),
        ai_timeout=_int("VKS_AI_TIMEOUT", 180),
    )


settings = load_settings()
