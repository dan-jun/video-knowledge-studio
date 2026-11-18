# Docker quick start

Docker packages Python, FFmpeg and the application into one image, so users do
not need to install Python or system dependencies manually.

Install Docker Desktop for Windows or macOS, or Docker Engine with the Compose
plugin on Linux, before running the commands below. Docker Desktop requires a
one-time graphical setup and cannot be silently installed by this repository.

The default image also includes the optional video-production environment:
Manim, Edge TTS, Cairo/Pango, FFmpeg and Noto CJK fonts. This makes the image
larger than a viewer-only build, but enables all three production modes without
a second manual dependency setup. Build a viewer-only image with
`--build-arg VKS_INSTALL_PRODUCTION=0` when rendering is not needed.

The launchers first pull the published image:

```text
ghcr.io/dan-jun/video-knowledge-studio:latest
```

If the pull fails, they fall back to a local source build. Use
`.\docker-up.ps1 -BuildFromSource` on Windows or
`VKS_BUILD_FROM_SOURCE=1 ./docker-up.sh` on macOS/Linux when testing local code.

## One command

Windows:

```powershell
.\docker-up.ps1 -Open
```

macOS/Linux:

```bash
./docker-up.sh
```

The helper:

1. finds Docker, including the default Docker Desktop install locations when
   `docker` is not yet available on the current terminal's PATH;
2. selects a free local port;
3. generates a random login password and writes `.env.docker`;
4. runs `docker compose up -d --build`;
5. waits for `/login.html` to become healthy;
6. prints the URL and password and optionally opens the browser.

The generated password is shown only in command output and `.env.docker`.
`.env.docker` is excluded from Git.

## AI inside the container

The container cannot use a Codex CLI installed on the host. Use an
OpenAI-compatible endpoint by editing `.env.docker`:

```text
VKS_PASSWORD=<generated password>
VKS_DOCKER_PORT=7870
VKS_AI_PROVIDER=openai
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=<your key>
VKS_MODEL=gpt-4.1-mini
```

Then rerun the Docker helper. For a model running on the host, use the Docker
host address appropriate to your platform instead of `127.0.0.1`.

## Manual Compose

Create `.env.docker`:

```text
VKS_PASSWORD=choose-a-strong-password
VKS_DOCKER_PORT=7870
VKS_AI_PROVIDER=mock
VKS_MODEL=gpt-4.1-mini
```

Then run:

```bash
docker compose --env-file .env.docker up -d --build
```

The host port binds to `127.0.0.1`, so this configuration is for one user on
one computer. Do not change the binding to `0.0.0.0` for a public service
without HTTPS, authentication review and a proper reverse proxy.

## Data and course packs

- `packs/` is mounted read-only.
- `./data` holds annotations, revisions, frame cache and the session secret.
- `data/production/` holds generated storyboards, audio, slides and final videos.
- Stopping or replacing the container keeps `./data`.
- The bundled demo is included in the image.

## Operations

```powershell
.\docker-up.ps1 -Command logs
.\docker-up.ps1 -Command down
```

## Verified by CI

`.github/workflows/ci.yml` builds the image on every push and pull request,
starts a container with a test password, waits for health and requests the
login page. This catches Dockerfile and startup regressions even when a
developer does not have Docker installed locally.
