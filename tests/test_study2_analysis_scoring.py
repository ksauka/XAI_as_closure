"""Decision-table checks for diagnostic scoring, including missing responses."""

import itertools
import unittest

from xai_as_closure.session_flatten import flatten_trial_rows, score_reliance


class DiagnosticScoringTests(unittest.TestCase):
    def test_complete_binary_decision_table(self):
        labels = ["Advance", "Reject"]
        for initial, final, ai, truth in itertools.product(labels, repeat=4):
            with self.subTest(initial=initial, final=final, ai=ai, truth=truth):
                row = score_reliance(initial, final, ai, truth)
                disagreement = initial != ai
                self.assertEqual(row["diagnostic_disagreement"], disagreement)
                self.assertEqual(
                    row["appropriate_reliance"],
                    final == truth if disagreement else None,
                )
                if not disagreement:
                    self.assertIsNone(row["correct_ai_reliance"])
                    self.assertIsNone(row["correct_self_reliance"])
                elif initial == truth:
                    self.assertEqual(row["correct_self_reliance"], final == truth)
                    self.assertEqual(row["overreliance"], final != truth)
                    self.assertIsNone(row["correct_ai_reliance"])
                else:
                    self.assertEqual(row["correct_ai_reliance"], final == truth)
                    self.assertEqual(row["underreliance"], final != truth)
                    self.assertIsNone(row["correct_self_reliance"])

    def test_flattened_agreement_and_missing_decisions_remain_unscored(self):
        archive = {
            "state": {
                "condition_id": "P0_A0_F0",
                "profile_order": ["C-01", "C-05"],
                "trials": {
                    "C-01": {
                        "unaided": {"decision": "Advance candidate to human interview"},
                        "aided": {"decision": "Advance candidate to human interview"},
                        "agent_output": {
                            "recommendation": "Advance candidate to human interview"
                        },
                    },
                    "C-05": {
                        "unaided": {"decision": "Reject candidate"},
                        "agent_output": {
                            "recommendation": "Advance candidate to human interview"
                        },
                    },
                },
            }
        }
        first, missing = flatten_trial_rows([archive])
        self.assertTrue(first["aided_correct"])
        self.assertFalse(first["diagnostic_disagreement"])
        self.assertIsNone(first["appropriate_reliance"])
        self.assertTrue(missing["diagnostic_disagreement"])
        self.assertIsNone(missing["aided_correct"])
        self.assertIsNone(missing["appropriate_reliance"])
        self.assertEqual(missing["decision_transition"], "")

    def test_missing_initial_is_not_a_diagnostic_opportunity(self):
        row = score_reliance("", "Advance", "Reject", "Advance")
        self.assertIsNone(row["diagnostic_disagreement"])
        self.assertIsNone(row["appropriate_reliance"])

    def test_missing_final_is_not_a_failure(self):
        row = score_reliance("Advance", "", "Reject", "Advance")
        self.assertTrue(row["diagnostic_disagreement"])
        self.assertIsNone(row["appropriate_reliance"])
        self.assertIsNone(row["overreliance"])

    def test_agreement_can_be_accurate_without_reliance_score(self):
        self.assertIsNone(
            score_reliance("Advance", "Advance", "Advance", "Advance")[
                "appropriate_reliance"
            ]
        )


if __name__ == "__main__":
    unittest.main()
