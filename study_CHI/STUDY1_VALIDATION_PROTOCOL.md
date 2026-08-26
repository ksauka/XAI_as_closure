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
criteria, minimum experience, recruitment source, compensation, target sample,
and exclusion rules must be fixed before launch. Eligibility may be verified
during recruitment rather than repeated in Qualtrics.

Study 1 experts cannot participate in Study 2.

## System Boundary

### Qualtrics

For Study 1, Qualtrics is deliberately minimal. It records:

- consent;
- a pseudonymous linkage identifier and application launch status; and
- verified completion, closing information, and debrief.

Qualtrics does not deliver the candidate task or duplicate its responses.

### Validation Application

One shared validation application records all six candidate judgments for each
expert, the randomized order, document interactions, response timing, completion,
and material versions. It must not receive names, email addresses, raw
recruitment-platform identifiers, or raw Qualtrics Response IDs.

## Source Materials

Every expert receives the same versioned materials:

- AI Governance Lead job description;
- recruitment policy and non-substitutable certification rule; and
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
2. Certification classification, typed as free text naming the accepted
   mandatory requirement the expert located in the profile, or "None" if it
   is not present. This is a recall measure, not a recognition measure: the
   expert is not shown the certification names as selectable options, and the
   prompt does not name "certification" directly.
3. Confidence in the judgment, from 0 to 100.
4. The decisive evidence, in an open-ended response.
5. Any ambiguity or missing information, in an open-ended response.
6. Any unrealistic detail or unintended cue that might signal how the candidate
   should be classified, in an open-ended response.

The final two fields require an explicit response such as “None” when the expert
has no concern. A submitted candidate judgment cannot be edited. After the sixth
judgment is submitted, the application records completion and returns the expert
to Qualtrics. There is no second task phase.

The application may log document opening, candidate-section visibility,
submission, and elapsed time. A click or dwell interval is a behavioral trace,
not evidence that the expert understood a document.

## Validation Analysis

Before launch, the preregistration must define:

- the minimum per-profile Advance or Reject agreement;
- the target inter-rater reliability and confidence interval;
- the intended-reason coding rule;
- how ambiguity, missing information, realism concerns, and unintended cues are
  coded and used in the pass decision;
- treatment of missing or low-effort responses; and
- the number of independent coders for open-ended responses.

Fleiss' kappa and profile-level agreement are reported for Advance or Reject.
Certification classification, now a free-text field, is coded against the
correct certification for each profile (correct, incorrect, or missing) before
agreement is summarized separately from the Advance or Reject judgment.
Open-ended decisive evidence is coded for whether the mandatory criterion drove
the judgment.
Ambiguity and cue responses are reviewed to identify profile features that could
invalidate or contaminate the intended ground truth.

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
- profile-level decision and certification agreement;
- inter-rater reliability;
- coded decisive-evidence results;
- coded ambiguity, missing-information, realism, and unintended-cue findings;
- a material revision history; and
- the final frozen material manifest.
