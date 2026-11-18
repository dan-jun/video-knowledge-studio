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
