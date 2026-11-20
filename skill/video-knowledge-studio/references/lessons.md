# Lessons

## 2026-11-20 — Local marketplace validity is not public-directory readiness

- **Symptom:** The plugin installed from the repository marketplace, but its final listing
  copy exceeded the public short-description limit and the package had no square icon,
  support URL, or published privacy policy.
- **Root cause:** The repository validated local installability and manifest structure,
  while public submission also enforces directory metadata, branding, legal, and
  review requirements.
- **Fix:** Add a deterministic submission validator and ZIP packager, correct the
  short description, add square branding, and publish privacy, terms, and support
  destinations. Keep repository-marketplace distribution distinct from the universal
  public directory.
- **Verification:** Run the packager in check and package modes, inspect the ZIP root
  layout and manifest, validate every referenced asset and HTTPS URL, and run the
  full plugin test and synchronization gates.

## 2026-11-19 — Keep unit tests independent of optional media binaries

- **Symptom:** The workflow success test passed locally but failed in GitHub CI after
  rendering, while the Docker build and service health checks passed.
- **Root cause:** A unit test called the optional system `ffprobe` executable directly;
  the CI test runner does not promise production media tools.
- **Fix:** Mock the probe lookup and successful probe result in the workflow unit test;
  reserve real FFmpeg/ffprobe checks for environments that explicitly install them.
- **Verification:** Run the complete suite in a clean Python 3.12 container without
  FFmpeg/ffprobe, as well as the normal local suite and plugin sync check.

## 2026-11-19 — Persist production checkpoints and use UTF-8 for Agent stdio

- **Symptom:** Production jobs disappeared on restart, cancellation left child
  processes alive, and a Windows MCP response containing Chinese text failed UTF-8
  decoding in an actual client.
- **Root cause:** Job state existed only in memory, termination targeted the parent
  alone, and Windows redirected standard output used the system code page.
- **Fix:** Save reviewable stage checkpoints, terminate the process tree, mark
  restart-interrupted steps explicitly, and configure MCP stdio as UTF-8.
- **Verification:** Exercise real HTTP and stdio calls, cancel a subprocess with a
  child, restart the service state, retry a failed step, and run the test suite and
  plugin synchronization check.

## 2026-11-19 — Do not accept stale or unverified renders

- **Symptom:** A successful exit code or pre-existing video could make a failed
  production run appear complete.
- **Root cause:** Some commands report failure in structured output even when the
  process exits normally; output files can survive earlier attempts.
- **Fix:** Require an explicit successful command result and a newly written,
  ffprobe-readable video before completing a render stage.
- **Verification:** Automated tests exercise a zero-exit command with an old video,
  successful fresh output, and full workflow checkpoint persistence.

## 2026-11-19 — Bind review checkpoints to their actual inputs

- **Symptom:** A reviewed check could be reused after the storyboard or spec changed.
- **Root cause:** A workflow stored only step statuses, not the files that were checked.
- **Fix:** Record hashes for the spec and generated storyboard and require a new
  workflow if either changes; reject resuming an older workflow after a newer one exists.
- **Verification:** Tests edit the storyboard after review and confirm resume is
  refused; the normal generate-check-render checkpoint sequence still succeeds.

## 2026-11-19 — Treat platform search failures as platform failures

- **Symptom:** A Bilibili search failed with HTTP 412 while the same metadata-only
  search approach returned YouTube results.
- **Root cause:** Platform access can reject automated requests even when the local
  search executable is installed and working.
- **Fix:** Expose optional metadata search with a clear failure response; do not use
  fabricated results or bypass platform access controls.
- **Verification:** Live YouTube search returned results; Bilibili 412 was reported,
  and tests cover failed searches, unverified metadata and URL filtering.

## 2026-11-19 — Preserve incomplete Bilibili search results

- **Symptom:** A successful Bilibili flat search appeared empty despite returning
  video links; another query returned HTTP 412.
- **Root cause:** The extractor returned bare HTTP Bilibili URLs with no title,
  while the initial filter accepted only HTTPS.
- **Fix:** Upgrade known Bilibili URLs to HTTPS and keep missing metadata explicitly
  empty; preserve platform errors without inventing titles or results.
- **Verification:** A captured real response contained HTTP video URLs; automated
  tests cover normalization and unknown fields. A live Agent call correctly reported
  a subsequent HTTP 412 without returning invented results.

## 2026-11-19 — Verify import and AI setup against actual defaults

- **Symptom:** The README's import example did not make an external pack discoverable,
  overstated duration detection, and blurred Docker and local AI defaults; the
  limitations page also contradicted the documented published image.
- **Root cause:** Documentation omitted `VKS_PACKS` and ffprobe prerequisites and
  retained outdated deployment claims after the launcher and registry changed.
- **Fix:** Show the pack path and startup command, explain zero-duration fallback and
  overwrite behavior, distinguish Docker from local AI setup, and align image wording.
- **Verification:** Check the importer, configuration, Compose mounts and launchers;
  validate local Markdown links and run the plugin synchronization check.

## 2026-11-18 — Docker Desktop can be running without `docker` on PATH

- **Symptom:** Docker Desktop and its Linux engine were healthy, but the launcher
  reported that Docker was not installed in a newly opened terminal.
- **Root cause:** Both launchers relied only on `PATH`/`shutil.which`, while the
  per-user Windows installation stores the CLI under
  `%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin`.
- **Fix:** Fall back to Docker Desktop's standard Windows and macOS CLI locations
  before reporting a missing installation.
- **Verification:** With the CLI absent from PATH, the PowerShell launcher built,
  started a healthy container on `127.0.0.1`, accepted login, served a video range,
  completed an offline AI job, and preserved an annotation across container
  recreation. The temporary annotation was then removed.

## 2026-11-18 — Ignore generated session state from the Docker build context

- **Symptom:** A local build copied `data/.session_secret` into the application
  image even though personal note state and cache directories were ignored.
- **Root cause:** `.dockerignore` covered the state and cache subdirectories but
  missed the session secret and PID files stored directly under `data/`.
- **Fix:** Exclude `data/.session_secret` and `data/studio.pid` from the Docker
  build context.
- **Verification:** Rebuild the image and confirm `/app/data/.session_secret` does
  not exist in an image run without the host data volume.

## 2026-11-18 — Explain the three-pane workspace before the feature inventory

- **Symptom:** The README listed individual capabilities but did not explain the
  course directory, synchronized player, and knowledge/AI pane as one learning
  workflow.
- **Root cause:** Feature-oriented documentation omitted the product's primary
  navigation model and the time-based connection between its regions.
- **Fix:** Add a three-pane table and a short select → watch → understand → ask →
  revise → review walkthrough before installation instructions. Label unchecked
  items explicitly as an unimplemented roadmap.
- **Verification:** Compare every table claim with the UI behavior in `web/app.js`
  and `web/knowledge.js`; distinguish the active-lesson marker from saved per-video
  playback position.

## 2026-11-18 — Separate upstream production modes from the learning workspace

- **Symptom:** The public README did not explain the three video-production modes:
  `remix`, `course`, and `scipop`.
- **Root cause:** The repository publishes the downstream knowledge workspace, while
  the production pipeline lives in a separate internal toolchain with additional
  Manim, TTS, rendering, and gate dependencies.
- **Fix:** Start with an explicit production/learning boundary and document the
  modes. This was the interim state before the pipeline was migrated into the public
  repository later the same day.
- **Verification:** Cross-check names, labels, duration ranges, source-count rules,
  chapter and practice constraints, and recap requirements against
  `tools/modes.py` in the production workspace.

## 2026-11-18 — Migrating the production pipeline requires portability proofs

- **Symptom:** The production toolchain initially depended on local drive letters,
  Windows font files and an external virtual environment; its first migrated render
  also failed on a font-constant naming mismatch.
- **Root cause:** The original scripts were optimized for one workstation rather than
  distribution, and a comment-only migration check cannot prove that Manim, TTS,
  FFmpeg and subtitle rendering still compose.
- **Fix:** Add a portable runtime module for FFmpeg, output roots and CJK fonts;
  expose the three modes through `/production.html`; install optional production
  dependencies in Docker; ignore generated projects and scenes; and add CI checks for
  the production page and packages.
- **Verification:** Render a two-page H.264/AAC project with Manim and Edge TTS,
  confirm 1920×1080 output, numeric drift 0.0, inspect a mid-page frame, then repeat
  generation and rendering inside the production Docker image and verify a ranged MP4
  response.

## 2026-11-18 — Lead the README with end-to-end outcomes

- **Symptom:** The README grew by appending production modes after the learning
  workspace, leaving setup, capabilities, privacy, deployment and roadmap mixed
  together.
- **Root cause:** The document was organized as cumulative feature inventory rather
  than around what a learner can accomplish from source video to review.
- **Fix:** Put terminology and the end-to-end value near the top, connect production
  and learning with one flow, then move interfaces, installation, privacy, development
  and roadmap into separate sections.
- **Verification:** Check every local Markdown link and image, keep modes consistent
  with `production/tools/modes.py`, and re-run the test, syntax and Skill validation
  suite after the documentation edit.

## 2026-11-18 — Document demand-driven learning without overclaiming discovery

- **Symptom:** The project's most valuable use case was easy to miss: starting from a
  work, research or project knowledge gap rather than from an existing course.
- **Root cause:** The documentation described video production and learning as separate
  capabilities, but did not connect goal decomposition, source discovery, integration,
  rendering, note taking and contextual AI into one intent-driven workflow.
- **Fix:** Add a demand-driven learning section with concrete examples, an end-to-end
  flow and a copyable Agent task. Mark automatic Bilibili/YouTube discovery and study
  planning as Roadmap items rather than pretending they are built-in.
- **Verification:** Recheck every current-versus-planned claim against the production
  UI and API, then validate all local links and Skill synchronization.

## 2026-11-18 — Package Skills and Plugin as tested release artifacts

- **Symptom:** A documentation-only workflow cannot reliably make a downloaded repository
  expose reusable Agent behavior, and duplicating Skills into a Plugin can silently drift
  from the canonical copies.
- **Root cause:** Codex discovers reusable workflows through Skills and installable Plugin
  bundles; the repository had one install-only Skill and no marketplace or packaging
  consistency check.
- **Fix:** Add a second demand-driven learning Skill, a portable skills-only Plugin,
  repo-local marketplace metadata, a deterministic synchronizer and one-command installers
  with direct-Skill fallback.
- **Verification:** Install the local Plugin in an isolated `CODEX_HOME`, confirm both
  Skills appear in its cache, exercise the `~/.agents/skills` fallback, and run packaging
  and synchronization tests.

## 2026-11-18 — A visual product needs a visual README

- **Symptom:** Even after reorganizing the text, the README still felt abstract because it
  had only one screenshot and no purpose-built flow for demand-driven learning.
- **Root cause:** The documentation explained interfaces and workflows in prose without
  showing the actual product surface or the long multi-step path from a knowledge gap to
  an integrated course and contextual follow-up questions.
- **Fix:** Add an end-to-end vector workflow, a dedicated demand-driven vector flow, a
  before/after problem-solution comparison, screenshots of both live workspaces, an AI
  tutor evidence-and-revision close-up, and a short GIF rendered by the real pipeline.
- **Verification:** Inspect the diagrams and screenshots visually, validate SVG XML,
  check every local README link, and bound demo-asset sizes in automated tests.

## 2026-11-18 — Product demos must show the product operating

- **Symptom:** A narrated static-slide demo looked like a PowerPoint and did not prove
  that video playback, note selection, AI tutoring, production controls, or rendering
  actually worked.
- **Root cause:** The recording focused on explaining features instead of performing
  them, and the default MiniMax speed of 0.85 made narration feel slow and synthetic.
- **Fix:** Combine a short Manim feature animation with an actual browser recording that
  includes a visible cursor, live page changes, an AI response, production controls and
  rendering logs. Use MiniMax `female-yujie` at a faster speed and normalize the final
  audio.
- **Verification:** Confirm the finished video contains both animation and live UI,
  inspect frames from each phase, check H.264/AAC output, and verify audio loudness.

## 2026-11-18 — Codex tutor must not inherit Windows TEMP blindly

- **Symptom:** The AI badge said `codex-cli`, but requests silently returned the
  offline-demo answer; a direct provider call raised `WinError 2/5` while creating
  scratch files.
- **Root cause:** A Windows launcher had inherited a stale, non-ASCII or unwritable
  `TEMP` path. Temporary-directory creation failed before the Codex subprocess
  started, and auto mode silently fell back to mock.
- **Fix:** Create a unique AI scratch directory under `VKS_DATA/ai-tmp`, pass that
  directory as both `TEMP` and `TMP` to the child, and remove the run directory in a
  `finally` block. The fallback remains for genuine provider failures.
- **Verification:** The same question returned a complete `codex-cli` response with
  timestamps, evidence and a proposed revision in about 11 seconds; a regression test
  confirms the child temp path stays inside the configured data directory.

## 2026-11-18 — Reference-inspired launch films need measured pacing

- **Symptom:** A 54-second mix of Manim and live UI was still perceived as a narrated
  slide deck.
- **Root cause:** The team treated “more animation” as sufficient without matching the
  reference's structure: no continuous voiceover, hard visual cuts, real state changes,
  and dense product examples after one complete workflow.
- **Fix:** Analyze frames and audio first, then build an 80-second film with kinetic
  typography, a licensed stock score, cursor-led recordings, real AI output,
  production gates and a purpose-built Raft lesson close.
- **Verification:** Inspect 1–2 second contact sheets and full-resolution keyframes,
  confirm no clipped labels, verify 1920×1080 H.264/AAC, no clipped audio, output under
  10 MB, and replay the learning and production workflows through the public UI.

## 2026-11-18 — Do not reuse an unrelated old render in a launch-video ending

- **Symptom:** The final product showcase dropped into an older linear-algebra video
  with unrelated pacing and visible letterboxing; the background cue also sounded
  mechanically synthesized.
- **Root cause:** The ending was assembled from an available file instead of a scene
  designed for the current story, while the score was generated from low-level pulses
  rather than a professionally arranged track.
- **Fix:** Use a licensed Mixkit track with recorded attribution, and replace the old
  ending with a purpose-built Raft log-replication lesson animation. The new ending
  shows client request, leader fan-out, follower logs, majority acknowledgement and
  commit, then hands off directly to the final product statement.
- **Verification:** Inspect the last 15 seconds frame by frame, verify no overlap in
  the Raft diagram, confirm approximately 80 seconds at 1920×1080/30 fps and under
  10 MB, and compare the uploaded release asset hash with the local file.

## 2026-11-18 — Product demos need a real job-to-be-done opening

- **Symptom:** A technically complete workflow demo still did not explain when a real
  user would need the product or what made it structurally different.
- **Root cause:** The opening led with category positioning, while differentiation was
  spread across unrelated interface scenes and never named.
- **Fix:** Open with “tomorrow's Raft log-replication change, only four hours,” show
  project/research/career entry cases, then label the four core differences: questions
  stay attached to source video, AI receives timestamp/transcript/frame context, notes
  form a network, and production returns to the same learning workspace.
- **Verification:** The 80-second cut matches every claim to a visible screen state or
  generated lesson; contact-sheet review confirms the scenario, workflow, all four
  differentiators, gate evidence and Raft lesson remain readable without narration.

## 2026-11-18 — Every advertised scenario must resolve later

- **Symptom:** The intro advertised project, research and career scenarios, but only
  the project example continued through the demo.
- **Root cause:** The other cards were visual examples rather than commitments connected
  to a shared workflow or a final payoff.
- **Fix:** Map all three scenarios through the same five-stage spine, keep Raft as the
  detailed walkthrough, and recap what each scenario receives at the end.
- **Verification:** Review the script as a promise-to-proof checklist: each intro card
  now reappears in the workflow matrix and in the closing recap, while every middle
  screen uses the same Raft task shown in the intro.

## 2026-11-18 — Cut waits and freeze evidence before cropping

- **Symptom:** Speeding up the AI spinner still left a visible waiting beat, while
  magnifying a live scrolling interface made the detail shots jitter.
- **Root cause:** Waiting was treated as compressible footage rather than removable
  state, and the crop source kept animating during the zoom.
- **Fix:** Cut directly from the submit action to the completed answer, capture a clean
  answer screenshot with selection handles and cursor removed, and crop that still image
  to the relevant panel. Do not use `zoompan` for interface closeups.
- **Verification:** The final cut contains no AI waiting spinner; answer, evidence and
  gate logs are shown from fixed cropped screenshots with no scroll or cursor drift.
