# XAI as Closure: CHI 2027 Research Brief

## Core Question

When an agentic assistant explains a recommendation through provenance, do
people use the cited evidence to verify the recommendation, or does the presence
of provenance help close the decision before the evidence is evaluated?

## Contribution

The project studies provenance as both an epistemic affordance and a possible
social credential. It tests whether provenance-based explanation supports
appropriate reliance, whether anthropomorphic delivery changes how provenance
is used, and whether a decision-time cognitive-forcing intervention restores
evidence engagement before the final decision.

## Two-Study Design

### Study 1: Expert Validation

Study 1 establishes the profile-level ground truth required to score appropriate
reliance in Study 2. Qualtrics handles consent, eligibility, expert background,
pseudonymous linkage, and completion routing. A dedicated validation application
presents the role, policy, and six anonymized profiles.

The application has two locked phases:

1. Experts independently classify all six profiles in randomized order. For
   each profile they record Advance or Reject, accepted-certification status,
   confidence, decisive evidence, and ambiguity or realism concerns.
2. Only after all independent judgments are locked, experts review the exact AI
   recommendation artifacts intended for Study 2 and assess their realism and
   plausibility.

Profiles that fail the prespecified agreement or intended-reason criteria are
revised and revalidated. Validated files are versioned and frozen before Study 2.

### Study 2: Six-Profile Experiment

Study 2 uses a mixed design. Participants are assigned to one fixed 2 x 2 x 2
between-subjects condition:

- provenance traceability: low or high;
- anthropomorphic delivery: low or high; and
- cognitive forcing: absent or present.

Every participant completes the same six profiles in randomized order:

- two correct advances;
- two correct rejects;
- one false advance; and
- one false reject.

Each trial records an unaided decision before the AI appears and an aided
decision after the AI workflow. This permits appropriate reliance to be scored
in both directions and identifies assistant-induced reversals.

## Manipulation Invariants

- The recommendation and substantive rationale are fixed for each profile.
- Provenance changes traceability only: high provenance adds source labels and
  inspectable passage links; low provenance omits that source mapping.
- Anthropomorphic delivery changes communication register and interface cues,
  not evidence, recommendation, confidence, or argument content.
- Cognitive forcing occurs after the complete AI recommendation is visible and
  before the final aided decision.
- In forcing-present conditions, participants identify evidence supporting the
  recommendation and evidence that could count against it. The task is identical
  across provenance and anthropomorphic-delivery conditions.
- The role, policy, full candidate file, and decision options remain available
  in every condition.

## Outcomes

Primary behavioral outcomes:

- appropriate reliance on correct and incorrect recommendations;
- unaided-to-aided decision transitions;
- overriding of incorrect recommendations; and
- extraction of the decisive evidence.

Secondary and exploratory outcomes:

- decision confidence;
- document and passage inspection;
- citation traversal;
- dwell and response time;
- cognitive-forcing responses; and
- post-task perceived explainability, anthropomorphism, and trust.

Clicks and dwell time are behavioral traces, not proof of comprehension.
Verification is based on whether the participant identifies the decisive
evidence in a neutral prompt administered consistently across trials.

## Data Architecture

Both studies use Qualtrics-linked applications. Qualtrics and application data
are joined through a pseudonymous linkage identifier. The applications record
append-only session, trial, and event logs. Direct recruitment-platform
identifiers and contact information are not written to application logs.

The Study 1 protocol, application architecture, logging schema, scoring rules,
power analysis, and preregistration must be locked before data collection.
