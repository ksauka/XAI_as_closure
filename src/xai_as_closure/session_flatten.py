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

ANALYSIS_SCHEMA_VERSION = "study2-analysis-v2"


def score_reliance(unaided: str, aided: str, ai: str, truth: str) -> dict[str, Any]:
    """Score initial disagreement; None means outside the estimand or missing.

    Missing/invalid decisions are never scored as errors. Directional outcomes
    use their own opportunity denominators rather than all six trials.
    """
    valid = {"Advance", "Reject"}
    initial_valid = unaided in valid and ai in valid and truth in valid
    final_valid = aided in valid and truth in valid
    diagnostic = unaided != ai if initial_valid else None
    direction = None
    if diagnostic:
        direction = "self" if unaided == truth else "ai"
    outcome = aided == truth if diagnostic and final_valid else None
    return {
        "analysis_schema_version": ANALYSIS_SCHEMA_VERSION,
        "diagnostic_disagreement": diagnostic,
        "reliance_direction": direction,
        "appropriate_reliance": outcome,
        "correct_self_reliance": outcome if direction == "self" else None,
        "correct_ai_reliance": outcome if direction == "ai" else None,
        "overreliance": (not outcome)
        if direction == "self" and outcome is not None
        else None,
        "underreliance": (not outcome)
        if direction == "ai" and outcome is not None
        else None,
    }


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
                "analysis_schema_version": ANALYSIS_SCHEMA_VERSION,
                "session_id": state.get("session_id", ""),
                "participant_id": state.get("participant_id", ""),
                "prolific_pid": state.get("prolific_pid", ""),
                "condition_id": condition,
                "explanation_present": condition.startswith("P1_"),
                "anthropomorphic": "_A1_" in condition,
                "forcing": condition.endswith("_F1"),
                "schema_version": state.get("schema_version", ""),
                "delivery_spec_version": state.get("delivery_spec_version", ""),
                "case_set_id": state.get("case_set_id", ""),
                "profile_order": json.dumps(state.get("profile_order", [])),
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


def _document_trace_metrics(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarise timed visits, without interpreting elapsed time as attention.

    Only matched visit IDs with a valid duration contribute to a document's
    elapsed total. An incomplete visit makes that total missing, not zero.
    Transitions count successive different document opens within each phase
    group; returning to the assessment between them is allowed.
    """
    documents = ("cv", "role", "policy")
    ordered = list(events)
    if ordered and all(isinstance(e.get("event_sequence"), int) for e in ordered):
        ordered.sort(key=lambda e: e["event_sequence"])
    result: dict[str, Any] = {}
    for group in ("all", "before_advice", "after_advice"):
        prefix = "" if group == "all" else f"{group}_"
        selected = [
            event for event in ordered
            if group == "all"
            or (group == "before_advice" and event.get("phase") in {"unaided", "forcing"})
            or (group == "after_advice" and event.get("phase") == "aided")
        ]
        opens = [
            event for event in selected
            if event.get("event_type") == "document_opened"
            and isinstance(event.get("payload"), dict)
            and event["payload"].get("document") in documents
        ]
        closes = {
            event["payload"]["document_visit_id"]: event["payload"]
            for event in selected
            if event.get("event_type") == "document_closed"
            and isinstance(event.get("payload"), dict)
            and event["payload"].get("document_visit_id")
        }
        sequence = [event["payload"]["document"] for event in opens]
        result[f"{prefix}document_transition_count"] = (
            sum(left != right for left, right in zip(sequence, sequence[1:]))
            if events else None
        )
        for document in documents:
            visits = [event["payload"] for event in opens if event["payload"]["document"] == document]
            durations = []
            incomplete = 0
            for visit in visits:
                closed = closes.get(visit.get("document_visit_id"), {})
                duration = closed.get("dwell_seconds")
                if (
                    closed.get("document") == document
                    and isinstance(duration, (int, float))
                    and not isinstance(duration, bool)
                    and 0 <= duration < float("inf")
                ):
                    durations.append(float(duration))
                else:
                    incomplete += 1
            result[f"{prefix}{document}_document_open_count"] = len(visits) if events else None
            result[f"{prefix}{document}_document_incomplete_visit_count"] = incomplete if events else None
            result[f"{prefix}{document}_document_dwell_seconds"] = (
                round(sum(durations), 3) if events and not incomplete else None
            )
    return result


def flatten_trial_rows(
    sessions: list[dict[str, Any]],
    cases: CaseRepository | None = None,
) -> list[dict[str, Any]]:
    """Return one row per candidate trial for mixed-effects analysis."""
    repository = cases or CaseRepository()
    rows: list[dict[str, Any]] = []
    for archive in sessions:
        state = _state(archive)
        events = _events(archive)
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
            valid_decisions = {"Advance", "Reject"}
            unaided_correct = (
                unaided_decision == ground_truth
                if unaided_decision in valid_decisions
                else None
            )
            aided_correct = (
                aided_decision == ground_truth
                if aided_decision in valid_decisions
                else None
            )
            aided_available = (
                aided_decision in valid_decisions and ai_verdict in valid_decisions
            )
            followed_ai = aided_decision == ai_verdict if aided_available else None
            transition = ""
            if (
                unaided_decision in valid_decisions
                and aided_decision in valid_decisions
            ):
                transition = (
                    f"{'correct' if unaided_correct else 'incorrect'}_to_"
                    f"{'correct' if aided_correct else 'incorrect'}"
                )
            trial_events = [
                event for event in events if event.get("trial_reference") == reference
            ]
            citation_events = [
                event
                for event in trial_events
                if event.get("event_type") == "citation_clicked"
            ]
            document_open_events = [
                event
                for event in trial_events
                if event.get("event_type") == "document_opened"
            ]
            document_close_events = [
                event
                for event in trial_events
                if event.get("event_type") == "document_closed"
            ]
            document_dwell_seconds = sum(
                float(event.get("payload", {}).get("dwell_seconds", 0) or 0)
                for event in document_close_events
                if isinstance(event.get("payload"), dict)
            )
            recommendation_events = [
                event
                for event in trial_events
                if event.get("event_type") == "agent_assessment_presented"
                and isinstance(event.get("elapsed_seconds"), (int, float))
            ]
            timed_citation_events = [
                event
                for event in citation_events
                if isinstance(event.get("elapsed_seconds"), (int, float))
            ]
            time_to_first_citation = ""
            if recommendation_events and timed_citation_events:
                time_to_first_citation = round(
                    max(
                        0.0,
                        min(
                            float(event["elapsed_seconds"])
                            for event in timed_citation_events
                        )
                        - min(
                            float(event["elapsed_seconds"])
                            for event in recommendation_events
                        ),
                    ),
                    3,
                )
            unaided_confidence = unaided.get("confidence", "")
            aided_confidence = aided.get("confidence", "")
            confidence_change: int | str = ""
            if isinstance(unaided_confidence, int) and isinstance(
                aided_confidence, int
            ):
                confidence_change = aided_confidence - unaided_confidence
            rows.append(
                {
                    "analysis_schema_version": ANALYSIS_SCHEMA_VERSION,
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
                    "ai_correct": ai_verdict == ground_truth
                    if ai_verdict in valid_decisions
                    else None,
                    "unaided_decision": unaided_decision,
                    "unaided_confidence": unaided_confidence,
                    "unaided_correct": unaided_correct,
                    "aided_decision": aided_decision,
                    "aided_confidence": aided_confidence,
                    "confidence_change": confidence_change,
                    "recommendation_dwell_seconds": aided.get(
                        "recommendation_dwell_seconds", ""
                    ),
                    "aided_correct": aided_correct,
                    **score_reliance(
                        unaided_decision, aided_decision, ai_verdict, ground_truth
                    ),
                    "followed_ai": followed_ai,
                    "appropriate_follow": aided_available
                    and (ai_verdict == ground_truth and followed_ai),
                    "appropriate_override": aided_available
                    and (ai_verdict != ground_truth and not followed_ai),
                    "inappropriate_override": aided_available
                    and (ai_verdict == ground_truth and not followed_ai),
                    "decision_transition": transition,
                    "assistant_induced_error": transition == "correct_to_incorrect",
                    "assistant_corrected_error": transition == "incorrect_to_correct",
                    "unaided_to_aided_reversal": (
                        unaided_decision in valid_decisions
                        and aided_decision in valid_decisions
                        and unaided_decision != aided_decision
                    ),
                    "forcing_requirement": forcing.get("mandatory_requirement", ""),
                    "forcing_correct": forcing.get("is_correct", ""),
                    "forcing_attempt_count": forcing.get("attempt_count", ""),
                    "forcing_elapsed_seconds": forcing.get("elapsed_seconds", ""),
                    "visible_source_count": (
                        len(visible_sources) if isinstance(visible_sources, list) else 0
                    ),
                    "citation_click_count": len(citation_events),
                    "time_to_first_citation_seconds": time_to_first_citation,
                    "document_open_count": len(document_open_events),
                    "document_close_count": len(document_close_events),
                    **_document_trace_metrics(trial_events),
                    "document_dwell_seconds": round(document_dwell_seconds, 3),
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
