"""Portable paths and external-tool discovery for the production pipeline."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


PRODUCTION_ROOT = Path(__file__).resolve().parent.parent
OUT_ROOT = Path(
    os.environ.get("VKS_PRODUCTION_ROOT")
    or os.environ.get("AI_INFRA_OUT")
    or PRODUCTION_ROOT / "projects"
).resolve()

FFMPEG = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = os.environ.get("FFPROBE") or shutil.which("ffprobe") or "ffprobe"


def _first_file(*candidates: str | None) -> str:
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    return ""


_WINDOWS_FONTS = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
_MAC_FONTS = Path("/System/Library/Fonts")

FONT_CJK = os.environ.get("VKS_FONT_CJK") or _first_file(
    str(_WINDOWS_FONTS / "msyh.ttc"),
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
    str(_MAC_FONTS / "PingFang.ttc"),
)
FONT_CJK_BOLD = os.environ.get("VKS_FONT_CJK_BOLD") or _first_file(
    str(_WINDOWS_FONTS / "msyhbd.ttc"),
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Bold.otf",
    str(_MAC_FONTS / "PingFang.ttc"),
)
FONT_HAND = os.environ.get("VKS_FONT_HAND") or _first_file(
    str(_WINDOWS_FONTS / "simkai.ttf"),
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJKsc-Regular.otf",
    str(_MAC_FONTS / "Songti.ttc"),
)
FONT_MONO = os.environ.get("VKS_FONT_MONO") or _first_file(
    str(_WINDOWS_FONTS / "consola.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    str(_MAC_FONTS / "Menlo.ttc"),
)

if sys.platform == "win32":
    _DEFAULT_CJK_NAME = "Microsoft YaHei"
elif sys.platform == "darwin":
    _DEFAULT_CJK_NAME = "PingFang SC"
else:
    _DEFAULT_CJK_NAME = "Noto Sans CJK SC"

CJK_FONT_NAME = os.environ.get("VKS_FONT_CJK_NAME") or _DEFAULT_CJK_NAME
FONT_CJK_NAME = CJK_FONT_NAME


def require_fonts() -> None:
    missing = [
        name
        for name, value in (
            ("VKS_FONT_CJK", FONT_CJK),
            ("VKS_FONT_CJK_BOLD", FONT_CJK_BOLD),
            ("VKS_FONT_HAND", FONT_HAND),
            ("VKS_FONT_MONO", FONT_MONO),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing CJK fonts for video production: "
            + ", ".join(missing)
            + ". Install Noto CJK fonts or set the corresponding environment variables."
        )
