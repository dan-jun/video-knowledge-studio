# Changelog

## 0.2.8 - 2026-11-19

- Added a complete English product experience for the learning workspace,
  production workspace, contextual AI output and the Raft demonstration course.
- Added an English 73-second launch film and new English workflow, comparison,
  demand-driven-learning and social-preview artwork.
- Translated the public README in full while keeping the existing Chinese product
  and technical documentation available for existing users.
- Added language-aware source citation prompts for contextual AI so English answers
  use the language of the active workspace.
- Added language-aware duration estimation, recap checks and opening-hook checks for
  English production specs.

## 0.2.7 - 2026-11-18

- Fixed generated project metadata so `scipop` and `course` runs no longer inherit
  hard-coded remix duration, speech-rate and quiz settings.
- The selected production mode now supplies the correct display label and executable
  parameter set in `agent.json`.
- Added a regression test that generates a project and verifies the persisted mode,
  label, duration range, speaking speed and quiz flag.

## 0.2.6 - 2026-11-18

- Removed the AI response waiting interval from the final cut instead of speeding up
  the spinner; the selection action now cuts directly to the completed answer.
- Changed all enlarged interface details to fixed screenshots with stable local crops,
  removing live zooming and scroll-induced jitter.
- Captured a clean answer screenshot with the selection toolbar and cursor removed.
- Fixed generated project metadata defaulting to remix settings regardless of the
  selected `scipop` or `course` mode, and added a regression test.

## 0.2.5 - 2026-11-18

- Replaced the mixed metaphor opening with a three-scenario matrix: project handoff,
  paper reproduction, and interview/career preparation.
- Added a workflow spine that maps all three scenarios to goal, source discovery,
  course generation, contextual study, and real-world use.
- Added a dedicated four-point differentiation frame and renamed the proof sections so
  each product capability is visibly tied to the stated difference.
- Unified the actual learning and production walkthroughs around the same Raft task,
  and added an original `raft-demo` course pack with synchronized notes and knowledge
  network for reproducible recording.
- Replaced the ending with a three-outcome recap followed by the product principle.

## 0.2.4 - 2026-11-18

- Reworked the launch film around a concrete real-world scenario:
  “明天要改 Raft 日志复制，但你只有四小时。”
- Added project, research, and career entry examples before introducing the
  end-to-end workflow.
- Added explicit differentiation chapters: questions stay attached to source video,
  AI receives timestamp/transcript/frame context, notes form a knowledge network, and
  generated courses return to the same learning workspace.
- Added a comparison bridge showing why “video finished” is not the end of learning,
  then handed off to the generated Raft lesson and the unified evidence model.

## 0.2.3 - 2026-11-18

- Replaced the synthesized rhythmic score with the licensed Mixkit track
  “Close Up” by Michael Ramir C.
- Replaced the weak final course clip with a generated Raft log-replication
  lesson animation that shows client request, leader fan-out, follower logs,
  majority acknowledgement and commit.
- Shortened the launch film to about 88 seconds and rechecked full-resolution
  frames, audio loudness, codec, file size and download integrity.

## 0.2.2 - 2026-11-18

- Rebuilt the product launch video as a 92-second music-driven film with kinetic
  feature animation, real learning-workspace recording, contextual AI evidence,
  production-line operation, visible gate results and rendered output.
- Removed the slow synthetic voiceover and replaced static slide pacing with hard
  cuts, cursor-led interactions, product closeups and licensed stock music.
- Fixed the Codex tutor failing when Windows inherited an unusable temporary
  directory; AI subprocess scratch files now stay under the workspace data root.

## 0.2.1 - 2026-11-18

- Added portable MiniMax TTS with configurable voice and speaking speed.
- Increased default TTS pacing and added an environment override for shorter videos.
- Published a prebuilt public GHCR image and made launchers pull it before falling back
  to a local build.
- Withdrew the rejected 54-second product walkthrough; a fully animated launch video
  with cinematic real-product recording is being rebuilt separately.
- Added a GitHub social preview, launch kit, public release asset and project discovery
  metadata.

## 0.2.0 - 2026-11-18

- Integrated the `remix`, `course` and `scipop` video-production modes.
- Added `/production.html` for project creation, spec editing, generation, gates,
  rendering, logs, video preview and download.
- Added the Manim animation kit, TTS/render pipeline and production quality checks.
- Added redistribution-safe original production templates.
- Added optional `production` and `transcription` dependency groups.
- Docker now includes Manim, Edge TTS, FFmpeg, Cairo/Pango and Noto CJK fonts by default.
- Added production API, dependency, build-context and Docker CI verification.
- Bundled the `video-knowledge-studio` and `demand-driven-video-learning` Agent Skills.
- Added a portable Codex Plugin, repo-local marketplace and one-command Agent installer.
- Added automatic Skill fallback when Codex Plugin installation is unavailable.

## 0.1.0 - 2026-11-18

- Initial open-source edition.
- Generic course-pack loader with multi-chapter ordering.
- Synchronized video and knowledge-note workspace.
- Text-selection tutor with evidence, annotations and reversible revisions.
- Codex CLI, OpenAI-compatible and offline demo providers.
- Background AI jobs and local state store.
- Tests, CI, Docker and redistribution-safe demo course.
- Codex Skill wrapper and one-command bootstrap for Agent-assisted local installs.
- Complete feature, API, configuration, deployment and limitation documentation.
- Runtime provider fallback in automatic AI mode.
- One-command Docker launcher with generated password and CI container health test.
