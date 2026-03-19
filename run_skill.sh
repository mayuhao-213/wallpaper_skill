#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="/tmp/wallpaper_skill_bash.log"
exec >> "$LOG_FILE" 2>&1

echo "==== $(date) ===="
echo "ARGS: $@"
echo "PWD before: $(pwd)"

source /home/admin/miniconda3/etc/profile.d/conda.sh
conda activate wallpaper_skill
cd /home/admin/.openclaw/workspace/skills/wallpaper_skill

mkdir -p /home/admin/.openclaw/workspace/skills/wallpaper_skill/runtime/uploads
mkdir -p /home/admin/.openclaw/workspace/skills/wallpaper_skill/runtime/outputs/openclaw_runs

echo "PWD after: $(pwd)"
echo "Python path: $(which python)"
echo "Python version: $(python --version)"

python skill.py "$@"