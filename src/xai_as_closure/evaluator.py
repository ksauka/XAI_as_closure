"""Candidate evaluator adapted from the working HAI pipeline."""

from __future__ import annotations

from .cases import CaseRepository
from .schemas import (
    AssessmentPlan,
    CandidateEvaluation,
    RetrievedCaseEvidence,
)


class CandidateEvaluator:
    """Return the pre-registered AI evaluation, including intended error trials."""

    def __init__(self, cases: CaseRepository) -> None:
        self.cases = cases

    def evaluate(
        self,
        plan: AssessmentPlan,
        retrieved: RetrievedCaseEvidence,
    ) -> CandidateEvaluation:
        if retrieved.reference not in plan.objective or not retrieved.passages:
            raise ValueError("Retrieved evidence does not match the assessment plan.")
        spec = self.cases.assessment_specification(retrieved.reference)
        return CandidateEvaluation(
            reference=retrieved.reference,
            recommendation=spec["recommendation"],
            rationale=spec["rationale"],
            claims=spec["claims"],
            retrieved_evidence=retrieved.passages,
        )
