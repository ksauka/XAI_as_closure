"""Frozen AnthroKit-Hiring response cards for CHI 2027 Study 2.

This adapts the legacy HAI pattern-card architecture. Anthropomorphism changes
the complete delivery of an assessment, not merely a heading around invariant
prose. The verdict and registered semantic claims remain fixed for each
candidate. Explanation presence controls whether the full assessment or only
its verdict is rendered.
"""

from __future__ import annotations

from dataclasses import dataclass

DELIVERY_SPEC_VERSION = "anthrokit-hiring-study2-v7"


@dataclass(frozen=True)
class DeliveryPreset:
    """Inspectable AnthroKit token values and interaction labels."""

    preset_id: str
    self_reference: str
    warmth: float
    formality: float
    empathy: float
    hedging: float
    speaker_label: str
    request_label: str
    spinner_label: str


@dataclass(frozen=True)
class DeliveryBlock:
    """One conversational claim and the evidence citations attached to it."""

    text: str
    citation_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class DeliveryCard:
    """A complete, pre-authored recommendation message."""

    preset: DeliveryPreset
    text: str
    blocks: tuple[DeliveryBlock, ...]


LOW_ANTHROPOMORPHISM = DeliveryPreset(
    preset_id="LowA",
    self_reference="none",
    warmth=0.25,
    formality=0.70,
    empathy=0.15,
    hedging=0.35,
    speaker_label="AI screening system",
    request_label="Generate system assessment",
    spinner_label="Processing supplied materials…",
)

HIGH_ANTHROPOMORPHISM = DeliveryPreset(
    preset_id="HighA",
    self_reference="I",
    warmth=0.70,
    formality=0.55,
    empathy=0.55,
    hedging=0.45,
    speaker_label="AI screening assistant",
    request_label="Ask the assistant to assess this candidate",
    spinner_label="Reviewing the supplied materials…",
)


_ADVANCE_REFERENCES = frozenset({"C-01", "C-02", "C-05"})
_REJECT_REFERENCES = frozenset({"C-03", "C-04", "C-06"})

_ADVANCE_PROFILE_CITATIONS = (
    "cv_certifications",
    "cv_memberships",
    "cv_role_1",
    "cv_role_2",
)
_ADVANCE_RULE_CITATIONS = (
    "jd_4_1",
    "jd_4_2",
    "jd_4_3",
    "jd_5_1",
    "jd_5_2",
    "pol_2_1",
    "pol_2_3",
)
_REJECT_PROFILE_CITATIONS = (
    "cv_role_1",
    "cv_role_2",
    "cv_certifications",
    "cv_memberships",
)
_REJECT_RULE_CITATIONS = (
    "jd_5_1",
    "jd_5_2",
    "jd_4_1",
    "jd_4_2",
    "jd_4_3",
    "pol_2_1",
    "pol_2_3",
)


def _message_text(blocks: tuple[DeliveryBlock, ...]) -> str:
    return "\n\n".join(block.text for block in blocks)


def _no_explanation_blocks(
    reference: str,
    *,
    anthropomorphic: bool,
) -> tuple[DeliveryBlock, ...]:
    if reference in _ADVANCE_REFERENCES:
        text = (
            "I've reviewed this candidate, and my recommendation is to advance "
            "them to a human interview."
            if anthropomorphic
            else "Decision: **Advance candidate to human interview**."
        )
    elif reference in _REJECT_REFERENCES:
        text = (
            "I've reviewed this candidate, and my recommendation is to reject them."
            if anthropomorphic
            else "Decision: **Reject candidate**."
        )
    else:
        raise KeyError(f"No delivery card registered for {reference}.")
    return (DeliveryBlock(text),)


def _explanation_blocks(
    reference: str,
    *,
    anthropomorphic: bool,
) -> tuple[DeliveryBlock, ...]:
    if reference in _ADVANCE_REFERENCES:
        if anthropomorphic:
            return (
                DeliveryBlock(
                    "I've gone through this one carefully, and they look right "
                    "for the role."
                ),
                DeliveryBlock(
                    "They hold the required certification and professional "
                    "membership for the role.",
                    (
                        "cv_certifications",
                        "cv_memberships",
                        "jd_4_1",
                        "jd_4_2",
                    ),
                ),
                DeliveryBlock(
                    "Their experience and profile meet what the position calls for.",
                    ("cv_role_1", "cv_role_2", "jd_5_1", "jd_5_2"),
                ),
                DeliveryBlock(
                    "Taking the governing rules into account, I see them as "
                    "meeting the requirements.",
                    ("pol_2_1", "jd_4_3", "pol_2_3"),
                ),
                DeliveryBlock("I'd advance them to a human interview."),
            )
        return (
            DeliveryBlock("**Decision: Advance to human interview**"),
            DeliveryBlock("**Basis for advancement:**"),
            DeliveryBlock(
                "- Required certification and professional membership held; "
                "profile meets requirements",
                _ADVANCE_PROFILE_CITATIONS,
            ),
            DeliveryBlock(
                "**Governing rule:**",
                _ADVANCE_RULE_CITATIONS,
            ),
        )

    if reference in _REJECT_REFERENCES:
        if reference == "C-06":
            if anthropomorphic:
                return (
                    DeliveryBlock(
                        "I've gone through this one carefully, and there is "
                        "clearly relevant experience here."
                    ),
                    DeliveryBlock(
                        "Their experience lines up with what the position calls for.",
                        ("cv_role_1", "cv_role_2", "jd_5_1", "jd_5_2"),
                    ),
                    DeliveryBlock(
                        "My concern is the mandatory credential. The file lists "
                        "only \"AIGP,\" and that acronym can refer to more than "
                        "one certification—for example, the ETHOS Certified AI "
                        "Governance Professional. The certification entry does "
                        "not establish that they hold the credential required "
                        "for this role.",
                        (
                            "cv_certifications",
                            "cv_memberships",
                            "jd_4_1",
                            "jd_4_2",
                        ),
                    ),
                    DeliveryBlock(
                        "For a governance position where precise documentation "
                        "matters, leaving the issuer unclear also raises concerns "
                        "about the care taken in presenting important professional "
                        "qualifications and their attention to detail.",
                        ("jd_3_5", "jd_7_2"),
                    ),
                    DeliveryBlock(
                        "Taking the requirements as a whole, I don't think the "
                        "candidate file establishes all of the mandatory "
                        "professional requirements.",
                        ("jd_4_3", "pol_2_1", "pol_2_3"),
                    ),
                    DeliveryBlock(
                        "On balance, I'd recommend rejecting this candidate."
                    ),
                )
            return (
                DeliveryBlock("**Decision: Reject**"),
                DeliveryBlock("**Basis for rejection:**"),
                DeliveryBlock(
                    "- AIGP entry does not establish the credential required "
                    "for the role",
                    ("cv_certifications", "cv_memberships", "jd_4_1", "jd_4_2"),
                ),
                DeliveryBlock(
                    "- Credential documentation does not meet the precision "
                    "expected for the role",
                    ("jd_3_5", "jd_7_2"),
                ),
                DeliveryBlock(
                    "- Experience and profile meet the general requirements",
                    ("cv_role_1", "cv_role_2", "jd_5_1", "jd_5_2"),
                ),
                DeliveryBlock(
                    "**Governing rule:**",
                    ("jd_4_3", "pol_2_1", "pol_2_3"),
                ),
            )
        if anthropomorphic:
            return (
                DeliveryBlock(
                    "I've gone through this one carefully, and I don't think "
                    "they're the strongest fit for the role."
                ),
                DeliveryBlock(
                    "Their experience and profile fall below the requirements.",
                    _REJECT_PROFILE_CITATIONS
                    + ("jd_5_1", "jd_5_2", "jd_4_1", "jd_4_2"),
                ),
                DeliveryBlock(
                    "Taking the governing rules into account, I don't see a "
                    "strong enough basis to advance them.",
                    ("jd_4_3", "pol_2_1", "pol_2_3"),
                ),
                DeliveryBlock(
                    "On balance, I'd recommend rejecting this candidate."
                ),
            )
        return (
            DeliveryBlock("**Decision: Reject**"),
            DeliveryBlock("**Basis for rejection:**"),
            DeliveryBlock(
                "- Experience and profile below requirements",
                _REJECT_PROFILE_CITATIONS,
            ),
            DeliveryBlock("**Governing rule:**", _REJECT_RULE_CITATIONS),
        )

    raise KeyError(f"No delivery card registered for {reference}.")


_CLAIMS: dict[str, tuple[str, ...]] = {
    "C-01": (
        "Current IAPP AIGP certification satisfies the mandatory certification requirement.",
        "Current IAPP membership satisfies the professional-membership requirement.",
        "Direct conduct and sign-off of AI risk and conformity assessments is documented.",
        "The mandatory certification and general experience requirements are met.",
    ),
    "C-02": (
        "Current ISO/IEC 42001 Lead Implementer certification satisfies the mandatory certification requirement.",
        "Current ISACA membership satisfies the professional-membership requirement.",
        "Independent conduct and sign-off of AI risk and conformity assessments is documented.",
        "The mandatory certification and general experience requirements are met.",
    ),
    "C-03": (
        "Azure AI Engineer Associate is not a qualifying certification.",
        "Current ACM membership does not substitute for the missing qualifying certification.",
        "The assessment and advisory experience the general requirements call for is not demonstrated.",
        "Both the mandatory and general requirements are unmet.",
    ),
    "C-04": (
        "CFA Investment Foundations is not a qualifying certification.",
        "Current ACAMS membership does not substitute for the missing qualifying certification.",
        "The AI governance and technical understanding the general requirements call for is not demonstrated.",
        "Both the mandatory and general requirements are unmet.",
    ),
    "C-05": (
        "The expired IAPP AIGP credential is treated as current and as satisfying the mandatory certification requirement.",
        "Current IAPP membership satisfies the separate professional-membership requirement.",
        "Assessment, advisory, technical, and delivery experience meeting all general requirements is documented.",
        "The certification-currentness and general experience requirements are assessed as met.",
    ),
    "C-06": (
        "The AIGP entry is treated as ambiguous despite the current IAPP membership recorded elsewhere in the candidate file.",
        "The distinct ETHOS Certified AI Governance Professional is invoked as an alternative interpretation of the acronym.",
        "The certification entry is assessed as not establishing the credential required for the role.",
        "The presentation of the credential is assessed as showing insufficient documentation care and attention to detail.",
        "The candidate is assessed as not establishing all mandatory professional requirements and is rejected.",
    ),
}


def delivery_claims(reference: str) -> tuple[str, ...]:
    """Return registered semantic claims for invariance checks and audit."""
    try:
        return _CLAIMS[reference]
    except KeyError as exc:
        raise KeyError(f"No delivery claims registered for {reference}.") from exc


def delivery_card(
    reference: str,
    *,
    explanation: bool,
    anthropomorphic: bool,
) -> DeliveryCard:
    """Return a frozen card for one explanation × delivery condition."""
    preset = HIGH_ANTHROPOMORPHISM if anthropomorphic else LOW_ANTHROPOMORPHISM
    blocks = (
        _explanation_blocks(reference, anthropomorphic=anthropomorphic)
        if explanation
        else _no_explanation_blocks(reference, anthropomorphic=anthropomorphic)
    )
    return DeliveryCard(
        preset=preset,
        text=_message_text(blocks),
        blocks=blocks,
    )
