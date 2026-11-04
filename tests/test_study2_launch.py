"""Synthetic full journeys across all condition apps; no external writes."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from xai_as_closure.conditions import get_study2_condition
from xai_as_closure.logger import EventLogger

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = (
    "A current IAPP AIGP certification and current relevant professional membership."
)


def click(app, label):
    next(button for button in app.button if button.label == label).click().run(
        timeout=20
    )
    if app.exception:
        raise AssertionError(str(app.exception))


class LaunchTests(unittest.TestCase):
    def test_preview_never_writes_remotely_even_with_credentials(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"STUDY2_LOCAL_PREVIEW": "1"}),
            patch("xai_as_closure.logger.save_to_github") as remote,
        ):
            logger = EventLogger(
                get_study2_condition("P0_A0_F0"), "LOCAL_TEST", log_dir=directory
            )
            self.assertFalse(
                logger.push_to_github(
                    repo="owner/private", github_token="synthetic-token"
                )
            )
            remote.assert_not_called()

    def test_all_eight_apps_complete_six_trials_and_resume(self):
        for index, path in enumerate(sorted((ROOT / "apps").glob("study2_0*.py"))):
            condition = f"P{index // 4}_A{(index // 2) % 2}_F{index % 2}"
            with (
                self.subTest(condition=condition),
                tempfile.TemporaryDirectory() as directory,
                patch.dict(
                    os.environ,
                    {
                        "STUDY2_LOCAL_PREVIEW": "1",
                        "STUDY2_PREVIEW_DATA_ROOT": directory,
                        "STUDY2_PREVIEW_ID": "LOCAL_TEST_" + condition,
                    },
                ),
                patch("xai_as_closure.background_save.test_github_connection") as connection,
                patch("xai_as_closure.study2_app.save_to_github") as remote,
            ):
                app = AppTest.from_file(str(path)).run(timeout=20)
                self.assertFalse(app.exception)
                click(app, "Begin candidate screening")
                session = app.session_state.filtered_state["_study2_session"]
                order = list(session.state["profile_order"])
                for trial in range(6):
                    app.radio[0].set_value("Reject candidate")
                    self.assertIsNone(app.select_slider[0].value)
                    app.select_slider[0].set_value(50)
                    click(app, "Lock initial decision")
                    if index % 2:
                        app.text_area[0].set_value("Looks fine to me")
                        click(app, "Confirm requirements and continue")
                        self.assertEqual(session.phase, "forcing")
                        self.assertTrue(app.error)
                        app.text_area[0].set_value(REQUIREMENTS)
                        click(app, "Confirm requirements and continue")
                    request = next(
                        button
                        for button in app.button
                        if "assess" in button.label.lower()
                        and "Back" not in button.label
                    )
                    click(app, request.label)
                    self.assertEqual(session.phase, "aided")
                    if trial == 0:
                        resumed = AppTest.from_file(str(path)).run(timeout=20)
                        self.assertFalse(resumed.exception)
                        session = resumed.session_state.filtered_state[
                            "_study2_session"
                        ]
                        self.assertEqual(session.phase, "aided")
                        self.assertEqual(session.state["profile_order"], order)
                        app = resumed
                    app.radio[0].set_value("Reject candidate")
                    self.assertIsNone(app.select_slider[0].value)
                    app.select_slider[0].set_value(50)
                    click(app, "Lock final decision")
                    self.assertEqual(session.phase, "recall")
                    app.text_area[0].set_value(
                        "Synthetic test response: professional requirements and dates."
                    )
                    click(app, "Submit and continue")
                self.assertTrue(session.complete)
                self.assertEqual(len(session.state["trials"]), 6)
                states = list(Path(directory).glob("*.state.json"))
                self.assertEqual(len(states), 1)
                state = json.loads(states[0].read_text())
                self.assertEqual(state["condition_id"], condition)
                event_path = states[0].with_name(
                    states[0].name.replace(".state.json", ".jsonl")
                )
                events = [
                    json.loads(line) for line in event_path.read_text().splitlines()
                ]
                self.assertEqual(
                    sum(e["event_type"] == "aided_decision_submitted" for e in events),
                    6,
                )
                self.assertEqual(
                    sum(e["event_type"] == "evidence_recall_submitted" for e in events),
                    6,
                )
                self.assertTrue(
                    any(e["event_type"] == "session_completed" for e in events)
                )
                self.assertEqual(
                    [e["event_sequence"] for e in events],
                    list(range(1, len(events) + 1)),
                )
                remote.assert_not_called()
                connection.assert_not_called()


class StorageAndValidationTests(unittest.TestCase):
    def test_forcing_accepts_related_answers_and_codes_completeness(self):
        from xai_as_closure.study2 import (
            _forcing_answer_feedback,
            _forcing_answer_is_correct,
            forcing_answer_coding,
        )

        for related in ("AIGP", "membership", "valid required certificate",
                        "current required certifivcate and valied membrship"):
            self.assertIsNone(_forcing_answer_feedback(related), related)
        for unrelated in ("This candidate looks suitable.", "I remember the CV"):
            self.assertIsNotNone(_forcing_answer_feedback(unrelated), unrelated)
        for complete in (REQUIREMENTS,
                         "valid required certificate and valid professional membership",
                         "current required certifivcate and valied membrship",
                         "certificate not expired, member of a professional body"):
            self.assertTrue(_forcing_answer_is_correct(complete), complete)
        for incomplete in ("A current IAPP AIGP certification",
                           "required certification and professional membership",
                           "A current AIGP certification and expired professional membership"):
            self.assertFalse(_forcing_answer_is_correct(incomplete), incomplete)
        coding = forcing_answer_coding("AIGP cert but membership lapsed")
        self.assertTrue(coding["describes_requirement_as_expired"])
        self.assertTrue(coding["names_specific_certification"])

    def test_production_first_screen_never_waits_for_github(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"STUDY2_LOCAL_PREVIEW": "0"}),
            patch(
                "xai_as_closure.background_save.test_github_connection",
                return_value=(True, "connected"),
            ),
            patch("requests.get") as lookup,
            patch(
                "xai_as_closure.study2_app.save_to_github",
                return_value=(False, "synthetic outage"),
            ) as save,
        ):
            app = AppTest.from_file(str(ROOT / "apps/study2_01_lowP_lowA_noF.py"))
            app.query_params = {
                "PROLIFIC_PID": "000000000000000000000111",
                "cond": "P0_A0_F0",
            }
            app.secrets = {
                "GITHUB_REPO": "owner/private",
                "GITHUB_TOKEN": "fake",
                "STUDY2_DATA_ROOT": directory,
            }
            app.run(timeout=20)
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
            self.assertTrue(
                any(b.label == "Begin candidate screening" for b in app.button)
            )
            lookup.assert_not_called()
            session = app.session_state.filtered_state["_study2_session"]
            self.assertTrue(session.state["archive_pending"])
            # A failed background save retries quietly until one succeeds.
            save.return_value = (True, None)
            for _ in range(4):
                job = app.session_state.filtered_state.get("_study2_backup_job")
                if job:
                    job[0].result(timeout=3)
                app.session_state["_study2_retry_after"] = 0
                app.run(timeout=20)
            self.assertFalse(session.state["archive_pending"])
            path = save.call_args.args[1]
            self.assertIn(session.state["archive_id"], path)
            self.assertTrue(path.startswith("sessions/xai_as_closure/study2/checkpoints/"))

    def test_review_hub_only_shows_pce_for_forcing(self):
        with patch.dict(os.environ, {"STUDY2_LOCAL_PREVIEW": "1"}):
            app = AppTest.from_file(str(ROOT / "apps/local_review.py")).run(timeout=20)
            self.assertFalse(app.exception)
            self.assertEqual(len(app.radio), 22)
            app.checkbox[0].uncheck().run(timeout=20)
            self.assertEqual(len(app.radio), 19)
