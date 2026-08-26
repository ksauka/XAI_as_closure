"""Regression tests for the migrated HAI architecture and infrastructure."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from xai_as_closure.cases import CaseRepository
from xai_as_closure.conditions import get_study2_condition
from xai_as_closure.decision_agent import AgenticHiringDecisionAgent
from xai_as_closure.logger import EventLogger
from xai_as_closure.session_flatten import (
    flatten_event_rows,
    flatten_participant_rows,
    flatten_trial_rows,
)
from xai_as_closure.study2 import Study2Session


class MigratedAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = CaseRepository()

    def test_audit_exposes_the_complete_hai_pipeline(self) -> None:
        output = AgenticHiringDecisionAgent(
            condition="P1_A1_F0", cases=self.cases
        ).assess("C-01")
        self.assertEqual(
            output.audit_payload()["pipeline"],
            [
                "evidence_store",
                "plan",
                "retrieve",
                "evaluate",
                "recommend",
                "render",
            ],
        )
        self.assertEqual(len(output.claims), 3)

    def test_bounded_examination_is_interactive_and_cannot_change_verdict(self) -> None:
        for condition_id in ("P1_A0_F0", "P1_A1_F0"):
            agent = AgenticHiringDecisionAgent(condition=condition_id, cases=self.cases)
            output = agent.assess("C-05")
            response = agent.examine("C-05", "policy")
            self.assertEqual(
                output.recommendation, "Advance candidate to human interview"
            )
            self.assertIn("mandatory certification", response.response_text)
            self.assertTrue(response.visible_sources)
            if "_A1_" in condition_id:
                self.assertIn(" I ", f" {response.response_text} ")
            else:
                self.assertNotIn(" I ", f" {response.response_text} ")

    def test_explanation_absent_condition_has_no_evidence_examination(self) -> None:
        for condition_id in ("P0_A0_F0", "P0_A1_F0"):
            agent = AgenticHiringDecisionAgent(condition=condition_id, cases=self.cases)
            output = agent.assess("C-05")
            self.assertFalse(output.explanation_present)
            self.assertEqual(output.visible_sources, ())
            with self.assertRaisesRegex(ValueError, "explanation is absent"):
                agent.examine("C-05", "policy")

    def test_session_retains_challenge_history(self) -> None:
        condition = get_study2_condition("P1_A1_F0")
        session = Study2Session.create(
            session_id="s2_migration",
            participant_id="participant-migration",
            prolific_pid="participant-migration",
            condition=condition,
            seed="migration-test",
            cases=self.cases,
        )
        agent = AgenticHiringDecisionAgent(condition=condition, cases=self.cases)
        for _ in range(3):
            session.advance_introduction()
        session.submit_unaided({"decision": "Reject candidate", "confidence": 70})
        session.request_agent_assessment(agent)
        response = session.examine_agent_assessment(agent, "caution")
        self.assertEqual(response["kind"], "caution")
        self.assertEqual(
            len(session.current_trial()["agent_output"]["challenge_history"]), 1
        )


class MigratedInfrastructureTests(unittest.TestCase):
    def test_no_parallel_study2_compatibility_wrappers_remain(self) -> None:
        source_root = Path(__file__).resolve().parents[1] / "src" / "xai_as_closure"
        for filename in (
            "study2_conditions.py",
            "study2_storage.py",
            "study2_agent.py",
            "study2_schemas.py",
        ):
            self.assertFalse((source_root / filename).exists(), filename)

    def test_production_apps_accept_streamlit_community_secrets(self) -> None:
        app_root = Path(__file__).resolve().parents[1] / "apps"
        cases = (
            (
                "study1_validation.py",
                "xai_as_closure.study1_app.test_github_connection",
                {},
                "STUDY1_DATA_ROOT",
            ),
            (
                "study2_01_lowP_lowA_noF.py",
                "xai_as_closure.study2_app.test_github_connection",
                {"cond": "P0_A0_F0"},
                "STUDY2_DATA_ROOT",
            ),
        )
        for filename, connection_target, extra_query, data_root_key in cases:
            with self.subTest(app=filename), tempfile.TemporaryDirectory() as directory:
                app = AppTest.from_file(str(app_root / filename))
                app.query_params = {
                    "PROLIFIC_PID": "5f8e3c2a1b9d4e6f7a8b9c0d",
                    **extra_query,
                }
                app.secrets = {
                    "GITHUB_REPO": "owner/private-study-data",
                    "GITHUB_TOKEN": "test-token",
                    data_root_key: directory,
                }
                with patch(
                    connection_target, return_value=(True, "connected")
                ) as check:
                    app.run(timeout=20)
                self.assertFalse(app.exception)
                self.assertEqual(check.call_count, 1)
                self.assertFalse(
                    any("storage" in error.value.lower() for error in app.error)
                )

    def test_production_app_blocks_when_cloud_secrets_are_missing(self) -> None:
        app_path = Path(__file__).resolve().parents[1] / "apps" / "study1_validation.py"
        app = AppTest.from_file(str(app_path))
        app.query_params = {"PROLIFIC_PID": "5f8e3c2a1b9d4e6f7a8b9c0d"}
        app.run(timeout=20)
        self.assertFalse(app.exception)
        self.assertTrue(
            any("storage is not configured" in error.value for error in app.error)
        )

    def test_each_document_visit_is_paired_and_timed_in_both_studies(self) -> None:
        app_root = Path(__file__).resolve().parents[1] / "apps"
        with tempfile.TemporaryDirectory() as directory:
            app = AppTest.from_file(str(app_root / "study1_validation.py"))
            app.query_params = {"PROLIFIC_PID": "study1-document-visit"}
            app.secrets = {
                "GITHUB_REPO": "owner/private-study-data",
                "GITHUB_TOKEN": "test-token",
                "STUDY1_DATA_ROOT": directory,
            }
            with (
                patch(
                    "xai_as_closure.study1_app.test_github_connection",
                    return_value=(True, "connected"),
                ),
                patch(
                    "xai_as_closure.study1_app.save_to_github",
                    return_value=(True, None),
                ) as save,
            ):
                app.run(timeout=20)
                next(
                    button
                    for button in app.button
                    if button.label == "Open job description"
                ).click()
                app.run(timeout=20)
                next(
                    button
                    for button in app.button
                    if button.label == "Back to candidate"
                ).click()
                app.run(timeout=20)
            event_path = next((Path(directory) / "events").glob("*.jsonl"))
            events = [
                json.loads(line)
                for line in event_path.read_text(encoding="utf-8").splitlines()
            ]
            document_events = [
                event
                for event in events
                if event["event_type"] in {"document_opened", "document_closed"}
            ]
            self._assert_paired_document_visit(document_events, "role")
            self.assertGreaterEqual(save.call_count, 2)

        with tempfile.TemporaryDirectory() as directory:
            app = AppTest.from_file(str(app_root / "study2_01_lowP_lowA_noF.py"))
            app.query_params = {
                "PROLIFIC_PID": "study2-document-visit",
                "cond": "P0_A0_F0",
            }
            app.secrets = {
                "GITHUB_REPO": "owner/private-study-data",
                "GITHUB_TOKEN": "test-token",
                "STUDY2_DATA_ROOT": directory,
            }
            with (
                patch(
                    "xai_as_closure.study2_app.test_github_connection",
                    return_value=(True, "connected"),
                ),
                patch(
                    "xai_as_closure.logger.save_to_github",
                    return_value=(True, None),
                ) as save,
            ):
                app.run(timeout=20)
                for label in (
                    "Continue to role description",
                    "Continue to recruitment policy",
                    "Begin candidate screening",
                ):
                    next(
                        button for button in app.button if button.label == label
                    ).click()
                    app.run(timeout=20)
                next(
                    button
                    for button in app.button
                    if button.label == "Open recruitment policy"
                ).click()
                app.run(timeout=20)
                self.assertTrue(
                    next(
                        button
                        for button in app.button
                        if button.label == "Open job description"
                    ).disabled
                )
                next(
                    button
                    for button in app.button
                    if button.label == "Back to candidate"
                ).click()
                app.run(timeout=20)
            event_path = next(Path(directory).glob("*.jsonl"))
            events = [
                json.loads(line)
                for line in event_path.read_text(encoding="utf-8").splitlines()
            ]
            document_events = [
                event
                for event in events
                if event["event_type"] in {"document_opened", "document_closed"}
            ]
            self._assert_paired_document_visit(document_events, "policy")
            self.assertGreaterEqual(save.call_count, 2)

    def _assert_paired_document_visit(
        self, events: list[dict[str, object]], expected_document: str
    ) -> None:
        self.assertEqual(
            [event["event_type"] for event in events],
            [
                "document_opened",
                "document_closed",
            ],
        )
        opened, closed = events
        opened_payload = opened["payload"]
        closed_payload = closed["payload"]
        self.assertIsInstance(opened_payload, dict)
        self.assertIsInstance(closed_payload, dict)
        self.assertEqual(opened_payload["document"], expected_document)
        self.assertEqual(
            opened_payload["document_visit_id"],
            closed_payload["document_visit_id"],
        )
        self.assertEqual(closed_payload["return_target"], "candidate")
        self.assertGreaterEqual(closed_payload["click_to_return_seconds"], 0)
        self.assertGreaterEqual(closed_payload["dwell_seconds"], 0)
        self.assertTrue(opened["trial_reference"])
        self.assertEqual(opened["trial_reference"], closed["trial_reference"])

    def test_explanation_citations_open_the_complete_focused_document(self) -> None:
        app_path = (
            Path(__file__).resolve().parents[1] / "apps" / "study2_05_highP_lowA_noF.py"
        )
        with tempfile.TemporaryDirectory() as directory:
            app = AppTest.from_file(str(app_path))
            app.query_params = {
                "PROLIFIC_PID": "study2-citation-document",
                "cond": "P1_A0_F0",
            }
            app.secrets = {
                "GITHUB_REPO": "owner/private-study-data",
                "GITHUB_TOKEN": "test-token",
                "STUDY2_DATA_ROOT": directory,
            }
            with (
                patch(
                    "xai_as_closure.study2_app.test_github_connection",
                    return_value=(True, "connected"),
                ),
                patch(
                    "xai_as_closure.logger.save_to_github",
                    return_value=(True, None),
                ),
            ):
                app.run(timeout=20)
                for label in (
                    "Continue to role description",
                    "Continue to recruitment policy",
                    "Begin candidate screening",
                ):
                    next(
                        button for button in app.button if button.label == label
                    ).click()
                    app.run(timeout=20)

                app.radio[0].set_value("Reject candidate")
                next(
                    button
                    for button in app.button
                    if button.label == "Lock initial decision"
                ).click()
                app.run(timeout=20)
                next(
                    button
                    for button in app.button
                    if button.label == "Generate system assessment"
                ).click()
                app.run(timeout=20)

                citation_labels = [
                    button.label
                    for button in app.button
                    if button.label.startswith("[")
                ]
                self.assertTrue(citation_labels)
                self.assertTrue(any("CV §" in label for label in citation_labels))
                self.assertFalse(
                    any(
                        "Certifications" in label or "Roles" in label
                        for label in citation_labels
                    )
                )

                next(
                    button for button in app.button if button.label.startswith("[CV §")
                ).click()
                app.run(timeout=20)
                visible_text = "\n".join(
                    [element.value for element in app.markdown]
                    + [element.value for element in app.caption]
                    + [element.value for element in app.subheader]
                )
                self.assertIn("Current focus:", visible_text)
                for section in ("§1", "§4", "§5"):
                    self.assertIn(section, visible_text)
                self.assertTrue(
                    any(button.label == "Back to candidate" for button in app.button)
                )

    def test_github_archive_uses_the_hai_logger_and_event_payload(self) -> None:
        cases = CaseRepository()
        condition = get_study2_condition("P1_A0_F1")
        session = Study2Session.create(
            session_id="migrationarchive",
            participant_id="prolific-migration",
            prolific_pid="prolific-migration",
            condition=condition,
            seed="archive-test",
            cases=cases,
        )
        with tempfile.TemporaryDirectory() as directory:
            logger = EventLogger(
                condition,
                "prolific-migration",
                session_id=session.state["session_id"],
                log_dir=Path(directory),
            )
            logger.log("session_created")
            logger.session_meta = dict(session.state)
            archive = logger.github_payload()
            self.assertEqual(archive["session_id"], "migrationarchive")
            self.assertEqual(len(archive["events"]), 1)
            with patch(
                "xai_as_closure.logger.save_to_github",
                return_value=(True, None),
            ) as save:
                success = logger.push_to_github(
                    repo="owner/private-data",
                    github_token="secret-token",
                )
            self.assertTrue(success)
            self.assertIn("sessions/xai_as_closure/study2/", save.call_args.args[1])

    def test_session_flatten_outputs_participant_trial_and_event_rows(self) -> None:
        cases = CaseRepository()
        condition = get_study2_condition("P1_A1_F0")
        session = Study2Session.create(
            session_id="s2_flatten",
            participant_id="participant-flatten",
            prolific_pid="participant-flatten",
            condition=condition,
            seed="flatten-test",
            cases=cases,
        )
        agent = AgenticHiringDecisionAgent(condition=condition, cases=cases)
        for _ in range(3):
            session.advance_introduction()
        session.submit_unaided({"decision": "Reject candidate", "confidence": 65})
        session.request_agent_assessment(agent)
        session.examine_agent_assessment(agent, "support")
        session.submit_aided(
            {"decision": "Advance candidate to human interview", "confidence": 80}
        )
        session.submit_evidence_recall("The certification and experience mattered.")
        event = {
            "event_id": "s2_flatten:000001",
            "event_sequence": 1,
            "event_type": "agent_assessment_presented",
            "payload": {"reference": "C-01"},
        }
        archive = {"state": session.state, "events": [event]}
        participant = flatten_participant_rows([archive])
        trials = flatten_trial_rows([archive], cases)
        events = flatten_event_rows([archive])
        self.assertEqual(len(participant), 1)
        self.assertEqual(len(trials), 1)
        self.assertEqual(trials[0]["challenge_count"], 1)
        self.assertEqual(len(events), 1)


if __name__ == "__main__":
    unittest.main()
