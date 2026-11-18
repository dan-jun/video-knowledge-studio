#!/usr/bin/env python3
"""Synchronize canonical skills into the distributable Codex plugin bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skill"
PLUGIN_ROOT = ROOT / "plugins" / "video-knowledge-studio"
PLUGIN_SKILLS = PLUGIN_ROOT / "skills"


def skill_dirs() -> list[Path]:
    return sorted(
        path
        for path in SKILLS_ROOT.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )


def tree_hashes(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        result[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def check() -> dict:
    mismatches = []
    for source in skill_dirs():
        destination = PLUGIN_SKILLS / source.name
        if tree_hashes(source) != tree_hashes(destination):
            mismatches.append(source.name)
    expected = {path.name for path in skill_dirs()}
    actual = {
        path.name
        for path in PLUGIN_SKILLS.iterdir()
        if path.is_dir()
    } if PLUGIN_SKILLS.is_dir() else set()
    mismatches.extend(sorted(expected - actual))
    mismatches.extend(sorted(actual - expected))
    return {"ok": not mismatches, "mismatches": sorted(set(mismatches))}


def sync() -> dict:
    if not (PLUGIN_ROOT / "plugin.json").is_file():
        raise SystemExit("plugin manifest is missing")
    PLUGIN_SKILLS.mkdir(parents=True, exist_ok=True)
    expected = {path.name for path in skill_dirs()}
    for stale in PLUGIN_SKILLS.iterdir():
        if stale.is_dir() and stale.name not in expected:
            shutil.rmtree(stale)
    for source in skill_dirs():
        destination = PLUGIN_SKILLS / source.name
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(
            source,
            destination,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    return {"ok": True, "skills": sorted(expected)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = check() if args.check else sync()
    print(json.dumps(result, ensure_ascii=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
