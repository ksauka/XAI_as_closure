# Hosting the participant apps through Cloudflare

Streamlit Community Cloud failed to deliver its own page files on 3 November
2026: 23–26 of 112 files timed out, so the first screen often never appeared.
Served from this machine through Cloudflare, the same app showed its first
screen in about 3 seconds with no failed files. This follows the ECTE pattern:
user services on this machine plus a dashboard-managed named tunnel.

```text
https://study1.aitheoryelaboration.org      -> 127.0.0.1:8601  apps/study1_validation_v2.py
https://study2-01.aitheoryelaboration.org   -> 127.0.0.1:8611  apps/study2_01_lowP_lowA_noF.py
...                                                            (full list: deploy/apps.tsv)
https://study2-08.aitheoryelaboration.org   -> 127.0.0.1:8618  apps/study2_08_highP_highA_F.py
```

## Layout

| What | Where |
|---|---|
| Code the participants run (a separate checkout of `main`) | `~/.local/share/xai-as-closure/app` |
| Python environment | `~/.local/share/xai-as-closure/venv` |
| Local session copies (resume after refresh) | `~/.local/share/xai-as-closure/data` |
| Tunnel token | `~/.config/xai-as-closure/tunnel.token` (mode 600) |
| GitHub data settings | copied from this repository's `.streamlit/secrets.toml` |
| Services | `xai-study@<slug>.service` (one per app), `xai-study-tunnel.service` |

Editing files or switching branches in the development copy never changes what
participants see. Only `deploy/release.sh` does.

## One-time setup

1. In the Cloudflare dashboard: Zero Trust → Networks → Tunnels → Create a
   tunnel → Cloudflared, name it `xai-study`. Copy the token (the long string
   after `--token` in the install command) and save it:

   ```bash
   mkdir -p ~/.config/xai-as-closure && chmod 700 ~/.config/xai-as-closure
   nano ~/.config/xai-as-closure/tunnel.token && chmod 600 ~/.config/xai-as-closure/tunnel.token
   ```

2. Under the tunnel's Public Hostnames, add one hostname per row of
   `deploy/apps.tsv`: subdomain = slug, domain = `aitheoryelaboration.org`,
   service = `HTTP` → `127.0.0.1:<port>`.

3. Install and start everything:

   ```bash
   bash deploy/install.sh
   ```

## Releasing a new version

Push to `main` (see `AGENTS.md`), then run between participant batches:

```bash
bash ~/.local/share/xai-as-closure/app/deploy/release.sh
```

A restart reconnects any open tab, which resumes from the local copy.

## Checks before each batch

```bash
systemctl --user status 'xai-study@*' xai-study-tunnel --no-pager
journalctl --user -u 'xai-study@*' --since today | grep -i "storage check\|GitHub save"
```

Open each study link the way a participant would, with a clearly marked test
Prolific ID, and time the first screen.
