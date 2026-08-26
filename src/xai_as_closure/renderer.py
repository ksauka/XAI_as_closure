"""Recommendation renderer adapted from the HAI AnthroKit renderer."""

from __future__ import annotations

from .anthrokit_prompts import card_challenge
from .conditions import Study2Condition
from .schemas import (
    ChallengeKind,
    ChallengeResponse,
    RecommendationState,
    RenderedMessageBlock,
    RenderedResponse,
    RetrievedCaseEvidence,
)
from .study2_delivery import CHALLENGE_LABELS, delivery_card


class RecommendationRenderer:
    """Render explanation-present or verdict-only cards without generation."""

    def render(
        self,
        recommendation: RecommendationState,
        retrieved: RetrievedCaseEvidence,
        condition: Study2Condition,
    ) -> RenderedResponse:
        card = delivery_card(
            recommendation.reference,
            explanation=condition.explanation,
            anthropomorphic=condition.anthropomorphic,
        )
        sources_by_id = {source.source_id: source for source in retrieved.passages}
        blocks = tuple(
            RenderedMessageBlock(
                text=block.text,
                citations=tuple(
                    sources_by_id[source_id] for source_id in block.citation_ids
                ),
            )
            for block in card.blocks
        )
        return RenderedResponse(
            speaker_label=(
                "AI screening assistant"
                if condition.anthropomorphic
                else "AI screening system"
            ),
            text=card.text,
            blocks=blocks,
            visible_sources=retrieved.passages if condition.explanation else (),
        )

    def render_challenge_response(
        self,
        reference: str,
        kind: ChallengeKind,
        retrieved: RetrievedCaseEvidence,
        condition: Study2Condition,
    ) -> ChallengeResponse:
        if not condition.explanation:
            raise ValueError(
                "Evidence examination is unavailable when explanation is absent."
            )
        return ChallengeResponse(
            kind=kind,
            prompt_label=CHALLENGE_LABELS[kind],
            response_text=card_challenge(
                reference,
                kind,
                high_a=condition.anthropomorphic,
            ),
            visible_sources=retrieved.passages,
        )
