"""Append-only Study 1 event storage and resumable session snapshots."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .cases import PROJECT_ROOT, material_manifest


DEFAULT_DATA_ROOT = PROJECT_ROOT / "study_CHI" / "data" / "raw" / "study1"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def pseudonymize_linkage(linkage_id: str, secret: str) -> str:
    if not linkage_id.strip() or not secret:
        raise ValueError("Linkage identifier and secret are required.")
    return hmac.new(
        secret.encode("utf-8"), linkage_id.strip().encode("utf-8"), hashlib.sha256
    ).hexdigest()


def stable_session_id(linkage_hash: str) -> str:
    return f"s1_{linkage_hash[:24]}"


def current_git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


class SessionStore:
    def __init__(self, root: Path | str = DEFAULT_DATA_ROOT) -> None:
        self.root = Path(root)
        self.sessions = self.root / "sessions"
        self.events = self.root / "events"
        self.sessions.mkdir(parents=True, exist_ok=True)
        self.events.mkdir(parents=True, exist_ok=True)

    def load(self, session_id: str) -> dict[str, Any] | None:
        path = self.sessions / f"{session_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, state: dict[str, Any]) -> None:
        path = self.sessions / f"{state['session_id']}.json"
        temporary = path.with_suffix(f".{uuid4().hex}.tmp")
        temporary.write_text(
            json.dumps(state, indent=2, ensure_ascii=True, sort_keys=True),
            encoding="utf-8",
        )
        os.replace(temporary, path)

    def append_event(
        self,
        state: dict[str, Any],
        event_type: str,
        *,
        phase: str,
        trial_reference: str | None = None,
        trial_position: int | None = None,
        component: str | None = None,
        elapsed_seconds: float | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state["event_sequence"] = int(state.get("event_sequence", 0)) + 1
        sequence = state["event_sequence"]
        event = {
            "schema_version": "study1-event-v1",
            "event_id": f"{state['session_id']}:{sequence:06d}",
            "event_sequence": sequence,
            "server_timestamp_utc": now_utc(),
            "application": "study1_validation",
            "application_version": "study1-app-v1",
            "git_commit": current_git_commit(),
            "material_manifest": material_manifest(),
            "session_id": state["session_id"],
            "linkage_hash": state["linkage_hash"],
            "study": "study1",
            "phase": phase,
            "trial_reference": trial_reference,
            "trial_position": trial_position,
            "profile_order": state["profile_order"],
            "component": component,
            "elapsed_seconds": elapsed_seconds,
            "event_type": event_type,
            "payload_version": "v1",
            "payload": payload or {},
            "write_status": "written",
        }
        path = self.events / f"{state['session_id']}.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=True, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.save(state)
        return event
