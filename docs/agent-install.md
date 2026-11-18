# Install with a Codex Agent

The repository ships two Skills and one portable Plugin:

- `video-knowledge-studio` — install, start, import and troubleshoot the local app;
- `demand-driven-video-learning` — turn a knowledge gap into a learning plan,
  multi-source research, animated course and synchronized notes;
- `video-knowledge-studio` Plugin — bundles both Skills for one-step Codex installation.

## What to send

Send the Agent:

1. the GitHub repository URL;
2. an optional absolute path to a folder containing the user's videos;
3. the preferred AI mode (`codex`, `openai`, `mock`, or `auto`).

Example prompt:

```text
Install Video Knowledge Studio from <github-url> on this computer.
Keep it local-only. Use my course folder at D:\courses\operating-systems.
Install the bundled Skills and Plugin, use my local Codex CLI for AI,
start the service, verify it, and open the workspace.
Do not upload or copy my course content anywhere else.
```

## What the Agent does

1. clones or locates the repository;
2. reads the bundled Agent guidance;
3. registers the repo-local Plugin marketplace and installs the Plugin, or falls back
   to copying both Skills into `~/.agents/skills`;
4. runs the importer only when a course folder is provided;
5. starts a loopback-only local server;
6. reports the actual URL, PID and Agent installation method.

## One-command local install

```powershell
install.ps1
```

With a course folder:

```powershell
install.ps1 -Course "D:\courses\my-course" -AiProvider codex
```

macOS/Linux:

```bash
VKS_COURSE="/home/me/courses/my-course" ./install.sh
```

Install the Agent bundle without starting the app:

```powershell
python scripts/bootstrap.py install
```

Codex CLI users can also register the marketplace explicitly:

```powershell
codex plugin marketplace add .
codex plugin add video-knowledge-studio@video-knowledge-studio-local
```

Restart Codex or open a new chat after installation so the Plugin and Skills are
discovered.

The installed workspace is still per-person. The loopback URL is not a shared public
service. See [Agent Skills and Codex Plugin](plugin.md) for the complete bundle layout,
fallback behavior and removal commands.
