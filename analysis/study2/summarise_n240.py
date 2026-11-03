"""N=240 extension of the completed budget comparison; all data synthetic."""
from pathlib import Path
import argparse
import csv
import hashlib
import importlib.util
import json
import zipfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

parser=argparse.ArgumentParser()
parser.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2])
parser.add_argument('--output-dir',type=Path)
args=parser.parse_args()
ROOT=args.repo_root.resolve();BASE=ROOT/'analysis/study2/budget_2026-11-03'
DEST=args.output_dir or BASE/'n240_report';DEST.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('budget',ROOT/'analysis/study2/compare_budget_precision.py')
budget=importlib.util.module_from_spec(spec);spec.loader.exec_module(budget)

def pct(v):return f'{100*v:.1f}%'
def interval(s,key):
    a,b=s[key+'_mc_interval95']
    return f'{pct(s[key+"_rejection_rate"])} ({100*a:.1f}–{100*b:.1f}%)'

def main():
    original=json.loads((BASE/'comparison_results.json').read_text())
    previous={(s['scenario'],s['n']):s for s in original['summaries']}
    output=[];diagnostics=[]
    paths=[BASE/'n240_500_q40',BASE/'n240_supplement_500_q40']
    for folder in paths:
        results=json.loads((folder/'results.json').read_text())
        for name,sha in results['source_hashes'].items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha
        config=results['config']
        for index,scenario in enumerate(config['scenarios']):
            records=json.loads((folder/'replicates'/(scenario['name']+'.json')).read_text())['replicates']
            strict=[];constant=0
            for row in records:
                rng=np.random.default_rng(np.random.SeedSequence([config['seed'],index,row['repetition']]))
                x,y,mask,truth,_=budget.planner.simulate(240,scenario,rng)
                assert row['diagnostic_trials']==int(mask.sum())
                cells=((x[:,0,1]+.5)*4+(x[:,0,2]+.5)*2+x[:,0,3]+.5).astype(int)
                assert all((cells==k).sum()==30 for k in range(8))
                profile=budget.profile_indices(x)
                separated=[]
                for p in range(6):
                    yy=y[mask&(profile==p)]
                    if len(yy) and len(np.unique(yy))==1:separated.append(p+1)
                constant+=bool(separated)
                if separated:diagnostics.append(dict(scenario=scenario['name'],rep=row['repetition'],profiles=separated,status=row['status']))
                if not separated and row['status']=='ok':strict.append(row)
            summary=dict(next(s for s in results['summaries'] if s['scenario']==scenario['name']))
            summary.update(profile_constant_outcome_panels=constant,strict_successful=len(strict),
                           strict_unusable_rate=1-len(strict)/500,
                           h1_strict_positive_power=sum(r['h1_positive_reject'] for r in strict)/500,
                           h3_strict_positive_power=sum(r['h3_positive_reject'] for r in strict)/500,
                           both_positive_holm_rate=sum(r.get('h1_positive_reject',False) and r.get('h3_positive_reject',False) for r in records)/500,
                           scenario_rationale=scenario['rationale'],explanation_or=scenario['explanation_or'],forcing_or=scenario['forcing_or'])
            output.append(summary)
    lookup={(s['scenario'],s['n']):s for s in output}
    result={'kind':'N240_simulation_extension_not_observed_data','fits_attempted':10500,'scenarios':21,'repetitions':500,
            'comparison':'N240 panels are not nested in the saved N200 panels; comparisons are point estimates with their individual Monte Carlo intervals, not paired incremental estimates.',
            'previous_comparison_sha256':hashlib.sha256((BASE/'comparison_results.json').read_bytes()).hexdigest(),
            'summaries':output,'constant_profile_diagnostics':diagnostics,
            'prior_N200_summaries':[s for s in original['summaries'] if s['n']==200]}
    (DEST/'N240_results.json').write_text(json.dumps(result,indent=2)+'\n')
    fields=['scenario','n','explanation_or','forcing_or','h1_positive_holm_rejection_rate','h3_positive_holm_rejection_rate',
            'h1_positive_holm_mc_interval95','h3_positive_holm_mc_interval95','both_positive_holm_rate',
            'h2_median_log_ci_width','h2_median_ci_multiplicative_half_span','h2_coverage_successful_fits','successful',
            'mean_ai_reliance_opportunities','mean_self_reliance_opportunities','profile_constant_outcome_panels',
            'strict_unusable_rate','h1_strict_positive_power','h3_strict_positive_power']
    with (DEST/'N200_N240_comparison.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader()
        for s in output:
            for row in (previous[(s['scenario'],200)],s):
                w.writerow({k:json.dumps(row[k]) if isinstance(row.get(k),(list,dict)) else row.get(k) for k in fields})
    lines=['# Study 2: N=240 extension','',
      'Completed on 3 November 2026. N=240 means 240 analysable main-study participants, 30 in each of eight cells. The separate 40-person technical pilot brings the minimum to 280 participant sessions, before replacements and expert validation. If 240 is the total session budget including that pilot, the main target would instead be N=200.','',
      'All 21 previously reported sensitivity scenarios were retained, with 500 datasets each, adding 10,500 model fits. The planned primary model and Holm family are unchanged. Original N=200 results are preserved. N=240 panels are not nested in those N=200 panels, so the difference between point estimates is not reported as a paired gain.','',
      '## Central scenario','',
      'Both main-effect ORs are assumed to be 1.5, the interaction OR is .67, conditional baseline appropriate reliance is .65, participant random-intercept SD is .75, and opportunity probabilities are .25 for each correct-AI profile and .60 for each incorrect-AI profile. All are planning assumptions.','',
      '| Main N | Per cell | H1 power, 95% Monte Carlo interval | H3 power, 95% Monte Carlo interval | Both detected | H2 median log-CI width |',
      '|---:|---:|---:|---:|---:|---:|']
    for n in (200,240):
        s=previous[('legacy_central',n)] if n==200 else lookup[('legacy_central',n)]
        lines.append(f'| {n} | {n//8} | {interval(s,"h1_positive_holm")} | {interval(s,"h3_positive_holm")} | {pct(s["both_positive_holm_rate"])} | {s["h2_median_log_ci_width"]:.3f} |')
    c=lookup[('legacy_central',240)];old=previous[('legacy_central',200)]
    lines+=['',f'The N=240 central median H2 interval half-span is ×/÷{c["h2_median_ci_multiplicative_half_span"]:.2f} around the estimated interaction odds ratio. Median log-CI width is {100*(1-c["h2_median_log_ci_width"]/old["h2_median_log_ci_width"]):.1f}% smaller than in the saved N=200 run. No substantively acceptable H2 width has been fixed.','',
      '## Sensitivity comparisons','',
      '| Scenario | N | H1 power | H3 power | H2 median log-CI width | Failed fits |',
      '|---|---:|---:|---:|---:|---:|']
    selected=['legacy_sparse','legacy_dense','historical_profile_anchor','historical_profile_main_or_2',
              'historical_profile_high_dependence','v6_round2_smoothed_anchor','v7_C05_recoverability_85_assumption']
    for name in selected:
        for n in (200,240):
            s=previous[(name,n)] if n==200 else lookup[(name,n)]
            lines.append(f'| {name} | {n} | {pct(s["h1_positive_holm_rejection_rate"])} | {pct(s["h3_positive_holm_rejection_rate"])} | {s["h2_median_log_ci_width"]:.3f} | {500-s["successful"]}/500 |')
    lines+=['',
      'H1 and H3 use two-sided Holm adjustment within familywise alpha .05; detection requires the predicted positive direction. H2 remains a focal estimation target outside Holm. Failed fits count as non-detections. Interval widths and coverage are conditional on successful fits. The stricter finite-profile diagnostic, exported separately, also flags profiles whose diagnostic outcomes are all identical. The existing 40/80-node checks and their limitations remain applicable; no new claim of exact small-sample calibration is made.','',
      'With 500 repetitions the maximum Monte Carlo standard error is 2.24 percentage points. The intervals quantify simulation error, not uncertainty about the actual treatment effects or disagreement rates. The initial and v6 expert patterns remain sensitivities from different samples and earlier materials. Neither has validated the current v7 C-05 profile. The .85 recovery scenario is an assumption, not a new expert finding.','',
      '## Planning implication','',
      'N=240 supplies 20% more main-study participants than N=200 and improves precision. It does not by itself establish adequate power. The same unresolved decisions remain: the smallest substantively important H1/H3 effects, the largest acceptable H2 width, and plausible opportunity/dependence bounds informed by the focused assessment and separate technical pilot. No recruitment target or confirmatory status has been changed.','',
      '- `N200_N240_comparison.csv`: all 21 scenarios at both sample sizes.','- `N240_results.json`: summaries, intervals and finite-profile diagnostics.','- `N240_reproducibility.zip`: source, configurations, metadata and every raw synthetic replicate for this extension. No participant records.']
    report='\n'.join(lines)+'\n';(DEST/'Study2_N240_Comparison.md').write_text(report)
    for name in ('N240_results.json','N200_N240_comparison.csv','Study2_N240_Comparison.md'):
        (BASE/name).write_bytes((DEST/name).read_bytes())
    fig,axes=plt.subplots(1,2,figsize=(8.2,3.5),layout='constrained')
    for name,label,colour in [('legacy_central','Central','#0072B2'),('legacy_dense','Dense','#009E73'),('v6_round2_smoothed_anchor','V6 expert sensitivity','#CC79A7')]:
        ss=[previous[(name,n)] for n in (160,192,200)]+[lookup[(name,240)]]
        for ax,key in zip(axes,['h1_positive_holm_rejection_rate','h3_positive_holm_rejection_rate']):
            ax.plot([160,192,200,240],[100*s[key] for s in ss],marker='o',label=label,color=colour)
    for ax,title in zip(axes,['H1: explanation','H3: cognitive forcing']):
        ax.set(title=title,xlabel='Analysable main-study N',ylabel='Holm-adjusted power (%)',ylim=(0,100));ax.set_xticks([160,200,240]);ax.grid(alpha=.2);ax.axhline(80,color='black',lw=.8,ls=':')
    fig.legend(*axes[0].get_legend_handles_labels(),loc='outside lower center',ncol=3,fontsize=8)
    fig.suptitle('Illustrative main-effect OR=1.5; 500 datasets per setting')
    fig.savefig(DEST/'N240_power_comparison.png',dpi=180);fig.savefig(DEST/'N240_power_comparison.pdf');plt.close(fig)
    with zipfile.ZipFile(DEST/'N240_reproducibility.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in (ROOT/'analysis/study2/simulate_precision.py',ROOT/'analysis/study2/compare_budget_precision.py',BASE/'n240_scenarios.json',BASE/'n240_supplement_scenarios.json'):
            z.write(p,str(p.relative_to(ROOT)))
        for folder in paths:
            for p in folder.rglob('*.json'):z.write(p,str(p.relative_to(ROOT)))
        z.write(Path(__file__),'analysis/study2/summarise_n240.py')
    print(json.dumps({'fits':10500,'scenarios':21,'central':{k:c[k] for k in ('h1_positive_holm_rejection_rate','h3_positive_holm_rejection_rate','h2_median_log_ci_width')},'report_words':len(report.split())}))

if __name__=='__main__':main()
