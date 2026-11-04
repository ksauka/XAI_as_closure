"""Upload Study 2 sessions whose private-GitHub backup did not finish while the page was open.

Participants may leave the completion page before its background save succeeds (for example,
when the hourly GitHub API quota is exhausted). Their local copies are complete; this command
uploads them with the same payload the app writes. It skips sessions still in progress, stops
at the first rate-limit refusal, and marks each uploaded session as no longer pending.

    PYTHONPATH=src python -m xai_as_closure.sync_pending [--data DIR] [--dry-run]
    PYTHONPATH=src python -m xai_as_closure.sync_pending --export-to DIR   # analysis copy, no upload
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .cases import PROJECT_ROOT
from .github_saver import RATE_LIMITED, save_to_github
from .logger import checkpoint_meta, checkpoint_path
from .storage import _atomic_write_json

IDLE_BEFORE_UPLOAD = timedelta(minutes=60)


def _settled(state: dict[str, Any], now: datetime) -> bool:
    """Complete sessions, or sessions idle long enough that no open page still saves them."""
    if state.get("phase") == "complete":
        return True
    updated = state.get("updated_at_utc")
    return bool(updated) and now - datetime.fromisoformat(updated) > IDLE_BEFORE_UPLOAD


def _events(path: Path) -> list[dict[str, Any]]:
    events = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                events.append(event)
    return events


def save_request(state: dict[str, Any], events: list[dict[str, Any]]) -> tuple[str, str, str]:
    """Same path, payload and message as EventLogger.github_save_request."""
    payload = {
        "session_id": state["session_id"],
        "participant_id": state["participant_id"],
        "prolific_pid": state["participant_id"],
        "condition_id": state["condition_id"],
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        **checkpoint_meta(state),
        "events": events,
    }
    archive_id = state.get("archive_id")
    return (
        checkpoint_path(state["session_id"], str(archive_id) if archive_id else None),
        json.dumps(payload, indent=2, ensure_ascii=True, default=str),
        f"Session: {state['participant_id']} | {state['condition_id']}",
    )


def sync_pending(data_dir: Path, repo: str, token: str, dry_run: bool = False) -> tuple[int, int, str | None]:
    """Return (uploaded, still pending, stop reason)."""
    now = datetime.now(timezone.utc)
    pending = []
    for state_path in sorted(data_dir.glob("*.state.json")):
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("archive_pending") and _settled(state, now):
            pending.append((state_path, state))
    uploaded = 0
    for state_path, state in pending:
        if dry_run:
            continue
        events = _events(state_path.with_name(state_path.name.replace(".state.json", ".jsonl")))
        success, detail = save_to_github(repo, *save_request(state, events), token)
        if not success:
            code = detail.rsplit(" ", 1)[-1].rstrip(".") if detail else ""
            if code.isdigit() and int(code) in RATE_LIMITED:
                return uploaded, len(pending) - uploaded, f"rate limited ({detail})"
            print(f"{state['session_id'][:12]}: {detail}", file=sys.stderr)
            continue
        state["archive_pending"] = False
        _atomic_write_json(state_path, state)
        uploaded += 1
    return uploaded, len(pending) - uploaded, None


def export_local(data_dir: Path, out_dir: Path) -> int:
    """Write every local session as the archive file the app uploads, without any GitHub call."""
    count = 0
    for state_path in sorted(data_dir.glob("*.state.json")):
        state = json.loads(state_path.read_text(encoding="utf-8"))
        events = _events(state_path.with_name(state_path.name.replace(".state.json", ".jsonl")))
        path, content, _message = save_request(state, events)
        target = out_dir / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=os.environ.get("STUDY2_DATA_ROOT"),
                        help="local Study 2 data folder (default: $STUDY2_DATA_ROOT)")
    parser.add_argument("--secrets", type=Path, default=PROJECT_ROOT / ".streamlit/secrets.toml")
    parser.add_argument("--dry-run", action="store_true", help="only count pending sessions")
    parser.add_argument("--export-to", type=Path, help="write local archives here for analysis; no upload")
    args = parser.parse_args()
    if not args.data:
        parser.error("set --data or STUDY2_DATA_ROOT")
    if args.export_to:
        print(f"exported {export_local(Path(args.data), args.export_to)} local sessions")
        return
    secrets = tomllib.loads(args.secrets.read_text(encoding="utf-8"))
    repo = secrets.get("GITHUB_REPO") or secrets.get("GITHUB_DATA_REPO")
    token = secrets.get("GITHUB_TOKEN") or secrets.get("GITHUB_DATA_TOKEN")
    if not repo or not token:
        sys.exit("GitHub storage is not configured in the secrets file")
    repo = str(repo).removeprefix("https://github.com/").removesuffix(".git")
    uploaded, remaining, stop = sync_pending(Path(args.data), repo, token, args.dry_run)
    print(f"{datetime.now():%Y-%m-%d %H:%M} uploaded {uploaded}, pending {remaining}"
          + (f"; stopped: {stop}" if stop else ""))


if __name__ == "__main__":
    main()
