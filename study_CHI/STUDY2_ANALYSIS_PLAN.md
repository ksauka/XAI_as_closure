# Study 2 Analysis Plan

Version: study2-analysis-v2, 22 October 2026. Working specification to freeze before recruitment. This replaces the older H4–H6/N=312 plan and follows the agreed FAccT manuscript H1–H3 model. Study 2 has not started. Simulation outputs are planning results, not observed participant results.

## Design and estimand

The fixed six-profile task crosses explanation-package presence, procedural/anthropomorphic delivery, and requirement re-entry in a 2 × 2 × 2 between-subjects design. Each participant completes all six profiles in random order within the assigned condition. C-01–C-04 receive correct advice, C-05 a false advance, and C-06 a false reject. Ground truth follows the frozen written requirements, including currency and whole-file identity rules, not the modal Study 1 response.

A diagnostic opportunity occurs when the unaided judgement and AI recommendation disagree. Appropriate reliance is the correctness of the final decision on those opportunities only. It is missing/not applicable on initial-agreement trials, not zero. Final accuracy is separately observed on all completed trials.

- Correct self-reliance: unaided correct, AI wrong, aided correct.
- Correct AI reliance: unaided wrong, AI correct, aided correct.
- Overreliance: failure on a self-reliance opportunity.
- Under-reliance: failure on an AI-reliance opportunity.

Agreement with correct advice when already correct is not evidence of diagnostic reliance. The export version is study2-analysis-v2; older exports must be regenerated. All-trial following/overriding remain separately labelled descriptive measures. Legacy assistant_induced_error and assistant_corrected_error fields denote observed transitions only; their names do not identify an individual causal counterfactual.

## Hypotheses and multiplicity

H1: On diagnostic human–AI disagreement trials, provenance-based explanation increases appropriate reliance relative to no explanation.

H2: Anthropomorphic delivery attenuates the beneficial effect of provenance-based explanation on appropriate reliance, relative to procedural delivery.

H3: On diagnostic human–AI disagreement trials, cognitive forcing increases appropriate reliance relative to no forcing.

H1 and H3 are two-sided confirmatory tests at familywise alpha .05 with Holm adjustment across the two p-values. Report the direction, estimate and 95% confidence interval as well as adjusted p-values. A significant effect in the opposite direction is not support for the directional prediction.

H2 is the focal directional interaction estimation target, not a binary hypothesis test. Report the interaction coefficient and odds ratio, 95% confidence interval, predicted probabilities, and explanation contrasts within both delivery levels. A negative explanation-by-delivery coefficient is the predicted attenuation direction. Uncertainty remains uncertainty; a delivery main effect cannot substitute for H2. H2 is excluded from the Holm family. Forcing interactions and the three-way interaction are exploratory.

## Primary model

Fit a logistic mixed-effects model to diagnostic trials:

logit Pr(appropriate_reliance_ij = 1) = intercept + b_i + beta_E E_i + beta_A A_i + beta_F F_i + beta_EA E_i A_i + beta_T (position_ij - 3.5) + profile fixed effects.

b_i is a normal participant random intercept. Profile is a fixed factor for this six-case set, with C-01 as the reference. E, A and F are coded -0.5/+0.5. H1 uses beta_E (the average explanation log-odds contrast across delivery levels under this model), H2 beta_EA, and H3 beta_F. H1 does not estimate an isolated citation effect: explanation supplies rationale and provenance together. Report explanation simple contrasts beta_E - 0.5*beta_EA under procedural and beta_E + 0.5*beta_EA under anthropomorphic delivery.

Predicted probabilities are marginalised over the fitted participant random-intercept distribution and standardised over the empirical diagnostic-trial covariate distribution, with the assigned treatment values set for each contrast. They supplement, rather than replace, the prespecified coefficient tests.

Profile fixes recommendation correctness, so diagnostic direction is aliased with profile and is not added as a separate main effect. Fit separate prespecified decomposition models for self-reliance opportunities (C-05/C-06 when initially correct) and AI-reliance opportunities (C-01–C-04 when initially wrong), retaining the treatment terms, order, participant intercept and identifiable fixed effects for the included profiles. Report sparse-cell counts and non-estimable terms honestly. These decompositions are not extra confirmatory tests in the Holm family.

Report diagnostic opportunities by profile, direction and cell, participants with no opportunities, and the composition of opportunities. Later unaided judgements can reflect earlier treatment exposure. Include trial position and examine treatment-by-position patterns in robustness analyses; do not describe every later unaided judgement as globally pre-treatment. Analyses restricted to diagnostic opportunities describe that selected disagreement population, whose composition may differ across conditions.

## Sample and simulation

The ceiling is N=400 analysable participants. No conventional .80 power claim is made for H2. analysis/study2/simulate_precision.py generates the actual six-profile design, opportunity selection, profile fixed effects, order, a participant random intercept and the primary interaction. It fits the marginal logistic random-intercept likelihood using Gauss–Hermite quadrature. Report the approximation and check stability at higher quadrature resolution.

The archived scenarios vary diagnostic-opportunity frequency, baseline appropriate reliance and participant dependence, including a null scenario for calibration. Nuisance values and treatment odds ratios are explicit assumptions, not estimates from manipulation checks or unpublished Study 2 results. For H1/H3 report Holm-adjusted rejection rates and Monte Carlo error, counting failed fits as non-rejections. For H2 report CI widths, coverage, bias, fit failures and opportunity counts, not interaction rejection rates.

Before launch, set the smallest substantively important effects for H1/H3 and the largest acceptable H2 log-odds CI width in STUDY2_OPERATIONAL_SPEC.json, incorporating pilot nuisance estimates without choosing effects from manipulation-check separation. Use the simulation to choose a target within the ceiling and document whether the criteria are met. Until these fields are set, the simulator establishes achievable precision under stated assumptions but does not certify design adequacy. Numerical results must remain traceable to seed, scenario file, package versions and source hash.

## Analysis population and exclusions

Include consented, occupationally eligible participants who are not in Study 1 or the excluded prior sample, entered their assigned route, used the frozen materials and register, completed all six trials, linked to a complete post-task survey, and passed the instructed-response attention item fixed before recruitment. Final item ID and correct response must be entered before the gate can pass. Do not invent or retrospectively select that item.

Exclude route/material mismatches, missing linked task or survey records, and incomplete sessions; report counts and reasons. A manipulation-check response, incorrect decision, no citation/document use, or rapid completion is never a primary exclusion. Do not exclude participants for failing the cognitive-forcing response check: log attempts and completion within the assigned workflow.

Duplicate records: every session writes its own private file, so a participant who returns after a host restart can have more than one record. Group records by Prolific ID and keep the first completed attempt (earliest `completed_at_utc`); if none completed, keep the earliest started one. Exclude all later attempts and report their count. `session_flatten.select_first_completed_attempts` applies this rule.

One eligible complete linked session is retained per participant: the earliest created valid session under the original assigned condition, ties broken lexically by session_id. Multiple archive snapshots of one session are consolidated using the greatest monotonic event sequence, with conflicting histories reported as data-integrity failures. Never choose a record by correctness or engagement. Trial outcome missingness is not scored as failure. Report item-level questionnaire missingness; do not impute behavioural decisions or substitute a single survey item for a scale.

## Measures and scoring

The operational specification records final scale IDs, verbatim wording, response anchors, timing and proposed analysis keys. PPBE (5), ANT (5), TRUST (9) and forcing-only PCE (3 candidate adapted items) use the researcher-confirmed 1–7 Strongly disagree to Strongly agree scale. Final Qualtrics mapping and export hash remain pending. The pre-task items are AI-use frequency, general interpersonal trust propensity and general generosity; their response options remain pending. Generosity is not risk aversion. NCS6 and risk aversion are not administered in the agreed active battery.

For a frozen k-item scale, reverse only declared items using min+max-value, then take the mean if at least ceil(.8*k) items are answered; otherwise score missing. PPBE_5 is reversed. Reject out-of-range data and report the issue. Do not drop items because reliability or treatment separation is inconvenient. Re-estimate reliability and discriminant validity. PCE characterises the perceived requirement re-entry experience only among forcing participants. F0 PCE is structurally not applicable, never zero; no between-condition PCE manipulation check or causal mediation is specified. Completion, attempts and timing remain the primary forcing implementation checks. analysis/study2/scale_scoring.py refuses to score an unfrozen/incomplete specification.

## Evidence coding

After every final decision, the same neutral free-text prompt asks: "In a few words, what was the main reason for your final decision?" Responses are required and capped at 200 characters. Use the versioned manual STUDY2_EVIDENCE_CODING.md. Responses are coded without final verdicts, treatment assignment, or trust scores. Complete responses receive 1 only when decisive evidence is identified, otherwise 0; missing responses remain missing. The code is independent of whether the final decision is correct.

Select 25% within each profile, rounded up, with a minimum of 20 responses per profile or all available if fewer, using seed 20261022 on a stable sorted response-ID frame. Two coders work independently. Report raw agreement, Cohen's kappa and the 2 × 2 counts; label kappa undefined when margins are degenerate. Lock independent codes before a third reviewer adjudicates. Freeze the clarified manual before remaining coding and recode the subset if criteria change. Keep original, adjudicated and final codes. No reliability threshold is retrospectively used to discard responses.

## Timing

No arbitrary minute limit is asserted. Pilot the frozen workflow separately from confirmatory data, including at least five complete sessions in every cell. analysis/study2/pilot_timing.py computes a candidate soft allowance: 1.25 times the largest cell-specific 95th percentile, rounded up to whole minutes. Inspect technical interruptions and all cell distributions; document deviations from the mechanical rule. No decision is automatically submitted and no primary speed exclusion follows from exceeding the allowance. The pilot-derived value and input hash must be recorded before launch; the current value remains unset because no complete eight-cell pilot has been supplied.

## Secondary analyses and robustness

Analyse final accuracy across all trials, evidence identification separately, and post-task trust in association with recommendation following. Perception–trust associations are secondary and not interpreted as a temporally established mediation chain. Citation clicks, document traversal and dwell times are exploratory, not evidence of understanding. The three agreed pre-task items are descriptive unless a specific covariate sensitivity model is documented before recruitment. Do not substitute generosity for risk aversion or carry forward the retired NCS6 model. Report trial-position interactions as robustness analyses.

For convergence problems increase iterations, then use a second suitable optimiser with the same likelihood/formula. Record zero-variance boundary fits. If necessary fit a prespecified reduced random-intercept structure (fixed effects with participant-clustered uncertainty) as sensitivity, clearly distinguished from the primary model. Rank-deficient or separated directional models are reported as such; do not silently omit profile effects, relabel accuracy, or substitute a different estimand.

## Freeze and reporting

The material freeze remains unchanged. Before recruitment archive this plan, the analysis-export version, completed operational specification, coding manual, final questionnaire export/hash, pilot timing result, and precision decision with executable simulation outputs. Report sample flow, cell/profile denominators, all decision transitions, both reliance directions, uncertainty and every deviation with timing and rationale. Use analysis/study2/readiness.py to list unresolved analysis/operational fields; a material-release audit alone does not certify these fields.
