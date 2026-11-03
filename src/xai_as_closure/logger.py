"""HAI JSONL event logger with private-GitHub session backup."""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import requests

from .cases import PROJECT_ROOT, material_manifest
from .conditions import Study2Condition
from .github_saver import save_to_github
from .storage import _append_json_line, _atomic_write_json, _private_directory

DEFAULT_LOG_DIR = (
    PROJECT_ROOT / "study_CHI" / "data" / "raw" / "study2" / "interaction_logs"
)
EVENT_SCHEMA_VERSION = "study2-event-v11"
APPLICATION_VERSION = "study2-app-v13"


class EventLogger:
    """Record the original HAI event stream for one Study 2 participant."""

    def __init__(
        self,
        condition: Study2Condition,
        participant_id: str,
        session_id: str | None = None,
        log_dir: Path | str = DEFAULT_LOG_DIR,
    ) -> None:
        self.condition = condition
        self.participant_id = participant_id.strip() or "pilot_anonymous"
        self.session_id = session_id or uuid4().hex
        if not self.session_id.isalnum():
            raise ValueError("Session IDs must contain only letters and numbers.")
        self.log_dir = Path(log_dir)
        _private_directory(self.log_dir)
        self.path = self.log_dir / f"{self.session_id}.jsonl"
        self.turn_id = 0
        self.session_meta: dict[str, Any] = {}

    def log(self, event_type: str, **fields: object) -> dict[str, object]:
        """Append one event using the working HAI JSONL record structure."""
        self.turn_id += 1
        record: dict[str, object] = {
            "schema_version": EVENT_SCHEMA_VERSION,
            "application_version": APPLICATION_VERSION,
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "prolific_pid": self.participant_id,
            "turn_id": self.turn_id,
            "event_sequence": self.turn_id,
            "event_id": f"{self.session_id}:{self.turn_id:06d}",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "condition_id": self.condition.condition_id,
            "explanation_present": self.condition.explanation,
            "anthropomorphic_cues_on": self.condition.anthropomorphic,
            "cognitive_forcing_on": self.condition.forcing,
            "material_manifest": material_manifest(),
            "event_type": event_type,
        }
        record.update(fields)
        _append_json_line(self.path, record)
        return record

    def save_state(self, state: dict[str, Any]) -> None:
        """Persist the current session state so an interruption can resume."""
        _atomic_write_json(self.log_dir / f"{self.session_id}.state.json", state)

    def read_events(self) -> list[dict[str, Any]]:
        """Return all valid events written to the local JSONL file."""
        if not self.path.exists():
            return []
        events: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                events.append(event)
        return events

    def github_payload(self) -> dict[str, Any]:
        """Build the same top-level session-plus-events payload used by HAI."""
        return {
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "prolific_pid": self.participant_id,
            "condition_id": self.condition.condition_id,
            "saved_at_utc": datetime.now(timezone.utc).isoformat(),
            **self.session_meta,
            "events": self.read_events(),
        }

    def push_to_github(
        self,
        repo: str | None = None,
        github_token: str | None = None,
        extra_meta: dict[str, Any] | None = None,
    ) -> bool:
        """Push the full session log to the configured private GitHub repository."""
        if os.getenv("STUDY2_LOCAL_PREVIEW") == "1":
            return False
        token = (
            github_token or os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_DATA_TOKEN")
        )
        resolved_repo = (
            repo or os.getenv("GITHUB_REPO") or os.getenv("GITHUB_DATA_REPO")
        )
        if not token or not resolved_repo:
            try:
                import streamlit as st
                from streamlit.errors import StreamlitSecretNotFoundError
            except ImportError:
                pass
            else:
                try:
                    token = (
                        token
                        or st.secrets.get("GITHUB_TOKEN")
                        or st.secrets.get("GITHUB_DATA_TOKEN")
                    )
                    resolved_repo = (
                        resolved_repo
                        or st.secrets.get("GITHUB_REPO")
                        or st.secrets.get("GITHUB_DATA_REPO")
                    )
                except (KeyError, TypeError, StreamlitSecretNotFoundError):
                    pass
        if not token or not resolved_repo:
            return False

        payload = self.github_payload()
        if extra_meta:
            payload.update(extra_meta)
        path = checkpoint_path(self.session_id)
        success, _error = save_to_github(
            resolved_repo,
            path,
            json.dumps(payload, indent=2, ensure_ascii=True, default=str),
            f"Session: {self.participant_id} | {self.condition.condition_id}",
            token,
        )
        return success


def load_state(
    session_id: str, log_dir: Path | str = DEFAULT_LOG_DIR
) -> dict[str, Any] | None:
    """Load a previously saved session state, if this session was interrupted."""
    path = Path(log_dir) / f"{session_id}.state.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def restored_logger(
    condition: Study2Condition,
    state: dict[str, object],
    log_dir: Path | str = DEFAULT_LOG_DIR,
) -> EventLogger:
    """Continue an HAI logger kept in Streamlit session state across reruns."""
    logger = EventLogger(
        condition,
        str(state.get("participant_id", "pilot_anonymous")),
        str(state["session_id"]) if state.get("session_id") else None,
        log_dir,
    )
    logger.turn_id = int(state.get("turn_id", 0))
    state["session_id"] = logger.session_id
    return logger


def checkpoint_path(session_id: str) -> str:
    if not session_id.isalnum():
        raise ValueError("Invalid checkpoint session identifier")
    return f"sessions/xai_as_closure/study2/checkpoints/{session_id}.json"


def load_remote_checkpoint(
    session_id: str,
    participant_id: str,
    condition_id: str,
    repo: str,
    token: str,
    log_dir: Path | str,
) -> dict[str, Any] | None:
    """Restore the durable state and complete event history after host storage loss.

    A network or validation failure never starts a replacement participant session.
    """
    if os.getenv("STUDY2_LOCAL_PREVIEW") == "1":
        return None
    try:
        response = requests.get(
            f"https://api.github.com/repos/{repo}/contents/{checkpoint_path(session_id)}",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=15,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        envelope = response.json()
        payload = json.loads(base64.b64decode(envelope["content"]).decode("utf-8"))
    except (requests.RequestException, KeyError, ValueError, TypeError) as exc:
        raise ValueError(
            "Saved task could not be recovered. Please retry or contact the researcher."
        ) from exc
    if not isinstance(payload, dict):
        raise TypeError("Saved task checkpoint is invalid.")
    if (
        payload.get("session_id") != session_id
        or payload.get("participant_id") != participant_id
        or payload.get("condition_id") != condition_id
    ):
        raise ValueError(
            "Saved task identity or condition does not match this study link."
        )
    events = payload.get("events")
    if not isinstance(events, list) or not events:
        raise ValueError("Saved task has no valid event history.")
    for sequence, event in enumerate(events, 1):
        if not isinstance(event, dict):
            raise TypeError("Saved task event history is invalid.")
        if (
            event.get("session_id") != session_id
            or event.get("participant_id") != participant_id
            or event.get("condition_id") != condition_id
            or event.get("event_sequence") != sequence
            or event.get("material_manifest") != material_manifest()
        ):
            raise ValueError("Saved task event history or materials are inconsistent.")
    if payload.get("turn_id") != len(events):
        raise ValueError("Saved task checkpoint and event history disagree.")
    from .cases import CaseRepository
    from .study2 import Study2Session

    state = {key: value for key, value in payload.items() if key != "events"}
    Study2Session.restore(state, CaseRepository())
    directory = Path(log_dir)
    _private_directory(directory)
    event_file = directory / f"{session_id}.jsonl"
    temporary = directory / f".{session_id}.{uuid4().hex}.tmp"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, event_file)
    _atomic_write_json(directory / f"{session_id}.state.json", state)
    return state
