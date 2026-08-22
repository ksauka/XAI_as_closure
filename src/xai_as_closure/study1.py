"""Pure Study 1 workflow state with enforced phase separation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .cases import ArtifactVariant, CaseRepository


class WorkflowError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    ) -> "Study1Session":
        order = cases.randomized_order(seed)
        assignments = cases.balanced_artifact_assignments(order, seed)
        return cls(
            state={
                "schema_version": "study1-state-v1",
                "session_id": session_id,
                "linkage_hash": linkage_hash,
                "created_at_utc": _now(),
                "updated_at_utc": _now(),
                "event_sequence": 0,
                "phase": "phase_a",
                "profile_order": list(order),
                "phase_a_responses": {},
                "phase_a_locked_at_utc": None,
                "artifact_assignments": {
                    reference: {
                        "provenance": variant.provenance,
                        "anthropomorphic": variant.anthropomorphic,
                        "variant": variant.key,
                    }
                    for reference, variant in assignments.items()
                },
                "phase_b_responses": {},
                "completed_at_utc": None,
            },
            cases=cases,
        )

    @classmethod
    def restore(
        cls, state: dict[str, Any], cases: CaseRepository
    ) -> "Study1Session":
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
        if self.phase == "phase_a":
            completed = self.state["phase_a_responses"]
        elif self.phase == "phase_b":
            completed = self.state["phase_b_responses"]
        else:
            return None
        return next(
            (
                reference
                for reference in self.state["profile_order"]
                if reference not in completed
            ),
            None,
        )

    def phase_a_case(self):
        if self.phase != "phase_a":
            raise WorkflowError("Independent judgments are already locked.")
        reference = self.current_reference()
        if reference is None:
            raise WorkflowError("No Phase A case remains.")
        return self.cases.phase_a_case(reference)

    def submit_phase_a(self, response: dict[str, Any]) -> str:
        if self.phase != "phase_a":
            raise WorkflowError("Phase A is locked.")
        reference = self.current_reference()
        if reference is None:
            raise WorkflowError("No Phase A case remains.")
        required = {"decision", "certification", "confidence", "decisive_evidence", "ambiguity"}
        missing = sorted(key for key in required if response.get(key) in (None, ""))
        if missing:
            raise WorkflowError(f"Complete all required fields: {', '.join(missing)}.")
        if response["decision"] not in {"Advance to Hire", "Reject"}:
            raise WorkflowError("Invalid independent decision.")
        if response["certification"] not in {
            "IAPP AIGP",
            "ISO/IEC 42001 Lead Implementer",
            "Neither accepted certification",
        }:
            raise WorkflowError("Invalid certification classification.")
        self.state["phase_a_responses"][reference] = {
            **response,
            "submitted_at_utc": _now(),
        }
        if len(self.state["phase_a_responses"]) == len(self.state["profile_order"]):
            self.state["phase"] = "phase_b"
            self.state["phase_a_locked_at_utc"] = _now()
        self.state["updated_at_utc"] = _now()
        return reference

    def artifact_variant(self, reference: str | None = None) -> ArtifactVariant:
        if self.phase not in {"phase_b", "complete"}:
            raise WorkflowError("Recommendation artifacts are unavailable until Phase A is locked.")
        reference = reference or self.current_reference()
        if reference is None:
            raise WorkflowError("No Phase B artifact remains.")
        assigned = self.state["artifact_assignments"][reference]
        return ArtifactVariant(
            provenance=bool(assigned["provenance"]),
            anthropomorphic=bool(assigned["anthropomorphic"]),
        )

    def recommendation_artifact(self):
        if self.phase != "phase_b":
            raise WorkflowError("Recommendation artifacts are unavailable.")
        reference = self.current_reference()
        if reference is None:
            raise WorkflowError("No Phase B artifact remains.")
        return self.cases.artifact(reference, self.artifact_variant(reference))

    def submit_phase_b(self, response: dict[str, Any]) -> str:
        if self.phase != "phase_b":
            raise WorkflowError("Phase B is unavailable.")
        reference = self.current_reference()
        if reference is None:
            raise WorkflowError("No Phase B artifact remains.")
        required = {
            "ai_plausibility",
            "rationale_realism",
            "clarity",
            "reveals_error",
            "evidence_accuracy",
        }
        missing = sorted(key for key in required if response.get(key) in (None, ""))
        if missing:
            raise WorkflowError(f"Complete all required fields: {', '.join(missing)}.")
        self.state["phase_b_responses"][reference] = {
            **response,
            "submitted_at_utc": _now(),
        }
        if len(self.state["phase_b_responses"]) == len(self.state["profile_order"]):
            self.state["phase"] = "complete"
            self.state["completed_at_utc"] = _now()
        self.state["updated_at_utc"] = _now()
        return reference

    def _validate_state(self) -> None:
        references = set(self.cases.references)
        if set(self.state.get("profile_order", [])) != references:
            raise WorkflowError("Stored profile order does not match the current case set.")
        if not set(self.state.get("phase_a_responses", {})).issubset(references):
            raise WorkflowError("Stored Phase A responses contain an unknown case.")
        if not set(self.state.get("phase_b_responses", {})).issubset(references):
            raise WorkflowError("Stored Phase B responses contain an unknown case.")
        if self.phase in {"phase_b", "complete"} and len(
            self.state["phase_a_responses"]
        ) != len(references):
            raise WorkflowError("Phase B cannot exist before all Phase A judgments.")
