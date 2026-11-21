#!/usr/bin/env python3
"""Generate validated deep notes for every episode in a course pack."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import threading
import time
from pathlib import Path

from vks.config import load_settings
from vks.courses import CourseStore
from vks.deep_notes import DeepNoteService


ROOT = Path(__file__).resolve().parents[1]


class State:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        try:
            self.data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.data = {"episodes": {}, "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        self.data.setdefault("episodes", {})

    def save(self):
        with self.lock:
            self.data["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp, self.path)

    def update(self, episode_id: str, **values):
        with self.lock:
            row = self.data["episodes"].setdefault(episode_id, {})
            row.update(values)
            row["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            self.save()

    def event(self, episode_id: str, event: str, **values):
        row = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "episode": episode_id,
            "event": event,
            **values,
        }
        with self.lock:
            event_path = self.path.with_name("events.jsonl")
            with event_path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(json.dumps(row, ensure_ascii=False), flush=True)


def generate_one(settings, episode, state: State, force: bool, retries: int):
    episode_id = episode["id"]
    started = time.perf_counter()
    service = DeepNoteService(settings)
    packet = service.build_packet(episode)
    if not force:
        cached = service.cached(episode)
        if cached:
            state.update(
                episode_id,
                status="complete",
                cached=True,
                inputHash=packet["inputHash"],
                elapsed=round(time.perf_counter() - started, 2),
                quality=cached.get("quality", {}),
            )
            state.event(episode_id, "skipped_valid")
            return {"episode": episode_id, "status": "complete", "cached": True}

    errors = []
    for attempt in range(1, retries + 1):
        state.update(episode_id, status="running", attempt=attempt)
        state.event(episode_id, "attempt", attempt=attempt)
        try:
            started_job = service.start(episode, force=attempt > 1 or force)
            if started_job.get("cached"):
                note = started_job["note"]
            else:
                job_id = started_job.get("job")
                if not job_id:
                    raise RuntimeError("deep-note job id missing")
                deadline = time.time() + max(900, settings.ai_timeout * 3)
                while time.time() < deadline:
                    row = service.job(job_id)
                    if not row:
                        raise RuntimeError("deep-note job disappeared")
                    if row.get("status") == "done":
                        note = row.get("note") or service.cached(episode)
                        break
                    if row.get("status") == "failed":
                        raise RuntimeError(row.get("error") or "deep-note job failed")
                    time.sleep(1)
                else:
                    raise RuntimeError("deep-note job timed out")
            if not note:
                raise RuntimeError("deep-note job completed without a note")
            state.update(
                episode_id,
                status="complete",
                attempt=attempt,
                error=None,
                inputHash=packet["inputHash"],
                elapsed=round(time.perf_counter() - started, 2),
                quality=note.get("quality", {}),
            )
            state.event(episode_id, "complete", attempt=attempt)
            return {"episode": episode_id, "status": "complete"}
        except Exception as exc:
            message = str(exc)[:1500]
            errors.append(message)
            state.event(episode_id, "attempt_failed", attempt=attempt, error=message)
            if attempt < retries:
                time.sleep(attempt * 3)
    state.update(episode_id, status="failed", error=errors[-1], attempts=retries)
    state.event(episode_id, "failed", error=errors[-1])
    return {"episode": episode_id, "status": "failed", "error": errors[-1]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--course", default="")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=9999)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--state", default="")
    args = parser.parse_args()

    settings = load_settings()
    store = CourseStore(settings.packs_dir)
    episodes = [
        episode for episode in store.episodes.values()
        if (not args.course or episode["courseId"] == args.course)
        and args.start <= int(episode["number"]) <= args.end
    ]
    episodes.sort(key=lambda row: (row["courseId"], int(row["number"])))
    if not episodes:
        raise SystemExit("no matching episodes")

    state_path = (
        Path(args.state).expanduser().resolve()
        if args.state
        else settings.data_dir / "cache" / "deep_notes" / "batch-state.json"
    )
    state = State(state_path)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [
            pool.submit(generate_one, settings, episode, state, args.force, args.retries)
            for episode in episodes
        ]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    failed = sorted(row["episode"] for row in results if row["status"] != "complete")
    print(json.dumps({
        "ok": not failed,
        "complete": len(results) - len(failed),
        "failed": failed,
        "state": str(state_path),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
