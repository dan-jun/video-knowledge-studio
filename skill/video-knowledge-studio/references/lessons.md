# Lessons

## 2026-11-18 — Docker Desktop can be running without `docker` on PATH

- **Symptom:** Docker Desktop and its Linux engine were healthy, but the launcher
  reported that Docker was not installed in a newly opened terminal.
- **Root cause:** Both launchers relied only on `PATH`/`shutil.which`, while the
  per-user Windows installation stores the CLI under
  `%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin`.
- **Fix:** Fall back to Docker Desktop's standard Windows and macOS CLI locations
  before reporting a missing installation.
- **Verification:** With the CLI absent from PATH, the PowerShell launcher built,
  started a healthy container on `127.0.0.1`, accepted login, served a video range,
  completed an offline AI job, and preserved an annotation across container
  recreation. The temporary annotation was then removed.

## 2026-11-18 — Ignore generated session state from the Docker build context

- **Symptom:** A local build copied `data/.session_secret` into the application
  image even though personal note state and cache directories were ignored.
- **Root cause:** `.dockerignore` covered the state and cache subdirectories but
  missed the session secret and PID files stored directly under `data/`.
- **Fix:** Exclude `data/.session_secret` and `data/studio.pid` from the Docker
  build context.
- **Verification:** Rebuild the image and confirm `/app/data/.session_secret` does
  not exist in an image run without the host data volume.

## 2026-11-18 — Explain the three-pane workspace before the feature inventory

- **Symptom:** The README listed individual capabilities but did not explain the
  course directory, synchronized player, and knowledge/AI pane as one learning
  workflow.
- **Root cause:** Feature-oriented documentation omitted the product's primary
  navigation model and the time-based connection between its regions.
- **Fix:** Add a three-pane table and a short select → watch → understand → ask →
  revise → review walkthrough before installation instructions. Label unchecked
  items explicitly as an unimplemented roadmap.
- **Verification:** Compare every table claim with the UI behavior in `web/app.js`
  and `web/knowledge.js`; distinguish the active-lesson marker from saved per-video
  playback position.

## 2026-11-18 — Separate upstream production modes from the learning workspace

- **Symptom:** The public README did not explain the three video-production modes:
  `remix`, `course`, and `scipop`.
- **Root cause:** The repository publishes the downstream knowledge workspace, while
  the production pipeline lives in a separate internal toolchain with additional
  Manim, TTS, rendering, and gate dependencies.
- **Fix:** Start with an explicit production/learning boundary and document the
  modes. This was the interim state before the pipeline was migrated into the public
  repository later the same day.
- **Verification:** Cross-check names, labels, duration ranges, source-count rules,
  chapter and practice constraints, and recap requirements against
  `tools/modes.py` in the production workspace.

## 2026-11-18 — Migrating the production pipeline requires portability proofs

- **Symptom:** The production toolchain initially depended on local drive letters,
  Windows font files and an external virtual environment; its first migrated render
  also failed on a font-constant naming mismatch.
- **Root cause:** The original scripts were optimized for one workstation rather than
  distribution, and a comment-only migration check cannot prove that Manim, TTS,
  FFmpeg and subtitle rendering still compose.
- **Fix:** Add a portable runtime module for FFmpeg, output roots and CJK fonts;
  expose the three modes through `/production.html`; install optional production
  dependencies in Docker; ignore generated projects and scenes; and add CI checks for
  the production page and packages.
- **Verification:** Render a two-page H.264/AAC project with Manim and Edge TTS,
  confirm 1920×1080 output, numeric drift 0.0, inspect a mid-page frame, then repeat
  generation and rendering inside the production Docker image and verify a ranged MP4
  response.

## 2026-11-18 — Lead the README with end-to-end outcomes

- **Symptom:** The README grew by appending production modes after the learning
  workspace, leaving setup, capabilities, privacy, deployment and roadmap mixed
  together.
- **Root cause:** The document was organized as cumulative feature inventory rather
  than around what a learner can accomplish from source video to review.
- **Fix:** Put terminology and the end-to-end value near the top, connect production
  and learning with one flow, then move interfaces, installation, privacy, development
  and roadmap into separate sections.
- **Verification:** Check every local Markdown link and image, keep modes consistent
  with `production/tools/modes.py`, and re-run the test, syntax and Skill validation
  suite after the documentation edit.

## 2026-11-18 — Document demand-driven learning without overclaiming discovery

- **Symptom:** The project's most valuable use case was easy to miss: starting from a
  work, research or project knowledge gap rather than from an existing course.
- **Root cause:** The documentation described video production and learning as separate
  capabilities, but did not connect goal decomposition, source discovery, integration,
  rendering, note taking and contextual AI into one intent-driven workflow.
- **Fix:** Add a demand-driven learning section with concrete examples, an end-to-end
  flow and a copyable Agent task. Mark automatic Bilibili/YouTube discovery and study
  planning as Roadmap items rather than pretending they are built-in.
- **Verification:** Recheck every current-versus-planned claim against the production
  UI and API, then validate all local links and Skill synchronization.
