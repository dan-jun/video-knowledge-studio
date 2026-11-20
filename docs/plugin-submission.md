# Public Plugin Submission

This document prepares the Skills-only Video Knowledge Studio plugin for the universal
ChatGPT/Codex Plugins Directory. It is not evidence that the plugin has been uploaded,
reviewed, or published.

## Current state

- The package uses the Agent Plugins 1.0 portable manifest.
- It bundles `video-knowledge-studio` and `demand-driven-video-learning`.
- It is Skills-only: there is no MCP server, hosted account, or bundled web service.
- The local application remains a separate installation.
- The repository marketplace is for development and direct GitHub distribution; it is
  not the universal public directory.

## Build the submission candidate

From the repository root:

```powershell
python scripts/package_plugin.py --check
python scripts/package_plugin.py
```

The default output is:

```text
dist/video-knowledge-studio-plugin-<version>.zip
```

The archive contains one top-level directory with root `plugin.json`, both Skills,
square branding, and the plugin license. The packager rejects missing files, unsafe
paths, unsupported listing lengths, non-HTTPS listing URLs, malformed Skills, and
non-square branding.

## Public listing copy

Display name: **Video Knowledge Studio**

Subtitle: **Turn gaps into video courses**

Starter prompts:

1. Turn my project knowledge gap into a sourced course and study notes.
2. Plan what I should learn, then build a local workspace with synchronized notes.

The listing must continue to state that:

- source search depends on the Agent's available tools and platform access;
- the application is local and separately installed;
- generated claims, notes, and media require review;
- third-party content licenses remain the user's responsibility.

## Submission blockers that require a human

1. Sign in to the OpenAI Platform with an organization that owns the submission and
   complete individual or business developer verification.
2. Confirm the publisher name and category in the dashboard.
3. Upload the generated ZIP through the **Skills only** path.
4. Resolve automated metadata and Skill-scan findings.
5. Submit for review and publish only after approval.

The listing documentation was published on the repository's default branch in commit
`ffb0cda`, and all four public HTTPS URLs returned HTTP 200. Re-run the URL check
immediately before upload. Repository presence, a repo-local marketplace, and
schema-valid JSON do not publish the plugin.

## Verification before upload

- `python scripts/package_plugin.py --check`
- `python -m unittest discover -s tests -v`
- `python scripts/sync_plugin.py --check`
- `node --check web/app.js`
- `node --check web/knowledge.js`
- `node --check web/production.js`
- confirm every listing URL is public over HTTPS from a signed-out browser.
