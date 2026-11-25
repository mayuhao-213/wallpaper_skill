#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SKILL_DIR"

# Prefer a local venv; otherwise use the caller's activated Python environment.
if [[ -x "$SKILL_DIR/.venv/bin/python" ]]; then
    PYTHON_BIN="$SKILL_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "Python was not found. Create .venv or activate a Python environment first." >&2
    exit 127
fi

mkdir -p runtime/uploads runtime/outputs/openclaw_runs

# Keep the result and errors visible to the calling agent or terminal.
exec "$PYTHON_BIN" skill.py "$@"
