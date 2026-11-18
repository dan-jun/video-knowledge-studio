# Feature reference

This file is the complete functional inventory for version 0.1.0.

## Course library

- Loads one or more course packs from `packs/`.
- Orders videos by chapter, then episode number.
- Searches across course title, chapter and episode title.
- Supports one course-pack directory or a directory containing multiple packs.
- Shows duration and knowledge-block count for every episode.

## Synchronized player

- Range-streams local MP4/WebM-compatible media.
- Remembers playback position in browser local storage.
- Supports chapter markers generated from the lesson timeline.
- Includes play/pause, seek, volume, playback speed, PiP, theater mode, fullscreen,
  screenshots and timeline preview frames.
- Keyboard controls include `Space`/`K`, arrow seeking, `J`/`L`, `M`, `F`, `T`,
  `I` and screenshot shortcuts supplied by the player.

## Knowledge notes

- Thesis, objectives, terms, timeline, core mechanisms, formula/rule, visual evidence,
  visual interpretation, traps, active recall, bridges and memory hooks.
- Time ranges and single anchors synchronize with video playback.
- Clicking a timestamp seeks the video; playback highlights and scrolls the active
  timeline block when follow mode is enabled.
- Clicking a key visual seeks the corresponding video position.
- Terms include a plain-language definition, minimal example, first occurrence and a
  learner self-assessment stored locally.
- Course networks render arbitrary nodes and directed/dashed edges.

## Tutor and revision workflow

- Select note text to reveal actions: explain, check, simplify, example, highlight and
  follow-up question.
- AI requests include the selected block ID, current video time, nearby transcript,
  lecture context and one nearest visual frame.
- AI jobs run in the background and the browser polls job status.
- Results include answer, optional side annotation, timestamp evidence, confidence,
  uncertainty flag and an optional proposed revision.
- Revisions show original and replacement text before anything changes.
- Options are accept, annotation only or reject.
- Accepted revisions can be undone.
- Side annotations can be inserted next to a stable note-block ID and deleted later.

## AI providers

- Local Codex CLI.
- OpenAI-compatible `/chat/completions` provider.
- Explicit offline demo provider.
- Automatic provider selection in the order Codex → OpenAI-compatible → offline demo.

## Local persistence

- Annotations, accepted overrides and revision history are stored in `data/state/`.
- Extracted frame cache is stored in `data/cache/`.
- State and cache are excluded from Git.
- Local browser self-assessment is stored in browser local storage.

## Authentication and deployment

- Passwordless access is available only for loopback local use.
- Non-loopback binding requires `VKS_PASSWORD`.
- Session cookies are HMAC-signed and HTTP-only.
- Docker and Docker Compose examples are included.

## Imports and development

- `scripts/import_course.py` scans a local video folder and creates accurate-duration
  structural skeletons.
- `scripts/make_demo_media.py` regenerates the redistribution-safe demo.
- Bootstrap installer copies the Codex skill and launches the local app.
- Unit and HTTP integration tests cover auth, path traversal, course loading, media
  ranges, annotations, revisions and the AI job lifecycle.
- Docker helper generates a password, picks a free port, builds and waits for health;
  CI performs a real image build and container health check.
