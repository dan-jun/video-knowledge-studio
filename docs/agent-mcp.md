# Agent MCP bridge

An Agent is an assistant that can call tools. MCP is a standard way for the Agent
to discover and call those tools. The bridge communicates with an already running
local Video Knowledge Studio application; it does not start the application.

| Term | Plain meaning | Example | First appearance | Self-check |
| --- | --- | --- | --- | --- |
| Agent | An assistant that can use tools for a task | Read a lesson and start a render | Opening | Know / Unsure / Need work |
| MCP | A protocol for exposing named tools to an assistant | `list_courses` | Opening | Know / Unsure / Need work |
| Workflow | A recorded sequence of production steps with review pauses | Generate → check → render | Tools | Know / Unsure / Need work |
| Spec | A structured source document describing a video | A reviewed `scipop` lesson plan | Tools | Know / Unsure / Need work |
| Token | A short-lived or session credential used to access a protected service | `VKS_MCP_TOKEN` | Setup | Know / Unsure / Need work |
| yt-dlp | An optional tool for retrieving video-site metadata | Search for video titles and URLs | Tools and boundaries | Know / Unsure / Need work |

## Setup

Start the app from the repository using `python -m vks`. Configure an MCP client to
launch the following command with the repository as its working directory:

```text
python -m vks.mcp_server
```

The bridge uses newline-delimited JSON-RPC over standard input and output. Set
`VKS_MCP_URL` to the actual local HTTP origin if the app uses another port. Only
`127.0.0.1`, `localhost`, or `::1` origins are accepted. If the app requires a
password, call `POST /api/login` locally and provide its returned token as
`VKS_MCP_TOKEN` in the MCP server environment. Do not put a token in the repository.
The token is invalid after expiration or a session-secret change.

## Tools and boundaries

`capabilities`, `search_sources`, `list_courses`, `read_lesson`, `list_production_projects`,
`create_production_project`, `create_workflow`, `workflow_status`,
`workflow_resume`, `workflow_cancel`, `workflow_abandon`, `ask_lesson`, and
`answer_status` expose existing app behavior. `ask_lesson` sends lesson context to the
configured AI provider; call it only when the user requests AI assistance. The
workflow pauses for review after generation and checks.

`search_sources` requires a separately installed `yt-dlp` executable. It sends the
query to the chosen platform and returns unverified metadata only. Access can fail;
for example, Bilibili returned HTTP 412 in a local test on 2026-11-19. It does not
download video or bypass platform restrictions.

Subtitle collection, transcription, source scoring, sourced spec authoring, and
complete note generation are not provided by this bridge. An Agent must use
available external tools and preserve source URLs, timestamps, license information,
and uncertainty. A placeholder is not a verified lesson.

See [HTTP API](api.md#reviewable-production-workflows) for interruption recovery.
The bridge does not expose the manual interrupted-process confirmation operation.
