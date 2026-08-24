"""Top-level agentic hiring decision agent for CHI 2027 Study 2.

This is the migrated HAI orchestrator. It retains the original lifecycle:
EvidenceStore → Planner → Retriever → Evaluator → Recommender → Renderer,
followed by bounded post-recommendation evidence examination.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .cases import CaseRepository, EvidencePassage
from .conditions import Study2Condition, get_study2_condition
from .evaluator import CandidateEvaluator
from .evidence_store import EvidenceStore, build_evidence_store
from .planner import AssessmentPlanner
from .recommender import RecommendationPolicy
from .renderer import RecommendationRenderer
from .retriever import EvidenceRetriever
from .schemas import (
    AgentState,
    AssessmentPlan,
    CandidateEvaluation,
    ChallengeKind,
    ChallengeResponse,
)
from .study2_delivery import DELIVERY_SPEC_VERSION, DeliveryPreset, delivery_card

AgentPlan = AssessmentPlan
AgentEvaluation = CandidateEvaluation


@dataclass(frozen=True)
class AgentOutput:
    reference: str
    condition_id: str
    recommendation: str
    rationale: str
    claims: tuple[str, ...]
    text: str
    speaker_label: str
    delivery_preset: DeliveryPreset
    visible_sources: tuple[EvidencePassage, ...]
    plan: AssessmentPlan
    evaluation: CandidateEvaluation

    def participant_payload(self) -> dict[str, Any]:
        return {
            "reference": self.reference,
            "condition_id": self.condition_id,
            "recommendation": self.recommendation,
            "rationale": self.rationale,
            "text": self.text,
            "speaker_label": self.speaker_label,
            "visible_sources": [asdict(source) for source in self.visible_sources],
            "challenge_history": [],
        }

    def audit_payload(self) -> dict[str, Any]:
        payload = self.participant_payload()
        payload["semantic_claims"] = list(self.claims)
        payload["agent_plan"] = asdict(self.plan)
        payload["agent_evaluation"] = {
            "reference": self.evaluation.reference,
            "recommendation": self.evaluation.recommendation,
            "rationale": self.evaluation.rationale,
            "claims": list(self.evaluation.claims),
            "retrieved_evidence_labels": [
                source.label for source in self.evaluation.retrieved_evidence
            ],
        }
        payload["delivery_spec_version"] = DELIVERY_SPEC_VERSION
        payload["delivery_preset"] = asdict(self.delivery_preset)
        payload["pipeline"] = [
            "evidence_store",
            "plan",
            "retrieve",
            "evaluate",
            "recommend",
            "render",
        ]
        return payload


class AgenticHiringDecisionAgent:
    """Stateful, bounded agent operating on the six frozen profiles."""

    def __init__(
        self,
        *,
        condition: Study2Condition | str,
        cases: CaseRepository | None = None,
    ) -> None:
        self.condition = (
            get_study2_condition(condition) if isinstance(condition, str) else condition
        )
        self.cases = cases or CaseRepository()
        self._planner = AssessmentPlanner()
        self._evaluator = CandidateEvaluator(self.cases)
        self._policy = RecommendationPolicy()
        self._renderer = RecommendationRenderer()
        self._states: dict[str, AgentState] = {}
        self.assessment_history: list[AgentOutput] = []

    def start_assessment(self, reference: str) -> AgentState:
        """Initialise candidate state and the candidate-scoped evidence store."""
        plan = self._planner.create_initial_plan(reference)
        state = AgentState(
            reference=reference,
            condition_id=self.condition.condition_id,
            plan=plan,
        )
        self._states[reference] = state
        return state

    def generate_recommendation(self, state: AgentState) -> AgentState:
        """Run the complete migrated HAI lifecycle for one candidate."""
        if state.plan is None:
            state.plan = self._planner.create_initial_plan(state.reference)
        store: EvidenceStore = build_evidence_store(state.reference, self.cases)
        retriever = EvidenceRetriever(store)
        retrieved = retriever.retrieve_for_plan(state.plan)
        evaluation = self._evaluator.evaluate(state.plan, retrieved)
        recommendation = self._policy.recommend(evaluation)
        rendered = self._renderer.render(recommendation, retrieved, self.condition)
        state.retrieved = retrieved
        state.evaluation = evaluation
        state.recommendation = recommendation
        state.rendered = rendered
        return state

    def handle_stage2_challenge(
        self,
        state: AgentState,
        kind: ChallengeKind,
    ) -> ChallengeResponse:
        """Examine a bounded evidence question without changing the verdict."""
        if kind not in {"support", "caution", "policy", "missing"}:
            raise ValueError("Unsupported evidence-examination request.")
        if state.retrieved is None or state.recommendation is None:
            self.generate_recommendation(state)
        if state.retrieved is None:
            raise RuntimeError("Evidence retrieval did not complete.")
        response = self._renderer.render_challenge_response(
            state.reference,
            kind,
            state.retrieved,
            self.condition,
        )
        state.challenge_history.append(response)
        return response

    def assess(self, reference: str) -> AgentOutput:
        state = self.start_assessment(reference)
        self.generate_recommendation(state)
        if (
            state.plan is None
            or state.evaluation is None
            or state.recommendation is None
            or state.rendered is None
        ):
            raise RuntimeError("The agent pipeline did not produce a complete output.")
        preset = delivery_card(
            reference,
            anthropomorphic=self.condition.anthropomorphic,
        ).preset
        output = AgentOutput(
            reference=reference,
            condition_id=self.condition.condition_id,
            recommendation=state.recommendation.recommendation,
            rationale=state.recommendation.rationale,
            claims=state.recommendation.claims,
            text=state.rendered.text,
            speaker_label=state.rendered.speaker_label,
            delivery_preset=preset,
            visible_sources=state.rendered.visible_sources,
            plan=state.plan,
            evaluation=state.evaluation,
        )
        self.assessment_history.append(output)
        return output

    def examine(self, reference: str, kind: ChallengeKind) -> ChallengeResponse:
        state = self._states.get(reference)
        if state is None:
            state = self.start_assessment(reference)
            self.generate_recommendation(state)
        return self.handle_stage2_challenge(state, kind)

    @staticmethod
    def create_plan(reference: str) -> AssessmentPlan:
        return AssessmentPlanner().create_initial_plan(reference)

    def retrieve_and_evaluate(self, reference: str) -> CandidateEvaluation:
        state = self.start_assessment(reference)
        self.generate_recommendation(state)
        if state.evaluation is None:
            raise RuntimeError("Candidate evaluation did not complete.")
        return state.evaluation


Study2DecisionAgent = AgenticHiringDecisionAgent


def create_decision_agent(
    condition: Study2Condition | str = "P0_A0_F0",
    cases: CaseRepository | None = None,
) -> AgenticHiringDecisionAgent:
    return AgenticHiringDecisionAgent(condition=condition, cases=cases)
