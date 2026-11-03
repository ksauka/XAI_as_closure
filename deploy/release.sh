#!/usr/bin/env bash
# Release what is on GitHub main to the participant apps. Run between batches:
# restarting reconnects open tabs, which then resume from the local copy.
set -euo pipefail

base="$HOME/.local/share/xai-as-closure"
git -C "$base/app" pull --quiet --ff-only origin main
"$base/venv/bin/pip" install --quiet -r "$base/app/requirements.txt"
install -m 0644 "$base/app/deploy/xai-study@.service" "$base/app/deploy/xai-study-tunnel.service" "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user restart 'xai-study@*.service'
echo "Released $(git -C "$base/app" log --oneline -1)"
