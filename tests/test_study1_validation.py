"""Tests for the single-phase CHI 2027 Study 1 validation application."""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from dataclasses import asdict
from pathlib import Path

from xai_as_closure.cases import (
    CASE_SET_PATH,
    INTERNAL_FIELDS,
    CaseRepository,
    material_manifest,
)
from xai_as_closure.storage import SessionStore, pseudonymize_linkage, stable_session_id
from xai_as_closure.study1 import Study1Session, WorkflowError
from xai_as_closure.tokens import (
    TokenError,
    create_token,
    require_deployment_secret,
    safe_qualtrics_return_url,
    verify_token,
)


class CaseRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = CaseRepository()

    def test_six_participant_cases_are_available(self) -> None:
        self.assertEqual(len(self.cases.references), 6)
        for reference in self.cases.references:
            case = self.cases.participant_case(reference)
            self.assertEqual(case.reference, reference)
            self.assertGreater(len(case.sections), 0)

    def test_participant_projection_contains_only_reference_and_cv(self) -> None:
        for reference in self.cases.references:
            projection = asdict(self.cases.participant_case(reference))
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
                "recommendation",
                "rationale",
                "provenance",
            ):
                self.assertNotIn(forbidden, serialized)

    def test_material_manifest_changes_are_detectable(self) -> None:
        manifest = material_manifest()
        self.assertEqual(manifest["material_set"], "chi_six_profiles_v1")
        self.assertEqual(
            set(manifest["files"]),
            {
                "six_profiles_case_set.json",
                "job_description.md",
                "recruitment_policy.md",
            },
        )
        self.assertEqual(len(manifest["manifest_sha256"]), 64)

    def test_candidate_order_is_shuffled_per_participant_not_sequential(
        self,
    ) -> None:
        sequential = tuple(sorted(self.cases.references))
        seeds = ["participant-a", "participant-b", "participant-c", "participant-d"]
        orders = [self.cases.randomized_order(seed) for seed in seeds]
        for order in orders:
            self.assertEqual(set(order), set(self.cases.references))
            self.assertNotEqual(
                order,
                sequential,
                "profile order must not default to C-01..C-06",
            )
        self.assertGreater(
            len({orders[i] for i in range(len(orders))}),
            1,
            "different participants must not all get the same shuffled order",
        )

    def test_case_set_rejects_a_changed_trial_composition(self) -> None:
        case_set = json.loads(CASE_SET_PATH.read_text(encoding="utf-8"))
        case_set["trial_composition"]["false_reject"] = 0
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "case-set.json"
            path.write_text(json.dumps(case_set), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Trial composition"):
                CaseRepository(path)


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
    def response() -> dict:
        return {
            "decision": "Advance candidate to human interview",
            "certification": "IAPP AIGP",
            "confidence": 80,
            "decisive_evidence": "The accepted certification is present.",
            "ambiguity": "None",
            "realism_cues": "None",
        }

    def test_session_contains_no_ai_or_experimental_assignments(self) -> None:
        self.assertEqual(self.session.state["schema_version"], "study1-state-v2")
        self.assertEqual(self.session.phase, "screening")
        self.assertNotIn("phase_b_responses", self.session.state)
        self.assertNotIn("artifact_assignments", self.session.state)
        self.assertNotIn("condition", self.session.state)

    def test_each_expert_gets_all_six_profiles_in_a_stable_randomized_order(
        self,
    ) -> None:
        same_seed = Study1Session.create(
            session_id="s1_second",
            linkage_hash="b" * 64,
            seed="test-seed",
            cases=self.cases,
        )
        self.assertEqual(
            self.session.state["profile_order"], same_seed.state["profile_order"]
        )
        self.assertEqual(
            set(self.session.state["profile_order"]), set(self.cases.references)
        )

    def test_sixth_judgment_completes_session_without_an_ai_phase(self) -> None:
        references = [self.session.submit_judgment(self.response()) for _ in range(6)]
        self.assertEqual(len(set(references)), 6)
        self.assertTrue(self.session.complete)
        self.assertEqual(len(self.session.state["responses"]), 6)
        self.assertIsNotNone(self.session.state["completed_at_utc"])
        with self.assertRaises(WorkflowError):
            self.session.submit_judgment(self.response())

    def test_realism_and_unintended_cues_response_is_required(self) -> None:
        response = self.response()
        response["realism_cues"] = ""
        with self.assertRaisesRegex(WorkflowError, "realism_cues"):
            self.session.submit_judgment(response)

    def test_whitespace_only_open_responses_are_rejected(self) -> None:
        response = self.response()
        response["decisive_evidence"] = "   "
        with self.assertRaisesRegex(WorkflowError, "decisive_evidence"):
            self.session.submit_judgment(response)

    def test_confidence_must_be_an_integer_percentage(self) -> None:
        for invalid in (-1, 101, 50.5, True):
            response = self.response()
            response["confidence"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(WorkflowError):
                self.session.submit_judgment(response)

    def test_restore_rejects_old_or_impossible_state(self) -> None:
        old_state = dict(self.session.state)
        old_state["schema_version"] = "study1-state-v1"
        with self.assertRaises(WorkflowError):
            Study1Session.restore(old_state, self.cases)

        impossible = dict(self.session.state)
        impossible["phase"] = "complete"
        with self.assertRaises(WorkflowError):
            Study1Session.restore(impossible, self.cases)


class TokenAndStorageTests(unittest.TestCase):
    def test_signed_launch_token_validates_study_and_expiry(self) -> None:
        secret = "test-secret"
        token = create_token(
            {
                "typ": "launch",
                "study": "study1",
                "linkage_id": "opaque-link",
                "phase": "validation",
                "iat": 100,
                "exp": 200,
            },
            secret,
        )
        payload = verify_token(token, secret, now=150)
        self.assertEqual(payload["linkage_id"], "opaque-link")
        self.assertEqual(payload["phase"], "validation")
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

    def test_malformed_token_timestamps_are_rejected_as_token_errors(self) -> None:
        token = create_token(
            {
                "typ": "launch",
                "study": "study1",
                "linkage_id": "opaque-link",
                "iat": "not-a-time",
                "exp": 200,
            },
            "test-secret",
        )
        with self.assertRaisesRegex(TokenError, "invalid timestamps"):
            verify_token(token, "test-secret", now=150)

    def test_deployment_secret_must_not_be_short_or_placeholder(self) -> None:
        for invalid in ("short", "replace-with-a-long-random-secret"):
            with self.subTest(invalid=invalid), self.assertRaises(TokenError):
                require_deployment_secret(invalid)
        require_deployment_secret("a-unique-deployment-secret-value-12345")

    def test_qualtrics_return_url_requires_https_and_approved_host(self) -> None:
        self.assertIsNone(
            safe_qualtrics_return_url(
                "http://example.qualtrics.com/jfe/form/SV_test", "token"
            )
        )
        self.assertIsNone(
            safe_qualtrics_return_url("https://qualtrics.com.evil.test/", "token")
        )
        safe = safe_qualtrics_return_url(
            "https://example.qualtrics.com/jfe/form/SV_test", "token"
        )
        self.assertIsNotNone(safe)
        self.assertIn("study1_complete=1", safe or "")

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
                phase="screening",
                payload={"pilot": True},
            )
            second = store.append_event(
                session.state,
                "profile_presented",
                phase="screening",
                trial_reference=session.current_reference(),
            )
            event_text = (Path(directory) / "events" / f"{session_id}.jsonl").read_text(
                encoding="utf-8"
            )
            self.assertNotIn(raw_linkage, event_text)
            self.assertEqual(first["event_id"], f"{session_id}:000001")
            self.assertEqual(second["event_id"], f"{session_id}:000002")
            restored = store.load(session_id)
            self.assertEqual(restored["event_sequence"], 2)
            self.assertEqual(second["schema_version"], "study1-event-v2")
            self.assertEqual(second["application_version"], "study1-app-v2")
            self.assertEqual(
                (Path(directory) / "sessions").stat().st_mode & 0o777,
                0o700,
            )
            self.assertEqual(
                (Path(directory) / "events" / f"{session_id}.jsonl").stat().st_mode
                & 0o777,
                0o600,
            )

    def test_storage_rejects_path_like_session_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = SessionStore(Path(directory))
            with self.assertRaises(ValueError):
                store.load("../../participant-data")


if __name__ == "__main__":
    unittest.main()
