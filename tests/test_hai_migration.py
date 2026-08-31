"""Regression tests for the migrated HAI architecture and infrastructure."""

from __future__ import annotations

import json
import re
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from xai_as_closure.cases import CaseRepository
from xai_as_closure.conditions import get_study2_condition
from xai_as_closure.config import read_project_storage_config
from xai_as_closure.decision_agent import AgenticHiringDecisionAgent
from xai_as_closure.logger import EventLogger
from xai_as_closure.session_flatten import (
    flatten_event_rows,
    flatten_participant_rows,
    flatten_trial_rows,
)
from xai_as_closure.study2 import Study2Session, Study2WorkflowError
from xai_as_closure.study2_app import (
    _citation_document_html,
    _resolve_inline_citation,
)


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
        self.assertEqual(len(output.claims), 4)

    def test_agent_exposes_only_the_current_registered_workflow(self) -> None:
        agent = AgenticHiringDecisionAgent(condition="P1_A1_F0", cases=self.cases)
        output = agent.assess("C-05")
        self.assertFalse(hasattr(agent, "examine"))
        self.assertNotIn("challenge_history", output.participant_payload())

    def test_inline_citation_tokens_resolve_only_registered_sources(self) -> None:
        condition = get_study2_condition("P1_A1_F0")
        session = Study2Session.create(
            session_id="citation-resolution",
            participant_id="citation-resolution",
            prolific_pid="citation-resolution",
            condition=condition,
            seed="citation-resolution",
            cases=self.cases,
        )
        reference = session.current_reference()
        self.assertIsNotNone(reference)
        output = AgenticHiringDecisionAgent(
            condition=condition, cases=self.cases
        ).assess(str(reference))
        blocks = output.participant_payload()["message_blocks"]
        block_index = next(
            index for index, block in enumerate(blocks) if block["citations"]
        )
        source, resolved_block, resolved_citation = _resolve_inline_citation(
            session, str(reference), blocks, f"{block_index}:0"
        )
        self.assertTrue(source["citation"])
        self.assertEqual((resolved_block, resolved_citation), (block_index, 0))
        with self.assertRaisesRegex(Study2WorkflowError, "citation token"):
            _resolve_inline_citation(session, str(reference), blocks, "../../policy")

    def test_every_registered_citation_opens_a_complete_highlighted_document(
        self,
    ) -> None:
        condition = get_study2_condition("P1_A0_F0")
        session = Study2Session.create(
            session_id="citation-documents",
            participant_id="citation-documents",
            prolific_pid="citation-documents",
            condition=condition,
            seed="citation-documents",
            cases=self.cases,
        )
        agent = AgenticHiringDecisionAgent(condition=condition, cases=self.cases)
        seen_documents: set[str] = set()
        for reference in self.cases.references:
            blocks = agent.assess(reference).participant_payload()["message_blocks"]
            for block_index, block in enumerate(blocks):
                for citation_index, expected in enumerate(block["citations"]):
                    source, _, _ = _resolve_inline_citation(
                        session,
                        reference,
                        blocks,
                        f"{block_index}:{citation_index}",
                    )
                    frame = _citation_document_html(session, reference, source)
                    self.assertEqual(source, expected)
                    self.assertEqual(frame.count('id="cited-passage"'), 1)
                    self.assertIn("Cited passage", frame)
                    self.assertIn("scrollIntoView", frame)
                    seen_documents.add(source["document"])
        self.assertEqual(seen_documents, {"cv", "role", "policy"})


class MigratedInfrastructureTests(unittest.TestCase):
    def test_local_pilot_storage_config_accepts_spaced_dotenv_assignments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"
            env_path.write_text(
                "GITHUB_REPO = owner/private-data\n"
                "GITHUB_TOKEN = 'test-token'\n"
                "OPENAI_API_KEY = must-not-be-returned\n",
                encoding="utf-8",
            )
            values = read_project_storage_config(env_path)
        self.assertEqual(
            values,
            {
                "GITHUB_REPO": "owner/private-data",
                "GITHUB_TOKEN": "test-token",
            },
        )

    def test_local_pilot_uses_project_storage_config_without_warning(self) -> None:
        app_path = (
            Path(__file__).resolve().parents[1] / "apps" / "study2_01_lowP_lowA_noF.py"
        )
        with tempfile.TemporaryDirectory() as directory:
            app = AppTest.from_file(str(app_path))
            app.secrets = {"STUDY2_DATA_ROOT": directory}
            with (
                patch(
                    "xai_as_closure.study2_app.read_project_storage_config",
                    return_value={
                        "GITHUB_REPO": "owner/private-study-data",
                        "GITHUB_TOKEN": "test-token",
                    },
                ),
                patch(
                    "xai_as_closure.study2_app.test_github_connection",
                    return_value=(True, "connected"),
                ),
            ):
                app.run(timeout=20)
                app.text_input[0].set_value("local-pilot-storage")
                next(
                    button
                    for button in app.button
                    if button.label == "Begin study task"
                ).click()
                app.run(timeout=20)
            self.assertFalse(
                any("storage" in warning.value.lower() for warning in app.warning)
            )

    def test_inline_component_uses_only_local_safe_dom_code(self) -> None:
        frontend = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "xai_as_closure"
            / "recommendation_component_frontend"
            / "index.html"
        ).read_text(encoding="utf-8")
        self.assertNotIn("<script src=", frontend)
        self.assertNotIn("innerHTML", frontend)
        self.assertNotIn("eval(", frontend)
        self.assertIn("textContent", frontend)
        self.assertIn("streamlit:setComponentValue", frontend)

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
        # AppTest.secrets only replaces the global st.secrets when truthy, so an
        # empty dict here would silently fall through to the real on-disk
        # .streamlit/secrets.toml. A placeholder key forces the override.
        app.secrets = {"_TEST_NO_STORAGE_SECRETS": "placeholder"}
        app.run(timeout=20)
        self.assertFalse(app.exception)
        self.assertTrue(
            any("storage is not configured" in error.value for error in app.error)
        )

    def test_study1_uses_streamlined_candidate_and_final_review_measures(self) -> None:
        app_path = Path(__file__).resolve().parents[1] / "apps" / "study1_validation.py"
        with tempfile.TemporaryDirectory() as directory:
            app = AppTest.from_file(str(app_path))
            app.query_params = {"PROLIFIC_PID": "study1-streamlined-measures"}
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
                ),
            ):
                app.run(timeout=20)
                radio_labels = {radio.label for radio in app.radio}
                self.assertIn("Screening decision", radio_labels)
                self.assertIn(
                    "Does this candidate satisfy the mandatory professional "
                    "requirements?",
                    radio_labels,
                )
                self.assertEqual(
                    [slider.label for slider in app.slider],
                    ["Confidence in this decision"],
                )
                self.assertIn(
                    "What information in the candidate file was most important "
                    'for your decision? Enter "None" if no information was decisive.',
                    {field.label for field in app.text_input},
                )

                session = app.session_state.filtered_state["_study1_session"]
                candidate_response = {
                    "decision": "Advance candidate to human interview",
                    "hard_criterion_judgment": "Yes",
                    "confidence": 80,
                    "decisive_evidence": "Certification identity and dates.",
                }
                for _ in range(6):
                    session.submit_judgment(candidate_response)
                app.run(timeout=20)

            final_radio_labels = {radio.label for radio in app.radio}
            self.assertIn(
                "1. The role requirements were clear enough to determine whether "
                "a candidate met the mandatory requirements.",
                final_radio_labels,
            )
            self.assertIn(
                "7. Were there any candidates for whom you believed reasonable "
                "recruitment professionals could disagree about whether the "
                "candidate met the mandatory professional requirements?",
                final_radio_labels,
            )
            self.assertEqual(len(app.multiselect), 1)
            self.assertFalse(
                any(
                    construct in label.lower()
                    for label in final_radio_labels
                    for construct in ("ppbe", "anthropomorphism", "pce", "trust")
                )
            )

    def test_study2_introduction_uses_summaries_with_optional_full_documents(
        self,
    ) -> None:
        app_path = (
            Path(__file__).resolve().parents[1] / "apps" / "study2_01_lowP_lowA_noF.py"
        )
        with tempfile.TemporaryDirectory() as directory:
            app = AppTest.from_file(str(app_path))
            app.query_params = {
                "PROLIFIC_PID": "study2-summary-introduction",
                "cond": "P0_A0_F0",
            }
            app.secrets = {
                "GITHUB_REPO": "owner/private-study-data",
                "GITHUB_TOKEN": "test-token",
                "STUDY2_DATA_ROOT": directory,
            }
            with patch(
                "xai_as_closure.study2_app.test_github_connection",
                return_value=(True, "connected"),
            ):
                app.run(timeout=20)
                brief_text = "\n".join(
                    [element.value for element in app.header]
                    + [element.value for element in app.markdown]
                    + [element.value for element in app.info]
                )
                self.assertIn("Recruitment brief", brief_text)
                self.assertIn("Suvh Trust Bank", brief_text)
                self.assertIn("AI Governance Lead", brief_text)
                self.assertIn("Recruitment guidance", brief_text)
                self.assertIn("20 July 2026", brief_text)
                self.assertIn("27–30 August 2026", brief_text)
                self.assertIn("20 September 2026", brief_text)
                self.assertIn("recruiters are advised", brief_text.lower())
                self.assertNotIn("mandatory requirement", brief_text.lower())
                self.assertNotIn("general requirements", brief_text.lower())
                self.assertNotIn("Section 1. Role Designation", brief_text)
                self.assertNotIn("Section 1. Purpose and Scope", brief_text)
                self.assertTrue(
                    any(
                        button.label == "View full job description"
                        for button in app.button
                    )
                )
                self.assertTrue(
                    any(
                        button.label == "View full recruitment policy"
                        for button in app.button
                    )
                )
                self.assertFalse(
                    any(button.label.startswith("Continue to") for button in app.button)
                )
                next(
                    button
                    for button in app.button
                    if button.label == "Begin candidate screening"
                ).click()
                app.run(timeout=20)
                self.assertTrue(app.radio)

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
                next(
                    button
                    for button in app.button
                    if button.label == "Begin candidate screening"
                ).click()
                app.run(timeout=20)
                next(
                    button
                    for button in app.button
                    if button.label == "View full recruitment policy"
                ).click()
                app.run(timeout=20)
                self.assertTrue(
                    next(
                        button
                        for button in app.button
                        if button.label == "View full job description"
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

    def test_explanation_component_receives_only_neutral_registered_locators(self) -> None:
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
                next(
                    button
                    for button in app.button
                    if button.label == "Begin candidate screening"
                ).click()
                app.run(timeout=20)

                app.radio[0].set_value("Reject candidate")
                next(
                    button
                    for button in app.button
                    if button.label == "Lock initial decision"
                ).click()
                app.run(timeout=20)
                self.assertFalse(
                    any(
                        "Curriculum vitae" in element.value
                        for element in app.subheader
                    )
                )
                self.assertTrue(
                    any(element.value == "AI assessment" for element in app.header)
                )
                next(
                    button
                    for button in app.button
                    if button.label == "Generate system assessment"
                ).click()
                app.run(timeout=20)
                recommendation_page_text = "\n".join(
                    element.value
                    for collection in (
                        app.markdown,
                        app.caption,
                        app.info,
                        app.subheader,
                    )
                    for element in collection
                )
                self.assertNotIn("Curriculum vitae", recommendation_page_text)
                self.assertEqual(len(app.expander), 0)
                self.assertEqual(len(app.selectbox), 0)

                component = app.get("component_instance")
                self.assertEqual(len(component), 1)
                component_args = json.loads(component[0].proto.json_args)
                citation_labels = [
                    citation["label"]
                    for block in component_args["blocks"]
                    for citation in block["citations"]
                ]
                self.assertTrue(citation_labels)
                self.assertTrue(any("CV(" in label for label in citation_labels))
                self.assertFalse(
                    any(
                        "Certifications" in label or "Roles" in label
                        for label in citation_labels
                    )
                )

                self.assertTrue(
                    all(
                        re.fullmatch(r"\d+:\d+", citation["token"])
                        for block in component_args["blocks"]
                        for citation in block["citations"]
                    )
                )

    def test_anthropomorphic_recommendation_is_one_passage_with_inline_locators(
        self,
    ) -> None:
        app_path = (
            Path(__file__).resolve().parents[1] / "apps" / "study2_07_highP_highA_noF.py"
        )
        with tempfile.TemporaryDirectory() as directory:
            app = AppTest.from_file(str(app_path))
            app.query_params = {
                "PROLIFIC_PID": "study2-anthropomorphic-passage",
                "cond": "P1_A1_F0",
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
                next(
                    button
                    for button in app.button
                    if button.label == "Begin candidate screening"
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
                    if button.label == "Ask the assistant to assess this candidate"
                ).click()
                app.run(timeout=20)

                component = app.get("component_instance")
                self.assertEqual(len(component), 1)
                component_args = json.loads(component[0].proto.json_args)
                self.assertTrue(component_args["anthropomorphic"])
                self.assertTrue(
                    " ".join(block["text"] for block in component_args["blocks"])
                    .startswith("I've ")
                )
                labels = [
                    citation["label"]
                    for block in component_args["blocks"]
                    for citation in block["citations"]
                ]
                self.assertTrue(any(label.startswith("CV(") for label in labels))
                self.assertTrue(any(label.startswith("JD(") for label in labels))
                self.assertEqual(len(app.expander), 0)
                self.assertEqual(len(app.selectbox), 0)

    def test_citation_document_keeps_assessment_and_final_form_in_place(self) -> None:
        app_path = (
            Path(__file__).resolve().parents[1] / "apps" / "study2_05_highP_lowA_noF.py"
        )
        with tempfile.TemporaryDirectory() as directory:
            app = AppTest.from_file(str(app_path))
            app.query_params = {
                "PROLIFIC_PID": "study2-in-page-citation",
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
                next(
                    button
                    for button in app.button
                    if button.label == "Begin candidate screening"
                ).click().run(timeout=20)
                app.radio[0].set_value("Reject candidate")
                next(
                    button
                    for button in app.button
                    if button.label == "Lock initial decision"
                ).click().run(timeout=20)
                next(
                    button
                    for button in app.button
                    if button.label == "Generate system assessment"
                ).click().run(timeout=20)

                session = app.session_state.filtered_state["_study2_session"]
                output = session.current_trial()["agent_output"]
                source = next(
                    citation
                    for block in output["message_blocks"]
                    for citation in block["citations"]
                )
                app.session_state["_study2_citation_document"] = {
                    "source": source,
                    "visit": {
                        "document_visit_id": "in-page-test",
                        "document": source["document"],
                        "origin": "ai_message_citation",
                        "clicked_at_monotonic": time.perf_counter(),
                    },
                }
                app.run(timeout=20)

                self.assertEqual(len(app.get("iframe")), 1)
                self.assertTrue(
                    any(
                        button.label == "Close source document"
                        for button in app.button
                    )
                )
                self.assertTrue(
                    any(button.label == "Lock final decision" for button in app.button)
                )
                self.assertTrue(
                    all(
                        button.disabled
                        for button in app.button
                        if button.label.startswith("View ")
                    )
                )
                next(
                    button
                    for button in app.button
                    if button.label == "Close source document"
                ).click().run(timeout=20)

            events = [
                json.loads(line)
                for line in next(Path(directory).glob("*.jsonl"))
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            closed = next(
                event
                for event in reversed(events)
                if event["event_type"] == "document_closed"
            )
            self.assertEqual(
                closed["payload"]["presentation"], "inline_complete_document"
            )
            self.assertEqual(closed["payload"]["return_target"], "ai_assessment")
            self.assertGreaterEqual(closed["payload"]["dwell_seconds"], 0)

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
        self.assertNotIn("challenge_count", trials[0])
        self.assertEqual(len(events), 1)


if __name__ == "__main__":
    unittest.main()
