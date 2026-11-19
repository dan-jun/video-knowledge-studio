"""Optional video-production service for the three Video Forge modes."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any


class ProductionError(ValueError):
    pass


class ProductionService:
    """Manage local remix/course/scipop projects and their subprocess jobs."""

    def __init__(self, root: Path, data_dir: Path):
        self.root = root / "production"
        self.tools = self.root / "tools"
        self.specs = self.root / "specs"
        self.projects = data_dir / "production" / "projects"
        self.projects.mkdir(parents=True, exist_ok=True)
        self.jobs: dict[str, dict[str, Any]] = {}
        self.processes: dict[str, subprocess.Popen] = {}
        self.lock = threading.RLock()
        self._modes = self._load_modes()

    def _load_modes(self) -> dict[str, dict[str, Any]]:
        path = self.tools / "modes.py"
        spec = importlib.util.spec_from_file_location("vks_forge_modes", path)
        if not spec or not spec.loader:
            raise ProductionError("production/tools/modes.py is missing")
        module = importlib.util.module_from_spec(spec)
        previous = sys.path[:]
        try:
            sys.path.insert(0, str(self.tools))
            spec.loader.exec_module(module)
        finally:
            sys.path[:] = previous
        return module.MODES

    def modes_payload(self) -> dict[str, Any]:
        return {
            "ok": True,
            "modes": [
                {
                    "id": key,
                    "label": value["label"],
                    "target_min": value["target_min"],
                    "rules": [desc for desc, _key in value["rules"]],
                }
                for key, value in self._modes.items()
            ],
            "dependencies": self.dependencies(),
        }

    def dependencies(self) -> dict[str, Any]:
        modules = {
            "manim": "manim",
            "edge_tts": "edge-tts",
            "PIL": "Pillow",
            "matplotlib": "matplotlib",
            "fontTools": "fonttools",
        }
        missing = [
            package
            for module, package in modules.items()
            if importlib.util.find_spec(module) is None
        ]
        ffmpeg = shutil.which("ffmpeg")
        ffprobe = shutil.which("ffprobe")
        if not ffmpeg:
            missing.append("ffmpeg")
        if not ffprobe:
            missing.append("ffprobe")
        return {
            "ready": not missing,
            "missing": missing,
            "install": 'python -m pip install -e ".[production]"',
        }

    def templates(self) -> list[dict[str, Any]]:
        rows = []
        for path in sorted(self.specs.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            rows.append({"name": path.stem, "title": data.get("title", path.stem)})
        return rows

    def template(self, name: str) -> dict[str, Any]:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", name or ""):
            raise ProductionError("invalid template name")
        path = self.specs / f"{name}.json"
        if not path.is_file():
            raise ProductionError("template not found")
        return json.loads(path.read_text(encoding="utf-8"))

    def _project(self, project_id: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,80}", project_id or ""):
            raise ProductionError("invalid project id")
        path = (self.projects / project_id).resolve()
        if path.parent != self.projects.resolve() or not path.is_dir():
            raise ProductionError("project not found")
        return path

    @staticmethod
    def _summary(path: Path) -> dict[str, Any]:
        agent = {}
        try:
            agent = json.loads((path / "agent.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
        video = path / "build" / "final_hardsub.mp4"
        return {
            "id": path.name,
            "title": agent.get("title") or path.name,
            "mode": agent.get("mode", ""),
            "label": agent.get("label", ""),
            "stage": agent.get("stage", "planned"),
            "hasStoryboard": (path / "storyboard.json").is_file(),
            "hasVideo": video.is_file() and video.stat().st_size > 1024,
            "videoBytes": video.stat().st_size if video.is_file() else 0,
            "updated": int(video.stat().st_mtime) if video.is_file() else int(path.stat().st_mtime),
        }

    def list_projects(self) -> list[dict[str, Any]]:
        rows = [
            self._summary(path)
            for path in self.projects.iterdir()
            if path.is_dir() and (path / "agent.json").is_file()
        ]
        return sorted(rows, key=lambda row: row["updated"], reverse=True)

    def project(self, project_id: str) -> dict[str, Any]:
        path = self._project(project_id)
        data = self._summary(path)
        spec_path = path / "spec.json"
        try:
            data["spec"] = json.loads(spec_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data["spec"] = None
        return data

    def create(self, mode: str, title: str, spec_text: str = "") -> dict[str, Any]:
        if mode not in self._modes:
            raise ProductionError("unknown production mode")
        title = str(title or "").strip()[:120]
        if not title:
            raise ProductionError("title is required")
        if spec_text.strip():
            try:
                spec = json.loads(spec_text)
            except json.JSONDecodeError as exc:
                raise ProductionError(f"invalid spec JSON: {exc}") from exc
            if not isinstance(spec, dict):
                raise ProductionError("spec must be a JSON object")
        else:
            spec = self._starter_spec(mode, title)

        pages = spec.get("pages") or [
            page
            for part in spec.get("parts", [])
            for page in part.get("pages", [])
        ]
        if not isinstance(pages, list) or not pages:
            raise ProductionError("spec must contain pages")
        if len(pages) > 240:
            raise ProductionError("spec exceeds 240 pages")

        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:36] or "video"
        project_id = f"{mode}-{slug}-{uuid.uuid4().hex[:6]}"
        path = self.projects / project_id
        path.mkdir(parents=True)
        spec["topic"] = project_id
        spec["title"] = title
        spec.setdefault("style", "SOLARA")
        (path / "spec.json").write_text(
            json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        mode_info = self._modes[mode]
        agent = {
            "mode": mode,
            "title": title,
            "label": mode_info["label"],
            "params": {
                key: value
                for key, value in mode_info.items()
                if key not in ("label", "rules", "rules_text")
            },
            "rules": [desc for desc, _key in mode_info["rules"]],
            "stage": "planned",
        }
        (path / "agent.json").write_text(
            json.dumps(agent, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return self.project(project_id)

    def save_spec(self, project_id: str, spec: dict[str, Any]) -> dict[str, Any]:
        path = self._project(project_id)
        if not isinstance(spec, dict):
            raise ProductionError("spec must be an object")
        guard = getattr(self, "mutation_guard", None)
        if guard:
            guard(project_id)
        with self.lock:
            if any(row["project"] == project_id and row["status"] == "running" for row in self.jobs.values()):
                raise ProductionError("cannot edit a spec while a production job is running")
            spec["topic"] = project_id
            (path / "spec.json").write_text(
                json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        return self.project(project_id)

    def _starter_spec(self, mode: str, title: str) -> dict[str, Any]:
        return {
            "topic": "draft",
            "title": title,
            "style": "SOLARA",
            "part": self._modes[mode]["label"],
            "keys": "本页要讲清的核心问题 | 核心问题\n最终结论 | 结论\n",
            "transcript": "请根据真实来源补充讲稿和出处。",
            "pages": [
                {
                    "id": "c01",
                    "type": "title",
                    "title": title,
                    "narration": f"这一集我们讲清：{title}。先说明问题，再给出证据和结论。",
                },
                {
                    "id": "c02",
                    "type": "bullets",
                    "title": "先问一个问题",
                    "narration": "先看一个问题：这个现象为什么发生？我们从一个具体例子开始。",
                    "items": ["先看具体现象", "再拆原因", "最后用例子验证"],
                },
                {
                    "id": "c03",
                    "type": "bullets",
                    "title": "证据与推理",
                    "narration": "接下来把来源中的证据按顺序整理，区分事实、推理和结论。",
                    "items": ["来源事实", "推理步骤", "可验证结论"],
                },
                {
                    "id": "c04",
                    "type": "quiz",
                    "title": "练一题",
                    "narration": "停一下做道题。哪一步最能验证结论？可以暂停三秒想一想，我们接着看答案。",
                    "question": ["哪一步最能验证结论？", "A. 引用事实并复现", "B. 只看标题"],
                },
                {
                    "id": "c05",
                    "type": "answer",
                    "title": "答案",
                    "narration": "答案是 A。结论必须能由事实和可复现步骤支持，标题本身不能当证据。",
                    "items": ["事实", "推理", "复现"],
                },
                {
                    "id": "c06",
                    "type": "recap",
                    "title": "复盘",
                    "narration": "我们回顾一下。第一，先说清问题；第二，用来源支撑推理；第三，给出可验证结论。",
                    "items": ["定义问题", "保留证据", "验证结论"],
                },
            ],
        }

    def _command(self, project_id: str, action: str, path: Path) -> list[str]:
        py = sys.executable
        if action == "generate":
            return [
                py,
                str(self.tools / "anim_gen.py"),
                str(path / "spec.json"),
                "--mode",
                json.loads((path / "agent.json").read_text(encoding="utf-8"))["mode"],
                "--project",
                str(path),
            ]
        if action == "gates":
            mode = json.loads((path / "agent.json").read_text(encoding="utf-8"))["mode"]
            return [
                py,
                str(self.tools / "modes.py"),
                "check",
                "--mode",
                mode,
                "--project",
                str(path),
            ]
        if action in {"render", "qa", "verify", "status"}:
            return [
                py,
                str(self.tools / "video_agent.py"),
                action,
                "--project",
                str(path),
            ]
        raise ProductionError("unsupported production action")

    def start_job(self, project_id: str, action: str, *, from_workflow: bool = False) -> dict[str, Any]:
        guard = getattr(self, "workflow_guard", None)
        if guard and not from_workflow:
            guard(project_id)
        path = self._project(project_id)
        dependencies = self.dependencies()
        if action in {"gates", "render", "qa", "verify"} and not dependencies["ready"]:
            raise ProductionError(
                "production dependencies are missing: "
                + ", ".join(dependencies["missing"])
                + '. Install with: python -m pip install -e ".[production]"'
            )
        if action in {"gates", "render", "qa", "verify"} and not (path / "storyboard.json").is_file():
            raise ProductionError("generate the storyboard first")
        command = self._command(project_id, action, path)
        jid = uuid.uuid4().hex[:12]
        with self.lock:
            for row in self.jobs.values():
                if row["project"] == project_id and row["status"] == "running":
                    raise ProductionError("another job is already running for this project")
            self.jobs[jid] = {
                "id": jid,
                "project": project_id,
                "action": action,
                "status": "running",
                "logs": [],
                "started": time.time(),
                "returncode": None,
            }

        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        env["VKS_PRODUCTION_ROOT"] = str(self.projects)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(self.tools), env.get("PYTHONPATH", "")]
        ).strip(os.pathsep)
        try:
            proc = subprocess.Popen(
                command, cwd=str(self.root), env=env, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", bufsize=1,
                start_new_session=(os.name != "nt"),
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0,
            )
        except OSError as exc:
            with self.lock:
                self.jobs[jid].update(status="failed", ended=time.time(), returncode=-1)
                self.jobs[jid]["logs"].append(f"Failed to start: {exc}")
            raise ProductionError(f"failed to start job: {exc}") from exc
        with self.lock:
            self.processes[jid] = proc
            self.jobs[jid]["pid"] = proc.pid

        def collect() -> None:
            try:
                assert proc.stdout is not None
                captured = []
                captured_size = 0
                for line in proc.stdout:
                    captured.append(line)
                    captured_size += len(line)
                    if captured_size > 1_000_000:
                        captured = captured[-1000:]
                        captured_size = sum(map(len, captured))
                    with self.lock:
                        logs = self.jobs[jid]["logs"]
                        logs.append(line.rstrip())
                        if len(logs) > 500:
                            del logs[:100]
                code = proc.wait()
                output = "".join(captured)
                structured_ok = None
                if action in {"render", "qa", "verify"}:
                    decoder = json.JSONDecoder()
                    parsed_until = 0
                    for match in re.finditer(r"\{", output):
                        if match.start() < parsed_until:
                            continue
                        try:
                            value, consumed = decoder.raw_decode(output[match.start():])
                        except json.JSONDecodeError:
                            continue
                        parsed_until = match.start() + consumed
                        if isinstance(value, dict) and isinstance(value.get("ok"), bool):
                            structured_ok = value["ok"]
                with self.lock:
                    self.jobs[jid]["returncode"] = code
                    success = code == 0 and (action not in {"render", "qa", "verify"} or structured_ok is True)
                    self.jobs[jid]["status"] = "cancelled" if self.jobs[jid].get("cancelRequested") else ("done" if success else "failed")
                    if code == 0 and not success:
                        self.jobs[jid]["logs"].append("Production command did not report a successful structured result.")
                    self.jobs[jid]["ended"] = time.time()
                if code == 0 and action == "generate" and not self.jobs[jid].get("cancelRequested"):
                    agent_path = path / "agent.json"
                    try:
                        meta = json.loads(agent_path.read_text(encoding="utf-8"))
                        meta["stage"] = "generated"
                        agent_path.write_text(
                            json.dumps(meta, ensure_ascii=False, indent=2),
                            encoding="utf-8",
                        )
                    except (OSError, json.JSONDecodeError):
                        pass
            except Exception as exc:
                with self.lock:
                    self.jobs[jid]["status"] = "failed"
                    self.jobs[jid]["returncode"] = -1
                    self.jobs[jid]["logs"].append(f"{type(exc).__name__}: {exc}")
                    self.jobs[jid]["ended"] = time.time()
            finally:
                if proc.stdout:
                    proc.stdout.close()
                with self.lock:
                    self.processes.pop(jid, None)

        threading.Thread(target=collect, daemon=True).start()
        return self.job(jid)

    def job(self, job_id: str) -> dict[str, Any] | None:
        with self.lock:
            row = self.jobs.get(job_id)
            return dict(row, logs=list(row["logs"])) if row else None

    def cancel(self, job_id: str) -> bool:
        with self.lock:
            proc = self.processes.get(job_id)
            row = self.jobs.get(job_id)
            if not proc or not row or row["status"] != "running":
                return False
            row["cancelRequested"] = True
            try:
                if os.name == "nt":
                    result = subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, timeout=10)
                    if result.returncode and proc.poll() is None:
                        row["cancelRequested"] = False
                        raise ProductionError("could not stop the process tree")
                else:
                    os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            return True
