"""Pure single-phase Study 1 expert-screening workflow state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .cases import CaseRepository


class WorkflowError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_judgment_response(response: dict[str, Any]) -> None:
    required = {
        "decision",
        "certification",
        "confidence",
        "decisive_evidence",
        "ambiguity",
        "realism_cues",
    }
    missing = sorted(
        key
        for key in required
        if response.get(key) is None
        or (isinstance(response.get(key), str) and not response[key].strip())
    )
    if missing:
        raise WorkflowError(f"Complete all required fields: {', '.join(missing)}.")
    if response["decision"] not in {
        "Advance candidate to human interview",
        "Reject candidate",
    }:
        raise WorkflowError("Invalid independent decision.")
    confidence = response["confidence"]
    if (
        not isinstance(confidence, int)
        or isinstance(confidence, bool)
        or not 0 <= confidence <= 100
    ):
        raise WorkflowError("Confidence must be a whole number from 0 to 100.")


@dataclass
class Study1Session:
    state: dict[str, Any]
    cases: CaseRepository

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        linkage_hash: str,
        seed: str,
        cases: CaseRepository,
    ) -> Study1Session:
        order = cases.randomized_order(seed)
        return cls(
            state={
                "schema_version": "study1-state-v3",
                "case_set_id": cases.case_set_id,
                "session_id": session_id,
                "linkage_hash": linkage_hash,
                "created_at_utc": _now(),
                "updated_at_utc": _now(),
                "event_sequence": 0,
                "phase": "screening",
                "profile_order": list(order),
                "responses": {},
                "completed_at_utc": None,
            },
            cases=cases,
        )

    @classmethod
    def restore(cls, state: dict[str, Any], cases: CaseRepository) -> Study1Session:
        session = cls(state=state, cases=cases)
        session._validate_state()
        return session

    @property
    def phase(self) -> str:
        return str(self.state["phase"])

    @property
    def complete(self) -> bool:
        return self.phase == "complete"

    def current_reference(self) -> str | None:
        if self.phase != "screening":
            return None
        return next(
            (
                reference
                for reference in self.state["profile_order"]
                if reference not in self.state["responses"]
            ),
            None,
        )

    def current_case(self):
        if self.phase != "screening":
            raise WorkflowError("All candidate judgments are already locked.")
        reference = self.current_reference()
        if reference is None:
            raise WorkflowError("No candidate remains.")
        return self.cases.participant_case(reference)

    def submit_judgment(self, response: dict[str, Any]) -> str:
        if self.phase != "screening":
            raise WorkflowError("All candidate judgments are locked.")
        reference = self.current_reference()
        if reference is None:
            raise WorkflowError("No candidate remains.")
        _validate_judgment_response(response)
        self.state["responses"][reference] = {
            **response,
            "submitted_at_utc": _now(),
        }
        if len(self.state["responses"]) == len(self.state["profile_order"]):
            self.state["phase"] = "complete"
            completed_at = _now()
            self.state["completed_at_utc"] = completed_at
            started_at = str(self.state["created_at_utc"])
            self.state["total_duration_seconds"] = round(
                (
                    datetime.fromisoformat(completed_at)
                    - datetime.fromisoformat(started_at)
                ).total_seconds(),
                3,
            )
        self.state["updated_at_utc"] = _now()
        return reference

    def _validate_state(self) -> None:
        if self.state.get("schema_version") != "study1-state-v3":
            raise WorkflowError("Stored session uses an unsupported Study 1 schema.")
        if self.state.get("case_set_id") != self.cases.case_set_id:
            raise WorkflowError("Stored session uses a different Study 1 case set.")
        references = set(self.cases.references)
        order = self.state.get("profile_order", [])
        if len(order) != len(references) or set(order) != references:
            raise WorkflowError(
                "Stored profile order does not match the current case set."
            )
        responses = self.state.get("responses", {})
        if not isinstance(responses, dict) or not set(responses).issubset(references):
            raise WorkflowError("Stored responses contain an unknown candidate.")
        for reference, response in responses.items():
            if not isinstance(response, dict):
                raise WorkflowError(f"Stored response for {reference} is invalid.")
            _validate_judgment_response(response)
            if not str(response.get("submitted_at_utc", "")).strip():
                raise WorkflowError(
                    f"Stored response for {reference} has no submission time."
                )
        if self.phase not in {"screening", "complete"}:
            raise WorkflowError("Stored session has an invalid phase.")
        if self.phase == "screening" and len(responses) >= len(references):
            raise WorkflowError("A complete response set cannot remain in screening.")
        if self.phase == "complete" and set(responses) != references:
            raise WorkflowError("A session cannot complete before all six judgments.")
        if self.phase == "complete" and not self.state.get("completed_at_utc"):
            raise WorkflowError("A completed session must include a completion time.")
