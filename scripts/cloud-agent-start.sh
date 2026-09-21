#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}/backend"

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

if [[ ! -d venv ]]; then
  echo "Backend virtualenv missing. Run install first." >&2
  exit 1
fi

./venv/bin/python reset_users.py
