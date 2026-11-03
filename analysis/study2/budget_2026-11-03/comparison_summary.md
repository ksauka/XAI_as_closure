# Study 2 power and precision comparison: N=160, 192 and 200

Completed on 3 November 2026. These are simulations, not observed Study 2 results. No recruitment target or analysis hierarchy has been changed.

The original computation completed 22,500 model fits across 15 scenarios. It was not an unrun R script. Six further opportunity scenarios, added after the v6 expert-result audit, contribute 9,000 fits. The combined comparison therefore contains 31,500 model fits, with 500 simulated datasets for each sample-size/scenario combination. The original outputs are retained unchanged.

None of the examined N values establishes adequate power for main-effect OR=1.5. H2 remains a focal estimation target, assessed by interval precision rather than significance. The gain from 192 to 200 is modest; it does not repair a substantial information shortage. These conclusions are conditional on the stated assumptions and are not a recommendation to spend on a larger sample before the validation and pilot inputs are available.

## Primary comparison under the inherited central opportunity assumptions

The central scenario assumes disagreement probabilities of .25 on each of C-01–C-04 and .60 on C-05/C-06. Baseline appropriate reliance is .65 at the model reference values; participant random-intercept SD is .75. H1 and H3 have illustrative conditional main-effect OR=1.5, and H2 has interaction OR=.67. The latter is the ratio between explanation effects across delivery conditions, not an assumed marginal risk ratio. These effects have not been established as expected effects or as the smallest substantively important effects.

| N | Per cell | H1 power, 95% Monte Carlo interval | H3 power, 95% Monte Carlo interval | Both detected | H2 median log-CI width | H2 interval half-span factor |
|---:|---:|---:|---:|---:|---:|---:|
| 160 | 20 | 22.0% (18.4–25.9) | 24.2% (20.5–28.2) | 10.8% | 2.156 | ×/÷2.94 |
| 192 | 24 | 28.0% (24.1–32.2) | 30.0% (26.0–34.2) | 14.0% | 1.962 | ×/÷2.67 |
| 200 | 25 | 28.0% (24.1–32.2) | 32.2% (28.1–36.5) | 15.2% | 1.921 | ×/÷2.61 |

A half-span factor of 2.61 means an H2 odds-ratio interval extends approximately from the fitted interaction OR divided by 2.61 to that estimate multiplied by 2.61. It is not a percentage-point margin or a claim of adequate precision. There were no numerical fit failures in the central scenario; the finite-profile sensitivity is reported below and in the complete export.

H1 and H3 use a two-sided Holm family with familywise alpha .05. The smaller p-value is compared with .025; if it passes, the other is compared with .05. This is not the same as testing both permanently at .025. Power in the table requires rejection in the predicted positive direction. H2 is excluded from Holm, with no H2 rejection-power criterion. The chance that both H1 and H3 are detected is reported separately from their individual power.

## Opportunity and effect sensitivities

| Scenario | N | H1 power | H3 power | H2 median width | AI-reliance opportunities | Self-reliance opportunities | Original failed fits |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy_sparse | 200 | 17.4% | 14.8% | 2.650 | 79.9 | 140.4 | 2/500 |
| legacy_central | 200 | 28.0% | 32.2% | 1.921 | 199.8 | 239.2 | 0/500 |
| legacy_dense | 200 | 46.0% | 45.6% | 1.600 | 360.5 | 319.5 | 0/500 |
| historical_profile_anchor | 200 | 22.2% | 20.6% | 2.149 | 93.0 | 247.1 | 67/500 |
| historical_profile_half_correct_ai_opportunities | 200 | 12.4% | 13.0% | 2.290 | 46.6 | 246.4 | 195/500 |
| historical_profile_double_correct_ai_opportunities | 200 | 33.2% | 32.2% | 1.938 | 188.7 | 246.9 | 6/500 |
| historical_profile_main_or_1_25 | 200 | 6.0% | 9.6% | 2.145 | 94.4 | 246.4 | 68/500 |
| historical_profile_main_or_2 | 200 | 61.4% | 59.6% | 2.150 | 94.2 | 247.2 | 56/500 |
| historical_profile_high_dependence | 200 | 16.0% | 14.8% | 2.555 | 94.2 | 248.1 | 51/500 |
| historical_profile_baseline_80 | 200 | 15.6% | 14.8% | 2.417 | 93.3 | 247.0 | 145/500 |
| v6_round2_smoothed_anchor | 200 | 31.4% | 31.6% | 1.867 | 255.1 | 218.3 | 0/500 |
| v7_C05_recoverability_50_assumption | 200 | 35.4% | 34.8% | 1.757 | 255.2 | 272.5 | 0/500 |
| v7_C05_recoverability_85_assumption | 200 | 41.2% | 38.0% | 1.668 | 254.3 | 343.0 | 0/500 |

The full CSV and JSON contain every scenario at all three N values, including the null, baseline, informative-opportunity and literal-zero C-01 checks. The table does not select assumptions because they give favourable power. Direction-specific opportunity counts do not establish direction-specific model power: this run evaluates the pooled primary model, not the separate decomposition models.

The initial 16-expert pattern is used only as a sensitivity anchor. Its raw disagreement vector is [0, .125, .0625, .1875, .5625, .6875]; finite smoothing gives [(count+.5)/17] for each profile. Zero observed C-01 disagreements among 16 experts is not evidence that the Study 2 probability is zero. The literal-zero scenario is a stress test. Halving or doubling selected rates is an explicit hypothetical perturbation, not an estimated confidence band.

The newer v6 assessment has ten fresh complete author-confirmed screened experts. Its raw disagreement vector is [.20, .20, .30, .50, .20, .90], with [(count+.5)/11] used for the additional finite anchor. The population differs from Study 2, its intended-reason validation remains unresolved, and its C-05 membership was current. The now-active v7 C-05 has an additional expired membership. Consequently, even the newer expert rates are not known v7 Study 2 opportunity probabilities. The .50 and .85 C-05 recovery scenarios are labelled assumptions, not findings from a focused validation round.

## Model and numerical checks

The simulator fits the planned logistic participant-random-intercept likelihood with profile fixed effects for the six cases, centred order, effect-coded explanation/delivery/forcing and explanation-by-delivery. The outcome is generated only for analysis on simulated initial-disagreement opportunities; agreement trials are outside that denominator. Outcomes and opportunities follow explicit assumed processes. The simulator does not reproduce document reading, a measured closure mechanism or all effects of earlier treatment exposure on later unaided decisions. Its informative-opportunity scenario is a conditional-estimand sensitivity, not a complete solution to selection.

An absent profile creates an unused contrast column. The numerical correction re-references to an observed profile and records absent profiles while preserving every treatment term. It is a reparameterisation of the identifiable fixed-effect space. It does not solve outcome separation. A profile that contributes only correct or only incorrect outcomes can have a diverging fixed effect even when the overall design matrix has full rank.

The initial blanket 40-versus-80-node check failed its predeclared maximum-difference tolerance: the largest standard-error difference was 17.85, at the nuisance intercept in a constant-profile-outcome replicate. That failed check is preserved. A follow-up on 280 preselected comparisons localised the issue: the maximum H1/H3/H2 coefficient difference was 0.000546, and the maximum standard-error difference was 0.001496. The largest relative H2 standard-error difference was 0.0060%. There were no status disagreements. Stable treatment contrasts do not certify a finite nuisance-parameter maximum-likelihood estimate.

| Scenario | N | Original fit failures | Constant-profile-outcome panels | Unusable under stricter finite-profile check | H1 power under stricter check | H3 power under stricter check |
|---|---:|---:|---:|---:|---:|---:|
| legacy_central | 160 | 0/500 | 0/500 | 0.0% | 22.0% | 24.2% |
| legacy_central | 192 | 0/500 | 0/500 | 0.0% | 28.0% | 30.0% |
| legacy_central | 200 | 0/500 | 0/500 | 0.0% | 28.0% | 32.2% |
| legacy_sparse | 160 | 9/500 | 5/500 | 1.8% | 13.4% | 13.4% |
| legacy_sparse | 192 | 3/500 | 1/500 | 0.6% | 16.4% | 14.6% |
| legacy_sparse | 200 | 2/500 | 0/500 | 0.4% | 17.4% | 14.8% |
| historical_profile_anchor | 160 | 110/500 | 110/500 | 22.2% | 14.2% | 13.6% |
| historical_profile_anchor | 192 | 74/500 | 74/500 | 15.0% | 20.4% | 20.8% |
| historical_profile_anchor | 200 | 67/500 | 66/500 | 13.4% | 22.2% | 20.6% |
| historical_profile_half_correct_ai_opportunities | 160 | 241/500 | 245/500 | 49.0% | 7.4% | 8.4% |
| historical_profile_half_correct_ai_opportunities | 192 | 199/500 | 206/500 | 41.6% | 10.8% | 11.0% |
| historical_profile_half_correct_ai_opportunities | 200 | 195/500 | 203/500 | 40.8% | 11.8% | 12.2% |
| v6_round2_smoothed_anchor | 160 | 0/500 | 0/500 | 0.0% | 25.4% | 23.2% |
| v6_round2_smoothed_anchor | 192 | 0/500 | 0/500 | 0.0% | 28.8% | 31.6% |
| v6_round2_smoothed_anchor | 200 | 0/500 | 0/500 | 0.0% | 31.4% | 31.6% |

Original failed fits count as non-rejections in the saved simulation. The stricter post-run sensitivity additionally counts any replicate with a single-outcome profile as unusable, even if the optimiser reports success. It does not delete cases, substitute a penalised estimator or change the registered model. It shows why a software success flag alone is insufficient. Interval coverage and median width are conditional on successful fits; the stricter versions are separately exported. Neither should be interpreted as unconditional guaranteed coverage across failed fits.

With 500 repetitions, the maximum Monte Carlo standard error of a rejection rate is about 2.24 percentage points. The displayed binomial intervals describe simulation error, not uncertainty in the assumed real-world effect or opportunity rates. Opportunity uncertainty is much larger than this computational error and is addressed only through the stated sensitivity grid.

The null-scenario familywise rejection rates and 95% Monte Carlo intervals are: N=160: 5.4% (3.6–7.8%), N=192: 6.0% (4.1–8.5%), N=200: 6.2% (4.3–8.7%). The point estimates are above nominal 5%, although the intervals include 5%. Failed fits still count as non-rejections. This check does not establish exact error control or successful-fit Wald calibration in sparse situations; further calibration is needed if a final decision relies on these approximations.

## What eight extra participants buy

| Scenario | H1 gain, 192→200 | H3 gain, 192→200 | Paired median H2 width reduction |
|---|---:|---:|---:|
| legacy_sparse | +1.0 percentage points | +0.2 percentage points | 1.9% |
| legacy_central | +0.0 percentage points | +2.2 percentage points | 2.2% |
| legacy_dense | +3.0 percentage points | +1.0 percentage points | 2.1% |
| historical_profile_anchor | +1.8 percentage points | -0.2 percentage points | 1.9% |
| v6_round2_smoothed_anchor | +2.6 percentage points | +0.0 percentage points | 2.0% |

Common simulated participants are retained within balanced cells when comparing N values, making the gains paired comparisons. The JSON includes their Monte Carlo intervals. Small reversals or differences should not be ranked as evidence that a smaller N is intrinsically better.

## Budget and the decision still required

| Main analysable N | Per cell | Main cost relative to N=200 | Separate technical pilot | Main plus pilot |
|---:|---:|---:|---:|---:|
| 160 | 20 | 80% | 40 | 200 |
| 192 | 24 | 96% | 40 | 232 |
| 200 | 25 | 100% | 40 | 240 |

The current operational plan requires at least five complete technical-pilot sessions in each of eight cells, separate from confirmatory data. Thus a total budget of 200 participant sessions would leave 160 main-study sessions before replacement for exclusions or incomplete records. New expert validation is another cost. Actual compensation and platform charges require the piloted duration and recruitment settings; no currency estimate is invented here.

The 40-person pilot is an operational minimum, not a precise nuisance-parameter estimation sample. Use its profile-level opportunities and completion patterns with wide uncertainty, compare cells for composition differences, and examine clustering. Do not choose a large assumed treatment effect from pilot separation to make the power calculation pass. The focused v7 expert assessment should establish recoverability and intended reasons, while the separate technical pilot should inform plausible Study 2 planning bounds. Neither can certify the treatment effects in advance.

Before selecting N, fix the smallest substantively important H1/H3 effects and the largest acceptable H2 log-CI width. Those fields and the selected analysable target remain unset in the operational specification. If 200 is the budget ceiling, the paper must describe the achievable power and precision honestly; the present simulations do not justify an 80% power claim for OR=1.5. The locked H1/H3 confirmatory status and focal H2 estimation status remain unchanged. A decision to proceed on budget grounds would need to acknowledge the shortfall explicitly.

Published sample sizes establish that different N values have appeared at FAccT; they cannot supply power for this diagnostic-subset design. The earlier sample-size precedent report remains separate. The sentence about an unrun R script does not describe these saved runs: these results use the checked Python marginal-likelihood implementation, with seeds, source hashes, package versions and every replicate retained. A separate R/lme4 replication has not been performed.

## Reproduction and files

The original run used seed 20261103; the supplementary scenario set uses seed 20261104 as a reproducibility label, not a collection date. Both use Python 3.13.11, NumPy 2.3.5, SciPy 1.17.1, 40 quadrature nodes and one BLAS thread per worker. The combined results record the original source hashes. The 80-node follow-up is a numerical diagnostic, not a replacement simulation selected for favourable power.

- `all_scenarios.csv`: all 63 sample-size/scenario combinations, original and stricter diagnostics.
- `comparison_results.json`: full summaries, paired comparisons and finite-profile diagnostics.
- `sample_size_comparison.png` and `.pdf`: scientific figure.
- `reproducibility_bundle.zip`: simulation source, configs, all raw synthetic replicates, result metadata and numerical checks. No participant records are included.

No manuscript results, material version, recruitment target or operational threshold has been changed by this report.
