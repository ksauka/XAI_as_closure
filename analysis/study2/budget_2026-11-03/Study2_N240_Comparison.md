# Study 2: N=240 extension

Completed on 3 November 2026. N=240 means 240 analysable main-study participants, 30 in each of eight cells. The separate 40-person technical pilot brings the minimum to 280 participant sessions, before replacements and expert validation. If 240 is the total session budget including that pilot, the main target would instead be N=200.

All 21 previously reported sensitivity scenarios were retained, with 500 datasets each, adding 10,500 model fits. The planned primary model and Holm family are unchanged. Original N=200 results are preserved. N=240 panels are not nested in those N=200 panels, so the difference between point estimates is not reported as a paired gain.

## Central scenario

Both main-effect ORs are assumed to be 1.5, the interaction OR is .67, conditional baseline appropriate reliance is .65, participant random-intercept SD is .75, and opportunity probabilities are .25 for each correct-AI profile and .60 for each incorrect-AI profile. All are planning assumptions.

| Main N | Per cell | H1 power, 95% Monte Carlo interval | H3 power, 95% Monte Carlo interval | Both detected | H2 median log-CI width |
|---:|---:|---:|---:|---:|---:|
| 200 | 25 | 28.0% (24.1–32.2%) | 32.2% (28.1–36.5%) | 15.2% | 1.921 |
| 240 | 30 | 41.2% (36.8–45.7%) | 41.0% (36.7–45.5%) | 21.6% | 1.743 |

The N=240 central median H2 interval half-span is ×/÷2.39 around the estimated interaction odds ratio. Median log-CI width is 9.2% smaller than in the saved N=200 run. No substantively acceptable H2 width has been fixed.

## Sensitivity comparisons

| Scenario | N | H1 power | H3 power | H2 median log-CI width | Failed fits |
|---|---:|---:|---:|---:|---:|
| legacy_sparse | 200 | 17.4% | 14.8% | 2.650 | 2/500 |
| legacy_sparse | 240 | 18.0% | 21.2% | 2.430 | 0/500 |
| legacy_dense | 200 | 46.0% | 45.6% | 1.600 | 0/500 |
| legacy_dense | 240 | 52.0% | 54.0% | 1.460 | 0/500 |
| historical_profile_anchor | 200 | 22.2% | 20.6% | 2.149 | 67/500 |
| historical_profile_anchor | 240 | 29.8% | 28.6% | 1.949 | 42/500 |
| historical_profile_main_or_2 | 200 | 61.4% | 59.6% | 2.150 | 56/500 |
| historical_profile_main_or_2 | 240 | 71.8% | 70.2% | 1.999 | 39/500 |
| historical_profile_high_dependence | 200 | 16.0% | 14.8% | 2.555 | 51/500 |
| historical_profile_high_dependence | 240 | 22.4% | 21.4% | 2.327 | 33/500 |
| v6_round2_smoothed_anchor | 200 | 31.4% | 31.6% | 1.867 | 0/500 |
| v6_round2_smoothed_anchor | 240 | 39.0% | 38.6% | 1.708 | 0/500 |
| v7_C05_recoverability_85_assumption | 200 | 41.2% | 38.0% | 1.668 | 0/500 |
| v7_C05_recoverability_85_assumption | 240 | 50.0% | 50.4% | 1.516 | 0/500 |

H1 and H3 use two-sided Holm adjustment within familywise alpha .05; detection requires the predicted positive direction. H2 remains a focal estimation target outside Holm. Failed fits count as non-detections. Interval widths and coverage are conditional on successful fits. The stricter finite-profile diagnostic, exported separately, also flags profiles whose diagnostic outcomes are all identical. The existing 40/80-node checks and their limitations remain applicable; no new claim of exact small-sample calibration is made.

With 500 repetitions the maximum Monte Carlo standard error is 2.24 percentage points. The intervals quantify simulation error, not uncertainty about the actual treatment effects or disagreement rates. The initial and v6 expert patterns remain sensitivities from different samples and earlier materials. Neither has validated the current v7 C-05 profile. The .85 recovery scenario is an assumption, not a new expert finding.

## Planning implication

N=240 supplies 20% more main-study participants than N=200 and improves precision. It does not by itself establish adequate power. The same unresolved decisions remain: the smallest substantively important H1/H3 effects, the largest acceptable H2 width, and plausible opportunity/dependence bounds informed by the focused assessment and separate technical pilot. No recruitment target or confirmatory status has been changed.

- `N200_N240_comparison.csv`: all 21 scenarios at both sample sizes.
- `N240_results.json`: summaries, intervals and finite-profile diagnostics.
- `N240_reproducibility.zip`: source, configurations, metadata and every raw synthetic replicate for this extension. No participant records.
