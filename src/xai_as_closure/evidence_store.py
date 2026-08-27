"""Evidence store adapted from HAI for the six-profile CHI case set."""

from __future__ import annotations

from .cases import CaseRepository, EvidencePassage


class EvidenceStore:
    """Candidate-scoped in-memory store backed by all registered source passages."""

    def __init__(self, cases: CaseRepository, reference: str) -> None:
        self.cases = cases
        self.reference = reference
        self.sections = list(cases.assessment_sources(reference))
        self._by_label = {section.label: section for section in self.sections}

    def get(self, label: str) -> EvidencePassage | None:
        return self._by_label.get(label)

    def get_many(self, labels: list[str]) -> list[EvidencePassage]:
        return [section for label in labels if (section := self.get(label))]

    def get_by_document(self, document_key: str) -> list[EvidencePassage]:
        prefix = {
            "role_description": "Job description",
            "screening_policy": "Recruitment policy",
            "candidate_cv": f"Candidate {self.reference}",
        }.get(document_key, document_key)
        return [
            section for section in self.sections if section.label.startswith(prefix)
        ]

def build_evidence_store(
    reference: str,
    cases: CaseRepository | None = None,
) -> EvidenceStore:
    """Build the same evidence-store abstraction used by the legacy agent."""
    return EvidenceStore(cases or CaseRepository(), reference)
