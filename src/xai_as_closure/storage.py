"""Append-only Study 1 event storage and resumable session snapshots."""

from __future__ import annotations

import fcntl
import hashlib
import hmac
import json
import os
import re
from collections import deque
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .cases import PROJECT_ROOT, material_manifest

DEFAULT_DATA_ROOT = PROJECT_ROOT / "study_CHI" / "data" / "raw" / "study1"
LINKAGE_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
SESSION_ID_PATTERN = re.compile(r"^s[12]_[0-9a-f]{24}$")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def pseudonymize_linkage(linkage_id: str, secret: str) -> str:
    if not linkage_id.strip() or not secret:
        raise ValueError("Linkage identifier and secret are required.")
    return hmac.new(
        secret.encode("utf-8"), linkage_id.strip().encode("utf-8"), hashlib.sha256
    ).hexdigest()


def stable_session_id(linkage_hash: str) -> str:
    return derive_session_id(linkage_hash, "s1")


def derive_session_id(linkage_hash: str, prefix: str) -> str:
    if prefix not in {"s1", "s2"} or not LINKAGE_HASH_PATTERN.fullmatch(linkage_hash):
        raise ValueError("A valid pseudonymous linkage hash is required.")
    return f"{prefix}_{linkage_hash[:24]}"


def _validated_session_id(session_id: str, expected_prefix: str) -> str:
    if not SESSION_ID_PATTERN.fullmatch(session_id) or not session_id.startswith(
        f"{expected_prefix}_"
    ):
        raise ValueError("Invalid study session identifier.")
    return session_id


def _private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(f".{uuid4().hex}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=True, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        path.chmod(0o600)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _append_json_line(path: Path, value: dict[str, Any]) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
        os.fchmod(handle.fileno(), 0o600)
        handle.write(json.dumps(value, ensure_ascii=True, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _last_event_sequence(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        last_lines = deque((line for line in handle if line.strip()), maxlen=1)
    if not last_lines:
        return 0
    try:
        event = json.loads(last_lines[0])
        return int(event["event_sequence"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Stored event log has an invalid final record.") from exc


@contextmanager
def _session_event_lock(events: Path, session_id: str):
    lock_path = events / f".{session_id}.lock"
    descriptor = os.open(lock_path, os.O_WRONLY | os.O_CREAT, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        os.fchmod(handle.fileno(), 0o600)
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def current_git_commit() -> str:
    try:
        marker = PROJECT_ROOT / ".git"
        if marker.is_file():
            marker_text = marker.read_text(encoding="utf-8").strip()
            if not marker_text.startswith("gitdir: "):
                return "unknown"
            git_directory = (
                PROJECT_ROOT / marker_text.removeprefix("gitdir: ")
            ).resolve()
        else:
            git_directory = marker
        head = (git_directory / "HEAD").read_text(encoding="ascii").strip()
        if head.startswith("ref: "):
            ref_name = head.removeprefix("ref: ")
            ref_path = git_directory / ref_name
            if ref_path.exists():
                commit = ref_path.read_text(encoding="ascii").strip()
            else:
                packed_refs = (git_directory / "packed-refs").read_text(
                    encoding="ascii"
                )
                commit = next(
                    line.split(" ", 1)[0]
                    for line in packed_refs.splitlines()
                    if line.endswith(f" {ref_name}")
                )
        else:
            commit = head
        return commit[:12] if re.fullmatch(r"[0-9a-f]{40,64}", commit) else "unknown"
    except (OSError, StopIteration):
        return "unknown"


class SessionStore:
    def __init__(self, root: Path | str = DEFAULT_DATA_ROOT) -> None:
        self.root = Path(root)
        self.sessions = self.root / "sessions"
        self.events = self.root / "events"
        _private_directory(self.sessions)
        _private_directory(self.events)

    def load(self, session_id: str) -> dict[str, Any] | None:
        _validated_session_id(session_id, "s1")
        path = self.sessions / f"{session_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, state: dict[str, Any]) -> None:
        session_id = _validated_session_id(str(state["session_id"]), "s1")
        _atomic_write_json(self.sessions / f"{session_id}.json", state)

    def read_events(self, session_id: str) -> list[dict[str, Any]]:
        session_id = _validated_session_id(session_id, "s1")
        path = self.events / f"{session_id}.jsonl"
        if not path.exists():
            return []
        events: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                events.append(event)
        return events

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
        session_id = _validated_session_id(str(state["session_id"]), "s1")
        with _session_event_lock(self.events, session_id):
            persisted = self.load(session_id)
            persisted_sequence = int((persisted or {}).get("event_sequence", 0))
            event_path = self.events / f"{session_id}.jsonl"
            state["event_sequence"] = (
                max(
                    int(state.get("event_sequence", 0)),
                    persisted_sequence,
                    _last_event_sequence(event_path),
                )
                + 1
            )
            sequence = state["event_sequence"]
            event = {
                "schema_version": "study1-event-v2",
                "event_id": f"{state['session_id']}:{sequence:06d}",
                "event_sequence": sequence,
                "server_timestamp_utc": now_utc(),
                "application": "study1_validation",
                "application_version": "study1-app-v2",
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
            _append_json_line(event_path, event)
            self.save(state)
        return event
