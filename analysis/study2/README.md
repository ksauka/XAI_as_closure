# Study 2 analysis and precision planning

The active specification is study_CHI/STUDY2_ANALYSIS_PLAN.md (study2-analysis-v2). Participant-facing materials and the 2 × 2 × 2 design are unchanged.

## Run

Use the dsagent environment. Install the optional analysis dependencies from analysis/study2/requirements.txt when preparing another environment. Numerical versions are recorded in every output; the checked environment is also archived in environment_versions.json. Keep OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1 for reproducible single-threaded planning.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python analysis/study2/simulate_precision.py --repetitions 200 --nodes 40 --output analysis/study2/precision_results.json
PYTHONPATH=src python -m unittest discover -s tests -p 'test_study2*py' -v
python analysis/study2/readiness.py
```

The simulator draws all six fixed profiles, balanced between-subject conditions, random profile order, diagnostic opportunities, and a logistic outcome with participant random intercept and profile fixed effects. The likelihood is marginalised by Gauss–Hermite quadrature, with numerical curvature for fixed-effect standard errors. No Bayesian prior or penalised substitute is used. Quadrature remains an approximation: tests compare 20 versus 40 nodes; final planning should inspect stability, fit failures, coverage and variance-boundary flags. Repetitions and seed are explicit.

scenarios.json contains assumptions, not participant estimates. Current core scenarios cover sparse/central/dense diagnostic opportunities, a central null and greater participant dependence at the N=400 ceiling. baseline_sensitivity.json additionally varies baseline appropriate-reliance probability. Effects are fixed illustrative odds ratios, not justified effect-size estimates. The reported H1/H3 rates apply only to those assumptions. The achieved H2 interval widths do not establish adequate precision without a substantive precision criterion. Finer effect-size and nuisance grids should be run after the pilot and before selecting a final target. Do not select a scenario because it produces favourable power.

precision_results.json stores every replicate, convergence failures, source hash, seed, versions and summaries. precision_summary.md explains the results. The empirical coverage and Monte Carlo error are reported so that 200 repetitions per scenario are not mistaken for exact probabilities.

## Outcomes

Use the v2 session_flatten exporter. appropriate_reliance is nullable: initial-agreement trials are outside its denominator, and missing decisions are not failures. diagnostic_disagreement and reliance_direction identify the opportunity set. Directional outcomes use their own opportunity denominators. Final accuracy remains aided_correct on all complete trials. All earlier flattened exports must be regenerated rather than relabelled.

## Operational inputs

STUDY2_OPERATIONAL_SPEC.json contains the coding subset, exclusion rules, scale-scoring policy and timing rule. Readiness is not inferred from the material freeze. readiness.py exits with code 2 and lists fields requiring actual evidence when the final questionnaire, pilot, precision criterion or final target are absent.

scale_scoring.py accepts only frozen scale specifications with item IDs, ranges and reverse keys. It uses the mean with at least 80% item completion. It does not manufacture missing items or assume response anchors. No post hoc alpha-driven deletion is allowed.

For the separate technical pilot, provide a CSV with session_id, condition_id, complete and total_duration_seconds, then run:

```sh
python analysis/study2/pilot_timing.py pilot_participants.csv --output analysis/study2/pilot_timing_result.json
```

At least five complete sessions in each cell are required. The output records the input hash, per-cell quantiles and proposed soft allowance. It does not alter the application or impose a hard deadline. Inspect interruptions and document the final decision before copying the value and hash to the operational specification.

Evidence coding follows STUDY2_EVIDENCE_CODING.md. Subset sampling is stratified by candidate, uses seed 20261022, and hides treatment and decisions. Codes require human interpretation; no automatic correct-keyword rule replaces the manual.

## Status

These updates align the agreed model and derived data. They do not freeze missing survey content, choose a substantively acceptable precision threshold, generate pilot observations, claim ethics approval, or open recruitment. No participant data were used in the planning simulation.

Create the blind independent-coding sheet with `python analysis/study2/coding_subset.py trial_export.csv --output blind_subset.csv`. Only pseudonymous response ID, reference, text and blank coding fields are retained. Preserve the secure original export for linkage; never distribute treatment/outcome columns to coders.

The researcher-supplied 19-item main battery, three forcing-only PCE candidate items, three pre-task questions and PPBE reverse item are recorded in [STUDY2_QUESTIONNAIRE.md](../../study_CHI/STUDY2_QUESTIONNAIRE.md). Main-scale agreement endpoints were confirmed on 30 October 2026. Pre-task response options and final Qualtrics mapping are pending; canonical keys are not asserted to be existing survey export IDs.


## Completed N=160, 192 and 200 comparison (3 November 2026)

`budget_2026-11-03/comparison_summary.md` reports 31,500 model fits: the original 15 scenarios and six separately labelled sensitivities added after the v6 expert audit, with 500 replicates per N/scenario. `comparison_summary.csv` and `comparison_results.json` contain all 63 configurations. No recruitment target, H1/H3 minimum effect or H2 acceptable-width threshold has been set.

The completed implementation uses the Python marginal logistic random-intercept likelihood, with H1 and H3 in a two-sided Holm family. It does not depend on an unrun R script. H2 is a precision/coverage target outside Holm. Published sample sizes are contextual precedents, not a power justification.

The historical and newer expert patterns remain hypothetical Study 2 opportunity scenarios. Neither expert round assesses the current v7 C-05 profile. Separate focused validation and a separate technical pilot must inform final planning bounds. The current project pilot rule is five complete sessions per cell, outside the main sample.

The original blanket 40/80-node check failed because a nuisance-intercept standard error was unstable in a separated profile. `quadrature_follow_up.json` localises the discrepancy; treatment contrasts were stable in the checked panels. The report also presents an explicit post-run finite-profile-MLE sensitivity. It does not silently delete cases or replace the planned estimator.

Reproduce from the repository root, with the recorded package versions:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python analysis/study2/compare_budget_precision.py --config analysis/study2/budget_2026-11-03/scenarios.json --output-dir analysis/study2/budget_2026-11-03/run_500_q40 --workers 3
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python analysis/study2/compare_budget_precision.py --config analysis/study2/budget_2026-11-03/supplement_scenarios.json --output-dir analysis/study2/budget_2026-11-03/supplement_500_q40 --workers 3
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python analysis/study2/diagnose_budget_numerics.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python analysis/study2/build_budget_report.py
```

The original per-replicate synthetic outputs, code and metadata are also retained in the manuscript workspace reproducibility ZIP. Raw synthetic replicate folders are omitted from Git to avoid unnecessary repository growth; no participant records enter this bundle. The checked-in result metadata retain their original source hashes and run commits. Reproduction creates new run metadata without changing the archived ZIP.
