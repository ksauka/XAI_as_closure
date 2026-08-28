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
                "explanation",
            ):
                self.assertNotIn(forbidden, serialized)

    def test_material_manifest_changes_are_detectable(self) -> None:
        manifest = material_manifest()
        self.assertEqual(manifest["material_set"], "chi_six_profiles_v2")
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

    def test_recruitment_timeline_and_dated_certifications_are_locked(self) -> None:
        timeline = self.cases.timeline
        self.assertEqual(timeline.posted_label, "20 July 2026")
        self.assertEqual(timeline.screening_window_label, "27–30 August 2026")
        self.assertEqual(timeline.target_fill_label, "20 September 2026")
        for reference in self.cases.references:
            certification = next(
                section
                for section in self.cases.participant_case(reference).sections
                if section.id == "cv_certifications"
            )
            lines = certification.text.splitlines()
            self.assertEqual(len(lines), 3)
            self.assertTrue(all("20" in line for line in lines))
        c05 = next(
            section
            for section in self.cases.participant_case("C-05").sections
            if section.id == "cv_certifications"
        )
        self.assertIn("AIGP", c05.text)
        self.assertIn("31 May 2026", c05.text)
        self.assertNotIn("PMI-CPMAI", c05.text)

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
            "hard_criterion_judgment": "Yes",
            "confidence": 80,
            "decisive_evidence": "The accepted certification is present.",
        }

    @staticmethod
    def post_study_response() -> dict:
        return {
            "role_requirement_clarity": 7,
            "candidate_profile_realism": 6,
            "qualification_difference_plausibility": 6,
            "mandatory_information_identifiability": 7,
            "information_sufficiency": 6,
            "task_ecological_validity": 6,
            "professional_disagreement": "No",
            "disputed_profiles": [],
            "disputed_profiles_reason": "",
            "materials_feedback": "",
        }

    def test_session_contains_no_ai_or_experimental_assignments(self) -> None:
        self.assertEqual(self.session.state["schema_version"], "study1-state-v4")
        self.assertEqual(
            self.session.state["instrument_version"], "study1-instrument-v4"
        )
        self.assertEqual(self.session.state["case_set_id"], self.cases.case_set_id)
        self.assertEqual(self.session.phase, "screening")
        self.assertNotIn("phase_b_responses", self.session.state)
        self.assertNotIn("artifact_assignments", self.session.state)
        self.assertNotIn("condition", self.session.state)
        for construct in ("ppbe", "ant", "pce", "trust"):
            self.assertNotIn(construct, json.dumps(self.session.state).lower())

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

    def test_final_review_is_required_after_all_six_judgments(self) -> None:
        references = [self.session.submit_judgment(self.response()) for _ in range(6)]
        self.assertEqual(len(set(references)), 6)
        self.assertEqual(self.session.phase, "post_study")
        self.assertFalse(self.session.complete)
        self.assertEqual(len(self.session.state["responses"]), 6)
        self.assertIsNone(self.session.state["completed_at_utc"])
        with self.assertRaises(WorkflowError):
            self.session.submit_judgment(self.response())
        self.session.submit_post_study(self.post_study_response())
        self.assertTrue(self.session.complete)
        self.assertIsNotNone(self.session.state["completed_at_utc"])
        self.assertEqual(
            self.session.state["post_study_response"]["professional_disagreement"],
            "No",
        )

    def test_hard_criterion_judgment_is_required_and_binary(self) -> None:
        invalid_values = (
            ("hard_criterion_judgment", None),
            ("hard_criterion_judgment", "Unsure"),
        )
        for field, value in invalid_values:
            response = self.response()
            response[field] = value
            with (
                self.subTest(field=field, value=value),
                self.assertRaises(WorkflowError),
            ):
                self.session.submit_judgment(response)

    def test_whitespace_only_open_responses_are_rejected(self) -> None:
        response = self.response()
        response["decisive_evidence"] = "   "
        with self.assertRaisesRegex(WorkflowError, "decisive_evidence"):
            self.session.submit_judgment(response)

    def test_study2_construct_fields_cannot_enter_study1_responses(self) -> None:
        response = self.response()
        response["trust"] = 7
        with self.assertRaisesRegex(WorkflowError, "Unexpected judgment fields"):
            self.session.submit_judgment(response)

    def test_confidence_must_be_an_integer_percentage(self) -> None:
        for invalid in (-1, 101, 50.5, True):
            response = self.response()
            response["confidence"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(WorkflowError):
                self.session.submit_judgment(response)

    def test_disputed_profile_explanation_is_required_only_for_yes(self) -> None:
        for _ in range(6):
            self.session.submit_judgment(self.response())
        response = self.post_study_response()
        response["professional_disagreement"] = "Yes"
        with self.assertRaisesRegex(WorkflowError, "disputed candidate"):
            self.session.submit_post_study(response)
        response["disputed_profiles"] = ["C-05"]
        response["disputed_profiles_reason"] = (
            "C-05, because the expiry date may be overlooked."
        )
        self.session.submit_post_study(response)
        self.assertTrue(self.session.complete)

    def test_post_study_likert_items_are_required_and_bounded(self) -> None:
        for _ in range(6):
            self.session.submit_judgment(self.response())
        for invalid in (None, 0, 8, 4.5, True):
            response = self.post_study_response()
            response["role_requirement_clarity"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(WorkflowError):
                self.session.submit_post_study(response)

    def test_study2_construct_fields_cannot_enter_final_review(self) -> None:
        for _ in range(6):
            self.session.submit_judgment(self.response())
        response = self.post_study_response()
        response["ppbe"] = 7
        with self.assertRaisesRegex(WorkflowError, "Unexpected final-review fields"):
            self.session.submit_post_study(response)

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
            self.assertEqual(second["schema_version"], "study1-event-v4")
            self.assertEqual(second["application_version"], "study1-app-v4")
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
