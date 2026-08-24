"""Evidence retriever adapted from the working HAI pipeline."""

from __future__ import annotations

from .evidence_store import EvidenceStore
from .schemas import AssessmentPlan, RetrievedCaseEvidence


class EvidenceRetriever:
    def __init__(self, evidence_store: EvidenceStore) -> None:
        self.store = evidence_store

    def retrieve_for_plan(self, plan: AssessmentPlan) -> RetrievedCaseEvidence:
        if self.store.reference not in plan.objective:
            raise ValueError("Assessment plan does not match the evidence store.")
        return RetrievedCaseEvidence(
            reference=self.store.reference,
            passages=tuple(self.store.sections),
        )

    def retrieve_for_challenge(self, challenge: str) -> tuple:
        return tuple(self.store.search(challenge, top_k=5))
