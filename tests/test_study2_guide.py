"""Tests for the non-recording Study 2 research artifact."""

from __future__ import annotations

import unittest
from pathlib import Path

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
        self.assertIn('"?guide=true"', source[guide : guide + 160])

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

    def test_all_condition_apps_open_the_guide_without_a_session(self) -> None:
        paths = sorted((ROOT / "apps").glob("study2_0*.py"))
        self.assertEqual(len(paths), 8)
        for path in paths:
            with self.subTest(app=path.name):
                app = AppTest.from_file(str(path), default_timeout=20)
                app.query_params = {"guide": "true"}
                app.run(timeout=20)
                self.assertFalse(app.exception)
                self.assertEqual(app.title[0].value, "Study Guide")
                rendered = " ".join(element.value for element in app.markdown)
                self.assertIn("non-recording research artifact", rendered)
                self.assertNotIn("_study2_session", app.session_state.filtered_state)


if __name__ == "__main__":
    unittest.main()
