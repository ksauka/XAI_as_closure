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
reliance in Study 2. Qualtrics is limited to consent, pseudonymous linkage,
completion, closing information, and debrief. One shared validation application
serves multiple experts and presents the role, policy, and all six anonymized
profiles in a participant-specific randomized order.

For every candidate, each expert records Advance candidate to human
interview or Reject candidate,
certification classification, confidence, decisive evidence, ambiguity or
missing information, and realism or unintended cues. Study 1 contains no AI
recommendation, rationale, provenance, anthropomorphism, cognitive forcing, or
experimental condition; it ends after the sixth candidate judgment.

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

The Study 2 assistant is a bounded agentic workflow. For each candidate it
constructs the fixed screening plan, retrieves the configured passages from the
current policy, job description, and candidate file, evaluates those materials,
and delivers the frozen recommendation and rationale. This makes the execution
stateful and inspectable without allowing uncontrolled generation to change the
experimental stimuli. After recommendation reveal, the assistant supports the
same bounded evidence-examination choices in every cell: strongest support,
strongest caution, mandatory-rule application, and missing or uncertain
information. These stateful responses cannot change the fixed verdict. In
forcing-present conditions, the participant must
re-enter the mandatory certification requirement from the complete job
description before the recommendation can be requested or revealed.

## Manipulation Invariants

- The recommendation and substantive rationale are fixed for each profile.
- Provenance changes traceability only: high provenance adds source labels and
  inspectable passage links; low provenance omits that source mapping.
- Anthropomorphic delivery uses the frozen `anthrokit-hiring-study2-v2`
  register. Each profile has a complete LowA/HighA assessment-card pair. Low
  delivery is procedural, impersonal, and system-labelled; high delivery is
  first-person, mildly hedged, warmer, and adviser-like. The same registered
  verdict and semantic claims appear in each pair, and persona names, emoji,
  humor, emotional claims, and live LLM rewriting are excluded. The paired
  complete responses are length-controlled.
- Cognitive forcing occurs after the unaided decision and before the AI
  recommendation is requested or visible.
- In forcing-present conditions, participants type or paste the mandatory
  certification requirement from the complete job description. The task is
  identical across provenance and anthropomorphic-delivery conditions and does
  not operate on the recommendation or citation apparatus.
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

Both studies use Qualtrics-linked applications. Study 1 uses pseudonymous
linkage; Qualtrics is only its consent, linkage, and closing shell. Study 2
retains the working HAI integration in which Qualtrics passes the Prolific ID,
condition, and return URL, and its protected JSONL/private-GitHub logs retain the
Prolific ID required by the existing cleaning and merge pipeline. Study 2 also
uses Qualtrics for condition assignment and questionnaires. Contact information
and Qualtrics Response IDs are not collected by the applications.

The Study 1 protocol, application architecture, logging schema, scoring rules,
power analysis, and preregistration must be locked before data collection.
