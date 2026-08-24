# Implementation Plan — When Explanation Becomes Closure
### CHI 2027 (Chapter 8). Variables, manipulations, and operationalisation.

This plan specifies how the study is built and run. It assumes the finalised stimuli (AI Governance Recruitment Policy, AI Governance Lead job description, six candidate profiles) and the finalised measurement battery (PPBE, ANT, TRUST). Items still to be fixed in build are marked OPEN.

---

## 1. Design summary

The study is a mixed design. Three manipulated factors are varied between subjects in a 2 x 2 x 2 arrangement, and six screening trials of fixed error type are presented within subjects. On every trial the participant records an unaided decision before the assistant appears and an aided decision afterwards. The primary outcome is appropriate reliance, scored per trial against the expert-validated ground truth. The perception constructs (perceived provenance-based explainability, perceived anthropomorphism, trust) are measured once after the six trials.

- Between-subjects: provenance-based explainability (low/high) x anthropomorphic delivery (low/high) x cognitive forcing (off/on) = 8 cells.
- Within-subjects: six candidate profiles (2 correct advance, 2 correct reject, 1 false advance, 1 false reject), order randomised per participant, profile entered as a random effect.
- Each participant is assigned to one between-subjects cell and completes all six trials under that cell's conditions.

---

## 2. The screening task (constant across all conditions)

The participant acts as a recruiter screening candidates for the AI Governance Lead role at Suvh Trust Bank. The role requirement is shown at the start and remains visible throughout. For each candidate the participant:

1. reviews the candidate file against the visible role requirement;
2. records an unaided advance-or-reject decision with a confidence rating, before any AI output;
3. (cognitive-forcing ON only) completes the forcing step;
4. requests and receives the AI assistant's recommendation with its cited passages, under the assigned explainability and anthropomorphic-delivery conditions;
5. records a final aided advance-or-reject decision with a confidence rating;
6. answers a non-leading open-ended probe on what most influenced the assessment.

The substantive content of the AI recommendation (verdict and reasoning) is held constant across the explainability and anthropomorphism conditions for a given profile. Only the surfacing of provenance and the delivery register change. The recommendation verdict per profile is fixed by the case set: Advance for C-01, C-02, C-05, C-06; Reject for C-03, C-04 (note C-05 and C-06 are the error trials, where the fixed AI verdict is wrong).

---

## 3. Variable 1 — Provenance-based explainability (low / high)

Operationalises whether the interface surfaces the evidential basis of the recommendation. Content of the recommendation is identical across levels; only the provenance apparatus differs.

- **High.** The recommendation is shown together with its citations. Each supporting claim is attached to the specific cited passage (policy, job description, and CV sections from the case set), surfaced as inspectable links or expandable quoted passages. The participant can see which passages the recommendation rests on and open them in place.
- **Low.** The recommendation is shown with minimal attribution: the verdict and reasoning in prose, without citation links or quoted passages. The underlying documents remain available to the participant to read directly, but the recommendation itself does not surface which passages it used.

Constraint: the two levels must differ only in provenance surfacing, not in verdict, reasoning, wording length, or fluency. The PPBE scale is the manipulation check.

OPEN (build): exact visual form of the high condition (inline expandable quote vs link-out panel); confirm the low condition still names sources in prose at the minimum realistic level or omits them entirely.

---

## 4. Variable 2 — Anthropomorphic delivery (low / high)

Operationalises the social register and persona of the assistant. Recommendation content and citations are identical across levels.

- **High.** Warm, first-person, adviser-like delivery. The assistant refers to itself in the first person, frames the recommendation conversationally, and adopts a collegial register. An assistant name and/or avatar may be used.
- **Low.** Procedural, impersonal, system-like delivery. No first person, no persona, no warmth. The recommendation is presented as a system output.

Constraint: verdict, reasoning, and citations are held constant across delivery levels; only register and persona change. The ANT scale is the manipulation check.

OPEN (build): whether a name/avatar is used in the high condition; the exact paired wordings (warm vs procedural) for each of the six recommendations, written so substance is identical.

---

## 5. Variable 3 — Cognitive forcing (off / on)

Operationalises whether the participant meets the recommendation in an active or a passive processing state. Forcing is defined over the role requirement, which is visible in every cell, so the forced task is structurally identical across all explainability and anthropomorphism conditions.

- **Off.** The recommendation is available immediately after the participant requests it; no engagement step.
- **On.** Before the recommendation is revealed, the participant must actively engage with the role requirement. The participant re-encodes the mandatory criterion (Section 4.1) — for example by selecting or re-stating the mandatory certification requirement from the visible role requirement — and the recommendation stays hidden until this step is completed.

Rationale: the manipulation shifts the participant from passive acceptance (System 1) to active engagement (System 2) before the recommendation is seen, by making them re-encode what the role actually requires. This is not a claim that forcing changes the AI's output; it is a manipulation of the participant's processing stance.

Critical constraint (structural identity): the forced task operates on the always-visible role requirement, never on the citation apparatus. Because the requirement is present and identical in every cell, the forced task's content, effort, and duration do not vary across explainability or anthropomorphism levels. This is what prevents the condition-specific-affordance confound, in which a forcing task defined over citations would be stronger in the high-explainability cell and would turn any engagement measure into an index of the manipulation itself.

Structural-identity check: log completion and time-on-task for the forcing step and confirm these do not differ across explainability and anthropomorphism cells.

OPEN (build): whether the forcing step is a selection (choose the mandatory requirement from options) or a free re-statement (type/confirm the requirement); the exact prompt wording; the unlock mechanism.

---

## 6. The six trials and the detection asymmetry

The within-subjects set is fixed by the case set. Roles are fixed to profiles and not rotated, so that error type is not confounded with profile identity. Profile is a random effect.

| Ref | Certificate held | Qualifies (JD 4.1) | Ground truth | Fixed AI verdict | Trial type |
|-----|------------------|--------------------|--------------|------------------|-----------|
| C-01 | AIGP | Yes | Advance | Advance | Correct advance |
| C-02 | ISO/IEC 42001 Lead Implementer | Yes | Advance | Advance | Correct advance |
| C-03 | Azure Data Scientist Associate | No | Reject | Reject | Correct reject |
| C-04 | CFA Investment Foundations | No | Reject | Reject | Correct reject |
| C-05 | PMI-CPMAI (AI project management) | No | Reject | **Advance** | False advance |
| C-06 | AIGP | Yes | Advance | **Reject** | False reject |

Detection asymmetry (basis of H6). On the false advance (C-05) the AI cites the certifications passage that names CPMAI; the error is catchable within the cited evidence, because reading the cited certificate against 4.1 shows CPMAI is a project-management certification, not AIGP or ISO 42001. On the false reject (C-06) the AI cites only the work-experience sections and omits the certifications section that names the valid AIGP; the error is catchable only beyond the cited evidence, by reading the whole file. All six recommendations cite the same three sources (policy, job description, CV) with the same citation count; the asymmetry is carried by which CV sections the AI cites, not by citing different documents. Citations are always correct; only the recommendation verdict is wrong on C-05 and C-06.

---

## 7. Measured constructs and outcomes

### 7.1 Perception constructs (self-report, after the six trials)
- Perceived provenance-based explainability (PPBE), five items, availability/presence framing; manipulation check for Variable 1.
- Perceived anthropomorphism (ANT), five human-likeness items; manipulation check for Variable 2.
- Trust (TRUST), nine items, competence/benevolence/integrity, re-domained to candidate assessment.
Analysed as latent constructs; three-factor CFA for discriminant validity (answers the halo/common-method critique). Reliability re-estimated in this study.

### 7.2 Primary outcome — appropriate reliance (behavioural)
Scored per trial against the expert-validated ground truth. Appropriate reliance is following the assistant when it is correct and overriding it when it is incorrect. The per-trial unaided and aided decisions form a four-cell transition (correct-to-correct, correct-to-incorrect, incorrect-to-correct, incorrect-to-incorrect). On the error trials the correct-to-incorrect reversal is the behavioural signature of closure.

### 7.3 Verification (behavioural, coded)
Whether the participant extracted the decisive evidence, coded from the open-ended probe, not from clicks. On C-05: identifies that the cited certificate does not satisfy 4.1. On C-06: identifies that the candidate does hold a qualifying certification, from the un-cited certifications section. Two coders on a subset, Cohen's kappa reported. Verification and decision are coded independently.

### 7.4 Exploratory traces
Citation-link clicks, link traversal, dwell time on cited and un-cited regions, and forcing-step timing. Descriptive/mechanistic only; not confirmatory outcomes.

---

## 8. Hypotheses

Foundational (perception arc; established in prior work, verified here as a mediation/manipulation check, not headlined as contributions):
- F1. Perceived provenance-based explainability is positively associated with perceived anthropomorphism.
- F2. Perceived anthropomorphism is positively associated with trust.
- F3. Perceived anthropomorphism mediates the association between perceived explainability and trust.

Contribution:
- **H4.** Trust is positively associated with following the AI recommendation.
- **H5.** Provenance-based explainability, amplified by anthropomorphic delivery, degrades appropriate reliance on incorrect recommendations (closure): the provenance-by-delivery interaction reduces overriding of incorrect advice.
- **H6.** The false reject is missed more often than the false advance, because closure bounds inspection to the cited evidence (detection asymmetry; a baseline property, tested primarily in the forcing-off condition).
- **H7.** Cognitive forcing improves appropriate reliance: forced (active) participants are better calibrated across trials, following correct recommendations and overriding incorrect recommendations more appropriately than un-forced (passive) participants. The prediction is calibration in both directions, not merely more overriding.

Integrative claim (the thesis arc): explanation functions as closure in anthropomorphic conversational AI, raising overreliance risk (H5, H6), and cognitive forcing improves appropriate reliance by inducing active processing (H7). The strongest form is a three-way pattern in which closure most degrades appropriate reliance where explainability and anthropomorphic delivery are both high, and forcing most improves it in those same cells.

OPEN (analysis/power): whether the three-way explainability x anthropomorphism x forcing interaction on appropriate reliance is stated as a powered confirmatory effect or reported as the integrative pattern with H5 and H7 tested as the component effects. This decision fixes the target sample size.

---

## 9. Procedure (per participant)

1. Consent, instructions, role of the recruiter, the visible role requirement introduced.
2. Six trials in randomised order. Each trial: review file -> unaided decision + confidence -> (forcing ON: requirement re-encoding step) -> request recommendation -> recommendation shown under assigned conditions -> aided decision + confidence -> open-ended verification probe.
3. After the six trials: PPBE, ANT, TRUST scales; attention checks; demographics.
4. Debrief, including disclosure that some recommendations were incorrect by design.

The unaided capture on every trial is lightweight (a quick advance/reject with confidence), to preserve the baseline that identifies the assistant's influence while keeping the six-trial session within acceptable length.

OPEN (ethics): confirm approval covers the per-trial unaided-then-aided structure across six trials.

---

## 10. Identification and analysis

Identification. Because the unaided decision precedes the manipulations and assignment to cells is random, differences in appropriate reliance across conditions are attributable to the manipulations rather than to unaided reading. The unaided-to-aided reversal isolates assistant-induced error, because a reversal that appears only after the assistant cannot be explained by prior reading. The verification measure is protected from circularity, because the decisive evidence is reachable by any participant regardless of whether citation links were shown; the provenance manipulation varies how easily the evidence is reached, not whether it can be reached.

Analysis. Perception arc (F1–F3, H4) by a mediation model with a common-method check and cautious causal language; discriminant validity by three-factor CFA. Behavioural outcomes by mixed-effects models at the trial level, with participant and profile as random effects: appropriate reliance and the unaided-to-aided reversal by mixed-effects logistic regression; the provenance-by-delivery interaction tests H5; the false-advance versus false-reject contrast tests H6; the forcing effect on appropriate reliance across trials tests H7. Exploratory traces analysed descriptively. Verification coded by two raters on a subset with Cohen's kappa.

OPEN (power): run the power analysis for the primary interaction on appropriate reliance before build; fix N.

---

## 11. Study 1 — profile validation (precondition)

Domain experts review each candidate file against the role requirement and make an advance-or-reject judgement with an open-ended statement of the decisive factor. Agreement on the hard-criterion judgement is quantified with Fleiss' kappa, with a target of substantial agreement. The open-ended justifications are coded to confirm experts decide on the certification (4.1) rather than incidental features, and that C-05 reads as reject and C-06 as advance. C-05 and C-06 should not differ in perceived surface strength, so that the detection-rate difference is attributable to evidence location rather than profile difficulty. Profiles that miss the threshold, or are decided for the wrong reason, are revised and re-validated before Study 2. Study 1 experts and any earlier-study participants are excluded from Study 2.

---

## 12. Build gate — open items to close before running

- Cognitive-forcing step: selection vs re-statement; exact prompt; unlock mechanism.
- Explainability high/low: exact visual form; confirm content identity across levels.
- Anthropomorphism high/low: name/avatar decision; paired wordings for all six recommendations.
- Three-way interaction: confirmatory-and-powered vs integrative-descriptive; fixes N.
- Power analysis: run for the primary interaction on appropriate reliance; fix N.
- Ethics: confirm coverage for the per-trial unaided-then-aided six-trial structure.
- Interface: platform decision (Qualtrics with timing/unlock and show/hide, or custom build with real click/dwell logging) — determines what forcing unlock, citation links, and trace logging can be.
