"""Tests for the non-recording Study 1 research artifact."""

from __future__ import annotations

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


class Study1GuideTests(unittest.TestCase):
    def test_guide_documents_all_profiles_and_rounds(self) -> None:
        guide = (ROOT / "study_CHI" / "STUDY1_STUDY_GUIDE.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("all six profiles", guide)
        self.assertIn("focused assessment covered C-05 and C-06 only", guide)
        self.assertIn("No AI recommendation", guide)

    def test_public_guide_opens_without_a_participant_session(self) -> None:
        app = AppTest.from_file(
            str(ROOT / "apps" / "study1_validation_v2.py"),
            default_timeout=30,
        )
        app.query_params = {"guide": "true"}
        app.run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.title[0].value, "Study 1 Guide")
        rendered = " ".join(element.value for element in app.markdown)
        self.assertIn("non-recording research artifact", rendered)
        for reference in ("C-01", "C-02", "C-03", "C-04", "C-05", "C-06"):
            self.assertIn(reference, [tab.label for tab in app.tabs])
        self.assertNotIn("_study1_session", app.session_state.filtered_state)


if __name__ == "__main__":
    unittest.main()

