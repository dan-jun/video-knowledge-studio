#!/usr/bin/env python3
"""Validate and package the public Video Knowledge Studio plugin submission."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "video-knowledge-studio"
ALLOWED_CATEGORIES = {
    "Productivity",
    "Creativity",
    "Developer Tools",
    "Business & Operations",
    "Data & Analytics",
    "Communication",
    "Education & Research",
    "Security",
    "Finance",
    "Healthcare",
    "Travel",
    "Entertainment",
    "Other",
}
IGNORED_PARTS = {"__pycache__", ".git"}
IGNORED_SUFFIXES = {".pyc"}
IGNORED_NAMES = {".DS_Store"}
ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
FIXED_ZIP_TIME = (2020, 1, 1, 0, 0, 0)


def _text_errors(
    field: str,
    value: Any,
    *,
    limit: int,
    single_line: bool = False,
    required: bool = True,
) -> list[str]:
    if not isinstance(value, str):
        return [f"{field} must be a string"]
    if required and not value.strip():
        return [f"{field} must not be empty"]
    errors = []
    if len(value) > limit:
        errors.append(f"{field} exceeds {limit} characters")
    if single_line and "\n" in value:
        errors.append(f"{field} must be a single line")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in value):
        errors.append(f"{field} contains unsupported control characters")
    return errors


def _https_error(field: str, value: Any) -> list[str]:
    if not isinstance(value, str):
        return [f"{field} must be an HTTPS URL"]
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        return [f"{field} must be an HTTPS URL without embedded credentials"]
    return []


def _resolve_inside(root: Path, value: str, field: str) -> tuple[Path | None, list[str]]:
    if not value.startswith("./"):
        return None, [f"{field} must start with ./"]
    root_resolved = root.resolve()
    candidate = (root / value).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        return None, [f"{field} resolves outside the plugin root"]
    if not candidate.is_file():
        return None, [f"{field} does not reference an existing file"]
    return candidate, []


def _svg_size(path: Path) -> tuple[int, int]:
    root = ElementTree.parse(path).getroot()
    width = root.attrib.get("width", "")
    height = root.attrib.get("height", "")

    def number(value: str) -> float | None:
        match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)(?:px)?\s*", value)
        return float(match.group(1)) if match else None

    parsed_width = number(width)
    parsed_height = number(height)
    if parsed_width and parsed_height:
        return round(parsed_width), round(parsed_height)
    view_box = root.attrib.get("viewBox", "")
    parts = re.split(r"[\s,]+", view_box.strip())
    if len(parts) == 4:
        return round(float(parts[2])), round(float(parts[3]))
    raise ValueError("SVG needs numeric width/height or a viewBox")


def _png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG image")
    return struct.unpack(">II", header[16:24])


def _image_size(path: Path) -> tuple[int, int]:
    suffix = path.suffix.lower()
    if suffix == ".svg":
        return _svg_size(path)
    if suffix == ".png":
        return _png_size(path)
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValueError("install Pillow to validate JPEG or WebP icons") from exc
    with Image.open(path) as image:
        return image.size


def _load_manifest(plugin_root: Path) -> dict[str, Any]:
    manifest_path = plugin_root / "plugin.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("plugin.json must contain a JSON object")
    return data


def _skill_inventory(plugin_root: Path, plugin_name: str) -> tuple[list[str], list[str]]:
    errors = []
    names = []
    skills_root = plugin_root / "skills"
    if not skills_root.is_dir():
        return [], ["root skills/ directory is missing"]
    for child in sorted(skills_root.iterdir()):
        if not child.is_dir() or child.is_symlink():
            continue
        skill_file = child / "SKILL.md"
        if not skill_file.is_file():
            continue
        try:
            text = skill_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{skill_file.relative_to(plugin_root)} is unreadable: {exc}")
            continue
        if not text.startswith("---"):
            errors.append(f"{child.name}/SKILL.md is missing front matter")
            continue
        parts = text.split("---", 2)
        if len(parts) < 3:
            errors.append(f"{child.name}/SKILL.md has unclosed front matter")
            continue
        frontmatter = parts[1]
        name_match = re.search(r"^name:\s*(\S.*?)\s*$", frontmatter, re.MULTILINE)
        desc_match = re.search(r"^description:\s*(\S.*?)\s*$", frontmatter, re.MULTILINE)
        if not name_match:
            errors.append(f"{child.name}/SKILL.md is missing name")
            continue
        skill_name = name_match.group(1).strip()
        names.append(skill_name)
        if skill_name != child.name:
            errors.append(f"{child.name}/SKILL.md name must match its directory")
        if not desc_match or len(desc_match.group(1)) > 1024:
            errors.append(f"{skill_name} needs a description of at most 1024 characters")
        if len(f"{plugin_name}:{skill_name}") > 64:
            errors.append(f"{plugin_name}:{skill_name} exceeds the 64-character identity limit")
    if not names:
        errors.append("at least one valid Skill is required")
    if len(names) != len(set(names)):
        errors.append("Skill names must be unique")
    return names, errors


def validate(plugin_root: Path = PLUGIN_ROOT) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        manifest = _load_manifest(plugin_root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {"ok": False, "errors": [f"plugin.json is invalid: {exc}"], "warnings": []}

    plugin_name = manifest.get("name")
    if not isinstance(plugin_name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", plugin_name):
        errors.append("plugin name must use lowercase kebab-case")
        plugin_name = "unknown"
    errors.extend(_text_errors("version", manifest.get("version"), limit=64, single_line=True))
    errors.extend(_text_errors("description", manifest.get("description"), limit=1024))

    extensions = manifest.get("extensions")
    openai = extensions.get("com.openai") if isinstance(extensions, dict) else None
    interface = openai.get("interface") if isinstance(openai, dict) else None
    if not isinstance(interface, dict):
        errors.append("extensions.com.openai.interface is required")
        interface = {}

    errors.extend(
        _text_errors(
            "interface.displayName",
            interface.get("displayName"),
            limit=30,
            single_line=True,
        )
    )
    errors.extend(
        _text_errors(
            "interface.shortDescription",
            interface.get("shortDescription"),
            limit=30,
            single_line=True,
        )
    )
    errors.extend(
        _text_errors(
            "interface.longDescription",
            interface.get("longDescription"),
            limit=4000,
        )
    )
    errors.extend(
        _text_errors(
            "interface.developerName",
            interface.get("developerName"),
            limit=80,
            single_line=True,
        )
    )
    category = interface.get("category")
    if category not in ALLOWED_CATEGORIES:
        errors.append("interface.category is not a supported public-directory category")

    capabilities = interface.get("capabilities", [])
    if not isinstance(capabilities, list):
        errors.append("interface.capabilities must be a list")
    else:
        if len(capabilities) > 20:
            errors.append("interface.capabilities must contain at most 20 entries")
        for index, capability in enumerate(capabilities):
            errors.extend(
                _text_errors(
                    f"interface.capabilities[{index}]",
                    capability,
                    limit=120,
                    single_line=True,
                )
            )
        if len(capabilities) != len(set(capabilities)):
            errors.append("interface.capabilities must be unique")

    prompts = interface.get("defaultPrompt", [])
    if isinstance(prompts, str):
        prompts = [prompts]
    if not isinstance(prompts, list):
        errors.append("interface.defaultPrompt must be a string or list")
    else:
        if len(prompts) > 3:
            errors.append("interface.defaultPrompt must contain at most 3 entries")
        for index, prompt in enumerate(prompts):
            errors.extend(
                _text_errors(
                    f"interface.defaultPrompt[{index}]",
                    prompt,
                    limit=128,
                    single_line=True,
                )
            )
        normalized = [" ".join(str(prompt).split()) for prompt in prompts]
        if len(normalized) != len(set(normalized)):
            errors.append("interface.defaultPrompt entries must be unique")

    for field in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
        errors.extend(_https_error(f"interface.{field}", interface.get(field)))

    for field in ("logo", "composerIcon"):
        value = interface.get(field)
        if not isinstance(value, str):
            errors.append(f"interface.{field} is required")
            continue
        path, path_errors = _resolve_inside(plugin_root, value, f"interface.{field}")
        errors.extend(path_errors)
        if not path:
            continue
        try:
            if path.stat().st_size > 5 * 1024 * 1024:
                errors.append(f"interface.{field} exceeds 5 MiB")
            if path.suffix.lower() not in ASSET_EXTENSIONS:
                errors.append(f"interface.{field} has an unsupported image extension")
                continue
            width, height = _image_size(path)
            if width != height:
                errors.append(f"interface.{field} must be square")
            if width < 48:
                errors.append(f"interface.{field} must be at least 48x48")
            if width > 4096 or height > 4096:
                errors.append(f"interface.{field} must not exceed 4096 pixels")
        except (OSError, ValueError, ElementTree.ParseError) as exc:
            errors.append(f"interface.{field} is invalid: {exc}")

    onboarding = openai.get("onboardingSkill") if isinstance(openai, dict) else None
    if onboarding is not None:
        path, path_errors = _resolve_inside(
            plugin_root, onboarding, "extensions.com.openai.onboardingSkill"
        )
        errors.extend(path_errors)
        if path and path.name != "SKILL.md":
            errors.append("onboardingSkill must reference a SKILL.md file")

    skills, skill_errors = _skill_inventory(plugin_root, plugin_name)
    errors.extend(skill_errors)

    for path in plugin_root.rglob("*"):
        if path.is_symlink():
            errors.append(f"plugin package contains a symlink: {path.relative_to(plugin_root)}")

    warnings.append("run --check-urls after pushing the legal and support pages")
    result = {
        "ok": not errors,
        "plugin": plugin_name,
        "version": manifest.get("version"),
        "skills": skills,
        "root": str(plugin_root),
        "errors": errors,
        "warnings": warnings,
    }
    return result


def _collect_files(plugin_root: Path) -> list[Path]:
    files = []
    for path in sorted(plugin_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(plugin_root)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if path.name in IGNORED_NAMES or path.suffix.lower() in IGNORED_SUFFIXES:
            continue
        files.append(path)
    return files


def package(output: Path | None = None) -> dict[str, Any]:
    result = validate()
    if not result["ok"]:
        raise ValueError("; ".join(result["errors"]))
    plugin_name = result["plugin"]
    version = result["version"]
    output = output or (ROOT / "dist" / f"{plugin_name}-plugin-{version}.zip")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    files = _collect_files(PLUGIN_ROOT)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(PLUGIN_ROOT).as_posix()
            archive_name = f"{plugin_name}/{relative}"
            info = zipfile.ZipInfo(archive_name, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    with zipfile.ZipFile(output, "r") as archive:
        names = archive.namelist()
        bad_member = archive.testzip()
        manifest_member = f"{plugin_name}/plugin.json"
        if bad_member:
            raise ValueError(f"ZIP member failed CRC validation: {bad_member}")
        if manifest_member not in names:
            raise ValueError(f"ZIP is missing {manifest_member}")
        if any(not name.startswith(f"{plugin_name}/") for name in names):
            raise ValueError("ZIP must contain one top-level plugin directory")
        extracted_manifest = json.loads(archive.read(manifest_member).decode("utf-8"))
        if extracted_manifest.get("name") != plugin_name:
            raise ValueError("packaged manifest name does not match the ZIP directory")

    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return {
        **result,
        "path": str(output),
        "sha256": digest,
        "bytes": output.stat().st_size,
        "files": len(files),
    }


def check_urls(plugin_root: Path = PLUGIN_ROOT, timeout: float = 15.0) -> dict[str, Any]:
    manifest = _load_manifest(plugin_root)
    interface = manifest["extensions"]["com.openai"]["interface"]
    results = []
    failed = []
    for field in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
        url = interface[field]
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Video-Knowledge-Studio-Plugin-Packager/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status = response.status
                final_url = response.geturl()
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            status = getattr(exc, "code", None)
            final_url = url
        item = {"field": field, "url": url, "status": status, "finalURL": final_url}
        results.append(item)
        if not isinstance(status, int) or status >= 400:
            failed.append(item)
    return {"ok": not failed, "urls": results, "failed": failed}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate without creating a ZIP")
    parser.add_argument("--check-urls", action="store_true", help="check public HTTPS listing URLs")
    parser.add_argument("--output", type=Path, help="ZIP output path")
    args = parser.parse_args(argv)

    result = validate()
    url_result = None
    if args.check_urls and result["ok"]:
        url_result = check_urls()
    if not args.check and result["ok"]:
        try:
            result = package(output=args.output)
        except ValueError as exc:
            result = {"ok": False, "errors": [str(exc)]}
    if url_result is not None:
        result["urls"] = url_result
        if not url_result["ok"]:
            result["ok"] = False
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
