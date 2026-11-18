# Configuration

The app reads `.env` from the repository root. Existing environment variables win over
`.env` values.

## Core settings

| Variable | Default | Meaning |
|---|---|---|
| `VKS_HOST` | `127.0.0.1` | Bind address for `python -m vks` |
| `VKS_PORT` | `7870` | Default port |
| `VKS_PASSWORD` | empty | Enables login; required for non-loopback binding |
| `VKS_PACKS` | `./packs` | Course-pack directory or one single pack |
| `VKS_DATA` | `./data` | State, cache, session secret and logs |
| `VKS_FFMPEG` | auto-detect | FFmpeg executable used for frame extraction |
| `VKS_SECRET` | generated | Override the local session-signing secret |

## AI settings

| Variable | Default | Meaning |
|---|---|---|
| `VKS_AI_PROVIDER` | `auto` | `auto`, `codex`, `openai` or `mock` |
| `VKS_AI_TIMEOUT` | `180` | Provider timeout in seconds |
| `VKS_CODEX_EXE` | `codex` | Codex CLI executable |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible API base |
| `OPENAI_API_KEY` | empty | Server-side API key |
| `VKS_MODEL` | `gpt-4.1-mini` | Exact model identifier |

`auto` tries Codex CLI when available, then an OpenAI-compatible configuration,
then the offline demo provider. If a configured provider fails during a request,
`auto` continues to the next provider and reports the provider that actually answered.

## Security behavior

- `127.0.0.1`/`localhost` may run without a password.
- Any other bind address without `VKS_PASSWORD` exits at startup.
- Session tokens are HMAC-signed, expire after 30 days and are HTTP-only cookies.
- Browser code never receives the OpenAI API key.

## Files excluded from Git

- `.env`
- `data/state/`
- `data/cache/`
- `data/.session_secret`
- logs and Python caches
