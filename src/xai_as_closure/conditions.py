"""Explanation × anthropomorphism × forcing Study 2 conditions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Study2Condition:
    """One fixed explanation × anthropomorphism × forcing assignment.

    The deployed ``P0``/``P1`` identifiers are retained as stable Qualtrics and
    Streamlit routing keys. Semantically they mean explanation absent/present.
    """

    condition_id: str
    explanation: bool
    anthropomorphic: bool
    forcing: bool


CONDITIONS = {
    condition.condition_id: condition
    for condition in (
        Study2Condition("P0_A0_F0", False, False, False),
        Study2Condition("P0_A0_F1", False, False, True),
        Study2Condition("P0_A1_F0", False, True, False),
        Study2Condition("P0_A1_F1", False, True, True),
        Study2Condition("P1_A0_F0", True, False, False),
        Study2Condition("P1_A0_F1", True, False, True),
        Study2Condition("P1_A1_F0", True, True, False),
        Study2Condition("P1_A1_F1", True, True, True),
    )
}


def get_study2_condition(condition_id: str) -> Study2Condition:
    try:
        return CONDITIONS[condition_id]
    except KeyError as exc:
        raise ValueError(f"Unknown Study 2 condition: {condition_id}") from exc
