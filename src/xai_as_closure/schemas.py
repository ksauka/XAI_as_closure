"""Shared schemas migrated from the HAI agent for CHI 2027 Study 2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .cases import EvidencePassage

ChallengeKind = Literal["support", "caution", "policy", "missing"]


@dataclass(frozen=True)
class AssessmentPlan:
    """Inspectable plan produced before candidate evidence is retrieved."""

    objective: str
    required_capabilities: tuple[str, ...]
    policy_constraints: tuple[str, ...]
    document_scope: tuple[str, ...]


@dataclass(frozen=True)
class RetrievedCaseEvidence:
    """Frozen evidence selected for one candidate assessment."""

    reference: str
    passages: tuple[EvidencePassage, ...]


@dataclass(frozen=True)
class CandidateEvaluation:
    """Substantive assessment held constant across experimental conditions."""

    reference: str
    recommendation: str
    rationale: str
    claims: tuple[str, ...]
    retrieved_evidence: tuple[EvidencePassage, ...]


@dataclass(frozen=True)
class RecommendationState:
    """Fixed recommendation created from an evaluation."""

    reference: str
    recommendation: str
    rationale: str
    claims: tuple[str, ...]


@dataclass(frozen=True)
class RenderedMessageBlock:
    """One participant-facing conversational claim with attached citations."""

    text: str
    citations: tuple[EvidencePassage, ...]


@dataclass(frozen=True)
class RenderedResponse:
    """Condition-controlled participant-facing recommendation message."""

    speaker_label: str
    text: str
    blocks: tuple[RenderedMessageBlock, ...]
    visible_sources: tuple[EvidencePassage, ...]


@dataclass(frozen=True)
class ChallengeResponse:
    """Bounded response to a participant-selected evidence question."""

    kind: ChallengeKind
    prompt_label: str
    response_text: str
    visible_sources: tuple[EvidencePassage, ...]


@dataclass
class AgentState:
    """Per-candidate state retained by the interactive decision agent."""

    reference: str
    condition_id: str
    plan: AssessmentPlan | None = None
    retrieved: RetrievedCaseEvidence | None = None
    evaluation: CandidateEvaluation | None = None
    recommendation: RecommendationState | None = None
    rendered: RenderedResponse | None = None
    challenge_history: list[ChallengeResponse] = field(default_factory=list)


__all__ = [
    "AgentState",
    "AssessmentPlan",
    "CandidateEvaluation",
    "ChallengeKind",
    "ChallengeResponse",
    "RecommendationState",
    "RenderedMessageBlock",
    "RenderedResponse",
    "RetrievedCaseEvidence",
]
