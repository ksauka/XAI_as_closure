"""Recommendation renderer adapted from the HAI AnthroKit renderer."""

from __future__ import annotations

from .anthrokit_prompts import card_challenge, card_main_recommendation
from .conditions import Study2Condition
from .schemas import (
    ChallengeKind,
    ChallengeResponse,
    RecommendationState,
    RenderedResponse,
    RetrievedCaseEvidence,
)
from .study2_delivery import CHALLENGE_LABELS


class RecommendationRenderer:
    """Orchestrate cards and provenance without generating new prose."""

    def render(
        self,
        recommendation: RecommendationState,
        retrieved: RetrievedCaseEvidence,
        condition: Study2Condition,
    ) -> RenderedResponse:
        return RenderedResponse(
            speaker_label=(
                "AI screening assistant"
                if condition.anthropomorphic
                else "AI screening system"
            ),
            text=card_main_recommendation(
                recommendation.reference,
                high_a=condition.anthropomorphic,
            ),
            visible_sources=retrieved.passages if condition.provenance else (),
        )

    def render_challenge_response(
        self,
        reference: str,
        kind: ChallengeKind,
        retrieved: RetrievedCaseEvidence,
        condition: Study2Condition,
    ) -> ChallengeResponse:
        return ChallengeResponse(
            kind=kind,
            prompt_label=CHALLENGE_LABELS[kind],
            response_text=card_challenge(
                reference,
                kind,
                high_a=condition.anthropomorphic,
            ),
            visible_sources=retrieved.passages if condition.provenance else (),
        )
