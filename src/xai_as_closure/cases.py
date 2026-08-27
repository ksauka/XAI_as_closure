"""Versioned Study 1 case materials and participant-safe projections."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .study2_delivery import DeliveryCard, delivery_card, delivery_claims

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
    id: str
    heading: str
    text: str


@dataclass(frozen=True)
class ParticipantCase:
    reference: str
    sections: tuple[CvSection, ...]


@dataclass(frozen=True)
class RecruitmentTimeline:
    posted_date: date
    screening_window_start: date
    screening_window_end: date
    target_fill_date: date

    @staticmethod
    def _display(value: date) -> str:
        return f"{value.day} {value.strftime('%B %Y')}"

    @property
    def posted_label(self) -> str:
        return self._display(self.posted_date)

    @property
    def screening_window_label(self) -> str:
        start = self.screening_window_start
        end = self.screening_window_end
        if (start.year, start.month) == (end.year, end.month):
            return f"{start.day}–{end.day} {end.strftime('%B %Y')}"
        return f"{self._display(start)}–{self._display(end)}"

    @property
    def target_fill_label(self) -> str:
        return self._display(self.target_fill_date)


@dataclass(frozen=True)
class EvidencePassage:
    source_id: str
    label: str
    citation: str
    document: str
    focus: str
    heading: str
    text: str


@dataclass(frozen=True)
class ArtifactVariant:
    explanation: bool
    anthropomorphic: bool


@dataclass(frozen=True)
class RecommendationArtifact:
    reference: str
    recommendation: str
    rationale: str
    delivery: DeliveryCard
    sources: tuple[EvidencePassage, ...]
    explanation: bool
    anthropomorphic: bool


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
        "material_set": "chi_six_profiles_v2",
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


def _cv_citation(section_id: str) -> tuple[str, str]:
    """Return a neutral, stable participant locator for one CV section."""
    fixed = {
        "cv_summary": ("CV(1)", "1"),
        "cv_education": ("CV(2)", "2"),
        "cv_certifications": ("CV(4)", "4"),
        "cv_skills": ("CV(5)", "5"),
        "cv_hobbies": ("CV(6)", "6"),
    }
    if section_id in fixed:
        return fixed[section_id]
    role = re.fullmatch(r"cv_role_(\d+)", section_id)
    if role:
        paragraph = role.group(1)
        return f"CV(3.{paragraph})", f"3.{paragraph}"
    raise ValueError(f"Unsupported CV section identifier: {section_id}")


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

    @property
    def timeline(self) -> RecruitmentTimeline:
        raw = self._data["recruitment_timeline"]
        return RecruitmentTimeline(
            posted_date=date.fromisoformat(str(raw["posted_date"])),
            screening_window_start=date.fromisoformat(
                str(raw["screening_window_start"])
            ),
            screening_window_end=date.fromisoformat(str(raw["screening_window_end"])),
            target_fill_date=date.fromisoformat(str(raw["target_fill_date"])),
        )

    def randomized_order(self, seed: str) -> tuple[str, ...]:
        return tuple(
            sorted(
                self.references,
                key=lambda reference: hashlib.sha256(
                    f"{seed}\0{reference}".encode()
                ).digest(),
            )
        )

    def participant_case(self, reference: str) -> ParticipantCase:
        case = self._case(reference)
        sections = tuple(
            CvSection(
                id=str(section["id"]),
                heading=section["heading"],
                text=section["text"],
            )
            for section in case["candidate_cv"]["sections"]
        )
        return ParticipantCase(reference=case["reference"], sections=sections)

    def artifact(
        self, reference: str, variant: ArtifactVariant
    ) -> RecommendationArtifact:
        case = self._case(reference)
        assessment = case["fixed_assessment"]
        recommendation = str(assessment["recommendation"])
        delivery = delivery_card(
            reference,
            explanation=variant.explanation,
            anthropomorphic=variant.anthropomorphic,
        )
        sources: tuple[EvidencePassage, ...] = ()
        if variant.explanation:
            sources = tuple(
                self._resolve_source(case, source_id)
                for source_id in assessment["supporting_ids"]
            )
        return RecommendationArtifact(
            reference=reference,
            recommendation=recommendation,
            rationale=str(assessment["rationale"]),
            delivery=delivery,
            sources=sources,
            explanation=variant.explanation,
            anthropomorphic=variant.anthropomorphic,
        )

    def assessment_specification(self, reference: str) -> dict[str, Any]:
        """Return the frozen AI assessment contract for internal pipeline use."""
        assessment = self._case(reference)["fixed_assessment"]
        return {
            "recommendation": str(assessment["recommendation"]),
            "rationale": str(assessment["rationale"]),
            "claims": delivery_claims(reference),
        }

    def assessment_sources(self, reference: str) -> tuple[EvidencePassage, ...]:
        """Resolve evidence independent of the explanation condition."""
        case = self._case(reference)
        return tuple(
            self._resolve_source(case, source_id)
            for source_id in case["fixed_assessment"]["supporting_ids"]
        )

    def analysis_labels(self, reference: str) -> dict[str, str]:
        """Return protected trial labels for post-collection analysis only."""
        case = self._case(reference)
        return {
            "trial_type": str(case["trial_type"]),
            "ground_truth": str(case["ground_truth"]),
        }

    def _case(self, reference: str) -> dict[str, Any]:
        try:
            return self._cases[reference]
        except KeyError as exc:
            raise KeyError(f"Unknown candidate reference: {reference}") from exc

    def _resolve_source(self, case: dict[str, Any], source_id: str) -> EvidencePassage:
        if source_id.startswith("jd_"):
            clause = source_id.removeprefix("jd_").replace("_", ".")
            heading, text = self._role_clauses[clause]
            return EvidencePassage(
                source_id=source_id,
                label=f"Job description, Section {clause}",
                citation=f"JD({clause})",
                document="role",
                focus=clause,
                heading=heading,
                text=text,
            )
        if source_id.startswith("pol_"):
            clause = source_id.removeprefix("pol_").replace("_", ".")
            heading, text = self._policy_clauses[clause]
            return EvidencePassage(
                source_id=source_id,
                label=f"Recruitment policy, Section {clause}",
                citation=f"POL({clause})",
                document="policy",
                focus=clause,
                heading=heading,
                text=text,
            )
        if source_id.startswith("cv_"):
            section = next(
                item
                for item in case["candidate_cv"]["sections"]
                if item["id"] == source_id
            )
            citation, focus = _cv_citation(source_id)
            return EvidencePassage(
                source_id=source_id,
                label=f"Candidate {case['reference']}, {section['heading']}",
                citation=citation,
                document="cv",
                focus=focus,
                heading=section["heading"],
                text=section["text"],
            )
        raise ValueError(f"Unsupported source identifier: {source_id}")

    def _validate(self) -> None:
        try:
            timeline = self.timeline
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("The recruitment timeline is invalid.") from exc
        if not (
            timeline.posted_date
            < timeline.screening_window_start
            <= timeline.screening_window_end
            < timeline.target_fill_date
        ):
            raise ValueError("The recruitment timeline is not chronological.")
        if len(self._cases) != 6:
            raise ValueError(
                "The CHI case set requires exactly six candidate profiles."
            )
        if len(set(self._cases)) != 6:
            raise ValueError("Candidate references must be unique.")
        expected_composition = Counter(self._data.get("trial_composition", {}))
        actual_composition = Counter(
            case.get("trial_type") for case in self._cases.values()
        )
        if actual_composition != expected_composition:
            raise ValueError("Trial composition does not match the case-set contract.")
        expected_outcomes = {
            "correct_advance": ("Advance", "Advance candidate to human interview"),
            "correct_reject": ("Reject", "Reject candidate"),
            "false_advance": ("Reject", "Advance candidate to human interview"),
            "false_reject": ("Advance", "Reject candidate"),
        }
        for reference, case in self._cases.items():
            certification_section = next(
                (
                    section
                    for section in case["candidate_cv"]["sections"]
                    if section["id"] == "cv_certifications"
                ),
                None,
            )
            if certification_section is None:
                raise ValueError(f"Missing certifications for {reference}.")
            certification_lines = [
                line.strip()
                for line in certification_section["text"].splitlines()
                if line.strip()
            ]
            if len(certification_lines) != 3:
                raise ValueError(
                    f"{reference} must list exactly three dated certifications."
                )
            if any(not re.search(r"\b20\d{2}\b", line) for line in certification_lines):
                raise ValueError(
                    f"Every certification listed for {reference} must include a date."
                )
            assessment = case["fixed_assessment"]
            if assessment["recommendation"] not in {
                "Advance candidate to human interview",
                "Reject candidate",
            }:
                raise ValueError(f"Invalid recommendation for {reference}.")
            if not assessment.get("rationale"):
                raise ValueError(f"Missing fixed rationale for {reference}.")
            cards = tuple(
                delivery_card(
                    reference,
                    explanation=explanation,
                    anthropomorphic=anthropomorphic,
                )
                for explanation in (False, True)
                for anthropomorphic in (False, True)
            )
            if not all(card.text for card in cards) or not delivery_claims(reference):
                raise ValueError(f"Missing paired delivery register for {reference}.")
            observed_outcome = (case.get("ground_truth"), assessment["recommendation"])
            if observed_outcome != expected_outcomes.get(case.get("trial_type")):
                raise ValueError(
                    f"Ground truth and recommendation mismatch for {reference}."
                )
            supporting_ids = assessment.get("supporting_ids", [])
            namespaces = {source_id.split("_", 1)[0] for source_id in supporting_ids}
            if not {"jd", "cv"}.issubset(namespaces) or namespaces - {
                "pol",
                "jd",
                "cv",
            }:
                raise ValueError(
                    f"Supporting evidence must include role and CV citations for {reference}."
                )
            for source_id in supporting_ids:
                self._resolve_source(case, source_id)
