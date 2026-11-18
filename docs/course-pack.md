# Course pack format

A course pack is a directory under `packs/`. Paths in `course.json` are relative
to that directory and cannot escape it.

## `course.json`

```json
{
  "schemaVersion": 1,
  "id": "my-course",
  "title": "My course",
  "description": "What this course teaches",
  "license": "CC-BY-4.0",
  "chapters": [
    {
      "id": "chapter-1",
      "title": "Chapter 1",
      "episodeIds": ["lesson-001"]
    }
  ],
  "episodes": [
    {
      "id": "lesson-001",
      "number": 1,
      "title": "Lesson title",
      "chapterId": "chapter-1",
      "duration": 612.4,
      "video": "media/lesson-001.mp4",
      "knowledge": "knowledge/e001.json"
    }
  ],
  "network": {
    "title": "Course knowledge network",
    "nodes": [
      {
        "id": "core",
        "label": "Core concept",
        "subtitle": "why it matters",
        "episodeIds": ["lesson-001"]
      }
    ],
    "edges": []
  }
}
```

## Knowledge note

Required top-level fields are deliberately small:

```json
{
  "title": "Lesson title",
  "thesis": "The central claim",
  "objectives": ["A testable learning objective"],
  "terms": [
    {
      "term": "Term",
      "plain": "Plain-language definition",
      "example": "Smallest useful example",
      "first": "00:42"
    }
  ],
  "timeline": [
    {
      "time": "00:00-02:20",
      "topic": "First semantic block",
      "must": "What cannot be omitted"
    }
  ],
  "core": [
    {
      "heading": "Mechanism",
      "time": "01:04",
      "body": "Explain the causal chain, not just the name."
    }
  ],
  "formula": "",
  "visuals": [
    {
      "file": "media/frame-01.jpg",
      "time": "01:12",
      "caption": "What the figure proves"
    }
  ],
  "visualThesis": "",
  "visualRead": [],
  "trap": "",
  "recall": [
    {"q": "Question", "a": "Answer"}
  ],
  "bridges": ["Related concept"],
  "memoryHook": "",
  "transcript": [
    {"start": 0, "end": 140, "text": "Timestamped transcript excerpt"}
  ]
}
```

`objectives`, `visualRead` and `bridges` accept either plain strings or objects
with an `id` and `text`. The loader normalizes clock strings into second-level
`start`/`end` fields, so front-end synchronization does not depend on manual
millisecond values.

## Content quality

- Do not summarize from titles alone; use the complete transcript.
- Extract relevant frames for diagrams, formulas, code and whiteboards.
- Keep a time span for every meaningful mechanism, example and warning.
- Record uncertain ASR or conflicting claims instead of guessing.
- Keep raw evidence separate from edited notes.
