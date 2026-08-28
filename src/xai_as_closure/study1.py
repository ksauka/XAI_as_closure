"""Pure Study 1 expert-screening and materials-validation workflow state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .cases import CaseRepository

STUDY1_INSTRUMENT_VERSION = "study1-instrument-v4"
STUDY1_STATE_VERSION = "study1-state-v4"


class WorkflowError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_judgment_response(response: dict[str, Any]) -> None:
    required = {
        "decision",
        "hard_criterion_judgment",
        "confidence",
        "decisive_evidence",
    }
    missing = sorted(
        key
        for key in required
        if response.get(key) is None
        or (isinstance(response.get(key), str) and not response[key].strip())
    )
    if missing:
        raise WorkflowError(f"Complete all required fields: {', '.join(missing)}.")
    unexpected = sorted(set(response) - required - {"submitted_at_utc"})
    if unexpected:
        raise WorkflowError(f"Unexpected judgment fields: {', '.join(unexpected)}.")
    if response["decision"] not in {
        "Advance candidate to human interview",
        "Reject candidate",
    }:
        raise WorkflowError("Invalid independent decision.")
    if response["hard_criterion_judgment"] not in {"Yes", "No"}:
        raise WorkflowError("Invalid hard-criterion judgment.")
    confidence = response["confidence"]
    if (
        not isinstance(confidence, int)
        or isinstance(confidence, bool)
        or not 0 <= confidence <= 100
    ):
        raise WorkflowError("Confidence must be a whole number from 0 to 100.")


def _validate_post_study_response(response: dict[str, Any]) -> None:
    likert_fields = {
        "role_requirement_clarity",
        "candidate_profile_realism",
        "qualification_difference_plausibility",
        "mandatory_information_identifiability",
        "information_sufficiency",
        "task_ecological_validity",
    }
    required = likert_fields | {"professional_disagreement"}
    missing = sorted(
        key
        for key in required
        if response.get(key) is None
        or (isinstance(response.get(key), str) and not response[key].strip())
    )
    if missing:
        raise WorkflowError(f"Complete all required fields: {', '.join(missing)}.")
    allowed = required | {
        "disputed_profiles",
        "disputed_profiles_reason",
        "materials_feedback",
    }
    unexpected = sorted(set(response) - allowed)
    if unexpected:
        raise WorkflowError(f"Unexpected final-review fields: {', '.join(unexpected)}.")
    for field in likert_fields:
        value = response[field]
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 7:
            raise WorkflowError(f"{field} must be a whole number from 1 to 7.")
    disagreement = response["professional_disagreement"]
    if disagreement not in {"Yes", "No"}:
        raise WorkflowError("Invalid professional-disagreement response.")
    disputed_profiles = response.get("disputed_profiles", [])
    valid_references = {f"C-{index:02d}" for index in range(1, 7)}
    if not isinstance(disputed_profiles, list) or any(
        reference not in valid_references for reference in disputed_profiles
    ):
        raise WorkflowError("Invalid disputed-profile selection.")
    disputed_reason = str(response.get("disputed_profiles_reason", "")).strip()
    if disagreement == "Yes" and (not disputed_profiles or not disputed_reason):
        raise WorkflowError(
            "Identify the disputed candidate profile(s) and explain why."
        )
    if disagreement == "No" and (disputed_profiles or disputed_reason):
        raise WorkflowError(
            "A No disagreement response cannot include disputed candidates."
        )
    if not isinstance(response.get("materials_feedback", ""), str):
        raise WorkflowError("Materials feedback must be text.")


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
                "schema_version": STUDY1_STATE_VERSION,
                "instrument_version": STUDY1_INSTRUMENT_VERSION,
                "case_set_id": cases.case_set_id,
                "session_id": session_id,
                "linkage_hash": linkage_hash,
                "created_at_utc": _now(),
                "updated_at_utc": _now(),
                "event_sequence": 0,
                "phase": "screening",
                "profile_order": list(order),
                "responses": {},
                "post_study_response": None,
                "post_study_submitted_at_utc": None,
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
            self.state["phase"] = "post_study"
        self.state["updated_at_utc"] = _now()
        return reference

    def submit_post_study(self, response: dict[str, Any]) -> None:
        if self.phase != "post_study":
            raise WorkflowError("The final materials review is not available.")
        _validate_post_study_response(response)
        submitted_at = _now()
        self.state["post_study_response"] = dict(response)
        self.state["post_study_submitted_at_utc"] = submitted_at
        self.state["phase"] = "complete"
        self.state["completed_at_utc"] = submitted_at
        started_at = str(self.state["created_at_utc"])
        self.state["total_duration_seconds"] = round(
            (
                datetime.fromisoformat(submitted_at)
                - datetime.fromisoformat(started_at)
            ).total_seconds(),
            3,
        )
        self.state["updated_at_utc"] = _now()

    def _validate_state(self) -> None:
        if self.state.get("schema_version") != STUDY1_STATE_VERSION:
            raise WorkflowError("Stored session uses an unsupported Study 1 schema.")
        if self.state.get("instrument_version") != STUDY1_INSTRUMENT_VERSION:
            raise WorkflowError("Stored session uses a different Study 1 instrument.")
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
        if self.phase not in {"screening", "post_study", "complete"}:
            raise WorkflowError("Stored session has an invalid phase.")
        if self.phase == "screening" and len(responses) >= len(references):
            raise WorkflowError("A complete response set cannot remain in screening.")
        if self.phase in {"post_study", "complete"} and set(responses) != references:
            raise WorkflowError(
                "The final materials review requires all six candidate judgments."
            )
        post_study_response = self.state.get("post_study_response")
        if self.phase != "complete" and post_study_response is not None:
            raise WorkflowError("An unsubmitted final review cannot contain responses.")
        if self.phase != "complete" and (
            self.state.get("post_study_submitted_at_utc")
            or self.state.get("completed_at_utc")
        ):
            raise WorkflowError(
                "An incomplete session cannot include completion timestamps."
            )
        if self.phase == "complete":
            if not isinstance(post_study_response, dict):
                raise WorkflowError(
                    "A completed session must include the final review."
                )
            _validate_post_study_response(post_study_response)
            if not self.state.get("post_study_submitted_at_utc"):
                raise WorkflowError(
                    "A completed session must include review submission time."
                )
            if not self.state.get("completed_at_utc"):
                raise WorkflowError(
                    "A completed session must include a completion time."
                )
            if not isinstance(self.state.get("total_duration_seconds"), (int, float)):
                raise WorkflowError("A completed session must include total duration.")
