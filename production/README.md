# Video production pipeline

This directory contains the locally integrated Video Forge production pipeline used
by `/production.html`.

## Modes

- `remix`: information-preserving remake from one source.
- `course`: multi-source integrated long lesson.
- `scipop`: dense 2–6 minute popular-science short.

## Install

```powershell
python -m pip install -e ".[production]"
python -m vks
```

The Docker image installs these dependencies by default. System FFmpeg and a CJK font
are required outside Docker.

## Layout

- `tools/`: generation, gates, TTS, rendering and verification scripts.
- `specs/`: redistribution-safe original demo specifications.
- `scenes/`: generated or hand-authored Manim scene modules.
- User projects are written to `data/production/projects/` and are not committed.

The web UI is the supported entry point. Tool scripts remain available for automation.
