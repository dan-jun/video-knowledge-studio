#!/usr/bin/env python3
"""Install the Codex skill and manage a local Video Knowledge Studio process."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_SOURCE = ROOT / "skill"
PLUGIN_SOURCE = ROOT / "plugins" / "video-knowledge-studio"
MARKETPLACE_NAME = "video-knowledge-studio-local"
PLUGIN_SELECTOR = f"video-knowledge-studio@{MARKETPLACE_NAME}"
PID_FILE = ROOT / "data" / "studio.pid"


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def agent_skills_home() -> Path:
    override = os.environ.get("VKS_AGENT_SKILLS_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    preferred = Path.home() / ".agents" / "skills"
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        return preferred
    except OSError:
        fallback = codex_home() / "skills"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def bundled_skills() -> list[Path]:
    return sorted(
        path
        for path in SKILLS_SOURCE.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )


def install_skills() -> list[Path]:
    installed = []
    destination_root = agent_skills_home()
    for source in bundled_skills():
        destination = destination_root / source.name
        if destination.exists():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            shutil.copytree(source, destination)
        installed.append(destination)
    return installed


def sync_plugin_bundle() -> None:
    try:
        from sync_plugin import sync
    except ModuleNotFoundError:
        from scripts.sync_plugin import sync

    sync()


def install_codex_plugin() -> dict:
    codex = shutil.which("codex")
    if not codex:
        return {"installed": False, "reason": "Codex CLI not found"}
    attempts = []
    marketplace = subprocess.run(
        [codex, "plugin", "marketplace", "add", str(ROOT), "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    attempts.append({
        "step": "marketplace",
        "returncode": marketplace.returncode,
        "output": (marketplace.stdout or marketplace.stderr or "").strip()[-1000:],
    })
    subprocess.run(
        [codex, "plugin", "remove", PLUGIN_SELECTOR, "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    installation = subprocess.run(
        [codex, "plugin", "add", PLUGIN_SELECTOR, "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    attempts.append({
        "step": "plugin",
        "returncode": installation.returncode,
        "output": (installation.stdout or installation.stderr or "").strip()[-1000:],
    })
    combined_output = (installation.stdout or "") + (installation.stderr or "")
    succeeded = installation.returncode == 0 or "already" in combined_output.lower()
    return {
        "installed": succeeded,
        "selector": PLUGIN_SELECTOR,
        "marketplace": str(ROOT),
        "attempts": attempts,
    }


def install_agent_bundle(no_plugin: bool = False) -> dict:
    if not (PLUGIN_SOURCE / "plugin.json").is_file():
        raise SystemExit(f"plugin manifest is missing: {PLUGIN_SOURCE}")
    sync_plugin_bundle()
    if not no_plugin:
        plugin = install_codex_plugin()
        if plugin["installed"]:
            return {
                "method": "plugin",
                "plugin": plugin,
                "skills": [],
                "restart_required": True,
            }
    else:
        plugin = {"installed": False, "reason": "disabled by --no-plugin"}
    skills = install_skills()
    return {
        "method": "skills",
        "plugin": plugin,
        "skills": [str(path) for path in skills],
        "restart_required": True,
    }


def port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def healthy(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=0.6) as response:
            return response.status in (200, 302)
    except (OSError, urllib.error.URLError):
        return False


def choose_port(requested: int) -> int:
    for port in range(requested, requested + 30):
        if not port_open(port):
            return port
    raise SystemExit(f"no free port in {requested}-{requested + 29}")


def prepare_course(path_value: str | None) -> tuple[Path, str]:
    if not path_value:
        return ROOT / "packs", "auto"
    course = Path(path_value).expanduser().resolve()
    if not course.is_dir():
        raise SystemExit(f"course folder does not exist: {course}")
    manifest = course / "course.json"
    if not manifest.is_file():
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "import_course.py"),
             "--input", str(course), "--title", course.name],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if result.returncode != 0:
            raise SystemExit(result.stderr.strip() or result.stdout.strip())
    return course, "auto"


def write_local_config(packs: Path) -> Path:
    env_file = ROOT / ".env"
    if env_file.exists():
        return env_file
    env_file.write_text(
        "# Generated by scripts/bootstrap.py. Review before remote deployment.\n"
        f"VKS_PACKS={packs}\n"
        f"VKS_DATA={ROOT / 'data'}\n"
        "VKS_AI_PROVIDER=auto\n",
        encoding="utf-8",
    )
    return env_file


def read_pid() -> int | None:
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def process_alive(pid: int) -> bool:
    if os.name == "nt":
        import ctypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return ctypes.get_last_error() == 5  # access denied still means it exists
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def start(args) -> dict:
    packs, provider = prepare_course(args.course)
    env_file = write_local_config(packs)
    port = choose_port(args.port)
    env = {
        **os.environ,
        "VKS_PACKS": str(packs),
        "VKS_DATA": str(ROOT / "data"),
        "VKS_AI_PROVIDER": args.ai_provider or provider,
    }
    log_path = ROOT / "data" / "studio.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    with log_path.open("ab") as log:
        proc = subprocess.Popen(
            [sys.executable, "-m", "vks", "--host", "127.0.0.1", "--port", str(port)],
            cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=log,
            stderr=subprocess.STDOUT, creationflags=creationflags,
        )
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    for _ in range(60):
        if healthy(port):
            break
        if proc.poll() is not None:
            raise SystemExit(f"studio exited early; see {log_path}")
        time.sleep(0.25)
    else:
        proc.terminate()
        raise SystemExit(f"studio did not become healthy; see {log_path}")
    url = f"http://127.0.0.1:{port}/"
    if args.open:
        webbrowser.open(url)
    return {
        "ok": True, "url": url, "pid": proc.pid, "packs": str(packs),
        "log": str(log_path), "env": str(env_file),
    }


def status() -> dict:
    pid = read_pid()
    if pid and process_alive(pid):
        return {"ok": True, "running": True, "pid": pid}
    return {"ok": True, "running": False}


def stop() -> dict:
    pid = read_pid()
    if not pid or not process_alive(pid):
        return {"ok": True, "running": False, "message": "not running"}
    os.kill(pid, 15)
    for _ in range(20):
        if not process_alive(pid):
            break
        time.sleep(0.1)
    try:
        PID_FILE.unlink()
    except OSError:
        pass
    return {"ok": True, "running": False, "pid": pid}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=["install", "start", "status", "stop"], default="install")
    parser.add_argument("--course", help="existing folder of videos; a starter course.json is created if absent")
    parser.add_argument("--port", type=int, default=7870)
    parser.add_argument("--ai-provider", choices=["auto", "codex", "openai", "mock"], default="auto")
    parser.add_argument("--open", action="store_true", help="open the local URL after startup")
    parser.add_argument(
        "--no-plugin",
        action="store_true",
        help="install the bundled skills directly instead of registering the Codex plugin",
    )
    args = parser.parse_args()
    result: dict = {}
    if args.command in {"install", "start"}:
        result["agent_bundle"] = install_agent_bundle(args.no_plugin)
    if args.command == "start":
        result.update(start(args))
    elif args.command == "status":
        result.update(status())
    elif args.command == "stop":
        result.update(stop())
    else:
        result.update({"ok": True, "installed": True})
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
