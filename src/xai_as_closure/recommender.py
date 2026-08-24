"""Fixed recommendation policy adapted from the working HAI pipeline."""

from __future__ import annotations

from .schemas import CandidateEvaluation, RecommendationState


class RecommendationPolicy:
    """Preserve registered verdicts; interaction cannot rewrite a stimulus."""

    def recommend(self, evaluation: CandidateEvaluation) -> RecommendationState:
        if evaluation.recommendation not in {
            "Advance candidate to human interview",
            "Reject candidate",
        }:
            raise ValueError("Unsupported Study 2 recommendation.")
        return RecommendationState(
            reference=evaluation.reference,
            recommendation=evaluation.recommendation,
            rationale=evaluation.rationale,
            claims=evaluation.claims,
        )
