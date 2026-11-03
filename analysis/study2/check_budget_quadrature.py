"""Preselected 40/80-node numerical check, separate from planning evidence."""
import argparse
import importlib.util
import json
from pathlib import Path
import numpy as np

spec = importlib.util.spec_from_file_location('budget', Path(__file__).with_name('compare_budget_precision.py'))
budget = importlib.util.module_from_spec(spec)
spec.loader.exec_module(budget)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    chosen = {'legacy_sparse', 'historical_profile_anchor', 'historical_profile_high_dependence',
              'historical_profile_baseline_80', 'historical_profile_informative_opportunities'}
    rows = []
    for index, scenario in enumerate(config['scenarios']):
        if scenario['name'] not in chosen:
            continue
        for repetition in range(20):
            rng = np.random.default_rng(np.random.SeedSequence([config['seed'], index, repetition]))
            x,y,mask,truth,_ = budget.planner.simulate(200, scenario, rng)
            for n in (160,200):
                selected = budget.balanced_subset(x,n)
                fits = [budget.planner.fit_glmm(x[selected], y[selected], mask[selected], k) for k in (40,80)]
                row = dict(scenario=scenario['name'], repetition=repetition, n=n,
                           statuses=[f['status'] for f in fits])
                if all(f['status']=='ok' for f in fits):
                    row['max_abs_core_beta_difference'] = float(np.max(np.abs(np.array(fits[0]['beta'][:6])-np.array(fits[1]['beta'][:6]))))
                    row['max_abs_core_se_difference'] = float(np.max(np.abs(np.array(fits[0]['se'][:6])-np.array(fits[1]['se'][:6]))))
                    row['h2_relative_se_difference'] = abs(fits[0]['se'][4]/fits[1]['se'][4]-1)
                    row['sigmas'] = [f['sigma'] for f in fits]
                rows.append(row)
        print(scenario['name'] + ' checked', flush=True)
    comparable = [r for r in rows if 'max_abs_core_beta_difference' in r]
    result = dict(kind='numerical_check_not_observed_data', seed=config['seed'],
                  design='First 20 panels in each of five preselected scenarios; N=160 and 200; 40 versus 80 quadrature nodes.',
                  predeclared_tolerance=dict(max_abs_core_beta_difference=.01, max_abs_core_se_difference=.01, h2_relative_se_difference=.005),
                  comparisons=len(rows), paired_successes=len(comparable),
                  status_disagreements=sum(r['statuses'][0]!=r['statuses'][1] for r in rows),
                  maxima={k:max(r[k] for r in comparable) for k in ('max_abs_core_beta_difference','max_abs_core_se_difference','h2_relative_se_difference')},
                  rows=rows)
    result['within_tolerance'] = result['status_disagreements']==0 and all(result['maxima'][k] <= v for k,v in result['predeclared_tolerance'].items())
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}),flush=True)

if __name__=='__main__':
    main()
