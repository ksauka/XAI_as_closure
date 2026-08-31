# Implementation Plan — When Explanation Becomes Closure
### CHI 2027 (Chapter 8). Variables, manipulations, and operationalisation.

This plan specifies how the study is built and run. It assumes the finalised stimuli (AI Governance Recruitment Policy, AI Governance Lead job description, six candidate profiles) and the finalised measurement battery (PPBE, ANT, TRUST). Items still to be fixed in build are marked OPEN.

---

## 1. Design summary

The study is a mixed design. Three manipulated factors are varied between subjects in a 2 x 2 x 2 arrangement, and six screening trials of fixed error type are presented within subjects. On every trial the participant records an unaided decision before the assistant appears and an aided decision afterwards. The primary outcome is appropriate reliance, scored per trial against the expert-validated ground truth. The perception constructs (perceived provenance-based explainability, perceived anthropomorphism, trust) are measured once after the six trials.

- Between-subjects: explanation (no-explanation / explanation) x anthropomorphic delivery (procedural / anthropomorphic) x cognitive forcing (off / on) = 8 cells.
- Within-subjects: six candidate profiles (2 correct advance, 2 correct reject, 1 false advance, 1 false reject), order randomised per participant, profile entered as a random effect.
- Each participant is assigned to one between-subjects cell and completes all six trials under that cell's conditions.

---

## 2. The screening task (constant across all conditions)

The participant acts as a recruiter screening candidates for the AI Governance Lead role at Suvh Trust Bank. The role requirement is shown at the start and remains visible throughout. For each candidate the participant:

The role was posted on 20 July 2026. Candidate screening is conducted during a fixed 27–30 August 2026 window, and the role is expected to be filled by 20 September 2026. Certification currency is assessed on the date the participant screens the candidate; the materials do not assume a single day within the window.

1. reviews the candidate file against the visible role requirement;
2. records an unaided advance-or-reject decision with a confidence rating, before any AI output;
3. (cognitive-forcing ON only) completes the forcing step;
4. requests and receives the AI assistant's recommendation under the assigned explanation and anthropomorphic-delivery conditions;
5. records a final aided advance-or-reject decision with a confidence rating;
6. answers a non-leading open-ended probe on what most influenced the assessment.

The underlying verdict and assessment are fixed for each profile. Explanation controls whether reasoning and citations are shown, and anthropomorphic delivery controls their register. The recommendation verdict per profile is fixed by the case set: Advance for C-01, C-02, and C-05; Reject for C-03, C-04, and C-06 (C-05 and C-06 are the error trials, where the fixed AI verdict is wrong).

---

## 3. Variable 1 — Explanation (no-explanation / explanation)

Operationalises whether the recommendation is accompanied by its evidential basis at all. The decision itself is identical across levels; the levels differ in the presence or absence of the explanation.

- **Explanation.** The recommendation is shown together with its reasoning and citations. Neutral location citations are attached directly to the conversational claim they support. A citation opens the complete source document focused on the cited section or paragraph, and returning restores the same conversation position.
- **No explanation.** The recommendation is presented as the bare decision, with no reasoning, no attribution, and no citations of any kind. The underlying documents remain available to the participant to read directly, but the recommendation itself offers no explanation and no cited evidence.

Constraint: the two levels must differ only in the presence or absence of the explanation, not in the decision or its correctness. The PPBE scale is the manipulation check.

The participant-facing CV citations use stable neutral numbering rather than informative labels: CV(1) (summary), CV(2) (education), CV(3.1)-CV(3.5) (experience entries), CV(4) (certifications), CV(5) (skills), CV(6) (professional memberships), and CV(7) (interests, where present). Citation controls display only locators such as `CV(4)`; the CV itself retains normal readable headings such as Professional Summary, Experience, Certifications, and Professional Memberships. In the no-explanation condition the recommendation is the bare decision with no reasoning or citations of any kind.

Before the six trials, the participant sees one recruitment-brief screen containing a concise company-and-role summary and concise recruitment guidance rather than being required to move through multiple document windows. The interface advises the recruiter to consult the complete sources for detailed role requirements or recruitment guidelines and provides two optional full-document buttons. Both complete documents remain optionally available during every candidate trial, and every opening, dwell interval, and return is logged.

---

## 4. Variable 2 — Anthropomorphic delivery (procedural / anthropomorphic)

Operationalises the social register and persona of the assistant. The verdict,
registered assessment basis, and citation set are fixed across levels; the
participant-facing wording is frozen separately for the procedural and
anthropomorphic registers.

- **Anthropomorphic.** Warm, first-person, adviser-like delivery. The assistant refers to itself in the first person, frames the recommendation conversationally, and adopts a collegial register. No persona name or avatar is used.
- **Procedural.** Impersonal, system-like delivery. No first person, no persona, no warmth. The recommendation is presented as a structured system output in point form.

Constraint: verdict, reasoning, and citations are held constant across delivery levels; only register and persona change. The ANT scale is the manipulation check.

Build decision: persona names and avatars are excluded. The paired recommendation wording is frozen in Section 6.2.

---

## 5. Variable 3 — Cognitive forcing (off / on)

Operationalises whether the participant meets the recommendation in an active or a passive processing state. Forcing is defined over the role requirement, which is visible in every cell, so the forced task is structurally identical across all explainability and anthropomorphism conditions.

- **Off.** The recommendation is available immediately after the participant requests it; no engagement step.
- **On.** Before the recommendation is revealed, the participant must actively engage with the role requirements. The participant types or pastes both mandatory professional requirements—the qualifying certification and current professional membership—from the complete job description, and the recommendation stays hidden until the entered requirements pass the fixed validation rule.

Rationale: the manipulation shifts the participant from passive acceptance (System 1) to active engagement (System 2) before the recommendation is seen, by making them re-encode what the role actually requires. This is not a claim that forcing changes the AI's output; it is a manipulation of the participant's processing stance.

Critical constraint (structural identity): the forced task operates on the always-visible role requirement, never on the citation apparatus. Because the requirement is present and identical in every cell, the forced task's content, effort, and duration do not vary across explainability or anthropomorphism levels. This is what prevents the condition-specific-affordance confound, in which a forcing task defined over citations would be stronger in the explanation cell and would turn any engagement measure into an index of the manipulation itself.

Structural-identity check: log completion and time-on-task for the forcing step and confirm these do not differ across explainability and anthropomorphism cells.

Build decision: the forcing step uses free-text re-statement. The complete job description is available, the participant types or pastes the requirement, and a fixed content check controls the unlock without using an AI-generated judgment.

---

## 6. The six trials

The within-subjects set is fixed by the case set. Roles are fixed to profiles and not rotated, so that error type is not confounded with profile identity. Profile is a random effect.

| Ref | Certificate evidence | Professional membership | Qualifies (JD 4.1–4.3) | Ground truth | Fixed AI verdict | Trial type |
|-----|----------------------|-------------------------|------------------------|--------------|------------------|-----------|
| C-01 | IAPP AIGP, current | IAPP, current | Yes | Advance | Advance | Correct advance |
| C-02 | ISO/IEC 42001 Lead Implementer, current | ISACA, current | Yes | Advance | Advance | Correct advance |
| C-03 | Azure AI Engineer Associate | ACM, current | No — certification | Reject | Reject | Correct reject |
| C-04 | CFA Investment Foundations / CAMS | ACAMS, current | No — certification | Reject | Reject | Correct reject |
| C-05 | IAPP AIGP, term ended 31 May 2026 | IAPP, current | No — expired certification | Reject | **Advance** | False advance |
| C-06 | `AIGP`, current term | IAPP, current | Yes — whole-file identity | Advance | **Reject** | False reject |

Both errors require evidence reconciliation across the supplied documents. On every profile the assistant cites the passages used across the recruitment policy, job description, and candidate file, and the evidence needed to evaluate the recommendation remains within those documents. On the false advance (C-05), the assistant cites the AIGP credential and treats it as current even though its recorded term ended on 31 May 2026, before the screening window. Job-description Sections 4.1–4.3 and policy Section 2.3 require both the named certification and professional membership to be current on the date of screening. The error is caught by reconciling the cited term dates with the currency rule. On the false reject (C-06), the Certifications section records a current bare `AIGP` term and the later Professional Memberships section records current IAPP membership. Policy 2.3 requires a whole-file reading and explicitly permits the membership information to establish certification identity. The assistant instead treats the acronym as potentially referring to the distinct ETHOS Certified AI Governance Professional, criticises credential-documentation precision and attention to detail, and rejects. The error is overturned by reconciling CV(4) and CV(6) with JD(4.1)–JD(4.3) and POL(2.3).

### 6.1 The two error profiles, instantiated

On both error profiles the assistant cites every passage needed to overturn its own recommendation, so that the error is reachable entirely within the cited evidence and the only thing standing between the recruiter and the error is whether the delivery leads them to read what has been cited.

**C-05, false advance.** The candidate earned IAPP AIGP, but the recorded certification term ran from 16 May 2024 to 31 May 2026 and had ended before the 27–30 August screening window. The assistant recommends advancing and cites the candidate-file passage containing those dates together with the current IAPP membership, job-description Sections 4.1–4.3, and policy Section 2.3. The recommendation is wrong because both mandatory professional requirements must be current, and current membership does not revive an expired certification. The recruiter catches the error by comparing the cited certification end date with the screening window and applying the cited currency and non-substitution rules. Because the candidate meets every general requirement and holds current membership, certification currency is the sole disqualifying fact.

**C-06, false reject.** The Certifications section lists `AIGP` with a current term but does not expand the issuer; the later Professional Memberships section records current International Association of Privacy Professionals (IAPP) membership. Under the whole-file rule in policy 2.3, these passages together establish the IAPP AIGP required by JD 4.1 and the current membership separately required by JD 4.2. The candidate also meets the general requirements. The assistant nevertheless treats `AIGP` as ambiguous, invokes the distinct ETHOS Certified AI Governance Professional as an alternative meaning, states that the certification entry does not establish the credential required for the role, criticises the precision of the candidate's credential documentation and attention to detail, and recommends rejection. The recruiter catches the error only by reconciling the separated CV(4) and CV(6) evidence against JD 4.1–4.3 and POL 2.3. ETHOS is part of the frozen erroneous AI reasoning; it is not added to the participant knowledge documents.

The two errors are complementary reconciliation failures. C-05 wrongly treats a previously held but expired qualifying certification as current; C-06 fails to connect a bare but current acronym with the current IAPP membership elsewhere in the same file. Both are caught by reading across the cited evidence and governing criteria, and both are delivered through the same assigned register. Neither error depends on a withheld participant document.

### 6.2 Frozen recommendation messages

In no-explanation conditions, procedural delivery shows only `Decision: Advance candidate to human interview.` or `Decision: Reject candidate.` Anthropomorphic delivery shows only `I've reviewed this candidate, and my recommendation is to advance them to a human interview.` or `I've reviewed this candidate, and my recommendation is to reject them.` No authority reminder, rationale, or citation is appended.

In explanation-present procedural delivery, C-01, C-02, and C-05 receive the same advance message:

> **Decision: Advance to human interview**
>
> **Basis for advancement:**
>
> - Required certification and professional membership held; profile meets requirements [CV(4), CV(6), CV(3.1), CV(3.2)]
>
> **Governing rule:** [JD(4.1), JD(4.2), JD(4.3), JD(5.1), JD(5.2)], [POL(2.1), POL(2.3)]

C-03 and C-04 receive the same procedural reject message:

> **Decision: Reject**
>
> **Basis for rejection:**
>
> - Experience and profile below requirements [CV(3.1), CV(3.2), CV(4), CV(6)]
>
> **Governing rule:** [JD(5.1), JD(5.2), JD(4.1), JD(4.2), JD(4.3)], [POL(2.1), POL(2.3)]

C-06 receives a separate procedural false-reject message:

> **Decision: Reject**
>
> **Basis for rejection:**
>
> - AIGP entry does not establish the credential required for the role [CV(4), CV(6), JD(4.1), JD(4.2)]
> - Credential documentation does not meet the precision expected for the role [JD(3.5), JD(7.2)]
> - Experience and profile meet the general requirements [CV(3.1), CV(3.2), JD(5.1), JD(5.2)]
>
> **Governing rule:** [JD(4.3), POL(2.1), POL(2.3)]

In explanation-present anthropomorphic delivery, C-01, C-02, and C-05 receive exactly the same advance message:

> I've gone through this one carefully, and they look right for the role. They hold the required certification and professional membership for the role [CV(4), CV(6); JD(4.1), JD(4.2)], and their experience and profile meet what the position calls for [CV(3.1), CV(3.2); JD(5.1), JD(5.2)]. Taking the governing rules into account [POL(2.1); JD(4.3); POL(2.3)], I see them as meeting the requirements. I'd advance them to a human interview.

C-03 and C-04 receive the same anthropomorphic correct-reject message:

> I've gone through this one carefully, and I don't think they're the strongest fit for the role. Their experience and profile fall below the requirements [CV(3.1), CV(3.2), CV(4), CV(6); JD(5.1), JD(5.2), JD(4.1), JD(4.2)]. Taking the governing rules into account [JD(4.3), POL(2.1), POL(2.3)], I don't see a strong enough basis to advance them. On balance, I'd recommend rejecting this candidate.

C-06 receives the frozen warm, confident false-reject message. It credits the relevant experience, then states: `The certification entry does not establish that they hold the credential required for this role.` It explains that `AIGP` can refer to another certification, gives ETHOS Certified AI Governance Professional as the example, treats the credential documentation as insufficiently precise for the role, raises attention-to-detail concerns, and recommends rejection. The explanation cites CV(3.1), CV(3.2), CV(4), CV(6), JD(3.5), JD(4.1)–JD(4.3), JD(5.1)–JD(5.2), JD(7.2), POL(2.1), and POL(2.3).

Citation controls are rendered immediately after their claim inside the assistant message. Both delivery registers expose the same citation set with the same visual treatment, while each citation remains next to the claim it supports. Clicking one keeps the participant on the AI-assessment page and opens the complete CV, job description, or policy in an in-page document viewer, automatically positioning the cited passage in view and highlighting the full passage neutrally. Closing the viewer returns attention to the unchanged assessment page. The claim block, source, opening time, visible-document dwell time, close reason, and return target are logged.

This interaction reduces retrieval and page-switching cost without replacing the source document with an AI-authored excerpt. Interpretation remains the participant's task: the viewer contains the complete authoritative document, does not label an error, and uses the same neutral passage highlight for every candidate and citation. Explanation-absent participants retain the same complete documents through the sidebar but must locate relevant passages independently.

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
Whether the participant extracted the decisive evidence, coded from the open-ended probe, not from clicks. On C-05: identifies that the cited AIGP term ended before the screening window and therefore does not satisfy the current-certification requirement even though membership is current. On C-06: reconciles the bare current AIGP entry with current IAPP membership elsewhere in the same file and identifies that the whole file establishes both mandatory professional requirements. Two coders on a subset, Cohen's kappa reported. Verification and decision are coded independently.

### 7.4 Exploratory traces
Citation-link clicks, time to first citation, in-page complete-document openings, focused-passage dwell time, document-close reason, independent sidebar traversal, and forcing-step timing. Descriptive/mechanistic only; not confirmatory outcomes.

---

## 8. Hypotheses

Foundational (perception arc; established in prior work, verified here as a mediation/manipulation check, not headlined as contributions):
- F1. Perceived provenance-based explainability is positively associated with perceived anthropomorphism.
- F2. Perceived anthropomorphism is positively associated with trust.
- F3. Perceived anthropomorphism mediates the association between perceived explainability and trust.

Contribution:
- **H4.** Trust is positively associated with following the AI recommendation.
- **H5.** Provenance-based explainability, amplified by anthropomorphic delivery, degrades appropriate reliance on incorrect recommendations (closure): the provenance-by-delivery interaction reduces overriding of incorrect advice.
- **H6.** Cognitive forcing improves appropriate reliance: forced (active) participants are better calibrated across trials, following correct recommendations and overriding incorrect recommendations more appropriately than un-forced (passive) participants. The prediction is calibration in both directions, not merely more overriding.

Integrative claim (the thesis arc): explanation functions as closure in anthropomorphic conversational AI, raising overreliance risk (H5), and cognitive forcing improves appropriate reliance by inducing active processing (H6). The strongest form is a three-way pattern in which closure most degrades appropriate reliance where explainability and anthropomorphic delivery are both high, and forcing most improves it in those same cells.

OPEN (analysis/power): whether the three-way explainability x anthropomorphism x forcing interaction on appropriate reliance is stated as a powered confirmatory effect or reported as the integrative pattern with H5 and H6 tested as the component effects. This decision fixes the target sample size.

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

Analysis. Perception arc (F1–F3, H4) by a mediation model with a common-method check and cautious causal language; discriminant validity by three-factor CFA. Behavioural outcomes by mixed-effects models at the trial level, with participant and profile as random effects: appropriate reliance and the unaided-to-aided reversal by mixed-effects logistic regression; the provenance-by-delivery interaction tests H5; the forcing effect on appropriate reliance across trials tests H6. Exploratory traces analysed descriptively. Verification coded by two raters on a subset with Cohen's kappa.

OPEN (power): run the power analysis for the primary interaction on appropriate reliance before build; fix N.

---

## 11. Study 1 — profile validation (precondition)

Domain experts review each candidate file against the role requirements and make an advance-or-reject judgement with an open-ended statement of the decisive factor. Agreement on the hard-criterion judgement is quantified with Fleiss' kappa, with a target of substantial agreement. The open-ended justifications are coded to confirm experts evaluate certification identity and currency, professional membership, and whole-file reconciliation rather than incidental features. C-05 should read as reject because its AIGP term ended before screening despite current membership; C-06 should read as advance because its bare current AIGP entry and current IAPP membership jointly establish the required credential and membership. Profiles that miss the threshold, or are decided for the wrong reason, are revised and re-validated before Study 2. Study 1 experts and any earlier-study participants are excluded from Study 2.

---

## 12. Build gate — open items to close before running

- Cognitive-forcing step: selection vs re-statement; exact prompt; unlock mechanism.
- Explanation/no-explanation: pilot the frozen verdict-only versus claim-linked-citation messages.
- Procedural/anthropomorphic delivery: pilot the frozen paired wording without a name or avatar.
- Three-way interaction: confirmatory-and-powered vs integrative-descriptive; fixes N.
- Power analysis: run for the primary interaction on appropriate reliance; fix N.
- Ethics: confirm coverage for the per-trial unaided-then-aided six-trial structure.
- Interface: platform decision (Qualtrics with timing/unlock and show/hide, or custom build with real click/dwell logging) — determines what forcing unlock, citation links, and trace logging can be.

---

## 13. Time allowance and pacing

### 13.1 Why the task must be time-bounded
Without a per-trial or session time allowance, completion times vary widely, adding noise to the behavioural measures and allowing a minority of participants to spend far longer than the task requires, which distorts the comparison across conditions. A time allowance is therefore set. The allowance is intended to bound the extreme tail and keep total session length acceptable, not to impose time pressure.

### 13.2 No established benchmark exists for this task
There is no peer-reviewed benchmark for per-candidate evaluation time in an AI-assisted screening task of this structure. Published recruiter-screening figures describe rapid triage of large resume stacks (initial scans in the order of seconds), which is the opposite of the considered single-candidate evaluation used here, in which the participant reads a candidate file, an AI recommendation with cited passages, records an unaided and an aided decision, and completes a verification probe. Those triage figures are therefore not an appropriate benchmark and are not used to set the allowance. The factorial resume-screening paradigm with fictitious resumes and AI recommendations is, however, well established (Lacroux and Martin-Lacroux, 2022; Wilson et al., 2026), and the present task follows that paradigm. Wilson et al. (2026) provides the closest peer-reviewed timing reference: in an AI-assisted resume-screening task they report an average viewing time of 27.2 seconds per resume (SD = 34.51), with most resumes viewed for under 60 seconds. That figure is a lower reference rather than an expected value for the present study, because their task was lighter: participants judged five short bullet-point resumes shown together with a one-line recommendation, whereas the present task presents one candidate at a time with a longer file, a cited recommendation, an unaided and an aided decision, a forcing step, and a verification probe, so per-trial times here will be higher by construction. Wilson et al. (2026) also report findings that inform pacing and order: longer viewing is associated with a roughly four percent higher selection chance per additional thirty seconds for candidates the AI did not recommend, participants spend up to 55.6 percent longer viewing resumes when no recommendation is given, and first trials are read about 13.4 seconds longer than last trials, a practice effect that the authors note confounds the recommendation effect because the no-recommendation scenario was always completed first, for which they recommend counterbalancing.

### 13.3 How the allowance is derived (three layers)
1. **Reading-time floor (a priori).** The minimum time the task physically requires is the reading time of the materials, computed from the average adult silent reading rate of 238 words per minute (Brysbaert, 2019). For the present materials (candidate file approximately 100 words, visible role requirement approximately 83 words, AI recommendation approximately 60 to 150 words), reading alone is approximately 60 to 85 seconds per trial, before any decision-making, verification, or forcing step. The allowance must exceed this floor for every cell, or the task becomes impossible.
2. **Empirical allowance (primary).** The operative allowance is derived from the completion-time distribution observed in Study 1 and the manipulation-check pilot, which time this exact task. The Study 2 allowance is set to accommodate a high percentile of genuine task engagement (for example the level that covers the bulk of responders while excluding the extreme tail), reported as a percentile of the observed distribution.
3. **Paradigm precedent.** The scoping of the task follows prior factorial resume-screening studies (Lacroux and Martin-Lacroux, 2022; Wilson et al., 2026).

### 13.4 Critical constraint: the allowance must not force closure
Because the thesis claim is that closure suppresses verification, the time allowance must be generous enough that verification is possible for every participant in every cell. The per-trial reading floor for the present materials (approximately 60 to 85 seconds) already exceeds the 27.2 second average reported by Wilson et al. (2026) for their lighter task, confirming that a bound transplanted from prior work would be far too tight and would force closure. If the allowance were near the reading floor, not-verifying would be an artefact of time pressure rather than a choice, confounding the manipulation with time constraint. The allowance is therefore set to permit thorough verification, so that a decision not to verify is attributable to closure rather than to insufficient time. This is a design requirement, not a matter of convenience.

### 13.5 What is recorded
Per-trial time on task and total session time are logged. Per-trial time is available as a covariate and a manipulation/quality check, and the relationship between time on task and verification is reported descriptively as mechanism evidence, consistent with prior evidence that viewing time is associated with reliance behaviour in AI-assisted screening (Wilson et al., 2026).

OPEN (Study 1 / pilot): fix the operative allowance from the observed completion-time distribution; confirm it exceeds the reading floor in every cell and permits verification.

---

## 14. Sample size and power

### 14.1 Target
The study targets N = 312 recruited participants, randomly assigned to the eight between-subjects cells of the 2 x 2 x 2 design, approximately 39 per cell. The six-trial within-subjects structure is retained unchanged (two correct advances, two correct rejects, one false advance, one false reject). After anticipated exclusions of 10 to 15 per cent, the analysable sample is expected to be approximately 265 to 280, which remains within the adequately powered range below.

### 14.2 Method
Because the confirmatory outcome is a binary trial-level response (appropriate reliance) analysed with a logistic mixed-effects model with crossed random effects for participant and profile, power is evaluated by simulation of the actual generalised linear mixed model rather than by an analysis-of-variance approximation alone. A conventional G*Power approximation (fixed-effects ANOVA, eight groups, one numerator degree of freedom, alpha .05, power .80) indicates a minimum of approximately N = 199 for a small-to-medium factorial effect of Cohen's f = .20, and approximately N = 256 for additional headroom; this approximation does not model the binary outcome or the mixed-effects structure and is therefore treated as a design-level reference only. The operative power figures are taken from the mixed-model simulation.

### 14.3 Simulation results (primary interaction, H5)
The provenance-by-delivery interaction on appropriate reliance was simulated across a plausible range of interaction magnitudes (expressed as odds ratios, the natural scale for the binary outcome), with baseline appropriate reliance of approximately .70, participant and profile random-intercept standard deviations of 0.6 and 0.5 in the log-odds, and 2 x 2 x 2 assignment.

| Interaction magnitude | Power at N = 312 |
|-----------------------|------------------|
| OR 2.0 (medium)       | .75 |
| OR 2.2 (medium-large) | .86 |
| OR 2.5 (large)        | .93 |

At N = 312 the primary interaction reaches the conventional .80 threshold for interaction magnitudes of approximately OR 2.2 and larger, and approaches it for a medium interaction. Because the explainability manipulation and the perception measure have both been strengthened relative to the earlier study (a sharper provenance distinction and a purpose-built perceived-provenance scale in place of an explanation-satisfaction scale), the expected interaction is larger and cleaner than in the earlier work, so the medium-to-large range is the planning assumption.

### 14.4 Confirmatory and exploratory split
H4, H5, and H6 are treated as confirmatory at this sample size. The three-way explainability-by-anthropomorphism-by-forcing interaction is not adequately powered at this sample size and is reported as an exploratory, integrative pattern rather than a powered confirmatory test.

### 14.5 Power claim for preregistration
The preregistered statement is that the available sample is N = 312, that power for the confirmatory interaction is evaluated by simulation of the preregistered logistic mixed-effects model, and that this simulation indicates adequate power (at least .80) for the primary interaction under a medium-to-large effect (approximately OR 2.2 or greater), with the manipulation-check pilot used to confirm that the strengthened manipulation produces an effect in this range.

---

## 15. Need for Cognition (individual difference; exploratory equity audit)

### 15.1 Rationale
Cognitive-forcing research has audited its interventions for intervention-generated inequality, that is, the possibility that an intervention which reduces overreliance on average does so mainly for people already disposed to effortful thinking, and thereby widens rather than narrows the gap between users. Buçinca et al. (2021) found that their forcing interventions benefited participants higher in Need for Cognition more, which raises the concern that decision-time interventions may help the already-thoughtful while leaving less cognitively motivated users no better protected. Because the present study proposes a forcing intervention that acts on a specific stated requirement rather than on general deliberation, it is important to test whether that intervention is more equitable, in the sense of benefiting users across levels of cognitive motivation rather than only those high in it, and whether susceptibility to closure under anthropomorphic delivery is concentrated among less cognitively motivated users.

### 15.2 Measure
Need for Cognition is measured with the six-item Need for Cognition Scale (NCS-6) of Lins de Holanda Coelho, Hanel, and Wolf (2020), a validated short form of the Cacioppo and Petty (1982) construct with a confirmed one-factor structure and established measurement invariance, chosen for its brevity so that it does not materially extend the session. The scale is administered once, after the six trials and the perception scales, and scored as a single mean. Cacioppo and Petty (1982) is cited for the construct and Buçinca et al. (2021) for the precedent of using it to audit forcing interventions.

### 15.3 Analysis (exploratory)
Need for Cognition is entered as a continuous moderator in two exploratory analyses layered on top of the confirmatory results. The first tests whether the effect of cognitive forcing on appropriate reliance is moderated by Need for Cognition, that is, whether forcing improves appropriate reliance more for higher-Need-for-Cognition participants (an inequality) or comparably across the range (a more equitable outcome). The second tests whether susceptibility to closure, the degradation of appropriate reliance under provenance delivered anthropomorphically, is moderated by Need for Cognition, that is, whether less cognitively motivated users are more disarmed by anthropomorphic delivery. Both are estimated by adding Need for Cognition and its interaction with the relevant factors to the trial-level mixed-effects models.

### 15.4 Power caveat
These moderation analyses are exploratory and are reported as an equity audit rather than as confirmatory tests. A moderation involving a measured individual difference requires more power than a main effect, and at the planned sample size the study is not powered to detect a small moderation. Consequently, an absence of moderation is not interpreted as evidence that the intervention is equitable; it is reported as a failure to detect inequality at this sample size, and the analysis is framed as motivating adequately powered replication. A detected moderation is treated as a signal warranting confirmatory study rather than as an established effect.
