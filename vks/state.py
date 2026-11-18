from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any


class StateStore:
    def __init__(self, data_dir: Path):
        self.root = (data_dir / "state").resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

    def _path(self, course_id: str, episode_id: str) -> Path:
        safe_course = "".join(c if c.isalnum() or c in "-_" else "_" for c in course_id)
        safe_episode = "".join(c if c.isalnum() or c in "-_" else "_" for c in episode_id)
        return self.root / safe_course / f"{safe_episode}.json"

    def load(self, course_id: str, episode_id: str) -> dict[str, Any]:
        path = self._path(course_id, episode_id)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        data.setdefault("annotations", [])
        data.setdefault("revisions", [])
        data.setdefault("overrides", {})
        return data

    def save(self, course_id: str, episode_id: str, data: dict[str, Any]) -> None:
        path = self._path(course_id, episode_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        data["updatedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)

    def annotation(self, course_id: str, episode_id: str, body: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            data = self.load(course_id, episode_id)
            if body.get("act") == "del":
                aid = str(body.get("annotationId") or "")
                data["annotations"] = [x for x in data["annotations"] if x.get("id") != aid]
            else:
                text = str(body.get("text") or "").strip()[:1200]
                if not text:
                    raise ValueError("annotation is empty")
                data["annotations"].append({
                    "id": uuid.uuid4().hex[:12],
                    "kid": str(body.get("kid") or "")[:160],
                    "time": max(0.0, float(body.get("time") or 0)),
                    "text": text,
                    "kind": str(body.get("kind") or "ai")[:24],
                    "at": time.strftime("%Y-%m-%d %H:%M"),
                })
            data["annotations"] = data["annotations"][-500:]
            self.save(course_id, episode_id, data)
            return data

    def revision(self, course_id: str, episode_id: str, body: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            data = self.load(course_id, episode_id)
            act = str(body.get("act") or "apply")
            rid = str(body.get("revisionId") or "")
            draft = body.get("draft") if isinstance(body.get("draft"), dict) else {}
            if act == "undo":
                row = next((x for x in data["revisions"] if x.get("id") == rid), None)
                if not row or row.get("status") != "applied":
                    raise KeyError("revision not found")
                kid, before = row.get("kid", ""), row.get("before")
                if before:
                    data["overrides"][kid] = before
                else:
                    data["overrides"].pop(kid, None)
                row["status"] = "undone"
                row["undoneAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                kid = str(draft.get("kid") or "")[:160]
                original = str(draft.get("original") or "")[:5000]
                replacement = str(draft.get("replacement") or "")[:5000]
                reason = str(draft.get("reason") or "")[:1500]
                block_before = str(draft.get("before") or "")[:12000]
                if not kid or (act == "apply" and not replacement):
                    raise ValueError("revision is incomplete")
                before = data["overrides"].get(kid, block_before or original)
                after = replacement
                if original and original in before:
                    after = before.replace(original, replacement, 1)
                status = {
                    "apply": "applied",
                    "annotation": "annotation_only",
                    "reject": "rejected",
                }.get(act, "rejected")
                data["revisions"].append({
                    "id": uuid.uuid4().hex[:12],
                    "kid": kid,
                    "before": before,
                    "after": after,
                    "original": original,
                    "reason": reason,
                    "status": status,
                    "at": time.strftime("%Y-%m-%d %H:%M:%S"),
                })
                if status == "applied":
                    data["overrides"][kid] = after
            data["revisions"] = data["revisions"][-300:]
            self.save(course_id, episode_id, data)
            return data
