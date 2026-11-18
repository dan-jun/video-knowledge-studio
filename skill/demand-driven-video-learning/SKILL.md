---
name: demand-driven-video-learning
description: Turn a work, research, project or interview knowledge gap into a sourced learning plan and an integrated animated course with synchronized notes. Use when the user asks an Agent to plan what to learn, find multiple Bilibili/YouTube explanations, synthesize them, render a teaching video, and create a study workspace.
---

# Demand-Driven Video Learning

Complete the learning task end to end rather than merely recommending videos. The
result is a compact learning path, a source ledger, an integrated animated course or
short-video series, and a course pack that opens in Video Knowledge Studio.

## Required inputs

Collect only what is needed:

- the target capability, concept or project question;
- current baseline and what is still confusing;
- available time or deadline;
- language, platform and output preferences;
- whether searching and downloading third-party sources is permitted.

If details are missing, make conservative defaults and state them. For a blocking
constraint such as no network/search capability, report it instead of inventing videos.

## Workflow

1. Locate the Video Knowledge Studio checkout. If the app is absent, use
   `$video-knowledge-studio` to install it.
2. Inspect the available capabilities. Source discovery may use platform search
   connectors, an in-app browser or web search plus `yt-dlp`. Local production requires
   Python/FFmpeg or the project's Docker image.
3. Convert the request into a learning brief: objective, prerequisites, priority,
   time budget and evidence that learning succeeded.
4. Search more than one query, translated when useful. Search both Bilibili and YouTube
   when both are reachable; use one platform when the other is unavailable or lacks
   relevant Chinese material.
5. Select complementary sources with [the source rubric](references/workflow.md).
   Record every URL, title, author, duration, caption availability and covered concept.
   Never fabricate a URL, transcript or timestamp.
6. Produce a learning plan that differentiates must-know, understand and defer. Allocate
   the available time across concepts, examples, practice and review.
7. Choose production units:
   - `scipop` for a 2-6 minute single concept or several short modules;
   - `course` for a 15-60 minute multi-source integrated lesson;
   - `remix` for an information-preserving remake of one source.
8. Write the production spec and source citations. Keep each conclusion attributable to
   a source and timestamp. Use the application's production page or:

   ```text
   python production/tools/anim_gen.py <spec.json> --mode <mode> --project <project-dir>
   python production/tools/modes.py check --mode <mode> --project <project-dir>
   python production/tools/video_agent.py render --project <project-dir>
   ```

9. Create the synchronized course pack: notes, glossary, visual evidence, examples,
   traps, active recall, exercises and a concept network. Use stable block IDs so AI
   annotations and reversible revisions work.
10. Validate the final artifacts: playable MP4, gate results, transcript/citation
    coverage, generated notes and a successful course-pack load. Inspect at least one
    mid-page video frame when visual quality is material.

## Output contract

Keep these in the project workspace:

- `learning-brief.md` - goal, baseline, time budget and success criteria;
- `sources.json` - selected sources and why each was included or rejected;
- `learning-plan.md` - ordered concepts, time boxes and practice points;
- `spec.json` / production project - source of truth for the video;
- `build/final_hardsub.mp4` - final rendered video;
- course pack with knowledge JSON and media;
- a short verification report with exact checks and remaining uncertainty.

Read [the detailed workflow and mode rules](references/workflow.md) before selecting
sources or choosing between `course`, `remix` and `scipop`.

## Boundaries

- Respect platform terms, access controls and content licenses. Do not bypass a login,
  paywall, DRM or regional restriction.
- Do not publish downloaded videos or transcripts unless redistribution is permitted.
- Preserve uncertainty and conflicting explanations; do not flatten disagreement into
  one confident answer.
- AI-generated notes and revisions are proposals until reviewed by the learner.
