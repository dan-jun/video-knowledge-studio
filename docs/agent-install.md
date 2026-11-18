# Install with a Codex Agent

## What to send

Send the Agent:

1. the GitHub repository URL;
2. an optional absolute path to a folder containing the user's videos;
3. the preferred AI mode (`codex`, `openai`, `mock`, or `auto`).

Example prompt:

```text
Install Video Knowledge Studio from <github-url> on this computer.
Keep it local-only. Use my course folder at D:\courses\operating-systems.
Use my local Codex CLI for AI, start the service, verify it, and open the workspace.
Do not upload or copy my course content anywhere else.
```

## What the Agent does

1. clones or locates the repository;
2. reads `skill/video-knowledge-studio/SKILL.md`;
3. copies the skill into `$CODEX_HOME/skills/video-knowledge-studio`;
4. runs the importer only when a course folder is provided;
5. starts a loopback-only local server;
6. reports the actual URL and PID.

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

The installed workspace is still per-person. The loopback URL is not a shared public
service.
