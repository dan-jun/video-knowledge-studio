---
name: video-knowledge-studio
description: Install, launch, import course folders into, or troubleshoot a private local Video Knowledge Studio instance. Use when a user wants each person to run an independent video-note workspace on their own machine.
---

# Video Knowledge Studio

Install and operate a local-first web application that synchronizes course videos with
timestamps, visual evidence, structured notes and an AI tutor.

## Scope

Use this skill to:

- install the app and Codex skill on the current computer;
- start or stop the private local server;
- import a folder of videos into a starter course pack;
- open `/production.html` and use the bundled `remix`, `course` or `scipop`
  production mode;
- validate, render and preview locally generated videos;
- use the local MCP bridge for course, production and workflow operations;
- configure local Codex, OpenAI-compatible or offline-demo AI;
- diagnose startup, media, FFmpeg or course-pack problems.

The default architecture is one instance per person. `127.0.0.1` means the current
computer; never tell another person to use the same loopback URL as a shared service.

The deep-note model is multiscale: 5–9 core anchors are a navigation recommendation,
not a knowledge limit. Schema v3 stores one evidence-linked `knowledgeAtom` for every
instructional coverage key point, then groups atoms under anchors and lessons. The
default player view should remain the compact anchor network. The knowledge panel uses
three views: **Learning** for goals, the knowledge line and the core network;
**Knowledge** for anchors, the complete atom layer and evidence; and **Review** for
locally persisted uncertain nodes. Clicking a core node must focus that anchor and its
direct neighbours rather than exposing the whole course graph at once.

Cross-lesson links are derived from canonical course-graph occurrences. Preserve both
the stable episode ID and the human-facing episode number in the graph; never assume
that equal concept labels alone are enough to build a working navigation target.
Mastery is per lesson and stored in browser local storage. Do not describe it as an
account-level or cross-device feature.

For requests that start from a work, research, project or interview knowledge gap rather
than an existing course, use the companion `$demand-driven-video-learning` Skill to plan
the learning path, find multiple sources, render the integrated course, and create notes.

## First action

Locate the repository root: the directory containing `pyproject.toml`, `vks/`,
`scripts/bootstrap.py` and `skill/video-knowledge-studio/SKILL.md`.

- If the repository is present, use it in place.
- If the user supplied a Git URL and the repository is absent, clone it to a
  user-approved directory.
- Do not copy personal course videos, transcripts or state into another user's folder.

## Normal workflow

1. Inspect `README.md` only for user-facing configuration not already supplied.
2. Install the skill:

   ```text
   python scripts/bootstrap.py install
   ```

3. If the user supplied a video folder, pass it explicitly:

   ```text
   python scripts/bootstrap.py start --course <absolute-folder> --open
   ```

   The importer writes `course.json` and a `knowledge/` skeleton into that folder.
   It does not invent teaching notes and does not move or delete the videos.

4. Without a course folder, start the bundled MIT demo:

   ```text
   python scripts/bootstrap.py start --open
   ```

5. Report the actual local URL, PID, course-pack path, provider and log path.
6. Use `status` or `stop` for lifecycle management:

   ```text
   python scripts/bootstrap.py status
   python scripts/bootstrap.py stop
   ```

7. For video production, install the optional environment and open the production page:

   ```text
   python -m pip install -e ".[production]"
   ```

   Then open `http://127.0.0.1:<actual-port>/production.html`. The default Docker
   image already includes production dependencies.

The bootstrap chooses another free local port if 7870 is occupied. Always report the
URL it actually returns.

## Safety boundaries

- Keep the server on `127.0.0.1` unless the user explicitly requests LAN or remote access.
- Remote binding requires `VKS_PASSWORD`; never expose a passwordless server.
- Never send videos, transcripts, notes or screenshots to a model provider unless the
  user requested AI assistance and understands the configured provider.
- Do not edit files under `data/state/` directly. Use `/api/annotations` and
  `/api/revisions` so history and undo remain consistent.
- A shared website with multiple accounts is outside this skill's current product scope.

## Validation

After an install or code change:

```text
python -m unittest discover -s tests -v
node --check web/app.js
node --check web/knowledge.js
node --check web/knowledge_plugin.js
node --check web/production.js
```

For production changes, also render at least one short project and inspect its output
with `ffprobe` and a mid-page frame.

For startup, permission, AI or course-pack failures, read
[references/operations.md](references/operations.md).

The production workflow starts from a reviewed spec, saves stage checkpoints and
pauses for review after generation and checks. It does not search or transcribe
sources. After a server restart interrupts a step, inspect and stop the previous
process tree before explicitly confirming it stopped; never kill a saved PID blindly.
See `docs/agent-mcp.md` and `docs/api.md` in the repository for the MCP bridge and
workflow recovery.
