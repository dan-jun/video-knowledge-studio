#!/usr/bin/env python3
"""Migrate cached deep notes to schema-v3 multiscale knowledge."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from pathlib import Path

from vks import knowledge_atoms
from vks.config import load_settings
from vks.courses import CourseStore
from vks.deep_notes import DeepNoteService, validate_deep_note


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--course", required=True)
    parser.add_argument("--episodes", default="")
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()

    settings = load_settings()
    store = CourseStore(settings.packs_dir)
    course = store.courses[args.course]
    service = DeepNoteService(settings)
    requested = {
        int(value) for value in args.episodes.split(",") if value.strip()
    }
    episodes = [
        row for row in sorted(course["episodes"], key=lambda row: int(row["number"]))
        if not requested or int(row["number"]) in requested
    ]
    backup = (
        settings.data_dir / "cache" / "deep_notes" / "backups"
        / "v2-before-multiscale-20261122"
    )
    backup.mkdir(parents=True, exist_ok=True)
    results = []
    errors = []
    for episode in episodes:
        path = service.cache_path(episode["id"])
        try:
            note = json.loads(path.read_text(encoding="utf-8"))
            if not args.no_backup and not (backup / path.name).exists():
                shutil.copy2(path, backup / path.name)
            atoms = knowledge_atoms.attach_knowledge_atoms(note)
            packet = service.build_packet(episode)
            note["inputHash"] = packet["inputHash"]
            validate_deep_note(
                note,
                packet["transcriptBlocks"],
                packet["visualCandidates"],
            )
            note.setdefault("quality", {})["atomMigration"] = {
                "version": 1,
                "deterministic": True,
                "source": "coverage.keyPoints",
                "migratedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            }
            write_json(path, note)
            results.append({
                "episode": int(episode["number"]),
                "atoms": len(atoms),
                "anchors": len(note.get("concepts") or []),
            })
        except Exception as exc:
            errors.append({
                "episode": int(episode["number"]),
                "error": str(exc)[:1200],
            })
    print(json.dumps({
        "ok": not errors,
        "migrated": len(results),
        "atoms": sum(row["atoms"] for row in results),
        "errors": errors,
        "backup": str(backup),
    }, ensure_ascii=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
