"""Pure six-trial Study 2 workflow state."""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .cases import CaseRepository
from .conditions import Study2Condition, get_study2_condition
from .decision_agent import AgentOutput, Study2DecisionAgent
from .study2_delivery import DELIVERY_SPEC_VERSION


class Study2WorkflowError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_decision_response(response: dict[str, Any]) -> None:
    missing = [
        key for key in ("decision", "confidence") if response.get(key) in (None, "")
    ]
    if missing:
        raise Study2WorkflowError(
            f"Complete all required fields: {', '.join(missing)}."
        )
    if response["decision"] not in {
        "Advance candidate to human interview",
        "Reject candidate",
    }:
        raise Study2WorkflowError("Invalid screening decision.")
    confidence = response["confidence"]
    if (
        not isinstance(confidence, int)
        or isinstance(confidence, bool)
        or not 0 <= confidence <= 100
    ):
        raise Study2WorkflowError("Confidence must be a whole number from 0 to 100.")


_FORCING_QUALIFYING_REFERENCES = frozenset({"C-01", "C-02", "C-06"})

_FORCING_NONE_QUALIFIES_PHRASES = (
    "none",
    "no certification",
    "no qualifying",
    "not qualif",
    "does not meet",
    "doesn t meet",
    "doesnt meet",
    "not accepted",
    "not one of",
    "not the required",
    "isn t accepted",
    "isnt accepted",
    "fails to meet",
    "lacks the",
)

_FORCING_EXPIRED_PHRASES = (
    "expired",
    "not current",
    "no longer current",
    "out of date",
    "lapsed",
    "term ended",
)


def _forcing_answer_is_correct(reference: str, answer: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", answer.lower())
    names_aigp = (
        "aigp" in normalized
        or "artificial intelligence governance professional" in normalized
    )
    names_iso = "42001" in normalized and "lead implementer" in normalized
    names_qualifying_cert = names_aigp or names_iso
    if reference in _FORCING_QUALIFYING_REFERENCES:
        return names_qualifying_cert
    states_none_qualifies = any(
        phrase in normalized for phrase in _FORCING_NONE_QUALIFIES_PHRASES
    )
    if reference == "C-05" and names_aigp:
        return any(phrase in normalized for phrase in _FORCING_EXPIRED_PHRASES)
    return states_none_qualifies and not names_qualifying_cert


@dataclass
class Study2Session:
    state: dict[str, Any]
    cases: CaseRepository

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        participant_id: str,
        prolific_pid: str,
        condition: Study2Condition,
        seed: str,
        cases: CaseRepository,
    ) -> Study2Session:
        return cls(
            state={
                "schema_version": "study2-state-v8",
                "delivery_spec_version": DELIVERY_SPEC_VERSION,
                "case_set_id": cases.case_set_id,
                "session_id": session_id,
                "participant_id": participant_id,
                "prolific_pid": prolific_pid,
                "condition_id": condition.condition_id,
                "created_at_utc": _now(),
                "updated_at_utc": _now(),
                "event_sequence": 0,
                "profile_order": list(cases.randomized_order(seed)),
                "trial_index": 0,
                "introduction_step": "instructions",
                "introduction_completed_at_utc": None,
                "phase": "unaided",
                "trials": {},
                "completed_at_utc": None,
            },
            cases=cases,
        )

    @classmethod
    def restore(cls, state: dict[str, Any], cases: CaseRepository) -> Study2Session:
        restored_state = deepcopy(state)
        session = cls(state=restored_state, cases=cases)
        session._validate_state()
        return session

    @property
    def condition(self) -> Study2Condition:
        return get_study2_condition(str(self.state["condition_id"]))

    @property
    def phase(self) -> str:
        return str(self.state["phase"])

    @property
    def complete(self) -> bool:
        return self.phase == "complete"

    def current_reference(self) -> str | None:
        if self.complete:
            return None
        return str(self.state["profile_order"][self.state["trial_index"]])

    def current_trial(self) -> dict[str, Any]:
        reference = self._require_current_reference()
        return self.state["trials"].setdefault(reference, {})

    def _require_current_reference(self) -> str:
        reference = self.current_reference()
        if reference is None:
            raise Study2WorkflowError("There is no active candidate trial.")
        return reference

    def advance_introduction(self) -> str:
        """Advance the required instructions → role → policy introduction."""
        steps = {
            "instructions": "role",
            "role": "policy",
            "policy": "complete",
        }
        current = str(self.state.get("introduction_step", ""))
        try:
            next_step = steps[current]
        except KeyError as exc:
            raise Study2WorkflowError("The study introduction is unavailable.") from exc
        self.state["introduction_step"] = next_step
        if next_step == "complete":
            self.state["introduction_completed_at_utc"] = _now()
        self.state["updated_at_utc"] = _now()
        return next_step

    def submit_unaided(self, response: dict[str, Any]) -> str:
        if self.state.get("introduction_step") != "complete":
            raise Study2WorkflowError(
                "Complete the study instructions before beginning candidate screening."
            )
        if self.phase != "unaided":
            raise Study2WorkflowError("The unaided decision is unavailable.")
        _validate_decision_response(response)
        reference = self._require_current_reference()
        trial = self.current_trial()
        trial["unaided"] = {**response, "submitted_at_utc": _now()}
        if self.condition.forcing:
            trial["forcing"] = {"started_at_utc": _now()}
            self._transition("forcing")
        else:
            self._transition("agent")
        return reference

    def request_agent_assessment(self, agent: Study2DecisionAgent) -> AgentOutput:
        if self.phase != "agent":
            raise Study2WorkflowError("The AI assessment is unavailable.")
        if agent.condition != self.condition:
            raise Study2WorkflowError("The agent condition does not match the session.")
        reference = self._require_current_reference()
        output = agent.assess(reference)
        trial = self.current_trial()
        trial["agent_output"] = output.participant_payload()
        trial["agent_presented_at_utc"] = _now()
        self._transition("aided")
        return output

    def submit_forcing(self, response: dict[str, Any]) -> str:
        if self.phase != "forcing" or not self.condition.forcing:
            raise Study2WorkflowError("Cognitive forcing is unavailable.")
        reference = self._require_current_reference()
        forcing = self.current_trial().setdefault("forcing", {})
        attempt_number = int(forcing.get("attempt_count", 0)) + 1
        forcing["attempt_count"] = attempt_number
        requirement = str(response.get("mandatory_requirement", "")).strip()
        if not requirement:
            raise Study2WorkflowError(
                "Enter your answer before continuing."
            )
        is_correct = _forcing_answer_is_correct(reference, requirement)
        max_attempts = 2
        if not is_correct and attempt_number < max_attempts:
            raise Study2WorkflowError(
                "Recheck the candidate's CV against the job description's "
                "mandatory requirement before continuing."
            )
        submitted_at = _now()
        started_at = str(forcing.get("started_at_utc", submitted_at))
        try:
            elapsed = max(
                0.0,
                (
                    datetime.fromisoformat(submitted_at)
                    - datetime.fromisoformat(started_at)
                ).total_seconds(),
            )
        except ValueError:
            elapsed = 0.0
        forcing.update(
            {
                "mandatory_requirement": requirement,
                "is_correct": is_correct,
                "submitted_at_utc": submitted_at,
                "elapsed_seconds": round(elapsed, 3),
            }
        )
        self._transition("agent")
        return reference

    def submit_aided(self, response: dict[str, Any]) -> str:
        if self.phase != "aided":
            raise Study2WorkflowError("The aided decision is unavailable.")
        _validate_decision_response(response)
        reference = self._require_current_reference()
        trial = self.current_trial()
        submitted_at = _now()
        presented_at = str(trial.get("agent_presented_at_utc", submitted_at))
        try:
            recommendation_dwell_seconds = max(
                0.0,
                (
                    datetime.fromisoformat(submitted_at)
                    - datetime.fromisoformat(presented_at)
                ).total_seconds(),
            )
        except ValueError:
            recommendation_dwell_seconds = 0.0
        trial["aided"] = {
            **response,
            "submitted_at_utc": submitted_at,
            "recommendation_dwell_seconds": round(recommendation_dwell_seconds, 3),
        }
        self._transition("recall")
        return reference

    def submit_evidence_recall(self, response: str) -> str:
        if self.phase != "recall":
            raise Study2WorkflowError("The evidence-recall response is unavailable.")
        response = response.strip()
        if not response:
            raise Study2WorkflowError("Complete the evidence-recall response.")
        reference = self._require_current_reference()
        self.current_trial()["evidence_recall"] = {
            "response": response,
            "submitted_at_utc": _now(),
        }
        next_index = int(self.state["trial_index"]) + 1
        if next_index == len(self.state["profile_order"]):
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
        else:
            self.state["trial_index"] = next_index
            self.state["phase"] = "unaided"
        self.state["updated_at_utc"] = _now()
        return reference

    def _transition(self, phase: str) -> None:
        self.state["phase"] = phase
        self.state["updated_at_utc"] = _now()

    def _validate_state(self) -> None:
        if self.state.get("schema_version") != "study2-state-v8":
            raise Study2WorkflowError(
                "Stored session uses an unsupported Study 2 schema."
            )
        if self.state.get("delivery_spec_version") != DELIVERY_SPEC_VERSION:
            raise Study2WorkflowError(
                "Stored session uses an unsupported delivery specification."
            )
        if self.state.get("case_set_id") != self.cases.case_set_id:
            raise Study2WorkflowError(
                "Stored session uses a different Study 2 case set."
            )
        try:
            get_study2_condition(str(self.state.get("condition_id", "")))
        except ValueError as exc:
            raise Study2WorkflowError(
                "Stored session has an invalid condition."
            ) from exc
        references = set(self.cases.references)
        order = self.state.get("profile_order", [])
        if len(order) != len(references) or set(order) != references:
            raise Study2WorkflowError(
                "Stored profile order does not match the case set."
            )
        phase = self.state.get("phase")
        if phase not in {"unaided", "agent", "forcing", "aided", "recall", "complete"}:
            raise Study2WorkflowError("Stored session has an invalid phase.")
        introduction_step = self.state.get("introduction_step")
        if introduction_step not in {"instructions", "role", "policy", "complete"}:
            raise Study2WorkflowError(
                "Stored session has an invalid introduction state."
            )
        index = self.state.get("trial_index")
        if not isinstance(index, int) or not 0 <= index < len(order):
            raise Study2WorkflowError("Stored session has an invalid trial position.")
        trials = self.state.get("trials")
        if not isinstance(trials, dict) or not set(trials).issubset(references):
            raise Study2WorkflowError("Stored session contains an unknown trial.")
        if introduction_step != "complete" and (
            trials or self.state.get("trial_index") != 0 or phase != "unaided"
        ):
            raise Study2WorkflowError(
                "Candidate screening cannot precede the study introduction."
            )
        if introduction_step == "complete" and not self.state.get(
            "introduction_completed_at_utc"
        ):
            raise Study2WorkflowError(
                "The completed study introduction is missing its timestamp."
            )
        if phase == "forcing" and not self.condition.forcing:
            raise Study2WorkflowError(
                "Forcing cannot appear in a forcing-absent session."
            )
        current_reference = None if phase == "complete" else order[index]
        current_trial = trials.get(current_reference, {}) if current_reference else {}
        completed_references = order if phase == "complete" else order[:index]
        permitted_trials = set(completed_references)
        if current_reference:
            permitted_trials.add(current_reference)
        if not set(trials).issubset(permitted_trials):
            raise Study2WorkflowError("Stored session contains a future trial.")
        for reference in completed_references:
            trial = trials.get(reference, {})
            required = {"unaided", "agent_output", "aided", "evidence_recall"}
            if not required.issubset(trial):
                raise Study2WorkflowError(
                    f"Completed trial {reference} is missing required responses."
                )
            if (
                self.condition.forcing
                and not str(
                    trial.get("forcing", {}).get("mandatory_requirement", "")
                ).strip()
            ):
                raise Study2WorkflowError(
                    f"Completed trial {reference} is missing cognitive forcing."
                )
            if not self.condition.forcing and "forcing" in trial:
                raise Study2WorkflowError(
                    f"Forcing-absent trial {reference} contains cognitive forcing."
                )
        if (
            phase in {"forcing", "agent", "aided", "recall"}
            and "unaided" not in current_trial
        ):
            raise Study2WorkflowError(
                "The current trial is missing its unaided decision."
            )
        if self.condition.forcing and phase in {"agent", "aided", "recall"}:
            forcing = current_trial.get("forcing", {})
            if not str(forcing.get("mandatory_requirement", "")).strip():
                raise Study2WorkflowError(
                    "The current trial is missing its requirement-reencoding response."
                )
        if not self.condition.forcing and "forcing" in current_trial:
            raise Study2WorkflowError(
                "A forcing-absent trial cannot contain a forcing response."
            )
        if phase in {"aided", "recall"} and "agent_output" not in current_trial:
            raise Study2WorkflowError("The current trial is missing its AI assessment.")
        trials_with_output = [
            trial for trial in trials.values() if "agent_output" in trial
        ]
        for trial in trials_with_output:
            output = trial["agent_output"]
            if not isinstance(output, dict):
                raise Study2WorkflowError("Stored AI assessment is invalid.")
            if output.get("explanation_present") is not self.condition.explanation:
                raise Study2WorkflowError(
                    "Stored AI assessment does not match the explanation condition."
                )
            rationale = output.get("rationale")
            visible_sources = output.get("visible_sources")
            message_blocks = output.get("message_blocks")
            if not isinstance(message_blocks, list) or not message_blocks:
                raise Study2WorkflowError(
                    "Stored AI assessment is missing its conversational message."
                )
            block_citations = [
                citation
                for block in message_blocks
                if isinstance(block, dict)
                for citation in block.get("citations", [])
            ]
            if self.condition.explanation:
                if (
                    not str(rationale or "").strip()
                    or not visible_sources
                    or not block_citations
                ):
                    raise Study2WorkflowError(
                        "Explanation-present assessment is missing its evidence."
                    )
            elif rationale is not None or visible_sources or block_citations:
                raise Study2WorkflowError(
                    "Explanation-absent assessment exposes explanatory evidence."
                )
        if phase == "recall" and "aided" not in current_trial:
            raise Study2WorkflowError(
                "The current trial is missing its aided decision."
            )
        if phase == "complete":
            if set(trials) != references or not self.state.get("completed_at_utc"):
                raise Study2WorkflowError("A Study 2 session cannot complete early.")
            if any("evidence_recall" not in trial for trial in trials.values()):
                raise Study2WorkflowError(
                    "A completed trial is missing evidence recall."
                )
