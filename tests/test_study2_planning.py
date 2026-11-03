"""Numerical and operational checks; all generated data are synthetic."""

import importlib.util
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    path = ROOT / "analysis" / "study2" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class PlanningTests(unittest.TestCase):
    def test_scale_reverse_missing_and_out_of_range(self):
        scorer = load("scale_scoring").score_scale
        spec = {
            "status": "frozen",
            "items": ["a", "b", "c", "d", "e"],
            "response_min": 1,
            "response_max": 7,
            "reverse_item_ids": ["b"],
        }
        self.assertEqual(scorer({"a": 1, "b": 1, "c": 7, "d": 5}, spec), 5)
        self.assertIsNone(scorer({"a": 1, "b": 1, "c": 7}, spec))
        with self.assertRaises(ValueError):
            scorer({"a": 8}, spec)
        with self.assertRaises(ValueError):
            scorer({}, dict(spec, status="unverified_items"))

    def test_timing_requires_all_cells_and_uses_slowest_cell(self):
        derive = load("pilot_timing").derive_timing
        rows = []
        for p in (0, 1):
            for a in (0, 1):
                for f in (0, 1):
                    for i in range(5):
                        rows.append(
                            {
                                "session_id": f"{p}{a}{f}{i}",
                                "condition_id": f"P{p}_A{a}_F{f}",
                                "complete": True,
                                "total_duration_seconds": 600 if f else 300,
                            }
                        )
        self.assertEqual(derive(rows)["soft_allowance_seconds"], 780)
        with self.assertRaises(ValueError):
            derive(rows[:5])

    def test_simulation_reproducible_and_matches_fixed_case_design(self):
        m = load("simulate_precision")
        scenario = json.loads((ROOT / "analysis/study2/scenarios.json").read_text())[
            "scenarios"
        ][1]
        first = m.simulate(400, scenario, np.random.default_rng(4))
        second = m.simulate(400, scenario, np.random.default_rng(4))
        for a, b in zip(first[:4], second[:4]):
            np.testing.assert_array_equal(a, b)
        x, y, mask, _, counts = first
        self.assertEqual(x.shape, (400, 6, 11))
        self.assertEqual(
            counts["diagnostic_trials"],
            counts["ai_reliance_opportunities"] + counts["self_reliance_opportunities"],
        )
        np.testing.assert_equal(x[:, :, 6:].sum(axis=1), np.ones((400, 5)))
        fit20 = m.fit_glmm(x, y, mask, 20)
        fit40 = m.fit_glmm(x, y, mask, 40)
        self.assertEqual(fit20["status"], "ok")
        self.assertEqual(fit40["status"], "ok")
        np.testing.assert_allclose(fit20["beta"], fit40["beta"], atol=0.01)
        np.testing.assert_allclose(fit20["se"], fit40["se"], atol=0.01)

    def test_coding_subset_is_stratified_blind_and_order_invariant(self):
        select = load("coding_subset").select_subset
        rows = [
            {
                "session_id": str(i),
                "reference": f"C-0{j}",
                "condition_id": "P1_A1_F1",
                "aided_correct": True,
                "evidence_recall": "example",
            }
            for i in range(100)
            for j in range(1, 7)
        ]
        subset = select(rows)
        self.assertEqual(len(subset), 150)
        self.assertEqual(subset, select(list(reversed(rows))))
        self.assertNotIn("condition_id", subset[0])
        self.assertNotIn("aided_correct", subset[0])
        self.assertNotIn("session_id", subset[0])
        with self.assertRaises(ValueError):
            select(rows + [rows[0]])

    def test_holm_adjustment(self):
        fn = load("simulate_precision").holm_rejections
        self.assertEqual(fn(0.03, 0.04), (False, False))
        self.assertEqual(fn(0.01, 0.04), (True, True))
        self.assertEqual(fn(0.06, 0.01), (False, True))

    def test_unfinalised_instrument_cannot_pass_readiness(self):
        spec = json.loads((ROOT / "study_CHI/STUDY2_OPERATIONAL_SPEC.json").read_text())
        spec["questionnaire"]["survey_export_sha256"] = None
        self.assertTrue(load("readiness").unresolved(spec))


if __name__ == "__main__":
    unittest.main()
