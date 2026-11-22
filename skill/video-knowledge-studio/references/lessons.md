# Lessons

## 2026-11-22 - A course graph needs normalized hierarchy keys

**Symptom:** The first galaxy layout displayed five chapter points but collapsed nearly
all 656 concepts and 3,486 atoms around the course center, producing a bright central
blob instead of chapter clusters.

**Root cause:** Chapter records used IDs such as `chapter-第1章…`, while lesson and
concept records used `第1章…`. Cluster lookups silently missed and every lesson fell
back to the world center.

**Fix:** Normalize `chapter-*` prefixes whenever chapter membership is joined, retain
the display chapter separately, and verify layout extents and per-chapter node counts
before rendering. Draw concepts and atoms on Canvas with chapter colors, real relation
edges, local anchor beams and focused pulsing neighbours.

**Verification:** The live map rendered 656 concept lights, 3,486 note stars, 983 beams
and 5 separated chapter clusters. Search for “系统调用” opened a detail panel with nine
neighbours and E01/E05/E06 links; selecting a chapter and resetting to the full course
also worked.

## 2026-11-22 - Do not stack the new knowledge plugin over the old report

**Symptom:** The new Learning/Knowledge/Review surface still felt noisy and its text
was too small. The page showed the deep-note view, then repeated the old summary,
timeline, terms, network, recall and evidence sections underneath it.

**Root cause:** The plugin added a second knowledge experience without hiding the
legacy renderer. The note pane also kept only 43% of the workspace, forcing dense
8–11px typography and a miniature graph.

**Fix:** Give the reading pane about 61% of the desktop width, raise primary questions
to 24px and body copy to 14–16px, replace tiny graph-first navigation with large anchor
cards, and collapse the graph until an anchor is selected. Toggle a `has-deep-note`
state that hides legacy duplicate sections only while a deep note is available.

**Verification:** In the live player the note pane was 902px wide, primary question
24px, anchor summaries 14px, the graph was closed by default, nine legacy sections were
hidden, and full anchors/atoms/course structure remained accessible from Knowledge.

## 2026-11-22 - Knowledge completeness still needs a usable learning entry

**Symptom:** The course graph contained 656 canonical concepts, 3,486 atoms and 983
core relations, but the player exposed one long scroll of anchors, atoms and course
indexes. Users could see that the data was complete while still not knowing where to
start, how to focus a concept or what to review next.

**Root cause:** Navigation compression, evidence completeness and learning workflow
were all rendered as sections of one report. Cross-lesson data also stored a numeric
episode but the frontend required an `episodeId`, so every intended cross-lesson link
was silently filtered out.

**Fix:** Split the surface into Learning, Knowledge and Review views. Keep the core
network in Learning, focus a clicked anchor and its direct neighbours, expose the full
atom layer only in Knowledge, preserve both `episodeId` and episode number in the
course graph, and add per-lesson browser-local mastery plus a review queue.

**Verification:** In the live player, the default view was Learning; clicking an
anchor opened a focus panel with direct relations and evidence; marking a node
"unsure" produced a review badge and queue item that survived refresh; E01 exposed
cross-lesson E05/E06 links and opening E05 changed the active lesson.

## 2026-11-21 — Visual audit is not a command to include every frame

- **Symptom:** Forcing one representative from every OCR cluster inserted course
  endings, watermarks and decorative cards into the knowledge note.
- **Root cause:** The quality gate counted cluster inclusion instead of whether the
  cluster carried unique teaching information.
- **Fix:** Require a decision for every candidate, but require inclusion only for
  instruction-bearing clusters. Allow explicit `noise` or `unreadable` groups and
  record every automatic inclusion or exclusion.
- **Verification:** The real 87-lesson audit reviewed 2,388 candidates in 1,441
  clusters, retained 1,438 evidence frames, and moved three automatically inserted
  non-instructional frames back to `noise`.

## 2026-11-21 — Time ranges must yield a numeric start and evidence must follow it

- **Symptom:** Ranges such as `06:02–08:29` became `start=0`, and concept evidence
  repeatedly quoted the course greeting.
- **Root cause:** The parser accepted only point timestamps, and generation trusted
  model timestamps without checking that the quote supported the claim.
- **Fix:** Parse the first timestamp of a range, then align low-confidence evidence
  inside the semantically linked transcript block. Store the correction in the
  visible repair ledger.
- **Verification:** A deterministic repair pass corrected 4,147 timestamp or visual
  fields across 87 episodes; regression tests cover range starts, intro avoidance and
  decorative-frame removal.

## 2026-11-21 — Bind semantic review to hashes and expose stale status

- **Symptom:** A note with blocking omissions could still pass a structural audit, and
  a review of the pre-repair note stayed visible after the note changed.
- **Root cause:** Structure and semantics were conflated, and review sidecars were not
  tied to current inputs.
- **Fix:** Store note/transcript/frame hashes and an input fingerprint in each review
  sidecar. Mark mismatched sidecars stale in the API and player, and keep delivery
  status false until every episode has a current passing review.
- **Verification:** The 87-note audit reports structural success separately from
  semantic delivery; 62 earlier reviews became stale after the repair instead of being
  silently reused.

## 2026-11-21 — Pause batch review on provider billing failures

- **Symptom:** The semantic-review batch returned HTTP 402 `Insufficient Balance`
  during a long run.
- **Root cause:** Provider availability was treated like an episode-level retry.
- **Fix:** Classify 401/402/403/429 as queue-level blocks, stop dispatching work,
  retain completed sidecars, and report blocked and unattempted episodes explicitly.
- **Verification:** The run preserved 62 sidecars and reported the exact blocked and
  unattempted range rather than producing fabricated or empty approvals.

## 2026-11-21 — Soft model judgments need deterministic evidence ledgers

- **Symptom:** A plugin could claim coverage while skipping useful diagrams and while
  returning only a linear knowledge flow.
- **Root cause:** The prompt asked for coverage and visuals, but the validator did not
  assign fixed transcript blocks or account for every frame candidate independently.
- **Fix:** Generate contiguous transcript blocks first, require a decision and key
  points for every block, cluster visual candidates but audit every frame, require an
  included representative from each cluster, and validate a connected multi-relation
  concept graph.
- **Verification:** Unit tests cover exact block union, stale cache rejection, visible
  candidate completeness, and disconnected graph failure. Real Codex runs completed for
  the demo course, and Episode 13 rendered 3 blocks, 28 audited frames in 21 clusters,
  21 included visuals, and an 8-node/12-edge graph in the live player.

## 2026-11-21 — Verify the listening PID before declaring a restart complete

- **Symptom:** After changing the studio server, a reload still served old code.
  The handoff PID was terminated, but another process still owned port 7870; a new
  process briefly started without becoming the listener.
- **Root cause:** Process readiness was inferred from a remembered handoff PID and
  from the existence of a newly launched process, rather than from the socket owner.
- **Fix:** Resolve the exact listener with `Get-NetTCPConnection`, validate its
  command line, stop that process and any failed contender, start the server hidden,
  then wait until the listener belongs to the intended service before testing routes.
- **Verification:** The final listener command points to `tools/studio_server.py
  --host 0.0.0.0 --port 7870`; the browser showed the new evidence label, a loaded
  deep-note result, loaded visual thumbnails, and a timestamp jump to `currentTime=31`.

## 2026-11-21 — Deep knowledge notes need a synthesis contract

- **Symptom:** A player plugin exposed a “generate notes” button, but the open-source
  server had no deep-note endpoints and no contract preventing a transcript dump.
- **Root cause:** The frontend and visual styling were implemented before the service
  generated, validated, cached and invalidated a distinct knowledge artifact.
- **Fix:** Add an asynchronous deep-note service with a strict JSON schema, full
  transcript and visual inputs, a 5–9 concept structure, 90% timeline coverage,
  source-hash cache invalidation, safe frame paths and explicit failure for offline
  demo mode.
- **Verification:** `tests/test_deep_notes.py` covers caching, stale-input rejection,
  thin-output rejection and offline behavior; `tests/test_server.py` covers all three
  routes and path scoping; the full 48-test suite and Node syntax checks pass.

## 2026-11-21 — Native cue styling is not a subtitle system

- **Symptom:** One long transcript segment became one giant native caption cue;
  the browser painted a full-width black block over the controls and wrapped speech
  mid-sentence.
- **Root cause:** The player delegated both segmentation and presentation to WebVTT.
  It neither split long transcript text into subtitle-sized phrases nor controlled
  position relative to the player chrome.
- **Reference:** Bilibili renders short white bold phrases with a black outline above
  the control bar. YouTube raises bottom captions while controls are visible and lets
  them fall when controls auto-hide; it also exposes size/style settings.
- **Fix:** Build short caption cues from punctuation and character limits, render them
  in a custom accessible overlay, keep them to two lines, move them with control
  visibility, and add persisted outline/box and size settings.
- **Verification:** In the live player, long transcript text became single-line short
  cues, no native `<track>` remained, controls-on bottom was 64px, controls-hidden
  bottom was 18px, and caption toggling hid/showed the overlay immediately.

## 2026-11-21 — Summary cards must be backed by full evidence coverage

- **Symptom:** Each episode showed only 2–5 core cards, 2–5 timeline rows and a few
  terms, so much of the lecture never appeared in the knowledge panel.
- **Root cause:** The renderer consumed only the pre-summarized `core` and `timeline`
  arrays and did not expose the complete timed transcript as readable knowledge cards.
- **Fix:** Group every valid transcript segment exactly once into timed, expandable
  knowledge cards; show section/segment coverage and keep per-line playback jumps.
- **Verification:** Episode 13 renders 10 expandable cards covering 243 transcript
  segments; a deterministic test compares flattened card segments with the input rows.

## 2026-11-21 — An overlay control needs its inverse transition

- **Symptom:** Pressing the settings gear repeatedly kept the menu open, and the menu
  could cover the video indefinitely.
- **Root cause:** The gear action always called `openMenu()`; there was no toggle,
  Escape handler, outside-click dismissal, or automatic close after choosing an option.
- **Fix:** Toggle from the gear, close on Escape/outside click, and close after applying
  speed, quality, or caption choices.
- **Verification:** In the real player, gear opened and closed the menu; Escape and an
  outside click closed it; selecting 1× speed closed it afterward.

## 2026-11-21 — A media control must change media state

- **Symptom:** The subtitle button changed its own `ccOn` flag and showed a toast, but
  the video displayed no captions because no text track existed.
- **Root cause:** The player treated burned-in captions as the only source and never
  received the course transcript, so the control had no media state to modify.
- **Fix:** Generate a WebVTT track from timed transcript cues, pass the lesson transcript
  into the player after knowledge loads, and toggle the track between `showing` and
  `disabled`. Disable the control when the lesson has no timed transcript.
- **Verification:** Load a real operating-system lesson, start playback, confirm the
  cue appears, then toggle captions off and confirm the cue disappears without changing
  the video source.

## 2026-11-21 — Windows reserved ports can pass a connection probe

- **Symptom:** The launcher chose port 7898 but the server exited with Windows
  `PermissionError 10013`; an explicit port 7900 started normally.
- **Root cause:** Port selection treated “no listener accepted a connection” as
  available, but Windows excluded-port ranges can reject `bind()` even when
  `connect_ex()` finds no listener.
- **Fix:** When automatic startup fails with `WinError 10013`, inspect the chosen
  port and retry with an explicitly available port. Launcher changes should probe
  actual socket binding rather than connection success alone.
- **Verification:** Port 7900 listened on `127.0.0.1`, the bootstrap status reported
  the saved process as running, and `GET /` returned HTTP 200 with the Video
  Knowledge Studio title.

## 2026-11-20 — Distinguish package readiness from account eligibility

- **Symptom:** A schema-valid plugin package passed local validation, but the Platform
  blocked the upload behind verified developer identity and then an organization
  payment-method requirement; mainland China is not in the supported-country list.
- **Root cause:** Submission checks covered metadata, skills, assets, and review links
  but not the publisher's supported-region, identity-verification, and billing status.
- **Fix:** Add platform eligibility to the preflight. Require a supported territory and
  an accepted payment method, and treat direct GitHub marketplace installation as the
  fallback when universal-directory eligibility is unavailable.
- **Verification:** Observe the Platform identity modal and required-payment modal, then
  check mainland China and Hong Kong against the official supported-countries page
  before deciding whether submission can continue.

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

## 2026-11-22 - Empty OCR is missing evidence, not proof a frame is unimportant

- **Symptom:** Two course episodes automatically excluded every independent frame
  group whose OCR was empty, then retained repair messages that contradicted the
  final visual decisions.
- **Root cause:** OCR presence was treated as the only proof of teaching value, and
  repair logs were append-only after later human review reversed a decision.
- **Fix:** Inspect the actual frame, add concise human OCR, record an explicit
  decision for every candidate, and rewrite stale repair messages. Rebuild visual
  evidence from the audit and keep the input hash synchronized.
- **Verification:** The affected episodes re-passed fresh semantic review after
  correcting a full working-set sequence, a per-channel CHCT definition, and two
  unsupported concept edges.

## 2026-11-22 - Core anchors must not cap knowledge coverage

- **Symptom:** A 5–9 core-concept range made complete lessons appear to contain only
  a handful of knowledge units.
- **Root cause:** Navigation compression and evidence coverage shared one array, so
  a readability heuristic became an accidental epistemic limit.
- **Fix:** Keep anchors for the compact graph, but add an unlimited deterministic
  `knowledgeAtoms` layer sourced from every instructional coverage key point. Bind
  each atom to block, time, anchors and visual evidence; expose the full layer on
  demand and retain the anchors as the default view.
- **Verification:** The migrated course preserves 677 anchors while carrying 3,486
  atoms and 18,347 atom-layer relations; every non-housekeeping key point maps once.
