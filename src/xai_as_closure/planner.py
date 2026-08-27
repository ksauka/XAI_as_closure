"""Assessment planner adapted from the working HAI pipeline."""

from __future__ import annotations

from .schemas import AssessmentPlan


class AssessmentPlanner:
    """Create the fixed screening plan for one of the six profiles."""

    def create_initial_plan(self, reference: str) -> AssessmentPlan:
        return AssessmentPlan(
            objective=f"Screen candidate {reference} for the AI Governance Lead role.",
            required_capabilities=(
                "Current AIGP or ISO/IEC 42001 Lead Implementer certification on the date of screening",
                "AI governance, risk, and conformity-assessment experience",
                "Cross-functional advisory and stakeholder capability",
            ),
            policy_constraints=(
                "Apply the mandatory certification rule before general requirements.",
                "Assess certification currency against the stated screening window.",
                "Use only the supplied recruitment policy, job description, and CV.",
                "Preserve human decision authority.",
            ),
            document_scope=(
                "AI Governance Recruitment Policy",
                "AI Governance Lead job description",
                f"Candidate {reference} CV",
            ),
        )
