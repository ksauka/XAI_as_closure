#!/usr/bin/env bash
# Install the participant apps and their Cloudflare tunnel as user services.
# Run once from this repository; re-running is safe.
set -euo pipefail

source_root="$(cd "$(dirname "$0")/.." && pwd)"
base="$HOME/.local/share/xai-as-closure"
config="$HOME/.config/xai-as-closure"
units="$HOME/.config/systemd/user"
python="${XAI_STUDY_PYTHON:-$HOME/miniconda3/bin/python}"
repo_url="$(git -C "$source_root" remote get-url origin)"

if ! systemctl --user show-environment >/dev/null 2>&1; then
  echo "The user service manager is unreachable (\"Failed to connect to bus\")." >&2
  echo "Restart WSL from Windows with 'wsl --shutdown', reopen a terminal, then run this again." >&2
  exit 1
fi

mkdir -p "$base/data" "$config" "$units"
chmod 700 "$base" "$base/data" "$config"

# The services run a separate checkout of main, so editing or switching
# branches in the development copy never changes what participants see.
if [[ ! -d "$base/app/.git" ]]; then
  git clone --quiet --branch main "$repo_url" "$base/app"
fi
if [[ ! -x "$base/venv/bin/streamlit" ]]; then
  "$python" -m venv "$base/venv"
  "$base/venv/bin/pip" install --quiet -r "$base/app/requirements.txt"
fi
install -m 600 "$source_root/.streamlit/secrets.toml" "$base/app/.streamlit/secrets.toml"

install -m 0644 "$base/app/deploy/xai-study@.service" "$base/app/deploy/xai-study-tunnel.service" "$units/"
loginctl enable-linger "$USER" >/dev/null 2>&1 || true
systemctl --user daemon-reload
for slug in $(awk '!/^#/ {print $1}' "$base/app/deploy/apps.tsv"); do
  systemctl --user enable --now "xai-study@$slug.service"
done

if [[ -s "$config/tunnel.token" ]]; then
  systemctl --user enable --now xai-study-tunnel.service
  echo "Apps and tunnel are running."
else
  echo "Apps are running locally. Save the tunnel token to $config/tunnel.token (chmod 600), then run:"
  echo "  systemctl --user enable --now xai-study-tunnel.service"
fi
