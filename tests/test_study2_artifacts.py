"""Invariant tests for fixed recommendation artifacts reserved for Study 2."""

from __future__ import annotations

import json
import unittest
from dataclasses import asdict

from xai_as_closure.cases import ArtifactVariant, CaseRepository
from xai_as_closure.study2_delivery import (
    HIGH_ANTHROPOMORPHISM,
    LOW_ANTHROPOMORPHISM,
)

RENDERING_VARIANTS = (
    ArtifactVariant(False, False),
    ArtifactVariant(True, False),
    ArtifactVariant(False, True),
    ArtifactVariant(True, True),
)


class Study2ArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = CaseRepository()

    def test_all_fixed_sources_resolve(self) -> None:
        for reference in self.cases.references:
            artifact = self.cases.artifact(reference, ArtifactVariant(True, False))
            self.assertGreater(len(artifact.sources), 0)
            self.assertTrue(
                all(source.label and source.text for source in artifact.sources)
            )

    def test_artifacts_never_expose_internal_labels_or_raw_ids(self) -> None:
        for reference in self.cases.references:
            for variant in RENDERING_VARIANTS:
                serialized = json.dumps(
                    asdict(self.cases.artifact(reference, variant))
                ).lower()
                for forbidden in (
                    "ground truth",
                    "trial type",
                    "design note",
                    "case_id",
                    "supporting_ids",
                    "pol_",
                    "jd_",
                    "cv_role",
                    "cv_certifications",
                    "false advance",
                    "false reject",
                ):
                    self.assertNotIn(forbidden, serialized)

    def test_provenance_changes_mapping_not_substantive_rationale(self) -> None:
        for reference in self.cases.references:
            low = self.cases.artifact(reference, ArtifactVariant(False, False))
            high = self.cases.artifact(reference, ArtifactVariant(True, False))
            self.assertEqual(low.recommendation, high.recommendation)
            self.assertEqual(low.rationale, high.rationale)
            self.assertEqual(low.delivery, high.delivery)
            self.assertEqual(low.sources, ())
            self.assertGreater(len(high.sources), 0)

    def test_delivery_register_preserves_substantive_content(self) -> None:
        for reference in self.cases.references:
            neutral = self.cases.artifact(reference, ArtifactVariant(True, False))
            social = self.cases.artifact(reference, ArtifactVariant(True, True))
            self.assertEqual(neutral.recommendation, social.recommendation)
            self.assertEqual(neutral.rationale, social.rationale)
            self.assertEqual(neutral.sources, social.sources)
            self.assertNotEqual(neutral.delivery, social.delivery)

    def test_frozen_delivery_uses_the_validated_anthrokit_presets(self) -> None:
        self.assertEqual(LOW_ANTHROPOMORPHISM.self_reference, "none")
        self.assertEqual(HIGH_ANTHROPOMORPHISM.self_reference, "I")
        self.assertLess(LOW_ANTHROPOMORPHISM.warmth, HIGH_ANTHROPOMORPHISM.warmth)
        self.assertGreater(
            LOW_ANTHROPOMORPHISM.formality,
            HIGH_ANTHROPOMORPHISM.formality,
        )
        self.assertLess(LOW_ANTHROPOMORPHISM.empathy, HIGH_ANTHROPOMORPHISM.empathy)
        self.assertLess(LOW_ANTHROPOMORPHISM.hedging, HIGH_ANTHROPOMORPHISM.hedging)

    def test_delivery_frames_are_distinct_but_length_matched(self) -> None:
        for reference in self.cases.references:
            low = self.cases.artifact(reference, ArtifactVariant(False, False))
            high = self.cases.artifact(reference, ArtifactVariant(False, True))
            low_text = low.delivery.text
            high_text = high.delivery.text
            self.assertGreaterEqual(len(low_text.split()), 70)
            self.assertGreaterEqual(len(high_text.split()), 70)
            self.assertNotIn(" I ", f" {low_text} ")
            self.assertNotIn(" you ", f" {low_text.lower()} ")
            self.assertIn(" I'd ", f" {high_text} ")
            self.assertTrue(
                " you " in f" {high_text.lower()} " or " yours" in high_text.lower()
            )
            self.assertLessEqual(
                max(len(low_text.split()), len(high_text.split()))
                / min(len(low_text.split()), len(high_text.split())),
                1.25,
            )

    def test_no_obsolete_within_subject_rendering_assignment_remains(self) -> None:
        self.assertFalse(hasattr(self.cases, "balanced_artifact_assignments"))


if __name__ == "__main__":
    unittest.main()
