"""Locate the earlier blanket quadrature-check discrepancy without rewriting it."""
from pathlib import Path
import importlib.util
import json
import os
import numpy as np

root=Path(os.environ.get('FACCT_REPO_ROOT',str(Path(__file__).resolve().parents[2])))
folder=root/'analysis/study2'
spec=importlib.util.spec_from_file_location('budget',folder/'compare_budget_precision.py')
budget=importlib.util.module_from_spec(spec);spec.loader.exec_module(budget)
base=folder/'budget_2026-11-03'
config=json.loads((base/'scenarios.json').read_text())
chosen={'legacy_sparse','legacy_central','legacy_dense','historical_profile_anchor',
        'historical_profile_high_dependence','historical_profile_baseline_80',
        'historical_profile_informative_opportunities'}
rows=[]
for index,scenario in enumerate(config['scenarios']):
    if scenario['name'] not in chosen: continue
    for rep in range(20):
        rng=np.random.default_rng(np.random.SeedSequence([config['seed'],index,rep]))
        x,y,mask,truth,_=budget.planner.simulate(200,scenario,rng)
        for n in (160,200):
            selected=budget.balanced_subset(x,n); xx=x[selected];yy=y[selected];mm=mask[selected]
            profile=budget.profile_indices(xx)
            separated=[]
            for p in range(6):
                outcomes=yy[mm&(profile==p)]
                if len(outcomes) and len(np.unique(outcomes))==1: separated.append(p+1)
            fits=[budget.planner.fit_glmm(xx,yy,mm,q) for q in (40,80)]
            row={'scenario':scenario['name'],'n':n,'rep':rep,'statuses':[f['status'] for f in fits],
                 'profiles_with_only_one_outcome':separated}
            if all(f['status']=='ok' for f in fits):
                a,b=fits
                row.update(beta_difference=(np.array(a['beta'][:6])-np.array(b['beta'][:6])).tolist(),
                           se_difference=(np.array(a['se'][:6])-np.array(b['se'][:6])).tolist(),
                           betas40=a['beta'][:6],ses40=a['se'][:6],
                           h2_relative_se_difference=abs(a['se'][4]/b['se'][4]-1))
            rows.append(row)
    print(scenario['name']+' diagnosed',flush=True)
ok=[r for r in rows if 'beta_difference' in r]
clean=[r for r in ok if not r['profiles_with_only_one_outcome']]
def maximum(rs,key,cols):
    return max(abs(r[key][i]) for r in rs for i in cols)
summary={
 'kind':'follow_up_numerical_diagnostic_not_a_replacement_for_the_original_failed_check',
 'seed':config['seed'],'panels':'First 20 replicates in each of seven scenarios, N160 and N200.',
 'comparisons':len(rows),'paired_successes':len(ok),'status_disagreements':sum(r['statuses'][0]!=r['statuses'][1] for r in rows),
 'core_parameter_order':budget.planner.NAMES[:6],
 'max_abs_beta_difference_by_parameter':{k:maximum(ok,'beta_difference',[i]) for i,k in enumerate(budget.planner.NAMES[:6])},
 'max_abs_se_difference_by_parameter':{k:maximum(ok,'se_difference',[i]) for i,k in enumerate(budget.planner.NAMES[:6])},
 'max_abs_H1_H3_H2_beta_difference':maximum(ok,'beta_difference',[1,3,4]),
 'max_abs_H1_H3_H2_se_difference':maximum(ok,'se_difference',[1,3,4]),
 'max_abs_H2_relative_se_difference':max(r['h2_relative_se_difference'] for r in ok),
 'no_constant_profile_outcome_paired_successes':len(clean),
 'no_constant_profile_outcome_max_abs_core_beta_difference':maximum(clean,'beta_difference',range(6)),
 'no_constant_profile_outcome_max_abs_core_se_difference':maximum(clean,'se_difference',range(6)),
 'note':'A profile with observations all equal to zero or all equal to one can have a diverging fixed-effect parameter. This is distinct from an absent profile, which needs a contrast-reference change only. Stable treatment contrasts alone do not certify a finite nuisance-parameter MLE.',
 'rows':rows}
(base/'quadrature_follow_up.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='rows'}),flush=True)
