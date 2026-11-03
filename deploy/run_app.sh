#!/usr/bin/env bash
# Run one participant app on its fixed local port; the Cloudflare tunnel publishes it.
# Usage: run_app.sh <slug from deploy/apps.tsv>
set -euo pipefail

slug="$1"
app_root="$(cd "$(dirname "$0")/.." && pwd)"
read -r port entry < <(awk -v slug="$slug" '$1 == slug {print $2, $3}' "$app_root/deploy/apps.tsv") || true
if [[ -z "${port:-}" ]]; then
  echo "Unknown app slug: $slug" >&2
  exit 1
fi

cd "$app_root"
export PYTHONPATH="$app_root/src"
exec "$XAI_STUDY_VENV/bin/streamlit" run "$entry" \
  --server.address 127.0.0.1 --server.port "$port" --server.headless true
