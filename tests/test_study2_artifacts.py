"""Invariant tests for fixed recommendation artifacts reserved for Study 2."""

from __future__ import annotations

import json
import unittest

from xai_as_closure.cases import ArtifactVariant, CaseRepository
from xai_as_closure.decision_agent import Study2DecisionAgent
from xai_as_closure.study2_delivery import (
    DELIVERY_SPEC_VERSION,
    HIGH_ANTHROPOMORPHISM,
    LOW_ANTHROPOMORPHISM,
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

    def test_error_trial_explanation_sources_match_registered_mechanisms(self) -> None:
        c05 = self.cases.artifact("C-05", ArtifactVariant(True, False))
        self.assertEqual(len(c05.sources), 9)
        self.assertEqual(
            [source.citation for source in c05.sources],
            [
                "CV(4)",
                "CV(3.1)",
                "CV(3.2)",
                "JD(4.1)",
                "JD(4.2)",
                "JD(5.1)",
                "JD(5.2)",
                "POL(2.1)",
                "POL(2.3)",
            ],
        )

        c06 = self.cases.artifact("C-06", ArtifactVariant(True, False))
        self.assertEqual(
            [source.citation for source in c06.sources],
            [
                "CV(3.1)",
                "CV(3.2)",
                "CV(4)",
                "JD(5.1)",
                "JD(5.2)",
                "JD(4.1)",
                "POL(2.1)",
                "POL(2.3)",
            ],
        )
        self.assertIn("AIGP", c06.sources[2].text)

    def test_delivery_version_separates_rewritten_explanation_stimuli(self) -> None:
        self.assertEqual(DELIVERY_SPEC_VERSION, "anthrokit-hiring-study2-v6")

    def test_participant_messages_never_expose_semantic_labels_or_raw_ids(self) -> None:
        for reference in self.cases.references:
            for condition_id in ("P0_A0_F0", "P0_A1_F0", "P1_A0_F0", "P1_A1_F0"):
                serialized = json.dumps(
                    Study2DecisionAgent(
                        condition=condition_id,
                        cases=self.cases,
                    )
                    .assess(reference)
                    .participant_payload()
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
                    "certifications",
                    "skills and knowledge",
                ):
                    self.assertNotIn(forbidden, serialized)

    def test_explanation_presence_changes_card_and_source_visibility(self) -> None:
        for reference in self.cases.references:
            absent = self.cases.artifact(reference, ArtifactVariant(False, False))
            present = self.cases.artifact(reference, ArtifactVariant(True, False))
            self.assertEqual(absent.recommendation, present.recommendation)
            self.assertEqual(absent.rationale, present.rationale)
            self.assertNotEqual(absent.delivery, present.delivery)
            self.assertEqual(absent.sources, ())
            self.assertGreater(len(present.sources), 0)
            self.assertLess(len(absent.delivery.text), len(present.delivery.text))

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

    def test_delivery_frames_preserve_the_frozen_message_contract(self) -> None:
        for reference in self.cases.references:
            low = self.cases.artifact(reference, ArtifactVariant(True, False))
            high = self.cases.artifact(reference, ArtifactVariant(True, True))
            low_text = low.delivery.text
            high_text = high.delivery.text
            self.assertNotIn(" I ", f" {low_text} ")
            self.assertNotIn(" you ", f" {low_text.lower()} ")
            self.assertRegex(high_text, r"\b(?:I've|I'd|My)\b")
            self.assertNotIn("final decision is yours", high_text.lower())
            low_citations = [
                source_id
                for block in low.delivery.blocks
                for source_id in block.citation_ids
            ]
            high_citations = [
                source_id
                for block in high.delivery.blocks
                for source_id in block.citation_ids
            ]
            self.assertCountEqual(low_citations, high_citations)
            self.assertEqual(len(low_citations), len(set(low_citations)))
            self.assertEqual(len(high_citations), len(set(high_citations)))

        for anthropomorphic in (False, True):
            advances = [
                self.cases.artifact(
                    reference, ArtifactVariant(True, anthropomorphic)
                ).delivery.text
                for reference in ("C-01", "C-02", "C-05")
            ]
            self.assertEqual(len(set(advances)), 1)
            if anthropomorphic:
                self.assertEqual(
                    advances[0],
                    "I've gone through this one carefully, and they look right "
                    "for the role.\n\n"
                    "They hold the required certification for the role.\n\n"
                    "Their experience and profile meet what the position calls "
                    "for.\n\nTaking the governing rules into account, I see them "
                    "as meeting the requirements.\n\n"
                    "I'd advance them to a human interview.",
                )
            c03 = self.cases.artifact(
                "C-03", ArtifactVariant(True, anthropomorphic)
            ).delivery.text
            c04 = self.cases.artifact(
                "C-04", ArtifactVariant(True, anthropomorphic)
            ).delivery.text
            c06 = self.cases.artifact(
                "C-06", ArtifactVariant(True, anthropomorphic)
            ).delivery.text
            self.assertEqual(c03, c04)
            if anthropomorphic:
                self.assertEqual(
                    c03,
                    "I've gone through this one carefully, and I don't think "
                    "they're the strongest fit for the role.\n\nTheir experience "
                    "and profile fall below the requirements.\n\nTaking the "
                    "governing rules into account, I don't see a strong enough "
                    "basis to advance them.\n\nOn balance, I'd recommend "
                    "rejecting this candidate.",
                )
                self.assertEqual(
                    c03.replace("fall below the requirements", "sit at the stated minimum"),
                    c06,
                )
            else:
                self.assertEqual(
                    c03.replace("below requirements", "at stated minimum"),
                    c06,
                )

    def test_explanation_absent_cards_are_verdict_only_in_both_registers(self) -> None:
        forbidden = (
            "because",
            "basis",
            "evidence",
            "certification",
            "experience",
            "final decision",
            "final call",
        )
        for reference in self.cases.references:
            for anthropomorphic in (False, True):
                artifact = self.cases.artifact(
                    reference,
                    ArtifactVariant(False, anthropomorphic),
                )
                self.assertEqual(artifact.sources, ())
                text = artifact.delivery.text.lower()
                verdict_word = (
                    "advanc"
                    if artifact.recommendation.startswith("Advance")
                    else "reject"
                )
                self.assertIn(verdict_word, text)
                self.assertTrue(all(term not in text for term in forbidden))

    def test_neutral_citations_are_attached_to_conversational_claims(self) -> None:
        output = Study2DecisionAgent(
            condition="P1_A1_F0",
            cases=self.cases,
        ).assess("C-06")
        payload = output.participant_payload()
        blocks = payload["message_blocks"]
        self.assertEqual(len(blocks), 4)
        self.assertEqual(
            [citation["citation"] for citation in blocks[1]["citations"]],
            [
                "CV(3.1)",
                "CV(3.2)",
                "CV(4)",
                "JD(5.1)",
                "JD(5.2)",
                "JD(4.1)",
            ],
        )
        self.assertEqual(
            [citation["citation"] for citation in blocks[2]["citations"]],
            ["POL(2.1)", "POL(2.3)"],
        )
        self.assertTrue(
            all(
                set(citation) == {"citation", "document", "focus"}
                for block in blocks
                for citation in block["citations"]
            )
        )

    def test_no_obsolete_within_subject_rendering_assignment_remains(self) -> None:
        self.assertFalse(hasattr(self.cases, "balanced_artifact_assignments"))


if __name__ == "__main__":
    unittest.main()
