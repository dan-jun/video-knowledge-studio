from __future__ import annotations

import argparse
import html
import json
import mimetypes
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.parse
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .ai import TutorService
from .auth import Auth
from .config import Settings, load_settings
from .courses import CourseStore, safe_child
from .production import ProductionError, ProductionService
from .state import StateStore
from .workflows import WorkflowService


class Runtime:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.courses = CourseStore(settings.packs_dir)
        self.state = StateStore(settings.data_dir)
        self.auth = Auth(settings.password, settings.session_secret)
        self.tutor = TutorService(settings)
        self.production = ProductionService(settings.root, settings.data_dir)
        self.workflows = WorkflowService(self.production, settings.data_dir)
        self.jobs: dict[str, dict[str, Any]] = {}
        self.jobs_lock = threading.Lock()
        self.cache = settings.data_dir / "cache"
        self.cache.mkdir(parents=True, exist_ok=True)
        self.ffmpeg = os.environ.get("VKS_FFMPEG") or shutil.which("ffmpeg") or ""

    def create_job(self, packet: dict[str, Any], image_path: Path | None) -> str:
        jid = uuid.uuid4().hex[:12]
        with self.jobs_lock:
            self.jobs[jid] = {
                "id": jid,
                "status": "running",
                "started": time.time(),
                "result": None,
                "error": None,
            }
            if len(self.jobs) > 120:
                old = sorted(self.jobs.values(), key=lambda x: x["started"])[:20]
                for row in old:
                    self.jobs.pop(row["id"], None)

        def work():
            try:
                result = self.tutor.answer(packet, image_path)
                self.jobs[jid]["result"] = result
                self.jobs[jid]["status"] = "done"
            except subprocess.TimeoutExpired:
                self.jobs[jid]["status"] = "failed"
                self.jobs[jid]["error"] = "AI request timed out"
            except Exception as exc:
                self.jobs[jid]["status"] = "failed"
                self.jobs[jid]["error"] = str(exc)[:1500]
            finally:
                self.jobs[jid]["ended"] = time.time()

        threading.Thread(target=work, daemon=True).start()
        return jid

    def job(self, jid: str) -> dict[str, Any] | None:
        with self.jobs_lock:
            row = self.jobs.get(jid)
            return dict(row) if row else None

    def frame(self, episode_id: str, at: float) -> Path | None:
        ep = self.courses.get(episode_id)
        if not ep or not self.ffmpeg:
            return None
        safe_id = re.sub(r"[^0-9A-Za-z_-]+", "-", episode_id)
        out = self.cache / f"{safe_id}_{int(max(0, at) * 10):07d}.jpg"
        if out.is_file() and out.stat().st_size > 1000:
            return out
        proc = subprocess.run(
            [self.ffmpeg, "-y", "-v", "error", "-ss", str(max(0, at)),
             "-i", str(ep["videoPath"]), "-frames:v", "1", "-vf", "scale=960:-1", str(out)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return out if proc.returncode == 0 and out.is_file() else None

    def nearest_frame(self, episode_id: str, at: float) -> tuple[Path | None, float]:
        ep = self.courses.get(episode_id)
        if not ep:
            return None, at
        candidates = []
        for visual in ep["knowledge"].get("visuals", []):
            if not isinstance(visual, dict):
                continue
            t = visual.get("start", visual.get("at"))
            try:
                t = float(t)
            except (TypeError, ValueError):
                t = at
            if visual.get("file"):
                try:
                    path = safe_child(ep["packDir"], str(visual["file"]))
                    if path.is_file():
                        candidates.append((abs(t - at), path, t))
                except ValueError:
                    pass
        if candidates:
            candidates.sort(key=lambda x: x[0])
            _, path, t = candidates[0]
            return path, t
        path = self.frame(episode_id, at)
        return path, at


RUNTIME: Runtime


class Handler(BaseHTTPRequestHandler):
    server_version = "VideoKnowledgeStudio/0.2.8"

    def log_message(self, fmt, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {fmt % args}", flush=True)

    def _send_json(self, obj, status=200, cookie: str | None = None):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path | None, content_type: str | None = None, download=False):
        if not path or not path.is_file():
            self.send_error(404)
            return
        size = path.stat().st_size
        ctype = content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        start, end = 0, size - 1
        partial = False
        match = re.match(r"bytes=(\d+)-(\d*)", self.headers.get("Range", ""))
        if match and ctype.startswith("video/"):
            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else size - 1
            end = min(end, size - 1)
            partial = True
        self.send_response(206 if partial else 200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("X-Content-Type-Options", "nosniff")
        if partial:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        if download:
            self.send_header("Content-Disposition", f'attachment; filename="{path.name}"')
        self.end_headers()
        try:
            with path.open("rb") as file:
                file.seek(start)
                left = end - start + 1
                while left > 0:
                    chunk = file.read(min(262144, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return

    def _query(self):
        return urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

    def _token_query(self) -> str:
        return (self._query().get("t") or [""])[0]

    def _authed(self) -> bool:
        if not RUNTIME.auth.enabled:
            return True
        return RUNTIME.auth.authorized(self.headers) or RUNTIME.auth.check(self._token_query())

    def _guard(self, api=False) -> bool:
        if self._authed():
            return True
        if api:
            self._send_json({"ok": False, "error": "authentication required", "needLogin": True}, 401)
        else:
            self.send_response(302)
            self.send_header("Location", "/login.html")
            self.end_headers()
        return False

    def _body(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length > 2 * 1024 * 1024:
                raise ValueError("request is too large")
            value = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if not isinstance(value, dict):
                raise ValueError("JSON object required")
            return value
        except Exception as exc:
            raise ValueError(str(exc)) from exc

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/login":
            body = self._body()
            if RUNTIME.auth.verify(str(body.get("password") or "")):
                token = RUNTIME.auth.issue()
                cookie = f"vks_session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000"
                return self._send_json({"ok": True, "token": token}, cookie=cookie)
            return self._send_json({"ok": False, "error": "密码不正确"}, 401)
        if path == "/api/logout":
            return self._send_json({"ok": True}, cookie="vks_session=; Path=/; Max-Age=0; HttpOnly")
        if not self._guard(api=True):
            return
        try:
            body = self._body()
            if path == "/api/ai/ask":
                ep = RUNTIME.courses.get(str(body.get("id") or ""))
                if not ep:
                    return self._send_json({"ok": False, "error": "episode not found"}, 404)
                at = max(0.0, min(float(ep["duration"]), float(body.get("time") or 0)))
                selected = str(body.get("selected") or "")[:4000]
                question = str(body.get("question") or "")[:1500]
                if not selected and not question:
                    return self._send_json({"ok": False, "error": "select text or ask a question"}, 400)
                lesson = ep["knowledge"]
                transcript = []
                for row in lesson.get("transcript", []):
                    if not isinstance(row, dict):
                        continue
                    start = float(row.get("start") or 0)
                    end = float(row.get("end") or start)
                    if end >= at - 150 and start <= at + 150:
                        transcript.append({
                            "time": _fmt_clock(start),
                            "text": str(row.get("text") or "")[:1200],
                        })
                image_path, image_at = RUNTIME.nearest_frame(ep["id"], at)
                packet = {
                    "action": str(body.get("action") or "explain")[:24],
                    "selectedText": selected,
                    "selectedBlockId": str(body.get("kid") or "")[:160],
                    "currentVideoTime": _fmt_clock(at),
                    "userQuestion": question,
                    "outputLanguage": "en" if body.get("language") == "en" else "zh-CN",
                    "lectureData": {
                        "title": ep["title"],
                        "chapter": ep["chapter"],
                        "thesis": lesson.get("thesis", ""),
                        "formula": lesson.get("formula", ""),
                        "trap": lesson.get("trap", ""),
                        "memoryHook": lesson.get("memoryHook", ""),
                        "core": lesson.get("core", []),
                    },
                    "transcriptContext": transcript,
                    "recentConversation": body.get("history", [])[-4:],
                    "attachedFrameTime": _fmt_clock(image_at),
                }
                job = RUNTIME.create_job(packet, image_path)
                return self._send_json({"ok": True, "job": job, "status": "running"}, 202)
            if path == "/api/annotations":
                ep = RUNTIME.courses.get(str(body.get("id") or ""))
                if not ep:
                    return self._send_json({"ok": False, "error": "episode not found"}, 404)
                state = RUNTIME.state.annotation(ep["courseId"], ep["id"], body)
                return self._send_json({"ok": True, "state": state})
            if path == "/api/revisions":
                ep = RUNTIME.courses.get(str(body.get("id") or ""))
                if not ep:
                    return self._send_json({"ok": False, "error": "episode not found"}, 404)
                state = RUNTIME.state.revision(ep["courseId"], ep["id"], body)
                return self._send_json({"ok": True, "state": state})
            if path == "/api/reload":
                RUNTIME.courses.reload()
                return self._send_json({"ok": True, "projects": len(RUNTIME.courses.episodes)})
            if path == "/api/production/create":
                row = RUNTIME.production.create(
                    str(body.get("mode") or ""),
                    str(body.get("title") or ""),
                    str(body.get("spec") or ""),
                )
                return self._send_json({"ok": True, "project": row})
            if path == "/api/production/save":
                row = RUNTIME.production.save_spec(
                    str(body.get("id") or ""),
                    body.get("spec"),
                )
                return self._send_json({"ok": True, "project": row})
            if path == "/api/production/action":
                job = RUNTIME.production.start_job(
                    str(body.get("id") or ""),
                    str(body.get("action") or ""),
                )
                return self._send_json({"ok": True, "job": job}, 202)
            if path == "/api/production/cancel":
                ok = RUNTIME.production.cancel(str(body.get("job") or ""))
                return self._send_json({"ok": ok})
            if path == "/api/workflows/create":
                return self._send_json({"ok": True, "workflow": RUNTIME.workflows.create(str(body.get("project") or ""))}, 201)
            if path == "/api/workflows/resume":
                return self._send_json({"ok": True, "workflow": RUNTIME.workflows.resume(str(body.get("id") or ""))}, 202)
            if path == "/api/workflows/cancel":
                return self._send_json({"ok": True, "workflow": RUNTIME.workflows.cancel(str(body.get("id") or ""))}, 202)
            if path == "/api/workflows/abandon":
                return self._send_json({"ok": True, "workflow": RUNTIME.workflows.abandon(str(body.get("id") or ""))})
            if path == "/api/workflows/acknowledge-stopped":
                if body.get("confirmed") is not True:
                    raise ProductionError("explicit confirmation is required")
                return self._send_json({"ok": True, "workflow": RUNTIME.workflows.acknowledge_stopped(str(body.get("id") or ""))})
            return self._send_json({"ok": False, "error": "not found"}, 404)
        except (ValueError, KeyError, ProductionError) as exc:
            return self._send_json({"ok": False, "error": str(exc)}, 400)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = self._query()

        if path == "/login.html":
            return self._send_file(RUNTIME.settings.web_dir / "login.html", "text/html; charset=utf-8")
        if path in {"/app.css", "/app.js", "/knowledge.css", "/knowledge.js", "/i18n.js",
                    "/player.css", "/player.js", "/production.css", "/production.js",
                    "/favicon.svg"}:
            return self._send_file(RUNTIME.settings.web_dir / path.lstrip("/"))
        if path in {"/", "/index.html"}:
            if not self._guard():
                return
            return self._send_file(RUNTIME.settings.web_dir / "index.html", "text/html; charset=utf-8")
        if path == "/production.html":
            if not self._guard():
                return
            return self._send_file(
                RUNTIME.settings.web_dir / "production.html",
                "text/html; charset=utf-8",
            )
        if path.startswith("/media/") or path.startswith("/api/"):
            if not self._guard(api=True):
                return

        if path == "/api/projects":
            return self._send_json(RUNTIME.courses.projects())
        if path == "/api/ai/status":
            return self._send_json({"ok": True, **RUNTIME.tutor.status()})
        if path == "/api/production/modes":
            payload = RUNTIME.production.modes_payload()
            payload["templates"] = RUNTIME.production.templates()
            return self._send_json(payload)
        if path == "/api/production/template":
            return self._send_json({
                "ok": True,
                "spec": RUNTIME.production.template((query.get("name") or [""])[0]),
            })
        if path == "/api/production/projects":
            return self._send_json({
                "ok": True,
                "projects": RUNTIME.production.list_projects(),
            })
        if path == "/api/production/project":
            return self._send_json({
                "ok": True,
                "project": RUNTIME.production.project((query.get("id") or [""])[0]),
            })
        if path == "/api/production/job":
            row = RUNTIME.production.job((query.get("id") or [""])[0])
            if not row:
                return self._send_json({"ok": False, "error": "job not found"}, 404)
            return self._send_json({"ok": True, "job": row})
        if path == "/api/workflows":
            return self._send_json({"ok": True, "workflows": RUNTIME.workflows.list((query.get("project") or [""])[0])})
        if path == "/api/workflows/item":
            row = RUNTIME.workflows.get((query.get("id") or [""])[0])
            if not row:
                return self._send_json({"ok": False, "error": "workflow not found"}, 404)
            return self._send_json({"ok": True, "workflow": row})
        if path == "/api/ai/job":
            row = RUNTIME.job((query.get("id") or [""])[0])
            if not row:
                return self._send_json({"ok": False, "error": "job not found"}, 404)
            if row["status"] == "done":
                return self._send_json({"ok": True, **row})
            if row["status"] == "failed":
                return self._send_json({"ok": False, "error": row["error"], "status": "failed"}, 502)
            return self._send_json({"ok": True, "status": "running", "job": row["id"]})
        if path == "/api/knowledge":
            ep = RUNTIME.courses.get((query.get("id") or [""])[0])
            if not ep:
                return self._send_json({"ok": False, "error": "episode not found"}, 404)
            payload = RUNTIME.courses.knowledge_payload(ep["id"])
            payload["state"] = RUNTIME.state.load(ep["courseId"], ep["id"])
            payload["ai"] = RUNTIME.tutor.status()
            return self._send_json({"ok": True, **payload})
        if path == "/media/video":
            ep = RUNTIME.courses.get((query.get("id") or [""])[0])
            return self._send_file(ep["videoPath"] if ep else None, "video/mp4")
        if path == "/media/production":
            project = RUNTIME.production.project((query.get("id") or [""])[0])
            video = (
                RUNTIME.production.projects
                / project["id"]
                / "build"
                / "final_hardsub.mp4"
            )
            return self._send_file(video if video.is_file() else None, "video/mp4")
        if path == "/media/frame":
            ep = RUNTIME.courses.get((query.get("id") or [""])[0])
            if not ep:
                return self._send_file(None)
            try:
                at = float((query.get("at") or ["0"])[0])
            except ValueError:
                at = 0
            return self._send_file(RUNTIME.frame(ep["id"], at))
        if path == "/media/knowledge-frame":
            ep = RUNTIME.courses.get((query.get("id") or [""])[0])
            if not ep:
                return self._send_file(None)
            try:
                file_path = safe_child(ep["packDir"], (query.get("file") or [""])[0])
            except ValueError:
                return self._send_file(None)
            return self._send_file(file_path)
        return self._send_json({"ok": False, "error": "not found"}, 404)


def _fmt_clock(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def run(host: str | None = None, port: int | None = None):
    global RUNTIME
    settings = load_settings()
    host = host or settings.host
    port = port or settings.port
    if host not in {"127.0.0.1", "localhost", "::1"} and not settings.password:
        raise SystemExit("Remote binding requires VKS_PASSWORD. Use 127.0.0.1 for passwordless local use.")
    RUNTIME = Runtime(settings)
    if not RUNTIME.courses.courses:
        print(f"No course packs found in {settings.packs_dir}", flush=True)
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Video Knowledge Studio: http://{host}:{port}/", flush=True)
    print(f"Course packs: {len(RUNTIME.courses.courses)} | Episodes: {len(RUNTIME.courses.episodes)}", flush=True)
    print(f"AI provider: {RUNTIME.tutor.status()['provider']}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()
    run(args.host, args.port)
