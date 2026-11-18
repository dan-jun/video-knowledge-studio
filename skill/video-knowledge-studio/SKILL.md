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
- configure local Codex, OpenAI-compatible or offline-demo AI;
- diagnose startup, media, FFmpeg or course-pack problems.

The default architecture is one instance per person. `127.0.0.1` means the current
computer; never tell another person to use the same loopback URL as a shared service.

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
```

For startup, permission, AI or course-pack failures, read
[references/operations.md](references/operations.md).
