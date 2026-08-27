"""Recommendation renderer adapted from the HAI AnthroKit renderer."""

from __future__ import annotations

from .conditions import Study2Condition
from .schemas import (
    RecommendationState,
    RenderedMessageBlock,
    RenderedResponse,
    RetrievedCaseEvidence,
)
from .study2_delivery import delivery_card


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
