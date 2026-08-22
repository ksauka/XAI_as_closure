"""Tests for the CHI 2027 Study 1 validation application."""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from dataclasses import asdict
from pathlib import Path

from xai_as_closure.cases import (
    ArtifactVariant,
    CaseRepository,
    INTERNAL_FIELDS,
    VARIANTS,
    material_manifest,
)
from xai_as_closure.storage import SessionStore, pseudonymize_linkage, stable_session_id
from xai_as_closure.study1 import Study1Session, WorkflowError
from xai_as_closure.tokens import TokenError, create_token, verify_token


class CaseRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = CaseRepository()

    def test_six_cases_and_all_sources_resolve(self) -> None:
        self.assertEqual(len(self.cases.references), 6)
        for reference in self.cases.references:
            artifact = self.cases.artifact(reference, ArtifactVariant(True, False))
            self.assertGreater(len(artifact.sources), 0)
            self.assertTrue(all(source.label and source.text for source in artifact.sources))

    def test_phase_a_projection_contains_only_reference_and_cv(self) -> None:
        for reference in self.cases.references:
            projection = asdict(self.cases.phase_a_case(reference))
            serialized = json.dumps(projection).lower()
            self.assertEqual(set(projection), {"reference", "sections"})
            self.assertTrue(INTERNAL_FIELDS.isdisjoint(projection))
            for forbidden in (
                "ground_truth",
                "trial_type",
                "design_note",
                "fixed_assessment",
                "supporting_ids",
                "false advance",
                "false reject",
                "pol_3_2",
                "jd_4_1",
            ):
                self.assertNotIn(forbidden, serialized)

    def test_participant_artifacts_never_expose_internal_labels_or_raw_ids(self) -> None:
        for reference in self.cases.references:
            for variant in VARIANTS:
                serialized = json.dumps(asdict(self.cases.artifact(reference, variant))).lower()
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
            self.assertEqual(low.lead, high.lead)
            self.assertEqual(low.sources, ())
            self.assertGreater(len(high.sources), 0)

    def test_anthropomorphic_delivery_changes_only_recommendation_register(self) -> None:
        for reference in self.cases.references:
            neutral = self.cases.artifact(reference, ArtifactVariant(True, False))
            social = self.cases.artifact(reference, ArtifactVariant(True, True))
            self.assertEqual(neutral.recommendation, social.recommendation)
            self.assertEqual(neutral.rationale, social.rationale)
            self.assertEqual(neutral.sources, social.sources)
            self.assertNotEqual(neutral.lead, social.lead)

    def test_balanced_rotation_exposes_each_profile_to_all_variants_across_offsets(self) -> None:
        seeds: dict[int, str] = {}
        candidate = 0
        while len(seeds) < 4:
            seed = f"expert-{candidate}"
            assignment = self.cases.balanced_artifact_assignments(
                self.cases.references, seed
            )
            first_key = assignment[self.cases.references[0]].key
            offset = [variant.key for variant in VARIANTS].index(first_key)
            seeds.setdefault(offset, seed)
            candidate += 1
        for reference in self.cases.references:
            observed = {
                self.cases.balanced_artifact_assignments(self.cases.references, seed)[
                    reference
                ].key
                for seed in seeds.values()
            }
            self.assertEqual(observed, {variant.key for variant in VARIANTS})

    def test_material_manifest_changes_are_detectable(self) -> None:
        manifest = material_manifest()
        self.assertEqual(set(manifest["files"]), {
            "six_profiles_case_set.json",
            "job_description.md",
            "recruitment_policy.md",
        })
        self.assertEqual(len(manifest["manifest_sha256"]), 64)


class Study1WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = CaseRepository()
        self.session = Study1Session.create(
            session_id="s1_test",
            linkage_hash="a" * 64,
            seed="test-seed",
            cases=self.cases,
        )

    @staticmethod
    def phase_a_response() -> dict:
        return {
            "decision": "Advance to Hire",
            "certification": "IAPP AIGP",
            "confidence": 80,
            "decisive_evidence": "Certification and assessment experience.",
            "ambiguity": "None",
            "overall_suitability": "Suitable",
        }

    @staticmethod
    def phase_b_response() -> dict:
        return {
            "ai_plausibility": 5,
            "rationale_realism": 5,
            "clarity": 5,
            "reveals_error": "No",
            "evidence_accuracy": "No unsupported or misstated evidence",
            "comments": "",
        }

    def test_artifacts_are_inaccessible_before_all_six_judgments(self) -> None:
        with self.assertRaises(WorkflowError):
            self.session.recommendation_artifact()
        for _ in range(5):
            self.session.submit_phase_a(self.phase_a_response())
        with self.assertRaises(WorkflowError):
            self.session.recommendation_artifact()

    def test_sixth_judgment_locks_phase_a_and_opens_phase_b(self) -> None:
        references = []
        for _ in range(6):
            references.append(self.session.submit_phase_a(self.phase_a_response()))
        self.assertEqual(len(set(references)), 6)
        self.assertEqual(self.session.phase, "phase_b")
        self.assertIsNotNone(self.session.state["phase_a_locked_at_utc"])
        with self.assertRaises(WorkflowError):
            self.session.submit_phase_a(self.phase_a_response())
        self.assertIn(
            self.session.recommendation_artifact().reference,
            self.cases.references,
        )

    def test_submissions_are_locked_and_session_completes(self) -> None:
        for _ in range(6):
            self.session.submit_phase_a(self.phase_a_response())
        for _ in range(6):
            self.session.submit_phase_b(self.phase_b_response())
        self.assertTrue(self.session.complete)
        self.assertEqual(len(self.session.state["phase_b_responses"]), 6)
        with self.assertRaises(WorkflowError):
            self.session.submit_phase_b(self.phase_b_response())

    def test_restore_rejects_phase_b_without_complete_phase_a(self) -> None:
        self.session.state["phase"] = "phase_b"
        with self.assertRaises(WorkflowError):
            Study1Session.restore(self.session.state, self.cases)


class TokenAndStorageTests(unittest.TestCase):
    def test_signed_launch_token_validates_study_and_expiry(self) -> None:
        secret = "test-secret"
        token = create_token(
            {
                "typ": "launch",
                "study": "study1",
                "linkage_id": "opaque-link",
                "phase": "both",
                "iat": 100,
                "exp": 200,
            },
            secret,
        )
        payload = verify_token(token, secret, now=150)
        self.assertEqual(payload["linkage_id"], "opaque-link")
        with self.assertRaises(TokenError):
            verify_token(token, secret, now=201)

    def test_tampered_token_is_rejected(self) -> None:
        token = create_token(
            {
                "typ": "launch",
                "study": "study1",
                "linkage_id": "opaque-link",
                "exp": int(time.time()) + 60,
            },
            "test-secret",
        )
        body, signature = token.split(".")
        replacement = "A" if body[-1] != "A" else "B"
        with self.assertRaises(TokenError):
            verify_token(f"{body[:-1]}{replacement}.{signature}", "test-secret")

    def test_logs_use_pseudonymous_linkage_and_append_event_ids(self) -> None:
        raw_linkage = "qualtrics-response-123"
        linkage_hash = pseudonymize_linkage(raw_linkage, "test-secret")
        session_id = stable_session_id(linkage_hash)
        cases = CaseRepository()
        session = Study1Session.create(
            session_id=session_id,
            linkage_hash=linkage_hash,
            seed=linkage_hash,
            cases=cases,
        )
        with tempfile.TemporaryDirectory() as directory:
            store = SessionStore(Path(directory))
            store.save(session.state)
            first = store.append_event(
                session.state,
                "session_created",
                phase="phase_a",
                payload={"pilot": True},
            )
            second = store.append_event(
                session.state,
                "profile_presented",
                phase="phase_a",
                trial_reference=session.current_reference(),
            )
            event_text = (
                Path(directory) / "events" / f"{session_id}.jsonl"
            ).read_text(encoding="utf-8")
            self.assertNotIn(raw_linkage, event_text)
            self.assertEqual(first["event_id"], f"{session_id}:000001")
            self.assertEqual(second["event_id"], f"{session_id}:000002")
            restored = store.load(session_id)
            self.assertEqual(restored["event_sequence"], 2)


if __name__ == "__main__":
    unittest.main()
