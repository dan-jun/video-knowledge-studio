# Operations and troubleshooting

## Install layout

`scripts/bootstrap.py install` copies this skill to:

```text
$CODEX_HOME/skills/video-knowledge-studio
```

If `CODEX_HOME` is unset, the destination is `~/.codex/skills/video-knowledge-studio`.
The application itself remains in its repository; installing the skill does not copy
course media elsewhere.

## Process lifecycle

- `start`: checks Python and course paths, starts `python -m vks` in the background,
  waits for HTTP readiness and writes `data/studio.pid`.
- `status`: reports whether that PID is alive.
- `stop`: sends a normal termination signal and removes the PID file.

Logs are written to `data/studio.log`.

## Course import

When `--course` points to a folder without `course.json`, the importer:

1. finds common video extensions recursively;
2. reads exact duration with `ffprobe` when available;
3. creates chapter and episode IDs;
4. writes `course.json` and `knowledge/eNNN.json`;
5. leaves video files in place.

The resulting notes are structural skeletons. Complete the transcript, visual evidence
and semantic audit before treating the notes as educational content.

## AI provider selection

`auto` resolves in this order:

1. local `codex` executable;
2. OpenAI-compatible settings with an API key and model;
3. offline demo provider.

The offline provider verifies the UI/job path only. It must not be presented as a
source of trustworthy explanations.

For an OpenAI-compatible endpoint, set:

```text
VKS_AI_PROVIDER=openai
OPENAI_BASE_URL=https://provider.example/v1
OPENAI_API_KEY=...
VKS_MODEL=model-name
```

Visual questions attach one nearest relevant frame. If the selected model does not
support image input, configure text-only operation or use a vision-capable model.

## Common failures

### Port already occupied

The bootstrap skips occupied ports. Use the returned URL instead of assuming 7870.

### Video opens but frames fail

Install FFmpeg and confirm `ffmpeg`/`ffprobe` are on `PATH`, or set `VKS_FFMPEG` to the
FFmpeg executable.

### Course pack does not load

Check that `course.json`, all `knowledge` files and all media paths stay inside the
pack root. Path traversal is intentionally rejected.

### AI stays in running state

Inspect `data/studio.log`. Codex mode requires an authenticated local CLI. OpenAI mode
requires a reachable base URL, key and model.

### Remote access

Local use needs no password. Binding to a non-loopback address without
`VKS_PASSWORD` is rejected by design. Put HTTPS and an authenticated reverse proxy in
front of any public deployment. This project does not yet provide per-user accounts or
tenant isolation on one shared server.
