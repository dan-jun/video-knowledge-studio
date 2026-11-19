"""Durable, stage-level production workflows with explicit review checkpoints."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path

from .production import ProductionError, ProductionService

STEPS = ("generate", "gates", "render")
ACTIVE = {"running", "cancelling"}


class WorkflowService:
    def __init__(self, production: ProductionService, data_dir: Path):
        self.production = production
        self.root = data_dir / "production" / "workflows"
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.rows = {}
        self.production.workflow_guard = self.assert_idle
        self.production.mutation_guard = self.assert_editable
        for path in self.root.glob("*.json"):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
                if not re.fullmatch(r"[0-9a-f]{12}", str(row.get("id", ""))) or path.stem != row["id"]:
                    continue
                if row.get("status") in ACTIVE or any(step.get("status") == "running" for step in row.get("steps", [])):
                    row["status"] = "interrupted"
                    row["message"] = "Server restarted; check for an unfinished process before resuming."
                    self._save(row)
                self.rows[row["id"]] = row
            except (OSError, ValueError, TypeError):
                continue

    def _save(self, row):
        row["updated"] = time.time()
        path = self.root / (row["id"] + ".json")
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)

    def _spec_hash(self, project):
        path = self.production._project(project) / "spec.json"
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def assert_idle(self, project):
        with self.lock:
            if any(r["project"] == project and r["status"] in ACTIVE | {"interrupted"} for r in self.rows.values()):
                raise ProductionError("cannot edit a spec while a workflow is active")

    def assert_editable(self, project):
        with self.lock:
            if any(r["project"] == project and r["status"] in ACTIVE | {"interrupted", "waiting_review"} for r in self.rows.values()):
                raise ProductionError("cannot edit a spec while a workflow is active or awaiting review")

    def get(self, workflow_id):
        with self.lock:
            row = self.rows.get(workflow_id)
            return json.loads(json.dumps(row)) if row else None

    def list(self, project=None):
        with self.lock:
            return sorted((self.get(r["id"]) for r in self.rows.values() if not project or r["project"] == project), key=lambda x: x["updated"], reverse=True)

    def create(self, project):
        with self.lock:
            spec_hash = self._spec_hash(project)
            if any(r["project"] == project and r["status"] in ACTIVE | {"interrupted", "waiting_review"} for r in self.rows.values()):
                raise ProductionError("an existing workflow is active, interrupted or awaiting review")
            if any(j["project"] == project and j["status"] == "running" for j in self.production.jobs.values()):
                raise ProductionError("a production job is already running for this project")
            for previous in self.rows.values():
                if previous["project"] == project and previous["status"] == "ready":
                    previous.update(status="abandoned", message="Superseded by a new workflow.")
                    self._save(previous)
            row = {"id": uuid.uuid4().hex[:12], "project": project, "status": "ready",
                   "steps": [{"action": s, "status": "pending", "job": None} for s in STEPS],
                   "specHash": spec_hash, "created": time.time(), "message": "Review the spec before starting."}
            self.rows[row["id"]] = row
            self._save(row)
            return self.get(row["id"])

    def resume(self, workflow_id):
        with self.lock:
            row = self.rows.get(workflow_id)
            if not row:
                raise ProductionError("workflow not found")
            if row["status"] in ACTIVE or row["status"] in {"done", "abandoned"}:
                raise ProductionError("workflow cannot be resumed in its current state")
            if any(other["id"] != workflow_id and other["project"] == row["project"] and other["status"] in ACTIVE | {"interrupted", "waiting_review"} for other in self.rows.values()):
                raise ProductionError("another workflow is active, interrupted or awaiting review for this project")
            if self._spec_hash(row["project"]) != row["specHash"]:
                raise ProductionError("spec changed; create a new workflow")
            if row["status"] == "interrupted":
                raise ProductionError("interrupted process may still be running; stop it and create a new workflow")
            if any(r["project"] == row["project"] and r["id"] != workflow_id and r["created"] > row["created"] for r in self.rows.values()):
                raise ProductionError("a newer workflow exists for this project; use it or create a new one")
            generate = row["steps"][0]
            storyboard = self.production._project(row["project"]) / "storyboard.json"
            if generate["status"] == "done" and (not storyboard.is_file() or hashlib.sha256(storyboard.read_bytes()).hexdigest() != row.get("storyboardHash")):
                raise ProductionError("storyboard changed or disappeared; create a new workflow")
            step = next((s for s in row["steps"] if s["status"] != "done"), None)
            if not step:
                raise ProductionError("workflow is already complete")
            row["status"] = "running"
            row["cancelRequested"] = False
            row["message"] = "Running " + step["action"]
            step.update(status="running", job=None, startedNs=time.time_ns())
            self._save(row)
            try:
                job = self.production.start_job(row["project"], step["action"], from_workflow=True)
            except Exception as exc:
                step["status"] = "failed"
                row.update(status="failed", message=str(exc), activePid=None)
                self._save(row)
                raise ProductionError(str(exc)) from exc
            if self._spec_hash(row["project"]) != row["specHash"]:
                self.production.cancel(job["id"])
                step["job"] = job["id"]
                row.update(status="failed", message="Spec changed while starting; inspect the project and create a new workflow.", activePid=None)
                step["status"] = "failed"
                self._save(row)
                raise ProductionError(row["message"])
            step["job"] = job["id"]
            row["activePid"] = job.get("pid")
            self._save(row)
            threading.Thread(target=self._watch, args=(workflow_id, step["action"], job["id"]), daemon=True).start()
            return self.get(workflow_id)

    def abandon(self, workflow_id):
        with self.lock:
            row = self.rows.get(workflow_id)
            if not row or row["status"] not in {"ready", "waiting_review", "failed", "cancelled", "interrupted"}:
                raise ProductionError("workflow cannot be abandoned in its current state")
            if row["status"] == "interrupted":
                raise ProductionError("inspect and stop the previous process tree, then explicitly confirm it is stopped")
            row["activePid"] = None
            row.update(status="abandoned", message="Workflow abandoned; a new spec or workflow may be created.")
            self._save(row)
            return self.get(workflow_id)

    def acknowledge_stopped(self, workflow_id):
        with self.lock:
            row = self.rows.get(workflow_id)
            if not row or row["status"] != "interrupted":
                raise ProductionError("workflow is not interrupted")
            row.update(status="abandoned", activePid=None, message="Abandoned after the operator confirmed the old process tree stopped.")
            self._save(row)
            return self.get(workflow_id)

    def _watch(self, workflow_id, action, job_id):
        while True:
            job = self.production.job(job_id)
            if not job or job["status"] != "running":
                break
            time.sleep(.15)
        with self.lock:
            row = self.rows[workflow_id]
            step = next(s for s in row["steps"] if s["action"] == action)
            step["logs"] = (job or {}).get("logs", [])[-100:]
            status = (job or {}).get("status", "failed")
            step["status"] = status
            row["activePid"] = None
            if status == "done":
                try:
                    spec_matches = self._spec_hash(row["project"]) == row["specHash"]
                except OSError:
                    spec_matches = False
                if not spec_matches:
                    step["status"] = "failed"
                    row.update(status="failed", message="Spec changed during execution; inspect the output and create a new workflow.")
                    self._save(row)
                    return
                if action == "generate":
                    storyboard = self.production._project(row["project"]) / "storyboard.json"
                    if not storyboard.is_file():
                        step["status"] = "failed"
                        row.update(status="failed", message="Generation finished without a storyboard.")
                        self._save(row)
                        return
                    row["storyboardHash"] = hashlib.sha256(storyboard.read_bytes()).hexdigest()
                if action == "render":
                    output = self.production._project(row["project"]) / "build" / "final_hardsub.mp4"
                    ffprobe = shutil.which("ffprobe")
                    playable = False
                    if ffprobe and output.is_file() and output.stat().st_size > 1024 and output.stat().st_mtime_ns >= step.get("startedNs", 0):
                        try:
                            probe = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(output)], capture_output=True, text=True, timeout=15)
                            playable = probe.returncode == 0 and float(probe.stdout.strip()) > 0
                        except (OSError, ValueError, subprocess.TimeoutExpired):
                            pass
                    if not playable:
                        step["status"] = "failed"
                        row.update(status="failed", message="Render finished without an ffprobe-readable output file.")
                    else:
                        row.update(status="done", message="Render finished; inspect playback, frames and evidence.")
                else:
                    row.update(status="waiting_review", message=f"{action} completed. Review before continuing.")
            else:
                row.update(status=status, message=f"{action} {status}; inspect logs before retrying.")
            self._save(row)

    def cancel(self, workflow_id):
        with self.lock:
            row = self.rows.get(workflow_id)
            if not row or row["status"] != "running":
                raise ProductionError("workflow is not running")
            step = next(s for s in row["steps"] if s["status"] == "running")
            if not self.production.cancel(step["job"]):
                raise ProductionError("job already finished or cannot be cancelled")
            row.update(status="cancelling", cancelRequested=True, message="Stopping process tree.")
            self._save(row)
            return self.get(workflow_id)
