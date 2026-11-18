# HTTP API

All API and media responses require authentication when `VKS_PASSWORD` is set. API
clients use `X-VKS-Token`; browser media elements may use the `t` query parameter.

## Read endpoints

### `GET /api/projects`

Returns the flattened course list. It never includes local video paths.

### `GET /api/knowledge?id=<episode-id>`

Returns:

```json
{
  "ok": true,
  "episode": {"id": "...", "title": "...", "timeline": []},
  "index": {"course": "...", "chapters": [], "network": {}, "episodes": []},
  "state": {"annotations": [], "revisions": [], "overrides": {}},
  "ai": {"provider": "codex-cli", "offline": false}
}
```

### `GET /api/ai/status`

Returns the selected provider and whether it is the offline demo.

### `GET /api/ai/job?id=<job-id>`

Returns `status: running`, a completed `result`, or an HTTP 502 with an error.

### `GET /media/video?id=<episode-id>`

Range-capable local video response.

### `GET /media/frame?id=<episode-id>&at=<seconds>`

Extracts and caches one video frame. Requires FFmpeg.

### `GET /media/knowledge-frame?id=<episode-id>&file=<relative-path>`

Returns an existing image inside the episode's course pack.

## Write endpoints

### `POST /api/ai/ask`

```json
{
  "id": "demo-e01",
  "selected": "text selected in a note",
  "kid": "E01:core:1",
  "action": "explain",
  "question": "optional follow-up",
  "time": 42.5,
  "history": []
}
```

Returns HTTP 202:

```json
{"ok": true, "job": "12-character-id", "status": "running"}
```

### `POST /api/annotations`

Add:

```json
{"id": "demo-e01", "text": "side note", "kid": "E01:core:1", "time": 42}
```

Delete:

```json
{"id": "demo-e01", "act": "del", "annotationId": "..."}
```

### `POST /api/revisions`

Accept a revision:

```json
{
  "id": "demo-e01",
  "act": "apply",
  "draft": {
    "kid": "E01:core:1",
    "before": "complete current block",
    "original": "selected fragment",
    "replacement": "replacement fragment",
    "reason": "why"
  }
}
```

Other actions are `annotation`, `reject` and:

```json
{"id": "demo-e01", "act": "undo", "revisionId": "..."}
```

The server replaces only the selected fragment inside the complete block, records the
previous block text and supports undo.

### `POST /api/reload`

Reloads course packs without restarting the process.

## Authentication endpoints

- `POST /api/login` with `{"password":"..."}` returns a token and cookie.
- `POST /api/logout` clears the cookie.

## Error shape

```json
{"ok": false, "error": "human-readable message"}
```

Notable statuses: 400 invalid request/course data, 401 authentication required,
404 missing resource, 502 provider failure.

## Current API limits

- No multi-user accounts or ownership checks beyond one deployment password.
- No API rate limiter.
- AI jobs are in memory and are lost on process restart.
- No upload endpoint; course media is read from configured local packs.
