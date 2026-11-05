"""Tests for the non-recording Study 2 research artifact."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


class Study2GuideTests(unittest.TestCase):
    def test_sidebar_places_guide_below_recruitment_policy(self) -> None:
        source = (ROOT / "src" / "xai_as_closure" / "study2_app.py").read_text(
            encoding="utf-8"
        )
        policy = source.index('"View full recruitment policy"')
        guide = source.index('"View Study Guide"')
        candidate = source.index('"View candidate CV"')
        self.assertLess(policy, guide)
        self.assertLess(guide, candidate)
        self.assertIn('"?guide=true&view=tour"', source[guide : guide + 180])

    def test_guide_matches_the_administered_questionnaire(self) -> None:
        guide = (ROOT / "study_CHI" / "STUDY2_STUDY_GUIDE.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("PPBE_5", guide)
        self.assertIn("PPBE_4", guide)
        self.assertIn("Agency 4", guide)
        self.assertIn("PCE_3", guide)
        self.assertIn("Extremely unlikely", guide)
        self.assertIn("In a few words, what was the main reason", guide)
        self.assertIn("https://doi.org/10.1007/s12525-023-00640-9", guide)

    def test_all_condition_apps_open_the_tour_without_a_session(self) -> None:
        paths = sorted((ROOT / "apps").glob("study2_0*.py"))
        self.assertEqual(len(paths), 8)
        for path in paths:
            with self.subTest(app=path.name):
                app = AppTest.from_file(str(path), default_timeout=20)
                app.query_params = {"guide": "true"}
                app.run(timeout=20)
                self.assertFalse(app.exception)
                self.assertEqual(app.title[0].value, "Tour Guide")
                rendered = " ".join(element.value for element in app.markdown)
                self.assertIn("non-recording research artifact", rendered)
                self.assertNotIn("_study2_session", app.session_state.filtered_state)
                self.assertNotIn("_study2_demo_session", app.session_state.filtered_state)

    def test_all_condition_apps_open_an_in_memory_demo(self) -> None:
        paths = sorted((ROOT / "apps").glob("study2_0*.py"))
        self.assertEqual(len(paths), 8)
        for path in paths:
            with self.subTest(app=path.name):
                app = AppTest.from_file(str(path), default_timeout=20)
                app.query_params = {"guide": "true", "view": "demo"}
                app.run(timeout=20)
                self.assertFalse(app.exception)
                self.assertEqual(app.title[0].value, "Interactive Study Platform")
                state = app.session_state.filtered_state
                self.assertIn("_study2_demo_session", state)
                self.assertNotIn("_study2_session", state)
                self.assertNotIn("_study2_logger", state)
                self.assertTrue(
                    any(button.label == "Begin candidate screening" for button in app.button)
                )

    def test_demo_reaches_the_real_condition_assessment_without_saving(self) -> None:
        path = ROOT / "apps" / "study2_08_highP_highA_F.py"
        with patch("xai_as_closure.study2_app.save_to_github") as remote:
            app = AppTest.from_file(str(path), default_timeout=30)
            app.query_params = {"guide": "true", "view": "demo"}
            app.run(timeout=30)

            def click(label: str) -> None:
                next(button for button in app.button if button.label == label).click().run(
                    timeout=30
                )
                self.assertFalse(app.exception)

            click("Begin candidate screening")
            session = app.session_state.filtered_state["_study2_demo_session"]
            app.radio[0].set_value("Reject candidate")
            app.select_slider[0].set_value(50)
            click("Lock initial decision")
            app.text_area[0].set_value(
                "A current qualifying certification and current professional membership."
            )
            click("Confirm requirements and continue")
            request = next(
                button
                for button in app.button
                if "assess" in button.label.lower() and "back" not in button.label.lower()
            )
            click(request.label)
            self.assertEqual(session.phase, "aided")
            output = session.current_trial()["agent_output"]
            self.assertTrue(output["explanation_present"])
            self.assertTrue(output["rationale"])
            self.assertTrue(output["visible_sources"])
            self.assertTrue(
                any(block["citations"] for block in output["message_blocks"])
            )
            state = app.session_state.filtered_state
            self.assertNotIn("_study2_session", state)
            self.assertNotIn("_study2_logger", state)
            remote.assert_not_called()


if __name__ == "__main__":
    unittest.main()
