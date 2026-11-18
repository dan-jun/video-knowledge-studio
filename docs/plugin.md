# Agent Skills and Codex Plugin

The repository distributes a portable Codex Plugin containing two Skills.

## What is included

| Component | Purpose |
| --- | --- |
| `video-knowledge-studio` Skill | Install and operate the local learning workspace and video production pipeline |
| `demand-driven-video-learning` Skill | Turn a work, research or project knowledge gap into a learning plan, multi-source video course and synchronized notes |
| `video-knowledge-studio` Plugin | Install both Skills together through a local marketplace |

The plugin is skills-only. It does not ship credentials, an MCP server or a privileged
search service. Source discovery uses the tools available to the installed Agent, such
as platform search connectors, browser/search tools and `yt-dlp`.

## One-command installation

Windows:

```powershell
.\install.ps1
```

macOS/Linux:

```bash
./install.sh
```

To install only the Agent bundle:

```powershell
.\install-agent.ps1
```

```bash
./install-agent.sh
```

The installer:

1. attempts to register `./.agents/plugins/marketplace.json`;
2. installs `video-knowledge-studio@video-knowledge-studio-local`;
3. falls back to copying both Skills into `~/.agents/skills/` when Codex CLI or Plugin
   installation is unavailable;
4. reports whether a restart is required.

The Docker launcher performs the same best-effort Agent installation before starting
the container.

## Manual Codex installation

```bash
codex plugin marketplace add .
codex plugin add video-knowledge-studio@video-knowledge-studio-local
codex plugin list --json
```

Open a new Codex chat after installation.

## Example requests

After installation:

```text
Use $demand-driven-video-learning to help me understand Raft in four hours.
My baseline is HTTP and basic databases. I need enough to read a project's
log-replication code. Find several complementary Bilibili and YouTube sources,
build a study plan, render an integrated animated course, and create notes I
can ask follow-up questions about.
```

or:

```text
Use $video-knowledge-studio to install the local workspace and import my course folder.
```

## Boundaries

- Automatic search quality depends on the Agent's connected search/browser tools and
  network access.
- Platform login, regional restrictions, missing captions and content licenses can stop
  a source from being usable.
- The Agent must record real URLs and timestamps; it must not fabricate research.
- Downloaded media and transcripts must not be redistributed without permission.
- Generated notes and revisions remain proposals until reviewed.

## Removal

```bash
codex plugin remove video-knowledge-studio@video-knowledge-studio-local
codex plugin marketplace remove video-knowledge-studio-local
```

For a direct-Skill installation, remove the two matching folders under
`~/.agents/skills/`.
