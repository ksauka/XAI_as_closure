"""Flatten Study 2 archives into analysis-ready participant, trial, and event rows.

This retains the old HAI extraction interface while supporting the current
state-plus-events GitHub archive and six within-participant candidate trials.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .cases import CaseRepository


def load_sessions(source: str | Path) -> list[dict[str, Any]]:
    """Load GitHub archives or local session snapshots from JSON/JSONL."""
    src = Path(source)
    sessions: list[dict[str, Any]] = []
    if src.is_file() and src.suffix.lower() == ".jsonl":
        for line in src.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                sessions.append(item)
        return sessions
    if src.is_dir():
        for path in sorted(src.rglob("*.json")):
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(item, dict):
                item.setdefault("_source_path", str(path.relative_to(src)))
                sessions.append(item)
        return sessions
    raise FileNotFoundError(f"Session source not found: {source}")


def _state(archive: dict[str, Any]) -> dict[str, Any]:
    state = archive.get("state", archive)
    return state if isinstance(state, dict) else {}


def _events(archive: dict[str, Any]) -> list[dict[str, Any]]:
    events = archive.get("events", [])
    return [event for event in events if isinstance(event, dict)]


def _advance_label(value: Any) -> str:
    text = str(value)
    if text == "Advance candidate to human interview":
        return "Advance"
    if text == "Reject candidate":
        return "Reject"
    return text


def flatten_participant_rows(
    sessions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return one condition and completion summary row per participant."""
    rows: list[dict[str, Any]] = []
    for archive in sessions:
        state = _state(archive)
        condition = str(state.get("condition_id", ""))
        trials = state.get("trials", {})
        trials = trials if isinstance(trials, dict) else {}
        rows.append(
            {
                "session_id": state.get("session_id", ""),
                "participant_id": state.get("participant_id", ""),
                "prolific_pid": state.get("prolific_pid", ""),
                "condition_id": condition,
                "explanation_present": condition.startswith("P1_"),
                "anthropomorphic": "_A1_" in condition,
                "forcing": condition.endswith("_F1"),
                "schema_version": state.get("schema_version", ""),
                "delivery_spec_version": state.get("delivery_spec_version", ""),
                "created_at_utc": state.get("created_at_utc", ""),
                "completed_at_utc": state.get("completed_at_utc", ""),
                "total_duration_seconds": state.get("total_duration_seconds", ""),
                "complete": state.get("phase") == "complete",
                "completed_trial_count": sum(
                    "evidence_recall" in trial
                    for trial in trials.values()
                    if isinstance(trial, dict)
                ),
                "event_count": len(_events(archive)),
                "source_path": archive.get("_source_path", ""),
            }
        )
    return rows


def flatten_trial_rows(
    sessions: list[dict[str, Any]],
    cases: CaseRepository | None = None,
) -> list[dict[str, Any]]:
    """Return one row per candidate trial for mixed-effects analysis."""
    repository = cases or CaseRepository()
    rows: list[dict[str, Any]] = []
    for archive in sessions:
        state = _state(archive)
        condition = str(state.get("condition_id", ""))
        order = state.get("profile_order", [])
        trials = state.get("trials", {})
        if not isinstance(order, list) or not isinstance(trials, dict):
            continue
        for position, reference in enumerate(order, 1):
            trial = trials.get(reference)
            if not isinstance(trial, dict):
                continue
            labels = repository.analysis_labels(str(reference))
            unaided = trial.get("unaided", {})
            aided = trial.get("aided", {})
            output = trial.get("agent_output", {})
            forcing = trial.get("forcing", {})
            recall = trial.get("evidence_recall", {})
            ground_truth = labels["ground_truth"]
            ai_verdict = _advance_label(output.get("recommendation", ""))
            unaided_decision = _advance_label(unaided.get("decision", ""))
            aided_decision = _advance_label(aided.get("decision", ""))
            visible_sources = output.get("visible_sources", [])
            challenges = output.get("challenge_history", [])
            rows.append(
                {
                    "session_id": state.get("session_id", ""),
                    "participant_id": state.get("participant_id", ""),
                    "prolific_pid": state.get("prolific_pid", ""),
                    "condition_id": condition,
                    "explanation_present": condition.startswith("P1_"),
                    "anthropomorphic": "_A1_" in condition,
                    "forcing": condition.endswith("_F1"),
                    "trial_position": position,
                    "reference": reference,
                    "trial_type": labels["trial_type"],
                    "ground_truth": ground_truth,
                    "ai_verdict": ai_verdict,
                    "ai_correct": ai_verdict == ground_truth,
                    "unaided_decision": unaided_decision,
                    "unaided_confidence": unaided.get("confidence", ""),
                    "unaided_correct": unaided_decision == ground_truth,
                    "aided_decision": aided_decision,
                    "aided_confidence": aided.get("confidence", ""),
                    "recommendation_dwell_seconds": aided.get(
                        "recommendation_dwell_seconds", ""
                    ),
                    "aided_correct": aided_decision == ground_truth,
                    "appropriate_reliance": aided_decision == ground_truth,
                    "followed_ai": aided_decision == ai_verdict,
                    "unaided_to_aided_reversal": (
                        bool(unaided_decision)
                        and bool(aided_decision)
                        and unaided_decision != aided_decision
                    ),
                    "forcing_requirement": forcing.get("mandatory_requirement", ""),
                    "forcing_elapsed_seconds": forcing.get("elapsed_seconds", ""),
                    "visible_source_count": (
                        len(visible_sources) if isinstance(visible_sources, list) else 0
                    ),
                    "challenge_count": (
                        len(challenges) if isinstance(challenges, list) else 0
                    ),
                    "evidence_recall": recall.get("response", ""),
                }
            )
    return rows


def flatten_event_rows(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return one row per append-only event, retaining its full payload."""
    rows: list[dict[str, Any]] = []
    for archive in sessions:
        state = _state(archive)
        for event in _events(archive):
            payload = event.get("payload", {})
            rows.append(
                {
                    "session_id": state.get("session_id", event.get("session_id", "")),
                    "condition_id": state.get(
                        "condition_id", event.get("condition_id", "")
                    ),
                    "event_id": event.get("event_id", ""),
                    "event_sequence": event.get(
                        "event_sequence", event.get("turn_id", "")
                    ),
                    "timestamp_utc": event.get(
                        "server_timestamp_utc", event.get("timestamp_utc", "")
                    ),
                    "event_type": event.get("event_type", ""),
                    "trial_reference": event.get("trial_reference", ""),
                    "trial_position": event.get("trial_position", ""),
                    "phase": event.get("phase", ""),
                    "component": event.get("component", ""),
                    "elapsed_seconds": event.get("elapsed_seconds", ""),
                    "payload_json": json.dumps(payload, ensure_ascii=True),
                    "raw_event_json": json.dumps(event, ensure_ascii=True),
                }
            )
    return rows


def write_csv(
    rows: Iterable[dict[str, Any]],
    output_path: str | Path,
    fieldnames: list[str],
) -> int:
    """Write flattened rows using the original HAI helper interface."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            count += 1
    return count
