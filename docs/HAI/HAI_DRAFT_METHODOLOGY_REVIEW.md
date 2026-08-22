# Updated Methodological Review of `HAI_draft.tex`

## Verdict

As an **HAI poster paper**, the draft now has a compelling behavioural finding and a much clearer story. The 46-of-70 recommendation override is defensible and worth centring. The separation of experimentally assigned cues, post-interaction perceptions, and logged behaviour is also methodologically appropriate: perceived explainability and perceived anthropomorphism necessarily capture how participants experienced the cues during interaction, and measuring them after the task avoids priming the behavioural decision.

The paper is nevertheless **not yet methodologically submission-ready**. The most serious remaining problem is the interpretation of post-settledness latency, which is confounded by outcome-specific interface requirements. The experimental-effect models, HIC description, decision standard, and reproducibility reporting also require repair. The perception-layer pathway can remain, provided it is consistently presented as a post-interaction associational model rather than a temporally established causal mechanism.

## Major Findings

### 1. Post-settledness latency is confounded by the decision interface

The paper treats post-settledness latency as the strongest behavioural discriminator of advancement ([HAI_draft.tex:152](HAI_draft.tex#L152), [HAI_draft.tex:176](HAI_draft.tex#L176)). After reporting settledness, however:

- **Advance** required one selection and submission.
- **Reject** required one selection and submission.
- **Hold** additionally required selecting at least one unresolved issue before submission ([streamlit_app.py:1165](../../src/agentic_hiring/streamlit_app.py#L1165)).

The latency pattern reflects this asymmetry:

| Decision | n | Mean post-settledness latency |
|---|---:|---:|
| Advance | 159 | 20.6 s |
| Hold | 40 | 45.8 s |
| Reject | 12 | 24.8 s |

Among document openers, Reject averaged 17.7 seconds while Hold averaged 43.7 seconds. The reported resistance difference is therefore driven substantially by the option that required extra interface work. The interval before settledness, which is not affected by the final-decision form, did not reliably distinguish advancement from resistance: Wilcoxon \(p=.324\), Welch \(p=.151\).

**Required repair:** Remove post-settledness latency as a deliberative mechanism or central contribution. It can be reported only as exploratory decision-completion latency, explicitly qualified by outcome-specific form burden. The phrase "strongest association" should not carry a theoretical interpretation.

### 2. Post-task perception measurement is appropriate, but its analytical role must be explicit

Perceived explainability and perceived anthropomorphism are not pre-existing participant attributes. They are manipulation-proximal experiential measures of how users experienced the explainability and anthropomorphic cues during interaction. Measuring them before exposure would be impossible, while measuring them during the workflow could interrupt the task, sensitise participants to the manipulations, and alter evidence inspection or final decisions. Post-task measurement is therefore a defensible anti-priming design choice.

The study should explicitly separate two analytical layers:

1. **Assigned cues:** provenance-based explainability, anthropomorphic delivery, and HIC presence. Models using these variables estimate differences associated with experimental assignment.
2. **Experienced perceptions:** post-interaction perceived explainability, perceived anthropomorphism, and trust. Models using these variables estimate how participants' experiences of the cues covaried with one another and with logged behaviour.

The limitation concerns interpretation, not measurement timing. Because perceived explainability, perceived anthropomorphism, and trust were collected together after the final decision, their relationships do not establish temporal mediation. Trust may still be reported as associated with advancement, and the indirect effect may be reported as a statistical indirect association. The paper should avoid wording such as explanation "contributed to trust" ([HAI_draft.tex:187](HAI_draft.tex#L187)) or trust "led to" advancement.

**Required Method disclosure:**

> To avoid priming participants to attend specifically to explainability, anthropomorphic delivery, or trust during the decision task, perceived explainability, perceived anthropomorphism, and trust were measured in the post-task questionnaire. Perceived explainability and perceived anthropomorphism captured participants' experience of the experimentally varied cues. Condition-based models estimate differences associated with assigned cues, whereas perception-based models estimate post-interaction associations and are not interpreted as temporally ordered causal effects.

### 3. The experimental null effects are estimated using a post-treatment-adjusted model

The odds ratios at [HAI_draft.tex:147](HAI_draft.tex#L147) come from a regression that simultaneously adjusts for HIC Stage 2 use, recommendation-path change, verification behaviour, settledness, decision latency, and post-settledness latency. These variables arise during the workflow and can be consequences of assigned conditions. The resulting condition coefficients are controlled direct associations, not clean estimates of total assigned-condition differences.

An additive assigned-condition model fitted to the same \(N=211\) produced:

- Explainability: OR \(=0.82\), 95% CI \([0.44,1.54]\), \(p=.538\)
- Anthropomorphism: OR \(=0.98\), 95% CI \([0.52,1.84]\), \(p=.948\)
- HIC: OR \(=0.78\), 95% CI \([0.42,1.46]\), \(p=.439\)

The substantive null conclusion survives, but the manuscript currently reports estimates from the wrong model for that conclusion.

**Required repair:** Report a factorial or additive condition model for assigned-condition differences. Present the model containing trust and workflow traces separately as an exploratory associational model. Do not interpret non-significant coefficients as evidence of equivalence.

### 4. The HIC intervention is incompletely and partly inaccurately described

The statement that HICs "require an evaluative priority to be articulated" is inaccurate ([HAI_draft.tex:111](HAI_draft.tex#L111)). Priority selection was optional, and participants could continue without selecting one.

The correct flow is:

- 104 participants received HICs and reached the Stage 1 screen.
- 91 selected at least one evaluation priority.
- 70 selected at least one caution-relevant priority.
- The programmed rule changed all 70 recommendations from Advance to Hold.
- 46 of those 70 subsequently advanced.

The Method also omits the substantive second checkpoint, although 86 of 104 HIC participants used it. HIC exposure was therefore a two-stage intervention bundle: pre-recommendation evaluation-priority steering and optional post-recommendation targeted review.

**Required repair:** Distinguish HIC exposure, general priority-selection uptake, caution-relevant priority selection, deterministic recommendation redirection, and Stage 2 use. Do not label the 70 caution-triggering selections as everyone who completed Stage 1.

### 5. Anthropomorphism changed procedural framing as well as social delivery

In high-anthropomorphism HIC conditions, the priority control explicitly described selection as "optional"; the low-anthropomorphism wording did not ([streamlit_app.py:770](../../src/agentic_hiring/streamlit_app.py#L770)). Button and checkpoint language also differed.

This does not invalidate the anthropomorphism manipulation, because interactional wording is part of how anthropomorphic delivery was instantiated. It does mean that the treatment should be described as a bundle of socially fluent and interactionally framed cues, rather than as surface warmth alone. Stage 2 use differed descriptively across these versions, 90.9% versus 73.5%, Fisher \(p=.022\), although this post-hoc comparison should not become a headline result.

### 6. The weak-support outcome lacks an independent decision standard

The manuscript acknowledges this limitation ([HAI_draft.tex:198](HAI_draft.tex#L198)), but the Method initially treats Hold as objectively defensible. The standard was derived by the researchers from the constructed role description, candidate CV, and screening policy, without reported independent expert validation or preregistration.

Therefore:

- "Advancement under the study's caution criterion" is defensible.
- "Overreliance" or "inappropriate reliance" is not fully established.
- The clearest behavioural result is override of the agent's current Hold recommendation.

The asymmetric final-decision form also matters here: choosing Hold required an additional justification action, whereas Advance and Reject did not. This may have discouraged Hold and must be acknowledged when interpreting the 46-of-70 result.

### 7. The perception-layer analysis is now reproducible from the current repository

The revised paper-facing R script now generates the additive manipulation checks, scale-quality and missingness statistics, post-task perception regressions, 10,000-resample percentile-bootstrap indirect association, and model-specific sample sizes. These outputs are written to B4a_manipulation_checks.csv, B4b_post_task_perception_associations.csv, and S1_measure_quality_and_missingness.csv, with the full analysis contract recorded in analysis_manifest.csv.

The remaining measurement-reporting gap is documentary rather than statistical: the repository does not contain the original Qualtrics item wording or verified source citations. Those must be recovered from the questionnaire record and added to the manuscript and supplementary material.

### 8. Sample and consent reporting require repair

The Method says only "after cleaning" ([HAI_draft.tex:81](HAI_draft.tex#L81)). The source contains 224 rows, four duplicate records, and 211 retained participants. Experimental cell sizes range from 24 to 29. A compact poster still needs the starting sample, exclusion logic, final sample, and allocation procedure.

The analysis script treats a missing consent value as passing. The prefixed consent field records "Yes" for 210 retained participants and is blank for participant `35795446`. This does not by itself require excluding that behavioural record, but the statement that all participants provided consent requires verification from the original recruitment or consent record.

## What Is Strong

The deterministic HIC rule is now disclosed clearly. The paper correctly distinguishes steering from verification, defines recommendation following against the agent's current recommendation, and acknowledges that entry into the redirected path was self-selected. The use of post-task perception measures also preserves the behavioural workflow and avoids drawing participants' attention to the focal constructs before their decisions are logged.

The two strongest defensible findings are:

> Seventy participants selected a role-critical evaluation priority that deterministically redirected the agent from Advance to Hold. Forty-six nevertheless made the final decision to Advance.

> Participants' post-interaction perceptions of explainability, anthropomorphism, and trust were systematically associated, while assigned interface cues were not significantly associated with the final advancement decision.

The first is the poster's central behavioural contribution. The second explains how the assigned cues were experienced, but should remain explicitly associational.

## Poster-Level Repair

The compact Method should include:

1. Recruitment, allocation, starting sample, exclusions, cell sizes, ethics, and compensation.
2. The exact sequence: role and policy summaries with optional full-document access, Stage 1 HIC, recommendation, Stage 2 HIC, settledness, final decision, and post-task questionnaire.
3. The six Stage 1 options and the deterministic two-option Hold rule.
4. The rationale for post-task perception measurement as protection against priming.
5. Measure item counts, response scales, reliability, questionnaire timing, and model-specific missingness.
6. Separate analyses for assigned-condition differences and post-interaction perceptual associations.
7. Explicit exploratory status for analyses that were not preregistered.
8. The asymmetric Hold-justification interface as a limitation affecting latency and possibly decision choice.

## Concrete Revision Block

The following passages implement the checklist above. Statistics marked as audit reruns were calculated directly from the retained dataset and should be added to the canonical analysis script before submission. Bracketed administrative fields cannot be recovered from the analysis data and require confirmation from the Prolific, Qualtrics, or ethics records.

### Replacement Method

#### Design and participants

> We conducted a controlled $2 \times 2 \times 2$ between-subjects online experiment varying provenance-based explainability cues (absent or present), anthropomorphic delivery cues (low or high), and Human Intervention Checkpoints (HICs; absent or present). Participants were recruited through Prolific using prescreening criteria requiring English fluency and current or recent experience in human resources, talent acquisition, or personnel management. Qualtrics randomly assigned participants to one of the eight experimental conditions. The merged dataset contained 224 rows. Four duplicate records were removed by retaining the most complete and most recent matched session for each participant identifier; records without a passed attention check, matched interaction log, or final decision were then excluded. The resulting sample comprised 211 participants, with 24--29 participants per condition: E0-A0-HIC0 ($n=25$), E0-A0-HIC1 ($n=29$), E0-A1-HIC0 ($n=27$), E0-A1-HIC1 ($n=24$), E1-A0-HIC0 ($n=26$), E1-A0-HIC1 ($n=26$), E1-A1-HIC0 ($n=29$), and E1-A1-HIC1 ($n=25$). The study received approval from [insert committee and reference]. Participants provided informed consent and received [insert payment] for approximately [insert expected duration] minutes.

The consent statement requires confirmation for participant `35795446`, whose behavioural record satisfies the analysis criteria but whose consent value is absent from the merged questionnaire fields.

#### Task and procedure

> Participants acted as recruiters evaluating a fictional candidate for a Strategic Talent Operations Partner role. All participants received the same company context, role summary, screening-policy summary, and candidate CV. Before the assistant recommendation, participants could open the full role description and screening policy through controls available in every condition. Participants in HIC-present conditions then encountered a pre-recommendation evaluation-priority checkpoint. The assistant subsequently presented its assessment and current recommendation. HIC-present conditions also included an optional post-recommendation checkpoint through which participants could request targeted review of a selected issue. Participants then reported how settled their judgement was, made a final decision from Reject application, Advance to human interview, or Hold for further review, and returned to the survey to complete the perceived-explainability, perceived-anthropomorphism, and trust measures. These perception measures were placed after the behavioural task to prevent the questionnaire from sensitising participants to the experimental cues before their evidence-access and decision behaviour had been recorded.

#### Agent and experimental manipulations

> The assistant implemented a bounded agentic screening workflow. It retrieved and organised evidence from the fixed organisational documents, evaluated the candidate against role and policy requirements, generated one of the permitted recommendations, adapted its assessment to participant-selected priorities, and supported targeted follow-up review. Pre-authored recommendation and follow-up cards held the evidential content and permitted outcomes stable across participants. Explainability-present conditions added provenance links connecting assessment claims to inspectable document sections. High-anthropomorphism conditions used first-person, cooperative, and socially fluent wording, whereas low-anthropomorphism conditions used socially thin report-style wording. The anthropomorphism manipulation also varied interactional framing in checkpoint prompts and action labels; it should therefore be understood as a bundle of social-delivery cues rather than warmth alone. The system supported an evidence-grounded model fallback for novel open-ended Stage 2 queries, but no retained participant selected the open-ended `Other question` route; the analysed recommendation and named follow-up paths therefore used the controlled cards and deterministic recommendation policy.

#### Human Intervention Checkpoints

> At Stage 1, HIC-present participants could select up to three of six evaluation priorities: independent ownership, stakeholder communication, transferable experience, structured evaluation or screening experience, operational coordination, and growth potential. Selection was optional. All 104 HIC-present participants reached and completed the checkpoint screen, and 91 selected at least one priority. Independent ownership and structured evaluation or screening experience were designated caution-relevant because the controlled CV did not provide evidence satisfying those role-critical requirements. Selecting either priority deterministically redirected the assistant's recommendation from Advance to human interview to Hold for further review; other selections adapted the assessment rationale without changing the recommendation. Seventy participants selected at least one caution-relevant priority and therefore received Hold. This was a programmed response to self-selected input, not an independently generated change of view by the model and not a randomly assigned subgroup. At Stage 2, participants could request a targeted review after seeing the recommendation; 86 of 104 HIC-present participants used this option. HIC use was analysed as workflow steering and was not counted as evidence verification unless a participant separately opened an underlying document or provenance link.

#### Decision criterion and behavioural measures

> The controlled CV showed relevant recruitment-coordination experience but did not document independent screening ownership, structured application of evaluation criteria, or responsibility for progression decisions. Under the study's screening policy, Hold for further review was the prespecified caution-consistent response, while Advance to human interview was coded as advancement under weak support. This coding represents the study's policy-based criterion rather than an independently validated ground truth. Recommendation following indicated whether the participant's final decision matched the assistant's current recommendation, including Hold after a HIC-triggered path change. Pre-recommendation full-document access indicated whether the participant opened the complete role description or screening policy before the recommendation. Citation inspection was recorded separately and was available only in explainability-present conditions.

The phrase "prespecified caution-consistent response" should be replaced with "study-defined caution-consistent response" unless an analysis plan created before data collection confirms that the coding was prespecified.

#### Perception measures

> Perceived explainability was computed as the mean of four seven-point items ($\alpha=.86$), perceived anthropomorphism as the mean of four seven-point items ($\alpha=.93$), and trust as the mean of six seven-point items ($\alpha=.91$). A composite was calculated only when all items for that scale were valid and complete. Complete scale scores were available for 203 participants for perceived explainability, 206 for perceived anthropomorphism, and 208 for trust; 195 participants had complete data on all three constructs. Full item wording and scale sources are provided in the supplementary material. Judgement settledness was recorded before the final-decision screen using a single seven-point item ranging from 1 (still need to examine it further) to 7 (fully settled).

#### Analysis strategy

> Assigned-condition differences in advancement were estimated using logistic regression containing the three assigned factors. Manipulation checks regressed each experienced cue measure on all three assigned factors. Perception-layer associations were estimated among participants with complete perceived-explainability, perceived-anthropomorphism, and trust scores ($n=195$). The indirect association between perceived explainability and trust involving perceived anthropomorphism was estimated using 10,000 percentile-bootstrap resamples. A separate logistic model related post-task trust to advancement while adjusting only for the three assigned factors ($n=208$); because trust was measured after the decision, this model estimates an association and is not interpreted prospectively. HIC steering and recommendation override were summarised descriptively within the HIC-present group because entry into the redirected path was self-selected and deterministically linked to the selected priorities. Pre-recommendation document access was compared with advancement using descriptive rates and Fisher's exact test. Analyses not specified before data collection are identified as exploratory.

Post-settledness latency should be omitted from the main analysis. If retained in supplementary material, it must be labelled decision-completion latency and accompanied by the Hold-form confound described below.
### Replacement Results

#### Assigned cues and experienced perceptions

> In additive manipulation-check models containing all three assigned factors, explainability-cue assignment was associated with higher perceived explainability, $F(1,199)=4.04$, $p=.046$, partial $\eta^2=.020$, and anthropomorphic-cue assignment was associated with higher perceived anthropomorphism, $F(1,202)=5.57$, $p=.019$, partial $\eta^2=.027$. Among the 195 participants with complete perception measures, perceived explainability was associated with perceived anthropomorphism ($b=0.811$, SE $=0.097$, $p<.001$). In the trust model, perceived explainability ($b=0.653$, SE $=0.058$, $p<.001$) and perceived anthropomorphism ($b=0.197$, SE $=0.037$, $p<.001$) were both positively associated with trust. The estimated statistical indirect association involving perceived anthropomorphism was $b=0.160$, bootstrap SE $=0.044$, 95\% percentile-bootstrap CI $[0.079,0.250]$. These estimates describe post-interaction perceptual associations and do not establish a temporal mediation process.

#### Assigned conditions and advancement

> Overall, 159 of 211 participants (75.4\%) selected Advance to human interview. In the additive assigned-condition model, advancement was not significantly associated with explainability cues (OR $=0.82$, 95\% CI $[0.44,1.54]$, $p=.538$), anthropomorphic cues (OR $=0.98$, 95\% CI $[0.52,1.84]$, $p=.948$), or HIC presence (OR $=0.78$, 95\% CI $[0.42,1.46]$, $p=.439$). The intervals do not exclude modest effects in either direction. Post-task trust was positively associated with advancement after adjustment for the three assigned factors, OR $=1.64$, 95\% CI $[1.14,2.35]$, $p=.008$, but this association is not interpreted as showing that trust temporally preceded or caused the decision.

#### Evidence access

> Before receiving the assistant's recommendation, 116 participants (55.0\%) opened at least one full source document through controls available in every condition. Of these participants, 83 (71.6\%) advanced the candidate, compared with 76 of 95 participants (80.0\%) who did not open a full document. The association was not statistically significant, Fisher's exact $p=.199$. Opening a document records evidence access rather than reading depth or comprehension, so this finding shows that access alone did not reliably distinguish the decisions.

#### Human-directed steering and recommendation override

> Of the 104 participants in HIC-present conditions, 91 (87.5\%) selected at least one evaluation priority. Seventy (67.3\%) selected independent ownership or structured evaluation or screening experience, the two caution-relevant priorities, and the deterministic policy changed the assistant's recommendation from Advance to Hold in every one of these cases. After receiving the resulting Hold recommendation, 21 participants (30.0\%) chose Hold, three (4.3\%) chose Reject, and 46 (65.7\%) chose Advance. Thus, most participants on the self-selected redirected path advanced the candidate despite receiving a cautious recommendation generated in response to their own evaluation priorities. This is a within-path descriptive result; it does not estimate the causal effect of selecting a caution-relevant priority or of receiving a Hold recommendation.

### Replacement Discussion and Limitation Text

> The behavioural result identifies a boundary of this implementation of workflow-level cognitive forcing. Human-selected priorities were consequential for the agent: caution-relevant selections changed its evidence emphasis and deterministically redirected its recommendation from Advance to Hold. They did not govern the final human decision, however, because 46 of the 70 participants on that redirected path still advanced the candidate. The finding is not an effect of randomly assigned steering content. Participants selected the priorities themselves, and the recommendation change followed a fixed policy rule. It therefore shows that a consequential opportunity to steer an agent can coexist with subsequent recommendation override, rather than demonstrating that HICs generally fail to improve decision quality.

> The perception-layer findings complement this behavioural account. Assigned cues determined what the interface presented, whereas post-task measures captured how those cues were experienced. Participants who experienced the assistant as more explainable also tended to experience it as more anthropomorphic and trustworthy, and greater post-task trust was associated with advancement. The questionnaire was intentionally administered after the behavioural task to avoid priming attention to the focal constructs. Accordingly, these relationships are interpreted as post-interaction associations, not as evidence that perceived explainability temporally produced anthropomorphism or trust, or that trust caused advancement.

> Two design features constrain the behavioural interpretation. First, Hold was defined as the caution-consistent response from researcher-authored task materials rather than an independently validated decision standard. Second, the final-decision interface required participants choosing Hold to select an additional unresolved issue, whereas Advance and Reject required no equivalent justification. This asymmetric friction may have discouraged Hold and makes post-settledness latency unsuitable as evidence of deliberation: Hold decisions averaged 45.8 seconds after settledness, compared with 20.6 seconds for Advance and 24.8 seconds for Reject. Future studies should impose equivalent justification requirements across all decision options, validate the decision criterion independently, and manipulate the reconciliation step when a participant's final decision conflicts with the recommendation produced from that participant's own priorities.

## Production Status

The current [HAI_draft.tex](HAI_draft.tex) is a manuscript fragment rather than a compilable submission: it has no document class or preamble, `HAI.bib` is absent, and the current build produces no PDF. These production issues are separate from the methodological assessment.
