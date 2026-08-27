# XAI as Closure: CHI 2027 Research Brief

## Core Question

When an agentic assistant explains a recommendation with inspectable evidence,
do people use that evidence to verify the recommendation, or can its
anthropomorphic delivery close the decision before the evidence is evaluated?

## Contribution

The project studies explanation as both an epistemic affordance and a possible
social credential. It tests whether explanation presence supports appropriate
reliance, whether anthropomorphic delivery changes how explanation is used, and
whether a decision-time cognitive-forcing intervention restores
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
recommendation, rationale, explanation, anthropomorphism, cognitive forcing, or
experimental condition; it ends after the sixth candidate judgment.

Profiles that fail the prespecified agreement or intended-reason criteria are
revised and revalidated. Validated files are versioned and frozen before Study 2.

### Study 2: Six-Profile Experiment

Study 2 uses a mixed design. Participants are assigned to one fixed 2 x 2 x 2
between-subjects condition:

- explanation: absent or present;
- delivery: procedural or anthropomorphic; and
- cognitive forcing: absent or present.

Every participant completes the same six profiles in randomized order:

- two correct advances;
- two correct rejects;
- one false advance; and
- one false reject.

The fictional role was posted on 20 July 2026, candidate screening occurs
during 27–30 August 2026, and the target fill date is 20 September 2026. The
mandatory criterion requires a named certification to be current on the date of
screening. The false advance, C-05, previously earned AIGP but has a recorded
term ending before the screening window; the fixed AI recommendation wrongly
treats that expired term as current.

Each trial records an unaided decision before the AI appears and an aided
decision after the AI workflow. This permits appropriate reliance to be scored
in both directions and identifies assistant-induced reversals.

The Study 2 assistant is a bounded agentic workflow. For each candidate it
constructs the fixed screening plan, retrieves the configured passages from the
current policy, job description, and candidate file, evaluates those materials,
and produces the frozen recommendation. This makes the execution stateful
without allowing uncontrolled generation to change the experimental stimuli.
Explanation-absent cells show only the verdict. Explanation-present cells show
the full fixed rationale and inspectable citations. In
forcing-present conditions, the participant must
re-enter the mandatory certification requirement from the complete job
description before the recommendation can be requested or revealed.

## Manipulation Invariants

- The recommendation is fixed for each profile in every condition. The fixed
  rationale is shown only when explanation is present.
- Explanation present adds the complete rationale, neutral claim-linked
  citations that open the complete source document inside the assessment page,
  position the cited passage in view, and highlight it neutrally. The document
  closes back to the unchanged assessment. Explanation absent shows a
  verdict-only card; all complete documents remain independently available.
- Anthropomorphic delivery uses the frozen `anthrokit-hiring-study2-v6`
  register. Each explanation level has a LowA/HighA card pair. Low
  delivery is procedural, impersonal, and system-labelled; high delivery is
  first-person, mildly hedged, warmer, and adviser-like. The same registered
  verdict, registered assessment basis, and citation set are fixed in each
  pair, while the participant-facing wording is frozen separately for each
  register. Persona names, emoji, humor, emotional claims, and live LLM
  rewriting are excluded.
- Cognitive forcing occurs after the unaided decision and before the AI
  recommendation is requested or visible.
- In forcing-present conditions, participants type or paste the mandatory
  certification requirement from the complete job description. The task is
  identical across explanation and delivery conditions and does
  not operate on the recommendation or citation apparatus.
- The role, policy, full candidate file, and decision options remain available
  in every condition. After the unaided decision, the CV leaves the primary
  page and remains available only through the source-document control or a
  recommendation citation.
- Before the trials, participants see one recruitment-brief screen containing a
  concise company-and-role summary, concise recruitment guidance, and two
  optional full-document buttons. Reading the long sources is advised for
  requirements and policy detail but is not forced as the primary task.

## Outcomes

Primary behavioral outcomes:

- appropriate reliance on correct and incorrect recommendations;
- unaided-to-aided decision transitions;
- overriding of incorrect recommendations; and
- extraction of the decisive evidence.

Secondary and exploratory outcomes:

- decision confidence;
- document and passage inspection;
- citation traversal, focused-passage dwell, and document-close route;
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
