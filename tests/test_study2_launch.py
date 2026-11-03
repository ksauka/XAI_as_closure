"""Synthetic full journeys across all condition apps; no external writes."""

import base64
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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
                patch("xai_as_closure.study2_app.test_github_connection") as connection,
                patch("xai_as_closure.logger.save_to_github") as remote,
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
                        app.text_area[0].set_value("membership")
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
    def test_forcing_requires_membership_not_only_issuer_name(self):
        from xai_as_closure.study2 import _forcing_answer_is_correct

        self.assertFalse(
            _forcing_answer_is_correct("A current IAPP AIGP certification")
        )
        self.assertFalse(
            _forcing_answer_is_correct(
                "A current AIGP certification and expired professional membership"
            )
        )
        self.assertTrue(_forcing_answer_is_correct(REQUIREMENTS))

    def test_remote_restart_recovers_event_history_and_rejects_corruption(self):
        from xai_as_closure.cases import CaseRepository
        from xai_as_closure.logger import load_remote_checkpoint, load_state
        from xai_as_closure.study2 import Study2Session

        condition = get_study2_condition("P1_A0_F0")
        with (
            tempfile.TemporaryDirectory() as original,
            tempfile.TemporaryDirectory() as restarted,
            patch.dict(os.environ, {"STUDY2_LOCAL_PREVIEW": "0"}),
        ):
            logger = EventLogger(
                condition, "synthetic", session_id="remotecheckpoint", log_dir=original
            )
            session = Study2Session.create(
                session_id=logger.session_id,
                participant_id="synthetic",
                prolific_pid="synthetic",
                condition=condition,
                seed="synthetic",
                cases=CaseRepository(),
            )
            logger.log("session_created")
            session.state["turn_id"] = logger.turn_id
            logger.session_meta = session.state
            payload = logger.github_payload()
            response = MagicMock(status_code=200)
            response.json.return_value = {
                "content": base64.b64encode(json.dumps(payload).encode()).decode()
            }
            with patch("xai_as_closure.logger.requests.get", return_value=response):
                state = load_remote_checkpoint(
                    logger.session_id,
                    "synthetic",
                    condition.condition_id,
                    "owner/private",
                    "fake",
                    restarted,
                )
            self.assertEqual(state["profile_order"], session.state["profile_order"])
            self.assertEqual(load_state(logger.session_id, restarted)["turn_id"], 1)
            self.assertEqual(
                len(
                    (Path(restarted) / "remotecheckpoint.jsonl")
                    .read_text()
                    .splitlines()
                ),
                1,
            )
            payload["events"][0]["event_sequence"] = 5
            response.json.return_value = {
                "content": base64.b64encode(json.dumps(payload).encode()).decode()
            }
            with (
                patch("xai_as_closure.logger.requests.get", return_value=response),
                self.assertRaisesRegex(ValueError, "inconsistent"),
            ):
                load_remote_checkpoint(
                    logger.session_id,
                    "synthetic",
                    condition.condition_id,
                    "owner/private",
                    "fake",
                    restarted,
                )
            response.status_code = 503
            import requests

            response.raise_for_status.side_effect = requests.HTTPError()
            with (
                patch("xai_as_closure.logger.requests.get", return_value=response),
                self.assertRaisesRegex(ValueError, "could not be recovered"),
            ):
                load_remote_checkpoint(
                    logger.session_id,
                    "synthetic",
                    condition.condition_id,
                    "owner/private",
                    "fake",
                    restarted,
                )

    def test_production_save_failure_blocks_until_retry_succeeds(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"STUDY2_LOCAL_PREVIEW": "0"}),
            patch(
                "xai_as_closure.study2_app.test_github_connection",
                return_value=(True, "connected"),
            ),
            patch(
                "xai_as_closure.study2_app.load_remote_checkpoint", return_value=None
            ),
            patch(
                "xai_as_closure.logger.save_to_github",
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
            self.assertTrue(app.error)
            self.assertFalse(
                any(b.label == "Begin candidate screening" for b in app.button)
            )
            save.return_value = (True, None)
            next(b for b in app.button if b.label == "Retry saving").click().run(
                timeout=20
            )
            self.assertFalse(app.exception)
            self.assertTrue(
                any(b.label == "Begin candidate screening" for b in app.button)
            )

    def test_review_hub_only_shows_pce_for_forcing(self):
        with patch.dict(os.environ, {"STUDY2_LOCAL_PREVIEW": "1"}):
            app = AppTest.from_file(str(ROOT / "apps/local_review.py")).run(timeout=20)
            self.assertFalse(app.exception)
            self.assertEqual(len(app.radio), 22)
            app.checkbox[0].uncheck().run(timeout=20)
            self.assertEqual(len(app.radio), 19)
