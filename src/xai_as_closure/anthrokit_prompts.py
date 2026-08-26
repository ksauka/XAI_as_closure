"""Study 2 pattern-card API adapted from the original HAI implementation."""

from __future__ import annotations

from .study2_delivery import (
    CHALLENGE_LABELS,
    ChallengeKind,
    challenge_card,
    delivery_card,
    delivery_claims,
)


def card_main_recommendation(
    reference: str,
    *,
    explanation: bool,
    high_a: bool,
) -> str:
    """Return the frozen card for one explanation × delivery condition."""
    return delivery_card(
        reference,
        explanation=explanation,
        anthropomorphic=high_a,
    ).text


def card_challenge(reference: str, kind: ChallengeKind, *, high_a: bool) -> str:
    """Return a bounded post-recommendation examination card."""
    return challenge_card(reference, kind, anthropomorphic=high_a)


__all__ = [
    "CHALLENGE_LABELS",
    "ChallengeKind",
    "card_challenge",
    "card_main_recommendation",
    "delivery_claims",
]
