"""Local MCP stdio bridge for the running Video Knowledge Studio HTTP service.

This bridge never starts a service or sends source material anywhere on its own.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from .discovery import search


def api(path, body=None):
    base = os.environ.get("VKS_MCP_URL", "http://127.0.0.1:7870").rstrip("/")
    parsed = urllib.parse.urlsplit(base)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"} or parsed.username or parsed.password or parsed.path:
        raise ValueError("VKS_MCP_URL must be a local HTTP origin")
    token = os.environ.get("VKS_MCP_TOKEN", "")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-VKS-Token"] = token
    request = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(), headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read(8192).decode("utf-8", "replace")
        raise ValueError(f"HTTP {exc.code}: {detail}") from exc


def schema(properties=None, required=None):
    return {"type": "object", "properties": properties or {}, "required": required or [], "additionalProperties": False}


S = {"type": "string"}
TOOLS = [
    {"name": "capabilities", "description": "Report current capabilities and explicit external-search limitations.", "inputSchema": schema()},
    {"name": "list_courses", "description": "List available local course episodes.", "inputSchema": schema()},
    {"name": "search_sources", "description": "Search Bilibili or YouTube metadata using an installed yt-dlp. Sends the query to the selected platform; does not download videos or verify rights.", "inputSchema": schema({"platform": {"type":"string", "enum":["bilibili","youtube"]}, "query": S, "limit": {"type":"number", "minimum":1}}, ["platform", "query"])},
    {"name": "read_lesson", "description": "Read a lesson and its source-linked notes.", "inputSchema": schema({"episode_id": S}, ["episode_id"])},
    {"name": "list_production_projects", "description": "List local video production projects.", "inputSchema": schema()},
    {"name": "create_production_project", "description": "Create a production project from a reviewed spec JSON or a placeholder. Never invent sources.", "inputSchema": schema({"mode": {"type":"string", "enum":["remix","course","scipop"]}, "title": S, "spec_json": S}, ["mode", "title"])},
    {"name": "create_workflow", "description": "Create a reviewable generate/check/render workflow for a production project.", "inputSchema": schema({"project_id": S}, ["project_id"])},
    {"name": "workflow_status", "description": "Read persistent workflow status and completed-step logs.", "inputSchema": schema({"workflow_id": S}, ["workflow_id"])},
    {"name": "workflow_resume", "description": "Start or retry the next production step after user review.", "inputSchema": schema({"workflow_id": S}, ["workflow_id"])},
    {"name": "workflow_cancel", "description": "Stop the running production step and its child processes.", "inputSchema": schema({"workflow_id": S}, ["workflow_id"])},
    {"name": "workflow_abandon", "description": "Abandon an idle workflow to edit its spec or create a new one.", "inputSchema": schema({"workflow_id": S}, ["workflow_id"])},
    {"name": "ask_lesson", "description": "Start a contextual question. This sends lesson context to the configured AI provider.", "inputSchema": schema({"episode_id": S, "question": S, "time": {"type":"number", "minimum":0}, "selected": S}, ["episode_id", "question"])},
    {"name": "answer_status", "description": "Read the result of a contextual question.", "inputSchema": schema({"job_id": S}, ["job_id"])},
]


def invoke(name, a):
    definition = next((tool for tool in TOOLS if tool["name"] == name), None)
    if not definition or not isinstance(a, dict):
        raise ValueError("unknown tool or invalid arguments")
    spec = definition["inputSchema"]
    if set(a) - set(spec["properties"]) or any(key not in a for key in spec["required"]):
        raise ValueError("missing or unexpected arguments")
    for key, value in a.items():
        rule = spec["properties"][key]
        if rule["type"] == "string" and not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        if rule["type"] == "number" and (isinstance(value, bool) or not isinstance(value, (int, float)) or value < rule.get("minimum", 0)):
            raise ValueError(f"{key} must be a nonnegative number")
        if "enum" in rule and value not in rule["enum"]:
            raise ValueError(f"invalid {key}")
    q = lambda v: urllib.parse.quote(str(v), safe="")
    if name == "capabilities":
        return {"built_in": ["course playback and notes", "contextual questions", "production projects", "reviewable production workflow"],
                "optional_tools": ["Bilibili/YouTube metadata search via yt-dlp (platform access may fail)"],
                "external_agent_required": ["source selection", "source transcription and review", "sourced lesson planning and spec authoring"],
                "limitations": ["imported notes are placeholders", "workflow starts from a reviewed spec", "review each checkpoint", "not a one-click topic-to-course pipeline"]}
    if name == "list_courses": return api("/api/projects")
    if name == "search_sources": return search(a["platform"], a["query"], a.get("limit", 5))
    if name == "read_lesson": return api("/api/knowledge?id=" + q(a["episode_id"]))
    if name == "list_production_projects": return api("/api/production/projects")
    if name == "create_production_project": return api("/api/production/create", {"mode": a["mode"], "title": a["title"], "spec": a.get("spec_json", "")})
    if name == "create_workflow": return api("/api/workflows/create", {"project": a["project_id"]})
    if name == "workflow_status": return api("/api/workflows/item?id=" + q(a["workflow_id"]))
    if name in {"workflow_resume", "workflow_cancel", "workflow_abandon"}: return api("/api/workflows/" + name.removeprefix("workflow_"), {"id": a["workflow_id"]})
    if name == "ask_lesson": return api("/api/ai/ask", {"id": a["episode_id"], "question": a["question"], "time": a.get("time", 0), "selected": a.get("selected", ""), "language": "en"})
    if name == "answer_status": return api("/api/ai/job?id=" + q(a["job_id"]))
    raise ValueError("unknown tool")


def dispatch(msg):
    method, request_id = msg.get("method"), msg.get("id")
    if request_id is None:
        return None
    if method == "initialize":
        result = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": "video-knowledge-studio", "version": "0.2.8"}}
    elif method == "ping": result = {}
    elif method == "tools/list": result = {"tools": TOOLS}
    elif method == "tools/call":
        params = msg.get("params") or {}
        try:
            value = invoke(params.get("name"), params.get("arguments") or {})
            result = {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}], "isError": False}
        except Exception as exc:
            result = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
    else:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Method not found"}}
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def main():
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        try:
            response = dispatch(json.loads(line))
            if response is not None:
                print(json.dumps(response, ensure_ascii=False), flush=True)
        except (ValueError, TypeError):
            print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}), flush=True)


if __name__ == "__main__":
    main()
