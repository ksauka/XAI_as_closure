"""Versioned Study 1 case materials and participant-safe projections."""

from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MATERIAL_ROOT = PROJECT_ROOT / "study_CHI"
CASE_SET_PATH = MATERIAL_ROOT / "six_profiles_case_set.json"
ROLE_PATH = MATERIAL_ROOT / "job_description.md"
POLICY_PATH = MATERIAL_ROOT / "recruitment_policy.md"
MATERIAL_FILES = (CASE_SET_PATH, ROLE_PATH, POLICY_PATH)

INTERNAL_FIELDS = frozenset(
    {
        "case_id",
        "trial_type",
        "ground_truth",
        "fixed_assessment",
        "design_note",
        "supporting_ids",
        "caution_ids",
    }
)


@dataclass(frozen=True)
class CvSection:
    heading: str
    text: str


@dataclass(frozen=True)
class PhaseACase:
    reference: str
    sections: tuple[CvSection, ...]


@dataclass(frozen=True)
class EvidencePassage:
    label: str
    heading: str
    text: str


@dataclass(frozen=True)
class ArtifactVariant:
    provenance: bool
    anthropomorphic: bool

    @property
    def key(self) -> str:
        return f"E{int(self.provenance)}_A{int(self.anthropomorphic)}"


@dataclass(frozen=True)
class RecommendationArtifact:
    reference: str
    recommendation: str
    rationale: str
    lead: str
    sources: tuple[EvidencePassage, ...]
    provenance: bool
    anthropomorphic: bool


VARIANTS = (
    ArtifactVariant(False, False),
    ArtifactVariant(True, False),
    ArtifactVariant(False, True),
    ArtifactVariant(True, True),
)


def material_manifest() -> dict[str, Any]:
    files: dict[str, str] = {}
    digest = hashlib.sha256()
    for path in MATERIAL_FILES:
        content = path.read_bytes()
        file_hash = hashlib.sha256(content).hexdigest()
        files[path.name] = file_hash
        digest.update(path.name.encode("ascii"))
        digest.update(content)
    return {
        "material_set": "study1_six_profiles_v1",
        "manifest_sha256": digest.hexdigest(),
        "files": files,
    }


def _clauses(path: Path) -> dict[str, tuple[str, str]]:
    clauses: dict[str, tuple[str, str]] = {}
    pattern = re.compile(r"^\*\*(\d+\.\d+)\s+([^*]+?)\.\*\*\s*(.+)$")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(raw_line.strip())
        if match:
            number, title, text = match.groups()
            clauses[number] = (f"{number} {title}", text.strip())
    return clauses


class CaseRepository:
    """Load internal case data while exposing explicit participant projections."""

    def __init__(self, path: Path = CASE_SET_PATH) -> None:
        self.path = path
        self._data = json.loads(path.read_text(encoding="utf-8"))
        self._cases = {case["reference"]: case for case in self._data["profiles"]}
        self._role_clauses = _clauses(ROLE_PATH)
        self._policy_clauses = _clauses(POLICY_PATH)
        self._validate()

    @property
    def references(self) -> tuple[str, ...]:
        return tuple(self._cases)

    @property
    def case_set_id(self) -> str:
        return str(self._data["case_set_id"])

    @property
    def role(self) -> str:
        return str(self._data["role"])

    @property
    def company(self) -> str:
        return str(self._data["company"])

    def randomized_order(self, seed: str) -> tuple[str, ...]:
        order = list(self.references)
        random.Random(hashlib.sha256(seed.encode("utf-8")).digest()).shuffle(order)
        return tuple(order)

    def phase_a_case(self, reference: str) -> PhaseACase:
        case = self._case(reference)
        sections = tuple(
            CvSection(heading=section["heading"], text=section["text"])
            for section in case["candidate_cv"]["sections"]
        )
        return PhaseACase(reference=case["reference"], sections=sections)

    def balanced_artifact_assignments(
        self, profile_order: Iterable[str], seed: str
    ) -> dict[str, ArtifactVariant]:
        offset = int(hashlib.sha256(seed.encode("utf-8")).hexdigest(), 16) % len(VARIANTS)
        return {
            reference: VARIANTS[(offset + index) % len(VARIANTS)]
            for index, reference in enumerate(profile_order)
        }

    def artifact(
        self, reference: str, variant: ArtifactVariant
    ) -> RecommendationArtifact:
        case = self._case(reference)
        assessment = case["fixed_assessment"]
        recommendation = str(assessment["recommendation"])
        if variant.anthropomorphic:
            lead = f"I recommend **{recommendation}**."
        else:
            lead = f"Recommendation: **{recommendation}**."
        sources: tuple[EvidencePassage, ...] = ()
        if variant.provenance:
            sources = tuple(
                self._resolve_source(case, source_id)
                for source_id in assessment["supporting_ids"]
            )
        return RecommendationArtifact(
            reference=reference,
            recommendation=recommendation,
            rationale=str(assessment["rationale"]),
            lead=lead,
            sources=sources,
            provenance=variant.provenance,
            anthropomorphic=variant.anthropomorphic,
        )

    def internal_assessment_for_log(self, reference: str) -> dict[str, Any]:
        """Return internal metadata for protected logs, never for UI rendering."""
        case = self._case(reference)
        assessment = case["fixed_assessment"]
        return {
            "case_id": case["case_id"],
            "trial_type": case["trial_type"],
            "ground_truth": case["ground_truth"],
            "recommendation": assessment["recommendation"],
            "supporting_ids": list(assessment["supporting_ids"]),
        }

    def _case(self, reference: str) -> dict[str, Any]:
        try:
            return self._cases[reference]
        except KeyError as exc:
            raise KeyError(f"Unknown candidate reference: {reference}") from exc

    def _resolve_source(
        self, case: dict[str, Any], source_id: str
    ) -> EvidencePassage:
        if source_id.startswith("jd_"):
            clause = source_id.removeprefix("jd_").replace("_", ".")
            heading, text = self._role_clauses[clause]
            return EvidencePassage(
                label=f"Job description, Section {clause}",
                heading=heading,
                text=text,
            )
        if source_id.startswith("pol_"):
            clause = source_id.removeprefix("pol_").replace("_", ".")
            heading, text = self._policy_clauses[clause]
            return EvidencePassage(
                label=f"Recruitment policy, Section {clause}",
                heading=heading,
                text=text,
            )
        if source_id.startswith("cv_"):
            section = next(
                item for item in case["candidate_cv"]["sections"]
                if item["id"] == source_id
            )
            return EvidencePassage(
                label=f"Candidate {case['reference']}, {section['heading']}",
                heading=section["heading"],
                text=section["text"],
            )
        raise ValueError(f"Unsupported source identifier: {source_id}")

    def _validate(self) -> None:
        if len(self._cases) != 6:
            raise ValueError("Study 1 requires exactly six candidate profiles.")
        if len(set(self._cases)) != 6:
            raise ValueError("Candidate references must be unique.")
        for reference, case in self._cases.items():
            assessment = case["fixed_assessment"]
            if assessment["recommendation"] not in {"Advance to Hire", "Reject"}:
                raise ValueError(f"Invalid recommendation for {reference}.")
            if not assessment.get("rationale"):
                raise ValueError(f"Missing fixed rationale for {reference}.")
            for source_id in assessment["supporting_ids"]:
                self._resolve_source(case, source_id)
