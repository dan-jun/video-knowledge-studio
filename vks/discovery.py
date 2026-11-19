"""Explicit, metadata-only source search via an optional yt-dlp executable."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import urllib.parse


class DiscoveryError(ValueError):
    pass


def search(platform: str, query: str, limit: int = 5):
    if platform not in {"bilibili", "youtube"}:
        raise DiscoveryError("platform must be bilibili or youtube")
    if not isinstance(query, str) or not query.strip() or len(query) > 200 or any(ord(c) < 32 for c in query):
        raise DiscoveryError("query must be 1–200 printable characters")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 10:
        raise DiscoveryError("limit must be an integer from 1 to 10")
    executable = shutil.which("yt-dlp")
    if not executable:
        raise DiscoveryError("yt-dlp is not installed or not on PATH")
    prefix = "bilisearch" if platform == "bilibili" else "ytsearch"
    command = [executable, "--ignore-config", "--no-plugin-dirs", "--flat-playlist", "--dump-single-json", "--skip-download", "--no-warnings", f"{prefix}{limit}:{query.strip()}"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
    except subprocess.TimeoutExpired as exc:
        raise DiscoveryError("source search timed out") from exc
    if result.returncode:
        if "412" in result.stderr or "429" in result.stderr or "403" in result.stderr:
            raise DiscoveryError("platform rejected the search request; try later or use an authorized search provider")
        raise DiscoveryError("source search failed; check network and platform availability")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise DiscoveryError("search provider returned invalid metadata") from exc
    rows = []
    for item in data.get("entries") or []:
        if not isinstance(item, dict):
            continue
        raw_url = str(item.get("url") or item.get("webpage_url") or "")
        if platform == "youtube" and re.fullmatch(r"[\w-]{11}", raw_url):
            raw_url = "https://www.youtube.com/watch?v=" + raw_url
        allowed = {"youtube.com", "www.youtube.com", "youtu.be"} if platform == "youtube" else {"bilibili.com", "www.bilibili.com", "b23.tv"}
        try:
            parsed = urllib.parse.urlsplit(raw_url)
            if platform == "bilibili" and parsed.scheme == "http" and parsed.hostname in allowed and not parsed.username and not parsed.password and parsed.port in {None, 80}:
                raw_url = urllib.parse.urlunsplit(("https", parsed.hostname, parsed.path, parsed.query, ""))
                parsed = urllib.parse.urlsplit(raw_url)
            valid = parsed.scheme == "https" and parsed.hostname in allowed and not parsed.username and not parsed.password and parsed.port in {None, 443}
        except ValueError:
            valid = False
        if not valid:
            continue
        rows.append({"url": raw_url, "title": str(item.get("title") or "")[:300],
                     "author": str(item.get("uploader") or item.get("channel") or "")[:200],
                     "durationSeconds": item.get("duration") if isinstance(item.get("duration"), (int, float)) else None,
                     "captionAvailability": "unknown", "license": "unknown"})
    return {"platform": platform, "query": query.strip(), "results": rows[:limit],
            "notice": "Search metadata is unverified; review relevance, captions, source rights, and accuracy."}
