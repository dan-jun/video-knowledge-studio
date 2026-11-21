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

### `GET /api/knowledge/deep?id=<episode-id>`

Returns the cached deep note for an episode, or `{"ok": true, "note": null}` when
no current note exists. A cached note is invalidated when the episode transcript,
lesson structure or visual evidence changes.

Deep notes contain a central question, thesis, causal model, 5–9 concepts with
mechanisms, examples, boundaries, misconceptions and evidence, plus comparisons,
formulas, exam points, recall questions, glossary entries, timeline coverage and
visual evidence.

### `GET /api/knowledge/deep/job?id=<job-id>`

Returns the asynchronous generation status:

```json
{
  "ok": true,
  "id": "job-id",
  "status": "running|done|failed",
  "stage": "校验概念结构、证据和全片覆盖",
  "error": null,
  "note": null
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

### `POST /api/knowledge/deep`

Starts or reuses deep-note generation:

```json
{"id": "demo-e01", "force": false}
```

Returns a cached note immediately, an existing in-flight job, or HTTP 202 with a new
job ID. The generator reads the complete transcript, course notes and safe,
course-pack-local visual files. It requires a configured Codex CLI or
OpenAI-compatible model. Offline demo mode returns HTTP 503 instead of fabricating a
knowledge summary.

The evidence gate assigns every second of the episode to one deterministic transcript
block. Every block must return exactly once with teaching, housekeeping or uncertainty
status; teaching blocks retain their key points. Every visual candidate must receive a
decision, and every near-duplicate visual cluster needs an included representative.
The synthesis gate also requires 5–9 complete concepts and a connected typed graph with
no isolated nodes and at least one contrast, example or application relationship.

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

## Reviewable production workflows

A workflow runs a reviewed production spec through `generate`, `gates`, and
`render`. Each successful step pauses for review; `resume` starts the next step.
Search, transcription, source review and note creation are not included. State and
completed step logs are saved under `data/production/workflows/`.

- `POST /api/workflows/create`: `{"project":"<project-id>"}` creates a workflow.
- `GET /api/workflows?project=<project-id>` lists workflows.
- `GET /api/workflows/item?id=<workflow-id>` reads status and steps.
- `POST /api/workflows/resume`: `{"id":"<workflow-id>"}` starts or retries the next step.
- `POST /api/workflows/cancel`: `{"id":"<workflow-id>"}` stops the current process tree.
- `POST /api/workflows/abandon`: `{"id":"<workflow-id>"}` ends an idle workflow so its spec can be changed.
- After a server restart interrupts a running step, inspect and stop the old process
  tree. Only then send `POST /api/workflows/acknowledge-stopped` with
  `{"id":"<workflow-id>","confirmed":true}` and create a new workflow. The stored
  `activePid` is a diagnostic hint; process IDs can be reused and must not be killed
  blindly. A spec or generated storyboard change requires a new workflow. Render success includes an ffprobe
  playback check, but visual and source review remain manual.

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
