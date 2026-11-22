# Changelog

## Unreleased

- Added an interactive **Knowledge Galaxy** view rendered on Canvas. All 656
  canonical concepts appear as glowing concept nodes, all 3,486 knowledge atoms as
  smaller note stars, and the 983 evidence-backed concept relations as luminous beams.
- The galaxy preserves the course → chapter → lesson → anchor → atom hierarchy:
  chapters become distinct colored clusters, lesson membership appears as faint local
  links, and the current lesson is marked in gold.
- Added semantic zoom and reduced label collisions: chapter cards remain visible at the
  course overview, the most connected concepts gain labels as the user zooms in, and a
  focused concept labels its direct neighbours and relationship types.
- Relation beams now use distinct colors for prerequisite, mechanism, causal, contrast,
  example, application and grouping links, with a star field, chapter orbit rings and
  focused travelling light pulses.
- The course sequence is drawn as an animated chapter flow with directional arrows and
  travelling pulses, while relationship groups in the detail panel distinguish incoming
  and outgoing mechanisms, causes, applications and prerequisites.
- Added search, chapter selection, current-lesson focus, drag-to-pan, wheel zoom,
  full-course reset, local-neighbour highlighting, animated relation pulses, and a
  detail panel with timestamps and other-lesson links.
- Added `/star_map.js` to both the local and open-source static asset routes.
- Added a reading-first layout for course notes: the knowledge pane now receives
  roughly 61% of the workspace, primary questions render at 24px, explanatory text at
  14–16px, and the core-anchor navigator uses large vertical cards instead of tiny
  graph labels.
- The core relationship graph is collapsed behind an explicit disclosure. Selecting an
  anchor opens that disclosure and focuses the anchor, its direct neighbours and
  source evidence without exposing the entire course network at once.
- When a deep-note artifact is available, the legacy summary, timeline, term, recall
  and visual sections are no longer stacked underneath the new note. The legacy view
  remains as a fallback when no deep note exists, while complete anchors, atoms,
  evidence and course structure remain available in the Knowledge tab.
- Reworked the knowledge surface into compact Learning, full Knowledge and personal
  Review views instead of one long report. The Learning view now shows the lesson,
  study goals, knowledge line and core network without exposing the complete atom
  catalog by default.
- Added click-to-focus behaviour to the core graph. A selected anchor highlights its
  direct neighbours, explains their typed relationships, exposes source evidence and
  keeps unrelated parts of the graph visually quiet.
- Added cross-lesson concept links from course-graph occurrences. The renderer now
  resolves stable episode IDs and tolerates legacy graphs that only provide display
  numbers, so a reused concept can open the other lesson instead of silently
  producing no link.
- Added per-lesson mastery states (`known`, `fuzzy`, `unknown`), browser-local
  persistence and a priority review queue for uncertain anchors and knowledge atoms.
- Added a player-embedded deep knowledge plugin that reconstructs a lesson into a
  central problem, causal model, structured concepts, boundaries, misconceptions,
  comparisons, recall, glossary and a timeline coverage ledger.
- Added asynchronous deep-note generation, per-episode caching and source-hash
  invalidation for the Codex CLI and OpenAI-compatible providers.
- Replaced soft percentage coverage with a deterministic, contiguous transcript ledger
  that requires every block and every extracted key point to be accounted for.
- Added a visual audit for every keyframe candidate and near-duplicate cluster.
  Instruction-bearing clusters require an included representative; end cards,
  watermarks and decoration are explicitly excluded instead of being forced into notes.
- Added hash-bound fresh-context semantic reviews. The player distinguishes current
  approval, failure, stale review and missing review, and 401/402/403/429 pause the
  resumable review queue instead of producing empty approvals.
- Added a typed, connected concept graph plus player rendering for prerequisite,
  mechanism, causal, contrast, example and application relationships.
- Added explicit `grouping` edges for course-overview branches, so structural
  taxonomy is represented honestly instead of forcing unsupported causal edges.
- Empty OCR no longer causes an instructional frame to be discarded automatically;
  manual frame review and restored OCR are preserved in the visual audit.
- Added a schema-v3 multiscale knowledge model: 5–9 is now a recommendation for
  core navigation anchors, while every instructional coverage key point becomes one
  evidence-linked `knowledgeAtom` without a total-count cap.
- Added a grouped, searchable complete-atom view and course-level lesson navigation;
  the compact core graph remains the default network instead of turning into a
  hundreds-of-node spiderweb.
- Added schema-v3 migration and validation helpers so ordinary coverage key points,
  not only the core anchors, can be audited and restored from source evidence.
- Added resumable course-wide generation and graph-building scripts for all episodes,
  with per-episode state, retries and input-hash validation.
- Added an embedded course-system view with chapter maps and a full canonical concept
  index.
- Demoted the raw transcript to a folded, explicitly evidence-only section and fixed
  the knowledge-frame URL contract.

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
