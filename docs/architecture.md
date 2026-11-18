# Architecture

```text
course pack
  ├─ video media
  ├─ timestamped transcript
  ├─ visual evidence
  └─ structured notes
          │
          ▼
CourseStore ──► /api/knowledge ──► synchronized player + note reader
     │                                  │
     │                                  ├─ text selection toolbar
     │                                  └─ AI result / revision diff
     │
     ├─ StateStore: annotations, overrides, history
     └─ TutorService
           ├─ Codex CLI provider
           ├─ OpenAI-compatible provider
           └─ explicit offline demo provider
```

## Trust boundaries

- Course packs are server-side local data.
- Browser code never receives provider credentials or local video paths.
- The AI provider receives only the selected note context, nearby transcript and
  one nearest visual frame.
- Revisions are proposals. `StateStore` changes content only after an explicit
  apply request, keeps the previous block text, and supports undo.
- Course-pack paths are resolved below the pack root; traversal is rejected.

## Job model

`POST /api/ai/ask` returns a job ID immediately. The browser polls
`GET /api/ai/job?id=...`. This avoids tying a long model request to one browser
HTTP connection and gives providers room for retries or local inference.
