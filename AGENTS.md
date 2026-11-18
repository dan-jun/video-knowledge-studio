# Agent guide

This repository contains the application, two distributable Skills and a local Codex
plugin marketplace.

- Install the Agent bundle with `powershell -File install-agent.ps1` on Windows or
  `./install-agent.sh` on macOS/Linux.
- Use `$video-knowledge-studio` for installation, startup, course packs and production
  troubleshooting.
- Use `$demand-driven-video-learning` when the user starts from a work, research,
  project or interview knowledge gap and wants sourced video discovery, an integrated
  animated course and synchronized notes.
- Run `python scripts/sync_plugin.py --check` after changing files under `skill/`.
- Never copy personal videos, transcripts, generated production projects or secrets into
  the plugin bundle.
