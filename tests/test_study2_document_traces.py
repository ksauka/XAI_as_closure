"""Export checks for document-specific elapsed intervals and phase transitions."""

import unittest

from xai_as_closure.session_flatten import flatten_trial_rows


class DocumentTraceTests(unittest.TestCase):
    def row(self, events):
        return flatten_trial_rows([{
            "state": {"condition_id": "P1_A0_F0", "profile_order": ["C-05"],
                      "trials": {"C-05": {}}},
            "events": events,
        }])[0]

    def events(self, visits):
        events = []
        for document, phase, duration in visits:
            visit = str(len(events))
            for kind in ("document_opened", "document_closed"):
                if kind == "document_closed" and duration is None:
                    continue
                events.append({
                    "event_sequence": len(events) + 1,
                    "trial_reference": "C-05", "phase": phase,
                    "event_type": kind,
                    "payload": {"document": document, "document_visit_id": visit,
                                "dwell_seconds": duration},
                })
        return events

    def test_document_totals_and_transitions_are_separate_by_phase(self):
        row = self.row(self.events([
            ("cv", "unaided", 5), ("role", "forcing", 3),
            ("role", "aided", 2), ("policy", "aided", 4),
            ("policy", "aided", 1), ("cv", "aided", 6),
        ]))
        self.assertEqual(row["cv_document_dwell_seconds"], 11)
        self.assertEqual(row["role_document_dwell_seconds"], 5)
        self.assertEqual(row["policy_document_dwell_seconds"], 5)
        self.assertEqual(row["before_advice_document_transition_count"], 1)
        self.assertEqual(row["after_advice_document_transition_count"], 2)
        self.assertEqual(row["after_advice_cv_document_dwell_seconds"], 6)

    def test_unclosed_visit_is_missing_not_zero(self):
        row = self.row(self.events([("policy", "aided", None)]))
        self.assertIsNone(row["policy_document_dwell_seconds"])
        self.assertEqual(row["policy_document_incomplete_visit_count"], 1)
        self.assertEqual(row["cv_document_dwell_seconds"], 0)

    def test_absent_event_history_does_not_imply_nonuse(self):
        row = self.row([])
        self.assertIsNone(row["cv_document_open_count"])
        self.assertIsNone(row["document_transition_count"])

    def test_export_uses_recorded_order_and_does_not_count_reopens_as_transitions(self):
        events = self.events([("cv", "aided", 2), ("cv", "aided", 3),
                              ("policy", "aided", 4)])
        row = self.row(list(reversed(events)))
        self.assertEqual(row["after_advice_document_transition_count"], 1)
        self.assertEqual(row["after_advice_cv_document_dwell_seconds"], 5)

    def test_document_fields_survive_csv_export(self):
        import csv
        import tempfile
        from pathlib import Path
        from xai_as_closure.session_flatten import write_csv

        row = self.row(self.events([("cv", "aided", 2.5), ("policy", "aided", 4)]))
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "trials.csv"
            write_csv([row], target, list(row))
            with target.open() as handle:
                exported = next(csv.DictReader(handle))
        self.assertEqual(exported["after_advice_cv_document_dwell_seconds"], "2.5")
        self.assertEqual(exported["after_advice_document_transition_count"], "1")

    def test_optional_candidate_open_retains_trial_identity(self):
        from types import SimpleNamespace
        from unittest.mock import MagicMock, patch
        from xai_as_closure.study2_app import _open_reference_document

        for step, expected in (("complete", "C-05"), ("brief", None)):
            with self.subTest(introduction_step=step):
                fake_st = MagicMock()
                fake_st.session_state = {"_study2_session": SimpleNamespace(
                    state={"introduction_step": step}, current_reference=lambda: "C-05"
                )}
                with (
                    patch("xai_as_closure.study2_app.st", fake_st),
                    patch("xai_as_closure.study2_app._log") as log,
                    patch("xai_as_closure.study2_app._sync_github"),
                ):
                    _open_reference_document("cv", "sidebar_source_documents")
                self.assertEqual(log.call_args.kwargs["reference"], expected)
                self.assertEqual(log.call_args.kwargs["payload"]["document"], "cv")
                self.assertTrue(log.call_args.kwargs["payload"]["document_visit_id"])


if __name__ == "__main__":
    unittest.main()
