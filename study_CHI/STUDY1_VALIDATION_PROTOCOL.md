# Study 1 Expert-Validation Protocol

## Purpose and Contribution

Study 1 establishes a defensible profile-level ground truth for the six
candidate cases used in Study 2. It tests whether eligible experts classify each
profile consistently against the written job description and recruitment policy,
whether they rely on the intended decisive evidence, and whether any profile
contains ambiguity, missing information, unrealistic details, or unintended cues.

Study 1 is not an explainability, anthropomorphism, trust, or appropriate-reliance
experiment. It contains no AI recommendation, rationale, explanation display,
agentic interaction, cognitive-forcing intervention, or experimental condition.
Those elements belong to Study 2.

## Participants and Eligibility

Multiple experts complete the validation independently. Every expert reviews all
six candidates in a participant-specific randomized order; the study is not split
into separate candidate or condition applications. Sessions are isolated through
pseudonymous linkage so that one shared validation application can serve all
experts.

Experts must have relevant recruitment, human-resources, hiring, compliance, AI
governance, or closely related screening experience. The final eligibility
criteria, minimum experience, recruitment source, compensation, and exclusion
rules must be fixed before launch. Recruit 12 eligible experts with a target of
10 complete, analysable validation sessions. Eligibility may be verified during
recruitment rather than repeated in the validation application.

Study 1 experts cannot participate in Study 2.

## System Boundary

### Qualtrics

For Study 1, Qualtrics is deliberately minimal. It records:

- consent;
- a pseudonymous linkage identifier and application launch status; and
- verified completion, closing information, and debrief.

Qualtrics does not deliver the candidate task or duplicate its responses.
Basic demographics—age range, gender, country or region of professional
experience, and highest education—are collected only in the Qualtrics closing
block and are not repeated in the validation application.

### Validation Application

One shared validation application records all six candidate judgments for each
expert, the randomized order, document interactions, response timing, completion,
and material versions. It must not receive names, email addresses, raw
recruitment-platform identifiers, or raw Qualtrics Response IDs.

## Source Materials

Every expert receives the same versioned materials:

- AI Governance Lead job description;
- recruitment policy and whole-file certification, membership, identity, and
  currency rules; and
- six participant-facing candidate profiles identified only as C-01 through
  C-06.

Labels such as false advance, false reject, qualified, unqualified, ground truth,
and trial type are never shown. AI recommendations and their associated
renderings are also never shown in Study 1.

## Procedure

The role description and recruitment policy remain available throughout the
task. The application presents the six profiles one at a time in a
participant-specific randomized order.

For every candidate, the expert records exactly:

1. Advance candidate to human interview or Reject candidate.
2. Whether the candidate satisfies the mandatory professional requirements, as
   a direct Yes or No hard-criterion judgment.
3. Confidence in the screening decision, from 0 to 100.
4. The information in the candidate file that was most important for the
   decision, in a short open-ended response.

A submitted candidate judgment cannot be edited. After the sixth judgment, the
expert completes a short final materials review within the validation
application. Six seven-point items assess role-requirement clarity, overall
profile realism, plausible rather than artificial qualification differences,
identifiability of the mandatory-requirements information, information
sufficiency, and realism of the CV pre-screening task. A Yes or No diagnostic
asks whether reasonable recruitment professionals could disagree about any
candidate's mandatory-requirements status; a Yes response requires the candidate
reference(s) and a short reason. One optional final response captures unrealistic
or artificially constructed profiles and requested material changes.

The validation application is designed for completion within approximately 10
minutes. A neutral elapsed-time clock remains visible throughout the application;
it counts upward, carries across candidate and document views, and neither imposes
a deadline nor triggers automatic submission. Per-profile realism and
decision-clarity ratings are not repeated because the overall stimulus items and
candidate-specific disagreement diagnostic capture the same validation risks with
substantially less response burden. Total session duration remains logged so the
10-minute target can be checked before expert recruitment is opened.

Only after this final review is submitted does the application record session
completion and return the expert to Qualtrics. Qualtrics remains limited to
consent and closing/debrief functions and does not duplicate these measures.

The application may log document opening, candidate-section visibility,
submission, and elapsed time. A click or dwell interval is a behavioral trace,
not evidence that the expert understood a document.

## Validation Analysis

Before launch, the preregistration must define:

- the minimum per-profile Advance or Reject agreement;
- the target inter-rater reliability and confidence interval;
- the intended-reason coding rule;
- how the final materials-review scales, optional feedback, and disputed-profile
  responses are used in the pass decision;
- treatment of missing or low-effort responses; and
- the number of independent coders for open-ended responses.

Fleiss' kappa and profile-level agreement are reported for Advance or Reject.
Hard-criterion Yes or No agreement is summarized separately from the Advance or
Reject judgment. C-05 passes validation only if experts recognise that its AIGP
term ended before the screening window and therefore answer No and reject it for
the intended reason.
C-06 passes only if experts reconcile the bare AIGP certification entry with the
current IAPP membership elsewhere in the same file, answer Yes, and advance it.
Open-ended decisive evidence is coded for whether certification identity and
currency, professional membership, and the whole-file evidence rule drove the
judgment where relevant.
The final materials-review scales, conditional disagreement response, and
optional feedback are used to identify ambiguity, artificial construction,
insufficient information, or disputed profiles that could invalidate or
contaminate the intended ground truth.

## Revision Gate

A profile does not pass merely because its modal decision matches the authors'
intended ground truth. It must also be decided for the intended reason and must
not depend on incidental ambiguity or unintended cues.

When a profile fails:

1. Record the failed criterion.
2. Revise only the affected profile or governing material.
3. Increment the material version.
4. Revalidate the revised material with eligible experts.
5. Preserve an audit record of the change without combining obsolete and revised
   ratings as though they concerned the same stimulus.

Study 2 cannot launch until every profile passes the prespecified Study 1
validation rules.

## Freeze and Outputs

The validated job description, policy, participant-facing profiles, and
structured case set receive immutable version identifiers and file hashes. Study
2 then uses those frozen materials as its ground-truth basis and logs their
identifiers on every session and trial.

Study 1 produces:

- participant-flow and exclusion counts;
- profile presentation orders;
- profile-level screening-decision and hard-criterion agreement;
- inter-rater reliability;
- coded decisive-evidence results;
- final role-clarity, realism, plausibility, information-sufficiency, and task-
  realism results;
- coded ambiguity, artificial-construction, requested-change, and disputed-
  profile findings;
- a material revision history; and
- the final frozen material manifest.
