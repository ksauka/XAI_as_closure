"""Summarise every saved planning scenario and audit finite-profile estimation."""
from pathlib import Path
import argparse
import csv
import hashlib
import importlib.util
import json
import math
import zipfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

parser=argparse.ArgumentParser()
parser.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2])
parser.add_argument('--output-dir',type=Path)
options=parser.parse_args()
ROOT=options.repo_root.resolve()
BASE=ROOT/'analysis/study2/budget_2026-11-03'
DEST=options.output_dir or BASE/'report'
DEST.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('budget',ROOT/'analysis/study2/compare_budget_precision.py')
budget=importlib.util.module_from_spec(spec);spec.loader.exec_module(budget)

def percent(p):return f'{100*p:.1f}%'
def power_with_interval(s,key):
    a,b=s[key+'_mc_interval95']
    return f'{percent(s[key+"_rejection_rate"])} ({100*a:.1f}–{100*b:.1f})'

def main():
    run_paths=[BASE/'run_500_q40',BASE/'supplement_500_q40']
    datasets=[json.loads((p/'results.json').read_text()) for p in run_paths]
    for d in datasets:
        for name,sha in d['source_hashes'].items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha
    all_rows=[];diagnostics=[]
    for path,dataset in zip(run_paths,datasets):
        config=dataset['config']
        summaries={(s['scenario'],s['n']):s for s in dataset['summaries']}
        for index,scenario in enumerate(config['scenarios']):
            records=json.loads((path/'replicates'/(scenario['name']+'.json')).read_text())['replicates']
            rows={(r['repetition'],r['n']):r for r in records}
            for rep in range(config['repetitions']):
                rng=np.random.default_rng(np.random.SeedSequence([config['seed'],index,rep]))
                x,y,mask,truth,_=budget.planner.simulate(200,scenario,rng)
                for n in config['sample_sizes']:
                    select=budget.balanced_subset(x,n);xx=x[select];yy=y[select];mm=mask[select]
                    profile=budget.profile_indices(xx)
                    r=rows[(rep,n)]
                    assert r['diagnostic_trials']==int(mm.sum())
                    r['constant_outcome_profiles']=[]
                    for p in range(6):
                        values=yy[mm&(profile==p)]
                        if len(values) and len(np.unique(values))==1:
                            r['constant_outcome_profiles'].append(p+1)
            for n in config['sample_sizes']:
                group=[r for r in records if r['n']==n]
                strict=[r for r in group if r['status']=='ok' and not r['constant_outcome_profiles']]
                s=dict(summaries[(scenario['name'],n)])
                s.update(run=path.name,explanation_or=scenario['explanation_or'],forcing_or=scenario['forcing_or'],
                         interaction_or=scenario['interaction_or'],baseline=scenario['baseline_appropriate_probability'],
                         random_intercept_sd=scenario['random_intercept_sd'],scenario_rationale=scenario['rationale'],
                         profile_constant_outcome_panels=sum(bool(r['constant_outcome_profiles']) for r in group),
                         strict_finite_profile_successes=len(strict),strict_unusable_rate=1-len(strict)/len(group),
                         original_fit_failure_rate=1-s['successful']/s['attempted'])
                for label in ('h1','h3'):
                    k=sum(r[label+'_positive_reject'] for r in strict)
                    s[label+'_strict_positive_power']=k/len(group)
                    s[label+'_strict_mc_interval95']=budget.rate_interval(k,len(group))
                    s[label+'_if_all_unusable_detected']=(k+len(group)-len(strict))/len(group)
                s['both_positive_holm_rate']=sum(r.get('h1_positive_reject',False) and r.get('h3_positive_reject',False) for r in group)/len(group)
                s['both_positive_holm_strict_rate']=sum(r['h1_positive_reject'] and r['h3_positive_reject'] for r in strict)/len(group)
                s['h2_strict_median_log_ci_width']=float(np.median([r['h2_log_ci_width'] for r in strict])) if strict else None
                s['h2_strict_coverage']=float(np.mean([r['h2_covered'] for r in strict])) if strict else None
                diagnostics.append({'scenario':scenario['name'],'n':n,'constant_outcome_panels':s['profile_constant_outcome_panels'],
                                    'strict_successful':len(strict),'replicate_constant_profiles':[{'rep':r['repetition'],'profiles':r['constant_outcome_profiles'],'fit_status':r['status']} for r in group if r['constant_outcome_profiles']]})
                all_rows.append(s)
    lookup={(s['scenario'],s['n']):s for s in all_rows}
    combined={'kind':'simulation_planning_not_Study2_findings','original_model_unchanged':True,
              'total_simulated_model_fits':sum(len(d['summaries'])*d['config']['repetitions'] for d in datasets),
              'original_scenarios':15,'additional_scenarios':6,'repetitions_per_configuration':500,
              'numerical_check':json.loads((BASE/'quadrature_follow_up.json').read_text()),
              'summaries':all_rows,'paired_comparisons':[c for d in datasets for c in d['paired_comparisons']],
              'finite_profile_diagnostics':diagnostics,
              'strict_note':'Post-run sensitivity, not a change to the primary analysis plan. Treat any profile with at least one diagnostic trial and all outcomes identical as not having an ordinary finite profile-effect MLE. Such replicates and other failed fits count as non-detections. No observations are silently deleted and no penalised estimator is substituted.'}
    (DEST/'comparison_results.json').write_text(json.dumps(combined,indent=2,allow_nan=False)+'\n')
    fields=['scenario','n','explanation_or','forcing_or','interaction_or','mean_diagnostic_trials',
            'mean_ai_reliance_opportunities','mean_self_reliance_opportunities','mean_participants_without_opportunities',
            'h1_positive_holm_rejection_rate','h3_positive_holm_rejection_rate','both_positive_holm_rate',
            'h1_positive_holm_mc_se','h3_positive_holm_mc_se','h1_positive_holm_mc_interval95','h3_positive_holm_mc_interval95',
            'h2_median_log_ci_width','h2_median_ci_multiplicative_half_span','h2_coverage_successful_fits',
            'h2_mean_bias','original_fit_failure_rate','profile_constant_outcome_panels','strict_unusable_rate',
            'h1_strict_positive_power','h3_strict_positive_power','h2_strict_median_log_ci_width','h2_strict_coverage',
            'zero_variance_boundaries','scenario_rationale']
    with (DEST/'all_scenarios.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader()
        for s in all_rows:
            writer.writerow({k:json.dumps(s[k]) if isinstance(s.get(k),(list,dict)) else s.get(k) for k in fields})
    # Scientific figure: every curve uses illustrative main OR=1.5.
    plots=[('legacy_sparse','Sparse'),('legacy_central','Central'),('legacy_dense','Dense'),
           ('historical_profile_anchor','Initial experts: sensitivity'),('v6_round2_smoothed_anchor','V6 experts: sensitivity')]
    fig,axes=plt.subplots(2,2,figsize=(10,7.3),layout='constrained')
    colours=['#666666','#0072B2','#009E73','#D55E00','#CC79A7']
    for (scenario,label),colour in zip(plots,colours):
        ss=[lookup[(scenario,n)] for n in (160,192,200)]
        for ax,key in zip(axes.flat,['h1_positive_holm_rejection_rate','h3_positive_holm_rejection_rate','h2_median_log_ci_width','strict_unusable_rate']):
            ax.plot([160,192,200],[s[key]*(100 if key!='h2_median_log_ci_width' else 1) for s in ss],marker='o',label=label,color=colour)
    for ax in axes.flat:
        ax.set_xticks([160,192,200]);ax.set_xlabel('Analysable participants');ax.grid(alpha=.22)
    for ax,label in zip(axes[0],['H1: explanation','H3: cognitive forcing']):
        ax.set_title(label);ax.set_ylabel('Holm-adjusted power (%)');ax.set_ylim(0,100);ax.axhline(80,color='black',lw=.8,ls=':')
    axes[1,0].set_title('H2: interval precision');axes[1,0].set_ylabel('Median 95% CI width (log odds)')
    axes[1,1].set_title('Estimation sensitivity');axes[1,1].set_ylabel('Unusable under finite-profile rule (%)');axes[1,1].set_ylim(0,100)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=3,fontsize=8)
    fig.suptitle('Study 2 planning: N=160, 192 and 200\nAssumed main-effect OR=1.5; interaction OR=0.67; 500 datasets per setting',fontsize=12)
    fig.savefig(DEST/'sample_size_comparison.png',dpi=180);fig.savefig(DEST/'sample_size_comparison.pdf');plt.close(fig)
    # Structured report; complete tables preserve unfavourable scenarios.
    lines=['# Study 2 power and precision comparison: N=160, 192 and 200','',
      'Completed on 3 November 2026. These are simulations, not observed Study 2 results. No recruitment target or analysis hierarchy has been changed.','',
      'The original computation completed 22,500 model fits across 15 scenarios. It was not an unrun R script. Six further opportunity scenarios, added after the v6 expert-result audit, contribute 9,000 fits. The combined comparison therefore contains 31,500 model fits, with 500 simulated datasets for each sample-size/scenario combination. The original outputs are retained unchanged.','',
      'None of the examined N values establishes adequate power for main-effect OR=1.5. H2 remains a focal estimation target, assessed by interval precision rather than significance. The gain from 192 to 200 is modest; it does not repair a substantial information shortage. These conclusions are conditional on the stated assumptions and are not a recommendation to spend on a larger sample before the validation and pilot inputs are available.','',
      '## Primary comparison under the inherited central opportunity assumptions','',
      'The central scenario assumes disagreement probabilities of .25 on each of C-01–C-04 and .60 on C-05/C-06. Baseline appropriate reliance is .65 at the model reference values; participant random-intercept SD is .75. H1 and H3 have illustrative conditional main-effect OR=1.5, and H2 has interaction OR=.67. The latter is the ratio between explanation effects across delivery conditions, not an assumed marginal risk ratio. These effects have not been established as expected effects or as the smallest substantively important effects.','',
      '| N | Per cell | H1 power, 95% Monte Carlo interval | H3 power, 95% Monte Carlo interval | Both detected | H2 median log-CI width | H2 interval half-span factor |',
      '|---:|---:|---:|---:|---:|---:|---:|']
    for n in (160,192,200):
        s=lookup[('legacy_central',n)]
        lines.append(f'| {n} | {n//8} | {power_with_interval(s,"h1_positive_holm")} | {power_with_interval(s,"h3_positive_holm")} | {percent(s["both_positive_holm_rate"])} | {s["h2_median_log_ci_width"]:.3f} | ×/÷{s["h2_median_ci_multiplicative_half_span"]:.2f} |')
    lines += ['', 'A half-span factor of 2.61 means an H2 odds-ratio interval extends approximately from the fitted interaction OR divided by 2.61 to that estimate multiplied by 2.61. It is not a percentage-point margin or a claim of adequate precision. There were no numerical fit failures in the central scenario; the finite-profile sensitivity is reported below and in the complete export.','',
      'H1 and H3 use a two-sided Holm family with familywise alpha .05. The smaller p-value is compared with .025; if it passes, the other is compared with .05. This is not the same as testing both permanently at .025. Power in the table requires rejection in the predicted positive direction. H2 is excluded from Holm, with no H2 rejection-power criterion. The chance that both H1 and H3 are detected is reported separately from their individual power.','',
      '## Opportunity and effect sensitivities','',
      '| Scenario | N | H1 power | H3 power | H2 median width | AI-reliance opportunities | Self-reliance opportunities | Original failed fits |',
      '|---|---:|---:|---:|---:|---:|---:|---:|']
    selected=['legacy_sparse','legacy_central','legacy_dense','historical_profile_anchor','historical_profile_half_correct_ai_opportunities',
              'historical_profile_double_correct_ai_opportunities','historical_profile_main_or_1_25','historical_profile_main_or_2',
              'historical_profile_high_dependence','historical_profile_baseline_80','v6_round2_smoothed_anchor',
              'v7_C05_recoverability_50_assumption','v7_C05_recoverability_85_assumption']
    for name in selected:
        s=lookup[(name,200)]
        lines.append(f'| {name} | 200 | {percent(s["h1_positive_holm_rejection_rate"])} | {percent(s["h3_positive_holm_rejection_rate"])} | {s["h2_median_log_ci_width"]:.3f} | {s["mean_ai_reliance_opportunities"]:.1f} | {s["mean_self_reliance_opportunities"]:.1f} | {500-s["successful"]}/500 |')
    lines += ['', 'The full CSV and JSON contain every scenario at all three N values, including the null, baseline, informative-opportunity and literal-zero C-01 checks. The table does not select assumptions because they give favourable power. Direction-specific opportunity counts do not establish direction-specific model power: this run evaluates the pooled primary model, not the separate decomposition models.','',
      'The initial 16-expert pattern is used only as a sensitivity anchor. Its raw disagreement vector is [0, .125, .0625, .1875, .5625, .6875]; finite smoothing gives [(count+.5)/17] for each profile. Zero observed C-01 disagreements among 16 experts is not evidence that the Study 2 probability is zero. The literal-zero scenario is a stress test. Halving or doubling selected rates is an explicit hypothetical perturbation, not an estimated confidence band.','',
      'The newer v6 assessment has ten fresh complete author-confirmed screened experts. Its raw disagreement vector is [.20, .20, .30, .50, .20, .90], with [(count+.5)/11] used for the additional finite anchor. The population differs from Study 2, its intended-reason validation remains unresolved, and its C-05 membership was current. The now-active v7 C-05 has an additional expired membership. Consequently, even the newer expert rates are not known v7 Study 2 opportunity probabilities. The .50 and .85 C-05 recovery scenarios are labelled assumptions, not findings from a focused validation round.','',
      '## Model and numerical checks','',
      'The simulator fits the planned logistic participant-random-intercept likelihood with profile fixed effects for the six cases, centred order, effect-coded explanation/delivery/forcing and explanation-by-delivery. The outcome is generated only for analysis on simulated initial-disagreement opportunities; agreement trials are outside that denominator. Outcomes and opportunities follow explicit assumed processes. The simulator does not reproduce document reading, a measured closure mechanism or all effects of earlier treatment exposure on later unaided decisions. Its informative-opportunity scenario is a conditional-estimand sensitivity, not a complete solution to selection.','',
      'An absent profile creates an unused contrast column. The numerical correction re-references to an observed profile and records absent profiles while preserving every treatment term. It is a reparameterisation of the identifiable fixed-effect space. It does not solve outcome separation. A profile that contributes only correct or only incorrect outcomes can have a diverging fixed effect even when the overall design matrix has full rank.','',
      'The initial blanket 40-versus-80-node check failed its predeclared maximum-difference tolerance: the largest standard-error difference was 17.85, at the nuisance intercept in a constant-profile-outcome replicate. That failed check is preserved. A follow-up on 280 preselected comparisons localised the issue: the maximum H1/H3/H2 coefficient difference was '+f'{combined["numerical_check"]["max_abs_H1_H3_H2_beta_difference"]:.6f}'+', and the maximum standard-error difference was '+f'{combined["numerical_check"]["max_abs_H1_H3_H2_se_difference"]:.6f}'+'. The largest relative H2 standard-error difference was '+f'{100*combined["numerical_check"]["max_abs_H2_relative_se_difference"]:.4f}%'+'. There were no status disagreements. Stable treatment contrasts do not certify a finite nuisance-parameter maximum-likelihood estimate.','',
      '| Scenario | N | Original fit failures | Constant-profile-outcome panels | Unusable under stricter finite-profile check | H1 power under stricter check | H3 power under stricter check |',
      '|---|---:|---:|---:|---:|---:|---:|']
    for name in ('legacy_central','legacy_sparse','historical_profile_anchor','historical_profile_half_correct_ai_opportunities','v6_round2_smoothed_anchor'):
        for n in (160,192,200):
            s=lookup[(name,n)]
            lines.append(f'| {name} | {n} | {500-s["successful"]}/500 | {s["profile_constant_outcome_panels"]}/500 | {percent(s["strict_unusable_rate"])} | {percent(s["h1_strict_positive_power"])} | {percent(s["h3_strict_positive_power"])} |')
    lines += ['', 'Original failed fits count as non-rejections in the saved simulation. The stricter post-run sensitivity additionally counts any replicate with a single-outcome profile as unusable, even if the optimiser reports success. It does not delete cases, substitute a penalised estimator or change the registered model. It shows why a software success flag alone is insufficient. Interval coverage and median width are conditional on successful fits; the stricter versions are separately exported. Neither should be interpreted as unconditional guaranteed coverage across failed fits.','',
      'With 500 repetitions, the maximum Monte Carlo standard error of a rejection rate is about 2.24 percentage points. The displayed binomial intervals describe simulation error, not uncertainty in the assumed real-world effect or opportunity rates. Opportunity uncertainty is much larger than this computational error and is addressed only through the stated sensitivity grid.','',
      'The null-scenario familywise rejection rates and 95% Monte Carlo intervals are: '+', '.join(f'N={n}: {percent(lookup[("historical_profile_null",n)]["either_h1_h3_rejection_rate"])} ({100*lookup[("historical_profile_null",n)]["either_h1_h3_mc_interval95"][0]:.1f}–{100*lookup[("historical_profile_null",n)]["either_h1_h3_mc_interval95"][1]:.1f}%)' for n in (160,192,200))+'. The point estimates are above nominal 5%, although the intervals include 5%. Failed fits still count as non-rejections. This check does not establish exact error control or successful-fit Wald calibration in sparse situations; further calibration is needed if a final decision relies on these approximations.','',
      '## What eight extra participants buy','',
      '| Scenario | H1 gain, 192→200 | H3 gain, 192→200 | Paired median H2 width reduction |',
      '|---|---:|---:|---:|']
    for name in ('legacy_sparse','legacy_central','legacy_dense','historical_profile_anchor','v6_round2_smoothed_anchor'):
        c=next(c for c in combined['paired_comparisons'] if c['scenario']==name and c['low_n']==192)
        lines.append(f'| {name} | {100*c["h1_positive_power_gain"]:+.1f} percentage points | {100*c["h3_positive_power_gain"]:+.1f} percentage points | {100*(1-1/c["median_h2_width_ratio_low_over_high"]):.1f}% |')
    lines += ['', 'Common simulated participants are retained within balanced cells when comparing N values, making the gains paired comparisons. The JSON includes their Monte Carlo intervals. Small reversals or differences should not be ranked as evidence that a smaller N is intrinsically better.','',
      '## Budget and the decision still required','',
      '| Main analysable N | Per cell | Main cost relative to N=200 | Separate technical pilot | Main plus pilot |',
      '|---:|---:|---:|---:|---:|']
    for n in (160,192,200):lines.append(f'| {n} | {n//8} | {100*n/200:.0f}% | 40 | {n+40} |')
    lines += ['', 'The current operational plan requires at least five complete technical-pilot sessions in each of eight cells, separate from confirmatory data. Thus a total budget of 200 participant sessions would leave 160 main-study sessions before replacement for exclusions or incomplete records. New expert validation is another cost. Actual compensation and platform charges require the piloted duration and recruitment settings; no currency estimate is invented here.','',
      'The 40-person pilot is an operational minimum, not a precise nuisance-parameter estimation sample. Use its profile-level opportunities and completion patterns with wide uncertainty, compare cells for composition differences, and examine clustering. Do not choose a large assumed treatment effect from pilot separation to make the power calculation pass. The focused v7 expert assessment should establish recoverability and intended reasons, while the separate technical pilot should inform plausible Study 2 planning bounds. Neither can certify the treatment effects in advance.','',
      'Before selecting N, fix the smallest substantively important H1/H3 effects and the largest acceptable H2 log-CI width. Those fields and the selected analysable target remain unset in the operational specification. If 200 is the budget ceiling, the paper must describe the achievable power and precision honestly; the present simulations do not justify an 80% power claim for OR=1.5. The locked H1/H3 confirmatory status and focal H2 estimation status remain unchanged. A decision to proceed on budget grounds would need to acknowledge the shortfall explicitly.','',
      'Published sample sizes establish that different N values have appeared at FAccT; they cannot supply power for this diagnostic-subset design. The earlier sample-size precedent report remains separate. The sentence about an unrun R script does not describe these saved runs: these results use the checked Python marginal-likelihood implementation, with seeds, source hashes, package versions and every replicate retained. A separate R/lme4 replication has not been performed.','',
      '## Reproduction and files','',
      'The original run used seed 20261103; the supplementary scenario set uses seed 20261104 as a reproducibility label, not a collection date. Both use Python '+datasets[0]['python']+', NumPy '+datasets[0]['numpy']+', SciPy '+datasets[0]['scipy']+', 40 quadrature nodes and one BLAS thread per worker. The combined results record the original source hashes. The 80-node follow-up is a numerical diagnostic, not a replacement simulation selected for favourable power.','',
      '- `all_scenarios.csv`: all 63 sample-size/scenario combinations, original and stricter diagnostics.','- `comparison_results.json`: full summaries, paired comparisons and finite-profile diagnostics.','- `sample_size_comparison.png` and `.pdf`: scientific figure.','- `reproducibility_bundle.zip`: simulation source, configs, all raw synthetic replicates, result metadata and numerical checks. No participant records are included.','',
      'No manuscript results, material version, recruitment target or operational threshold has been changed by this report.']
    report='\n'.join(lines)+'\n'
    (DEST/'Study2_Power_Precision_Comparison.md').write_text(report)
    (BASE/'comparison_summary.md').write_text(report)
    # Compact reproducibility archive: raw files are synthetic only.
    with zipfile.ZipFile(DEST/'reproducibility_bundle.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in [ROOT/'analysis/study2/simulate_precision.py',ROOT/'analysis/study2/compare_budget_precision.py',
                  ROOT/'analysis/study2/check_budget_quadrature.py',BASE/'scenarios.json',BASE/'supplement_scenarios.json',
                  BASE/'quadrature_check.json',BASE/'quadrature_follow_up.json']:
            z.write(p,str(p.relative_to(ROOT)))
        for folder in run_paths:
            for p in folder.rglob('*.json'):z.write(p,str(p.relative_to(ROOT)))
        z.write(Path(__file__),'analysis/study2/build_budget_report.py')
        z.write(Path(__file__).with_name('diagnose_budget_numerics.py'),'analysis/study2/diagnose_budget_numerics.py')
    print(json.dumps({'fits':combined['total_simulated_model_fits'],'configurations':len(all_rows),'report_words':len(report.split()),'output_directory':str(DEST)}))

if __name__=='__main__':main()
