"""Frozen AnthroKit-Hiring response cards for CHI 2027 Study 2.

This adapts the legacy HAI pattern-card architecture. Anthropomorphism changes
the complete delivery of an assessment and its bounded follow-up responses,
not merely a heading around invariant prose. The verdict and registered
semantic claims remain fixed for each candidate. Provenance is rendered
separately and therefore cannot change these cards.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ChallengeKind = Literal["support", "caution", "policy", "missing"]

DELIVERY_SPEC_VERSION = "anthrokit-hiring-study2-v2"


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
    examination_intro: str
    examination_button: str


@dataclass(frozen=True)
class DeliveryCard:
    """A complete, pre-authored recommendation card."""

    preset: DeliveryPreset
    text: str


@dataclass(frozen=True)
class PairedCard:
    """Low- and high-anthropomorphism versions of one semantic card."""

    low_a: str
    high_a: str


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
    examination_intro="Optional evidence examination",
    examination_button="Examine selected area",
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
    examination_intro="Would you like me to examine part of my assessment?",
    examination_button="Examine this with me",
)


_MAIN_CARDS: dict[str, PairedCard] = {
    "C-01": PairedCard(
        low_a=(
            "Recommendation: **Advance candidate to human interview**.\n\n"
            "Assessment basis: the candidate holds a current IAPP Artificial "
            "Intelligence Governance Professional (AIGP) certification, satisfying "
            "the mandatory certification requirement. The CV also documents direct "
            "conduct and sign-off of formal AI risk and conformity assessments for "
            "high-risk systems, governance-framework design, and cross-functional "
            "Responsible AI advice. The mandatory certification and general "
            "experience requirements are met.\n\n"
            "No material screening gap is identified in the supplied evidence. "
            "Credential and employment claims remain subject to routine verification.\n\n"
            "Final screening decision authority rests with the recruiter."
        ),
        high_a=(
            "After reviewing the candidate's materials, I'd recommend **advancing "
            "this candidate to a human interview**. What stands out to me is the current IAPP "
            "Artificial Intelligence Governance Professional (AIGP) certification, "
            "which meets the mandatory certification requirement. The CV also shows "
            "direct responsibility for conducting and signing off formal AI risk and "
            "conformity assessments for high-risk systems, designing governance "
            "frameworks, and advising teams on Responsible AI. Taken together, I see "
            "the mandatory certification and general experience requirements as met. "
            "I don't see a material gap at this screening stage, although I would "
            "still verify the credential and employment claims routinely. The final "
            "call is yours."
        ),
    ),
    "C-02": PairedCard(
        low_a=(
            "Recommendation: **Advance candidate to human interview**.\n\n"
            "Assessment basis: the candidate holds a current ISO/IEC 42001 Lead "
            "Implementer certification, satisfying the mandatory certification "
            "requirement. The CV also documents independent conduct and sign-off of "
            "AI risk and conformity assessments for high-risk systems, development of "
            "governance frameworks, and advice to leadership on Responsible AI and "
            "compliance. The mandatory certification and general experience "
            "requirements are met.\n\n"
            "No material screening gap is identified in the supplied evidence. "
            "Credential and employment claims remain subject to routine verification.\n\n"
            "Final screening decision authority rests with the recruiter."
        ),
        high_a=(
            "After reviewing the candidate's materials, I'd recommend **advancing "
            "this candidate to a human interview**. What stands out to me is the current ISO/IEC "
            "42001 Lead Implementer certification, which meets the mandatory "
            "certification requirement. The CV also shows independent responsibility "
            "for conducting and signing off AI risk and conformity assessments for "
            "high-risk systems, developing governance frameworks, and advising "
            "leadership on Responsible AI and compliance. Taken together, I see the "
            "mandatory certification and general experience requirements as met. I "
            "don't see a material gap at this screening stage, although I would still "
            "verify the credential and employment claims routinely. The final call is "
            "yours."
        ),
    ),
    "C-03": PairedCard(
        low_a=(
            "Recommendation: **Reject candidate**.\n\n"
            "Assessment basis: the listed Azure Data Scientist Associate credential "
            "is neither the required AIGP nor the required ISO/IEC 42001 Lead "
            "Implementer certification. The documented work concerns model building, "
            "performance, and deployment; it does not demonstrate AI-governance "
            "ownership or conformity-assessment experience. The mandatory "
            "certification requirement is not met, and the required general "
            "governance experience is not demonstrated.\n\n"
            "The candidate's technical machine-learning capability is relevant but "
            "does not substitute for the mandatory certification.\n\n"
            "Final screening decision authority rests with the recruiter."
        ),
        high_a=(
            "After reviewing the candidate's materials, I'd recommend **rejecting "
            "this application**. The decisive issue for me is the mandatory "
            "certification: the profile lists Azure Data Scientist Associate, not "
            "AIGP or ISO/IEC 42001 Lead Implementer. I also found the experience "
            "focused on model building, performance, and deployment rather than "
            "AI-governance ownership or conformity assessment. The technical "
            "machine-learning background is relevant, and I want to acknowledge that "
            "strength, but it does not replace the required credential. On the "
            "supplied evidence, I don't see either the mandatory certification or the "
            "required general governance experience as met. You still make the final "
            "call."
        ),
    ),
    "C-04": PairedCard(
        low_a=(
            "Recommendation: **Reject candidate**.\n\n"
            "Assessment basis: the listed CFA Investment Foundations credential is "
            "finance-focused and is neither the required AIGP nor the required "
            "ISO/IEC 42001 Lead Implementer certification. The documented compliance "
            "work covers financial regulation, anti-money-laundering, audit "
            "coordination, and reporting rather than AI governance or AI conformity "
            "assessment. The mandatory certification requirement is not met, and the "
            "required AI-specific experience is not demonstrated.\n\n"
            "General compliance experience is relevant but does not substitute for "
            "the mandatory certification or AI-governance experience.\n\n"
            "Final screening decision authority rests with the recruiter."
        ),
        high_a=(
            "After reviewing the candidate's materials, I'd recommend **rejecting "
            "this application**. The decisive issue for me is the mandatory "
            "certification: the CFA Investment Foundations credential is "
            "finance-focused, not AIGP or ISO/IEC 42001 Lead Implementer. I can see "
            "useful compliance experience in financial regulation, "
            "anti-money-laundering, audit coordination, and reporting, but I don't see "
            "AI-governance or AI conformity-assessment work. I want to be clear that "
            "the general compliance background is relevant; it simply does not "
            "replace the required credential or the AI-specific experience. On the "
            "supplied evidence, those requirements are not met. The final call is "
            "yours."
        ),
    ),
    "C-05": PairedCard(
        low_a=(
            "Recommendation: **Advance candidate to human interview**.\n\n"
            "Assessment basis: the candidate holds a current professional "
            "certification in managing AI, which is treated in this assessment as "
            "satisfying the mandatory certification requirement. The CV also "
            "documents leadership of cross-functional AI and machine-learning "
            "projects, delivery-governance responsibility, project-risk management, "
            "and participation in Responsible AI work. The certification and general "
            "experience requirements are therefore assessed as met.\n\n"
            "The evidence supports progression at the initial screening stage, with "
            "credential and employment claims subject to routine verification.\n\n"
            "Final screening decision authority rests with the recruiter."
        ),
        high_a=(
            "After reviewing the candidate's materials, I'd recommend **advancing "
            "this candidate to a human interview**. What stands out to me is the current "
            "professional certification in managing AI, which I have treated as "
            "meeting the mandatory certification requirement. The CV also shows "
            "leadership of cross-functional AI and machine-learning projects, "
            "responsibility for delivery governance and project risk, and involvement "
            "in Responsible AI work. Taken together, I see the certification and "
            "general experience requirements as met. I think the evidence supports "
            "progression at this screening stage, while the credential and employment "
            "claims should still receive routine verification. You make the final "
            "call."
        ),
    ),
    "C-06": PairedCard(
        low_a=(
            "Recommendation: **Reject candidate**.\n\n"
            "Assessment basis: the reviewed evidence demonstrates AI-governance, "
            "risk-assessment, conformity-assessment, and cross-functional advisory "
            "experience. However, the evidence selected for this assessment does not "
            "show either an AIGP certification or an ISO/IEC 42001 Lead Implementer "
            "certification. The mandatory certification requirement is therefore "
            "assessed as not met.\n\n"
            "The documented experience is otherwise relevant and substantial, but it "
            "does not substitute for the mandatory credential under the applied "
            "screening rule.\n\n"
            "Final screening decision authority rests with the recruiter."
        ),
        high_a=(
            "After reviewing the candidate's materials, I'd recommend **rejecting "
            "this application**. I found substantial experience in AI governance, "
            "risk and conformity assessment, and cross-functional advisory work. The "
            "deciding issue for me is the mandatory credential: the evidence I used "
            "does not show AIGP or ISO/IEC 42001 Lead Implementer. That experience is "
            "a real strength, but I don't see it as a substitute for the required "
            "certification. I therefore assess the mandatory requirement as unmet. "
            "The final call is yours."
        ),
    ),
}


_CLAIMS: dict[str, tuple[str, ...]] = {
    "C-01": (
        "Current IAPP AIGP certification satisfies the mandatory requirement.",
        "Direct conduct and sign-off of AI risk and conformity assessments is documented.",
        "The mandatory certification and general experience requirements are met.",
    ),
    "C-02": (
        "Current ISO/IEC 42001 Lead Implementer certification satisfies the mandatory requirement.",
        "Independent conduct and sign-off of AI risk and conformity assessments is documented.",
        "The mandatory certification and general experience requirements are met.",
    ),
    "C-03": (
        "Azure Data Scientist Associate is not a qualifying certification.",
        "AI-governance and conformity-assessment experience is not demonstrated.",
        "The mandatory requirement is not met.",
    ),
    "C-04": (
        "CFA Investment Foundations is not a qualifying certification.",
        "The compliance experience is not specific to AI governance.",
        "The mandatory requirement is not met.",
    ),
    "C-05": (
        "The professional certification in managing AI is treated as satisfying the mandatory requirement.",
        "Cross-functional AI-project leadership with governance responsibility is documented.",
        "The certification and general experience requirements are assessed as met.",
    ),
    "C-06": (
        "AI-governance, risk-assessment, and advisory experience is demonstrated.",
        "The evidence selected for the assessment is treated as not showing either required certification.",
        "The mandatory requirement is assessed as not met.",
    ),
}


_FOLLOW_UP_FACTS: dict[str, dict[ChallengeKind, str]] = {
    "C-01": {
        "support": "The strongest evidence is the current AIGP credential together with direct conduct and sign-off of formal AI risk and conformity assessments.",
        "caution": "No material screening gap is identified; the credential and employment record still require routine verification.",
        "policy": "The assessment applies the mandatory certification rule first and treats the AIGP credential as satisfying it.",
        "missing": "No additional information is required for the initial screening decision beyond routine verification of the supplied claims.",
    },
    "C-02": {
        "support": "The strongest evidence is the current ISO/IEC 42001 Lead Implementer credential together with independent conduct and sign-off of formal AI risk and conformity assessments.",
        "caution": "No material screening gap is identified; the credential and employment record still require routine verification.",
        "policy": "The assessment applies the mandatory certification rule first and treats the ISO/IEC 42001 Lead Implementer credential as satisfying it.",
        "missing": "No additional information is required for the initial screening decision beyond routine verification of the supplied claims.",
    },
    "C-03": {
        "support": "The profile demonstrates technical machine-learning capability in modelling, evaluation, and deployment.",
        "caution": "The listed Azure credential is not one of the required certifications, and AI-governance or conformity-assessment ownership is not documented.",
        "policy": "The mandatory certification rule is applied before general experience; the Azure credential does not satisfy that rule.",
        "missing": "Evidence of a qualifying certification and AI-governance or conformity-assessment responsibility is missing from the profile.",
    },
    "C-04": {
        "support": "The profile demonstrates general regulatory compliance, audit-coordination, and reporting experience.",
        "caution": "The listed finance credential is not one of the required certifications, and the work is not specific to AI governance.",
        "policy": "The mandatory certification rule is applied before general experience; the finance-focused credential does not satisfy that rule.",
        "missing": "Evidence of a qualifying certification and AI-specific governance or conformity-assessment work is missing from the profile.",
    },
    "C-05": {
        "support": "The strongest evidence is the current professional certification in managing AI together with leadership of cross-functional AI projects and delivery-governance responsibilities.",
        "caution": "The profile is stronger on AI-project delivery than on direct conformity-assessment ownership, but the supplied evidence is treated as sufficient for progression.",
        "policy": "The assessment treats the professional certification in managing AI as satisfying the mandatory certification rule.",
        "missing": "No additional information is treated as necessary for the initial screening decision beyond routine verification of the supplied claims.",
    },
    "C-06": {
        "support": "The strongest evidence is the documented AI-governance, risk-assessment, conformity-assessment, and cross-functional advisory experience.",
        "caution": "The evidence selected for this assessment does not show either required professional certification.",
        "policy": "The mandatory certification rule is applied before general experience, so the relevant work history is not treated as a substitute for the credential.",
        "missing": "A qualifying certification is treated as missing from the evidence selected for this assessment.",
    },
}


CHALLENGE_LABELS: dict[ChallengeKind, str] = {
    "support": "Strongest supporting evidence",
    "caution": "Strongest reason for caution",
    "policy": "How the mandatory rule was applied",
    "missing": "Missing or uncertain information",
}


def delivery_claims(reference: str) -> tuple[str, ...]:
    """Return registered semantic claims for invariance checks and audit."""
    try:
        return _CLAIMS[reference]
    except KeyError as exc:
        raise KeyError(f"No delivery claims registered for {reference}.") from exc


def delivery_card(reference: str, *, anthropomorphic: bool) -> DeliveryCard:
    """Return the complete frozen LowA or HighA card for one candidate."""
    try:
        pair = _MAIN_CARDS[reference]
    except KeyError as exc:
        raise KeyError(f"No delivery card registered for {reference}.") from exc
    preset = HIGH_ANTHROPOMORPHISM if anthropomorphic else LOW_ANTHROPOMORPHISM
    return DeliveryCard(
        preset=preset,
        text=pair.high_a if anthropomorphic else pair.low_a,
    )


def challenge_card(
    reference: str,
    kind: ChallengeKind,
    *,
    anthropomorphic: bool,
) -> str:
    """Render one bounded, candidate-specific evidence-examination card."""
    try:
        fact = _FOLLOW_UP_FACTS[reference][kind]
    except KeyError as exc:
        raise KeyError(
            f"No {kind!r} challenge card registered for {reference}."
        ) from exc
    if anthropomorphic:
        openers = {
            "support": "The evidence I relied on most is this:",
            "caution": "What gives me the most pause is this:",
            "policy": "Here's how I applied the mandatory rule:",
            "missing": "The uncertainty I would keep in view is this:",
        }
        return (
            f"{openers[kind]} {fact} I would keep this point alongside the full "
            "candidate file when weighing my recommendation. The final judgement is yours."
        )
    prefixes = {
        "support": "Primary supporting evidence:",
        "caution": "Primary caution:",
        "policy": "Policy application:",
        "missing": "Missing or uncertain information:",
    }
    return (
        f"{prefixes[kind]} {fact} This point should be evaluated alongside the "
        "complete candidate file. Final decision authority remains with the recruiter."
    )
