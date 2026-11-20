# Video Knowledge Studio Plugin Privacy Policy

Last updated: 2026-11-20

This policy describes the Codex plugin named **Video Knowledge Studio**. The plugin
bundles Agent Skills. It does not include a hosted account, MCP server, telemetry
service, advertising service, or central data store.

## Data the plugin may process

- Your prompt and the files, text, links, goals, preferences, course folders, or
  transcripts you explicitly provide while asking an Agent to use the Skills.
- Search results, captions, timestamps, screenshots, or metadata obtained through the
  search, browser, download, or media tools available to your Agent and authorized by
  you.
- Information stored by the separately installed local application, including course
  packs, notes, annotations, revision history, production projects, generated videos,
  local logs, and configuration.
- When you invoke the local AI tutor, the selected note, nearby transcript, timestamp,
  recent conversation context, relevant frame, and question sent to the model provider
  configured by the user.

The plugin does not request passwords, API keys, payment-card data, government
identifiers, protected health information, or precise location data.

## Purposes of use

The data is processed to plan a learning path, compare selected sources, generate a
course and synchronized notes, operate the local workspace, answer contextual
questions, and troubleshoot media or production workflows.

## Recipients

- The model provider selected in the user's Agent or Video Knowledge Studio
  configuration receives prompts and contextual content only when the user invokes an
  AI-assisted operation.
- Search, browsing, video-platform, transcript, or download tools selected by the user
  may receive the queries and URLs needed for the requested operation.
- No recipient is used for advertising, behavioral profiling, or sale of personal
  data by Video Knowledge Studio.

Third-party providers process requests under their own terms and privacy policies.

## Storage and retention

Video Knowledge Studio is local-first and stores user-created course, note, annotation,
revision, configuration, log, and production data on the user's computer or in a
user-selected Docker volume by default. These files remain until the user deletes
them, clears the relevant application data, or removes the installation.

The plugin package itself does not retain user content. A model or search provider may
retain requests according to the account, API, or provider settings selected by the
user. Users should review those provider settings before submitting sensitive content.

## User controls

- Choose whether to search external platforms or use a local course.
- Choose the local Codex, OpenAI-compatible, or offline-demo AI mode.
- Avoid sending a question or attachment to a model provider.
- Delete local course packs, notes, generated projects, and application data.
- Review or reject AI-proposed note revisions before accepting them.
- Remove the plugin or the local application independently.

## Security and external content

The application listens on `127.0.0.1` by default. Remote deployment requires the
user to configure authentication, HTTPS, and appropriate access controls. External
videos, captions, screenshots, and handouts remain subject to their own licenses and
platform terms.

## Contact

For support, privacy questions, or deletion guidance, open an issue at
<https://github.com/dan-jun/video-knowledge-studio/issues>. Do not include secrets or
personal course data in a public issue. Report sensitive security matters through the
repository's private security-reporting feature described in `SECURITY.md`.

This policy may be updated as the plugin or its local application changes. The latest
version is always published in the repository.
