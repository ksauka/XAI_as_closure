# Study 1 Expert-Validation Protocol

## Purpose

Study 1 establishes a defensible profile-level ground truth for the six
candidate cases used in Study 2. It also checks that the candidate files and the
assistant's correct and incorrect recommendations are realistic enough to
support the experimental task.

Study 1 is not a manipulation experiment and is not delivered solely in
Qualtrics. Qualtrics provides the recruitment and survey shell; a dedicated
validation application delivers the controlled profile task and records the
behavioral trace.

## Eligibility

Experts must have relevant recruitment, human-resources, hiring, compliance, AI
governance, or closely related screening experience. The final eligibility
criteria, minimum experience, recruitment source, compensation, target sample,
and exclusion rules must be fixed before launch.

Study 1 experts cannot participate in Study 2.

## Systems

### Qualtrics

Qualtrics records:

- consent;
- eligibility;
- expert background and relevant experience;
- a pseudonymous linkage identifier;
- application launch and return status; and
- completion and debrief responses.

### Validation Application

The application records the profile judgments, evidence responses, profile
order, document interactions, response timing, phase completion, and material
versions. It must not receive names, email addresses, or raw recruitment-platform
identifiers.

## Source Materials

Every expert receives the same versioned materials:

- AI Governance Lead job description;
- recruitment policy and non-substitutable certification rule;
- six candidate profiles identified only as C-01 through C-06; and
- in Phase B only, the recommendation artifacts intended for Study 2.

Labels such as false advance, false reject, qualified, unqualified, and ground
truth are never shown in the participant interface.

## Phase A: Independent Ground-Truth Judgments

The role description and recruitment policy remain available throughout Phase A.
The six profiles are presented in a participant-specific randomized order.

For each profile, the expert records:

1. Advance to Hire or Reject.
2. Whether the profile shows a current IAPP AIGP certification, a current
   ISO/IEC 42001 Lead Implementer certification, or neither accepted
   certification.
3. Confidence in the judgment.
4. The decisive evidence, in an open-ended response.
5. Any ambiguity, missing information, or realism concern.
6. An optional overall suitability assessment that is analytically separate
   from the mandatory-criterion judgment.

The application logs document opening, section visibility, response changes
before submission, and elapsed time. It does not interpret a click as evidence
that the expert understood the document.

A submitted profile judgment cannot be edited. After all six profile judgments
are submitted, Phase A is permanently locked for that session.

## Phase Separation

No AI recommendation, rationale, provenance link, correctness label, or intended
trial type is displayed before Phase A is locked. This prevents the assistant's
output from contaminating the expert ground-truth judgment.

The application displays a clear transition before Phase B and explains that the
next task concerns the realism of system outputs, not reconsideration of the
locked hiring judgments.

## Phase B: Recommendation-Artifact Validation

Experts review recommendation artifacts only after all independent judgments
are locked. For each assigned artifact, they rate:

- plausibility that an AI screening assistant could produce the recommendation;
- realism and coherence of the rationale;
- clarity of the recommendation;
- whether the artifact inadvertently reveals the study's intended error;
- whether any statement invents or misstates source evidence; and
- any wording or interface problem that could make the recommendation
  implausible for reasons unrelated to the intended experimental error.

Experts are not asked to treat plausibility as correctness. A false
recommendation must remain incorrect against the locked criterion while still
being credible as an AI error.

The provenance and anthropomorphic renderings should be distributed across
experts using a balanced assignment so that no expert must review every
profile-by-rendering combination. Cognitive forcing is a workflow intervention
and is usability-tested separately rather than treated as a recommendation
artifact.

## Validation Analysis

Before launch, the preregistration must define:

- the minimum per-profile decision agreement;
- the target inter-rater reliability and confidence interval;
- the intended-reason coding rule;
- the artifact-plausibility threshold;
- treatment of missing or low-effort responses; and
- the number of independent coders for open-ended evidence.

Fleiss' kappa and profile-level agreement are reported for Advance or Reject.
Certification classification is summarized separately. Open-ended decisive
evidence is coded for whether the mandatory criterion drove the judgment.

## Revision Gate

A profile does not pass merely because its modal decision matches the authors'
intended ground truth. It must also be decided for the intended reason and must
not depend on incidental ambiguity.

When a profile or recommendation artifact fails:

1. Record the failed criterion.
2. Revise only the affected material.
3. Increment the material version.
4. Revalidate the revised material with eligible experts.
5. Preserve an audit record of the change without combining obsolete and revised
   ratings as though they concerned the same stimulus.

Study 2 cannot launch until every profile and required recommendation artifact
passes the prespecified validation rules.

## Freeze and Outputs

The validated job description, policy, profiles, structured case set, rationale
content, and renderings receive immutable version identifiers and file hashes.
Study 2 logs those identifiers on every session and trial.

Study 1 produces:

- participant-flow and exclusion counts;
- profile presentation orders;
- profile-level decision and certification agreement;
- inter-rater reliability;
- coded decisive-evidence results;
- artifact plausibility summaries;
- a material revision history; and
- the final frozen material manifest.
