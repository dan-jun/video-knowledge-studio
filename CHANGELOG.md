# Changelog

## 0.2.1 - 2026-11-18

- Added portable MiniMax TTS with configurable voice and speaking speed.
- Increased default TTS pacing and added an environment override for shorter videos.
- Published a prebuilt public GHCR image and made launchers pull it before falling back
  to a local build.
- Added a 54-second product walkthrough combining Manim feature animation with real
  screen-recorded learning and production interactions.
- Added a GitHub social preview, launch kit, public release asset and project discovery
  metadata.

## 0.2.0 - 2026-11-18

- Integrated the `remix`, `course` and `scipop` video-production modes.
- Added `/production.html` for project creation, spec editing, generation, gates,
  rendering, logs, video preview and download.
- Added the Manim animation kit, TTS/render pipeline and production quality checks.
- Added redistribution-safe original production templates.
- Added optional `production` and `transcription` dependency groups.
- Docker now includes Manim, Edge TTS, FFmpeg, Cairo/Pango and Noto CJK fonts by default.
- Added production API, dependency, build-context and Docker CI verification.
- Bundled the `video-knowledge-studio` and `demand-driven-video-learning` Agent Skills.
- Added a portable Codex Plugin, repo-local marketplace and one-command Agent installer.
- Added automatic Skill fallback when Codex Plugin installation is unavailable.

## 0.1.0 - 2026-11-18

- Initial open-source edition.
- Generic course-pack loader with multi-chapter ordering.
- Synchronized video and knowledge-note workspace.
- Text-selection tutor with evidence, annotations and reversible revisions.
- Codex CLI, OpenAI-compatible and offline demo providers.
- Background AI jobs and local state store.
- Tests, CI, Docker and redistribution-safe demo course.
- Codex Skill wrapper and one-command bootstrap for Agent-assisted local installs.
- Complete feature, API, configuration, deployment and limitation documentation.
- Runtime provider fallback in automatic AI mode.
- One-command Docker launcher with generated password and CI container health test.
