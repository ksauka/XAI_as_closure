"""Checks that smaller-N planning preserves the design and the target coefficients."""
import importlib.util
import json
from pathlib import Path
import unittest
import warnings
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    path = ROOT / 'analysis/study2' / (name + '.py')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BudgetPlanningTests(unittest.TestCase):
    def setUp(self):
        self.simulator = load('simulate_precision')
        self.compare = load('compare_budget_precision')
        self.scenario = json.loads((ROOT / 'analysis/study2/scenarios.json').read_text())['scenarios'][1]

    def test_profile_endpoint_probabilities_are_preserved_without_warnings(self):
        scenario = dict(self.scenario, profile_disagreement_probabilities=[0,1,0,1,0,1], opportunity_random_intercept_slope=.5)
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            x, y, mask, _, counts = self.simulator.simulate(200, scenario, np.random.default_rng(11))
        profiles = self.compare.profile_indices(x)
        np.testing.assert_array_equal(mask, np.isin(profiles, [1,3,5]))
        with self.assertRaises(ValueError):
            self.simulator.simulate(200, dict(scenario, profile_disagreement_probabilities=[.5]*5), np.random.default_rng(1))

    def test_nested_panels_remain_balanced_in_all_eight_cells(self):
        x, y, mask, _, _ = self.simulator.simulate(200, self.scenario, np.random.default_rng(12))
        selections = [self.compare.balanced_subset(x,n) for n in (160,192,200)]
        for n, selected in zip((160,192,200), selections):
            cells = x[selected,0,1:4]
            _, counts = np.unique(cells, axis=0, return_counts=True)
            np.testing.assert_array_equal(counts, np.full(8,n//8))
            result = self.compare.count_opportunities(x[selected],mask[selected])
            self.assertEqual(result['diagnostic_trials'], result['ai_reliance_opportunities'] + result['self_reliance_opportunities'])
            self.assertEqual(result['diagnostic_trials'], sum(result['profile_opportunities']))
            self.assertEqual(result['diagnostic_trials'], np.array(result['cell_profile_opportunities']).sum())
        self.assertTrue(set(selections[0]).issubset(selections[1]))
        self.assertTrue(set(selections[1]).issubset(selections[2]))

    def test_absent_reference_is_a_reparameterisation_not_treatment_removal(self):
        x, y, mask, _, _ = self.simulator.simulate(200, self.scenario, np.random.default_rng(13))
        mask &= self.compare.profile_indices(x) != 0
        auto = self.simulator.fit_glmm(x,y,mask,40)
        manual = self.simulator.fit_glmm(x[:,:,[0,1,2,3,4,5,7,8,9,10]],y,mask,40)
        self.assertEqual(auto['status'], 'ok')
        self.assertEqual(manual['status'], 'ok')
        self.assertEqual(auto['profile_reference'], 2)
        self.assertEqual(auto['unobserved_profiles'], [1])
        self.assertIsNone(auto['beta'][6])
        np.testing.assert_allclose(auto['beta'][:6], manual['beta'][:6], atol=1e-8)
        np.testing.assert_allclose(auto['se'][:6], manual['se'][:6], atol=1e-8)
        self.assertTrue(set(range(6)).issubset(auto['active_columns']))

    def test_absent_nonreference_does_not_leave_a_zero_design_column(self):
        x, y, mask, _, _ = self.simulator.simulate(200, self.scenario, np.random.default_rng(14))
        mask &= self.compare.profile_indices(x) != 3
        result = self.simulator.fit_glmm(x,y,mask,40)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['profile_reference'], 1)
        self.assertEqual(result['unobserved_profiles'], [4])
        self.assertIsNone(result['beta'][8])


if __name__ == '__main__':
    unittest.main()
