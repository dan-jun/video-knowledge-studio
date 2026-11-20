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
   complete individual or business developer verification. The current verification
   flow requires an eligible payment method for the organization.
2. Confirm the publisher name and category in the dashboard.
3. Upload the generated ZIP through the **Skills only** path.
4. Resolve automated metadata and Skill-scan findings.
5. Submit for review and publish only after approval.

The listing documentation was published on the repository's default branch in commit
`ffb0cda`, and all four public HTTPS URLs returned HTTP 200. Re-run the URL check
immediately before upload. Repository presence, a repo-local marketplace, and
schema-valid JSON do not publish the plugin.

## Platform eligibility

OpenAI requires the submitting developer or organization to use a supported country
or territory and an accepted payment method. Consult the official
[supported countries and territories](https://developers.openai.com/api/docs/supported-countries)
list before starting verification. Mainland China is not currently listed.

Do not use an unsupported billing region, another person's payment method, or an
account-location workaround to bypass this gate; the official documentation warns
that unsupported access can result in account blocking or suspension.

When public-directory eligibility is unavailable, distribute through the public
GitHub repository marketplace instead:

```powershell
codex plugin marketplace add dan-jun/video-knowledge-studio
codex plugin add video-knowledge-studio@video-knowledge-studio-local
```

The local application, Docker image, Skills, and reviewable ZIP remain usable without
public-directory publication.

## Verification before upload

- `python scripts/package_plugin.py --check`
- `python -m unittest discover -s tests -v`
- `python scripts/sync_plugin.py --check`
- `node --check web/app.js`
- `node --check web/knowledge.js`
- `node --check web/production.js`
- confirm every listing URL is public over HTTPS from a signed-out browser.
