#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname "$0")" && pwd)

if [ "${1:-}" != "--skills-only" ] && command -v codex >/dev/null 2>&1; then
  codex plugin marketplace add "$ROOT" --json >/dev/null 2>&1 || true
  codex plugin remove "video-knowledge-studio@video-knowledge-studio-local" --json >/dev/null 2>&1 || true
  PLUGIN_OUTPUT=$(codex plugin add "video-knowledge-studio@video-knowledge-studio-local" --json 2>&1) || true
  if printf '%s' "$PLUGIN_OUTPUT" | grep -q '"pluginId"' || printf '%s' "$PLUGIN_OUTPUT" | grep -qi 'already'; then
    printf '%s\n' '{"ok":true,"method":"plugin","restartRequired":true}'
    exit 0
  fi
fi

SKILLS_ROOT="${VKS_AGENT_SKILLS_ROOT:-${HOME}/.agents/skills}"
mkdir -p "$SKILLS_ROOT"
for skill in "$ROOT"/skill/*; do
  if [ -f "$skill/SKILL.md" ]; then
    rm -rf "$SKILLS_ROOT/$(basename "$skill")"
    cp -R "$skill" "$SKILLS_ROOT/"
  fi
done
printf '%s\n' "{\"ok\":true,\"method\":\"skills\",\"skillsRoot\":\"$SKILLS_ROOT\",\"restartRequired\":true}"
