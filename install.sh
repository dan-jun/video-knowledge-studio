#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")"
python3 scripts/bootstrap.py install

if [ "${VKS_INSTALL_ONLY:-0}" = "1" ]; then
  exit 0
fi

set -- start --open
if [ -n "${VKS_COURSE:-}" ]; then
  set -- "$@" --course "$VKS_COURSE"
fi
if [ -n "${VKS_PORT:-}" ]; then
  set -- "$@" --port "$VKS_PORT"
fi
if [ -n "${VKS_AI_PROVIDER:-}" ]; then
  set -- "$@" --ai-provider "$VKS_AI_PROVIDER"
fi

python3 scripts/bootstrap.py "$@"
