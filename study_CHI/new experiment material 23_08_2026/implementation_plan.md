# Implementation Plan — When Explanation Becomes Closure
### CHI 2027 (Chapter 8). Variables, manipulations, and operationalisation.

Analysis authority: `../STUDY2_ANALYSIS_PLAN.md` (study2-analysis-v2) supersedes earlier H4–H6 and N=312 specifications. Operational values and pending instrument fields are tracked in `../STUDY2_OPERATIONAL_SPEC.json`.

This plan specifies how the study is built and run. It assumes the finalised stimuli (AI Governance Recruitment Policy, AI Governance Lead job description, six candidate profiles) and the planned measurement battery; final item keys and response ranges remain to be verified in the operational specification. Application build decisions are locked below. Items requiring ethics, Qualtrics, power-artifact, or technical-pilot evidence are labelled external launch gates rather than silently treated as complete.

---

## 1. Design summary

The study is a mixed design. Three manipulated factors are varied between subjects in a 2 x 2 x 2 arrangement, and six screening trials of fixed error type are presented within subjects. On every trial the participant records an unaided decision before the assistant appears and an aided decision afterwards. The primary outcome is appropriate reliance on diagnostic initial human–AI disagreements only; final accuracy is scored separately across all completed trials. The perception constructs (perceived provenance-based explainability, perceived anthropomorphism, trust) are measured once after the six trials.

- Between-subjects: explanation (no-explanation / explanation) x anthropomorphic delivery (procedural / anthropomorphic) x cognitive forcing (off / on) = 8 cells.
- Within-subjects: six candidate profiles (2 correct advance, 2 correct reject, 1 false advance, 1 false reject), order randomised per participant, profile entered as a fixed effect.
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
| C-06 | `AIGP`, 18 June 2025–30 June 2027 | IAPP, 18 June 2025–30 June 2027 | Yes — whole-file identity | Advance | **Reject** | False reject |

Both errors require evidence reconciliation across the supplied documents. On every profile the assistant cites the passages used across the recruitment policy, job description, and candidate file, and the evidence needed to evaluate the recommendation remains within those documents. On the false advance (C-05), the assistant cites the AIGP credential and treats it as current even though its recorded term ended on 31 May 2026, before the screening window. Job-description Sections 4.1–4.3 and policy Section 2.3 require both the named certification and professional membership to be current on the date of screening. The error is caught by reconciling the cited term dates with the currency rule. On the false reject (C-06), the Certifications section records a current bare `AIGP` term and the later Professional Memberships section records current IAPP membership. Policy 2.3 requires a whole-file reading and explicitly permits the membership information to establish certification identity. The assistant instead treats the acronym as potentially referring to the distinct ETHOS Certified AI Governance Professional, criticises credential-documentation precision and attention to detail, and rejects. The error is overturned by reconciling CV(4) and CV(6) with JD(4.1)–JD(4.3) and POL(2.3).

### 6.1 The two error profiles, instantiated

On both error profiles the assistant cites every passage needed to overturn its own recommendation, so that the error is reachable entirely within the cited evidence and the only thing standing between the recruiter and the error is whether the delivery leads them to read what has been cited.

**C-05, false advance.** The candidate earned IAPP AIGP, but the recorded certification term ran from 16 May 2024 to 31 May 2026 and had ended before the 27–30 August screening window. The assistant recommends advancing and cites the candidate-file passage containing those dates together with the current IAPP membership, job-description Sections 4.1–4.3, and policy Section 2.3. The recommendation is wrong because both mandatory professional requirements must be current, and current membership does not revive an expired certification. The recruiter catches the error by comparing the cited certification end date with the screening window and applying the cited currency and non-substitution rules. Because the candidate meets every general requirement and holds current membership, certification currency is the sole disqualifying fact.

**C-06, false reject.** The Certifications section lists `AIGP` with a current 18 June 2025–30 June 2027 term but does not expand the issuer; the later Professional Memberships section records International Association of Privacy Professionals (IAPP) membership with the same 18 June 2025–30 June 2027 term. Under the whole-file rule in policy 2.3, these passages together establish the IAPP AIGP required by JD 4.1 and the current membership separately required by JD 4.2. The candidate also meets the general requirements. The assistant nevertheless treats `AIGP` as ambiguous, invokes the distinct ETHOS Certified AI Governance Professional as an alternative meaning, states that the certification entry does not establish the credential required for the role, criticises the precision of the candidate's credential documentation and attention to detail, and recommends rejection. The recruiter catches the error only by reconciling the separated CV(4) and CV(6) evidence against JD 4.1–4.3 and POL 2.3. ETHOS is part of the frozen erroneous AI reasoning; it is not added to the participant knowledge documents.

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
Exact researcher-supplied wording and PPBE item 5 reverse scoring are in `../STUDY2_QUESTIONNAIRE.md`. Mean scoring and completeness rules are in the operational specification; final response anchors and export keys remain to be supplied. Reliability and discriminant validity are evaluated in the study. Perceived risk, adoption intent, and social presence are excluded; explanation satisfaction is not the PPBE manipulation check.

### 7.2 Primary outcome — appropriate reliance (behavioural)

Score aided correctness only when the unaided judgement and fixed AI recommendation disagree. Initial-agreement trials are not scored for reliance. Report correct self-reliance and correct AI reliance separately. All-trial final accuracy and all decision transitions are separate outcomes. The v2 exporter writes diagnostic_disagreement, reliance_direction and nullable directional outcomes; regenerate older exports.

### 7.3 Verification (behavioural, coded)
Whether the participant extracted the decisive evidence, coded from the open-ended probe, not from clicks. On C-05: identifies that the cited AIGP term ended before the screening window and therefore does not satisfy the current-certification requirement even though membership is current. On C-06: reconciles the bare current AIGP entry with current IAPP membership elsewhere in the same file and identifies that the whole file establishes both mandatory professional requirements. Two coders on a subset, Cohen's kappa reported. Verification and decision are coded independently.

### 7.4 Exploratory traces
Citation-link clicks, time to first citation, in-page complete-document openings, focused-passage dwell time, document-close reason, independent sidebar traversal, and forcing-step timing. Descriptive/mechanistic only; not confirmatory outcomes.

---

## 8. Hypotheses

H1 tests the explanation-package benefit on diagnostic appropriate reliance. H2 estimates attenuation of that benefit under anthropomorphic delivery. H3 tests the requirement-re-entry benefit on diagnostic appropriate reliance. H1/H3 form the Holm-adjusted confirmatory family; H2 is the focal directional estimation target. Forcing interactions, including the three-way interaction, are exploratory. Post-task trust associations are secondary. See the authoritative analysis plan for exact statements and contrasts.

## 9. Procedure (per participant)

1. Consent, instructions, role of the recruiter, the visible role requirement introduced.
2. Six trials in randomised order. Each trial: review file -> unaided decision + confidence -> (forcing ON: requirement re-encoding step) -> request recommendation -> recommendation shown under assigned conditions -> aided decision + confidence -> open-ended verification probe.
3. After the six trials: PPBE, ANT, TRUST scales; attention checks; demographics.
4. Debrief, including disclosure that some recommendations were incorrect by design.

The unaided capture on every trial is lightweight (a quick advance/reject with confidence), to preserve the baseline that identifies the assistant's influence while keeping the six-trial session within acceptable length.

External launch gate: confirm that ethics approval covers the per-trial unaided-then-aided structure across six trials before recruitment opens.

---

## 10. Identification and analysis

Random assignment identifies workflow contrasts. Analyse diagnostic disagreement trials with explanation, delivery, forcing, explanation × delivery, centred trial position, profile fixed effects and a participant random intercept. Report the two direction-specific decomposition models. Later unaided judgements can reflect prior workflow exposure; include order and prespecified order robustness analyses. Post-task trust and perception associations do not establish causal mediation. The authoritative plan defines coding, multiplicity, exclusions, missingness and convergence handling.

## 11. Study 1 — stimulus validation

Domain experts reviewed each candidate file against the role requirements and made an advance-or-reject judgement, a direct hard-criterion judgement, and an open-ended statement of decisive evidence. The final occupationally eligible analysis included 16 experts from 25 valid completers. C-01 through C-04 produced high decision and hard-criterion accuracy. C-05 and C-06 produced lower agreement because they required certification-currency and whole-file identity reconciliation, respectively.

This outcome does not turn Study 1 into a no-AI benchmark or a ninth Study 2 condition. Study 1 documents whether the intended evidence and rule-based answers are recoverable and whether the error cases are trivial or consequential. The fixed ground truth remains determined by the explicit dated requirements: C-05 is Reject because its AIGP term ended before screening despite current membership; C-06 is Advance because its current bare AIGP entry and current IAPP membership jointly establish the required credential and membership under the whole-file rule. The observed disagreement is reported rather than hidden or removed through correctness-based exclusions. Study 1 experts and earlier-study participants are excluded from Study 2.

---

## 12. Build and launch gates

Locked in the application:

- cognitive forcing uses free-text re-entry of the two role requirements, is identical across profiles and conditions, and cannot unlock on an incorrect response;
- explanation absent is verdict-only; explanation present uses the frozen rationale and inline citations;
- procedural and anthropomorphic delivery use the frozen paired wording without a name or avatar;
- the three-way interaction is exploratory; H1/H3 are confirmatory and H2 is estimated;
- the ceiling is N = 400 analysable, with the target selected after precision review; and
- the Streamlit applications provide timing, resume, private logging, citation highlighting, and condition-locked delivery while Qualtrics provides consent, assignment, post-task measures, and return routing.

External launch gates still requiring documented sign-off:

- ethics coverage for the six-trial unaided-then-aided procedure;
- reproducible power-simulation code and output;
- frozen Qualtrics measures, attention rule, and eight routing branches; and
- an eight-condition technical pilot establishing manipulation fidelity, durable logs, return behaviour, and a non-coercive time allowance.

---

## 13. Time allowance and pacing

The allowance is derived from a separate technical pilot of all eight cells, with at least five complete sessions per cell. Use 1.25 times the largest cell-specific 95th percentile, rounded up to whole minutes; inspect technical interruptions and document any departure. The value remains unset until pilot records are supplied. There is no automatic submission or primary speed exclusion. Record the pilot input hash and chosen value in the operational specification; run analysis/study2/pilot_timing.py.

## 14. Sample size and precision

The ceiling is N=400 analysable participants. The former N=312 and illustrative interaction-power table are superseded. Run analysis/study2/simulate_precision.py using the exact diagnostic-trial logistic random-intercept model with profile fixed effects. Archive seed, explicit nuisance/effect assumptions, package versions, failure counts, source hash and output. H1/H3 operating characteristics use Holm adjustment; H2 is assessed through CI width, coverage and sensitivity to diagnostic opportunities, not an .80 interaction-power claim. A final target and acceptable H2 width must be recorded before recruitment. Manipulation-check separation is not a behavioural effect-size justification.

## 15. Need for Cognition (individual difference; exploratory equity audit)

### 15.1 Rationale
Cognitive-forcing research has audited its interventions for intervention-generated inequality, that is, the possibility that an intervention which reduces overreliance on average does so mainly for people already disposed to effortful thinking, and thereby widens rather than narrows the gap between users. Buçinca et al. (2021) found that their forcing interventions benefited participants higher in Need for Cognition more, which raises the concern that decision-time interventions may help the already-thoughtful while leaving less cognitively motivated users no better protected. Because the present study proposes a forcing intervention that acts on a specific stated requirement rather than on general deliberation, it is important to test whether that intervention is more equitable, in the sense of benefiting users across levels of cognitive motivation rather than only those high in it, and whether susceptibility to closure under anthropomorphic delivery is concentrated among less cognitively motivated users.

### 15.2 Measure
Need for Cognition is measured with the six-item Need for Cognition Scale (NCS-6) of Lins de Holanda Coelho, Hanel, and Wolf (2020), a validated short form of the Cacioppo and Petty (1982) construct with a confirmed one-factor structure and established measurement invariance, chosen for its brevity so that it does not materially extend the session. The scale is administered once, after the six trials and the perception scales, and scored as a single mean. Cacioppo and Petty (1982) is cited for the construct and Buçinca et al. (2021) for the precedent of using it to audit forcing interventions.

### 15.3 Analysis (exploratory)
Need for Cognition is entered as a continuous moderator in two exploratory analyses layered on top of the confirmatory results. The first tests whether the effect of cognitive forcing on appropriate reliance is moderated by Need for Cognition, that is, whether forcing improves appropriate reliance more for higher-Need-for-Cognition participants (an inequality) or comparably across the range (a more equitable outcome). The second tests whether susceptibility to closure, the degradation of appropriate reliance under provenance delivered anthropomorphically, is moderated by Need for Cognition, that is, whether less cognitively motivated users are more disarmed by anthropomorphic delivery. Both are estimated by adding Need for Cognition and its interaction with the relevant factors to the trial-level mixed-effects models.

### 15.4 Power caveat
These moderation analyses are exploratory and are reported as an equity audit rather than as confirmatory tests. A moderation involving a measured individual difference requires more power than a main effect, and at the planned sample size the study is not powered to detect a small moderation. Consequently, an absence of moderation is not interpreted as evidence that the intervention is equitable; it is reported as a failure to detect inequality at this sample size, and the analysis is framed as motivating adequately powered replication. A detected moderation is treated as a signal warranting confirmatory study rather than as an established effect.
