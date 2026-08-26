# Qualtrics, Application, and Logging Architecture

## System Boundary

The project uses nine dedicated research applications connected to two
Qualtrics study flows:

- one Study 1 expert-validation application;
- eight condition-locked Study 2 six-profile experimental applications.

Qualtrics is the recruitment-facing survey and routing layer. The applications
are the controlled task and behavioral-logging layer. Neither application should
depend on Qualtrics page timing as its primary interaction record.

## Linkage Boundary

Study 1 uses a study-specific pseudonymous identifier and signed, short-lived
launch/completion tokens. Study 2 retains the previously working HAI linkage:
Qualtrics supplies:

- `PROLIFIC_PID` (with legacy `pid` fallback);
- `cond`, matching the selected condition-locked app; and
- an encoded Qualtrics `return` URL.

Study 2 records the Prolific ID in its protected application log, as the HAI
cleaning and merge pipeline expects. Names, email addresses, and Qualtrics
Response IDs are not collected by the application. Study 2 logs and GitHub
backups are restricted research data and must never be written to the public
code repository.

## Study 1 Flow

1. Qualtrics records consent and creates a pseudonymous linkage identifier;
   eligibility may already have been verified during recruitment.
2. Qualtrics launches the validation app with a signed Study 1 token.
3. The app randomizes and persists one six-profile order.
4. The expert submits one locked ground-truth judgment for each candidate.
5. After the sixth judgment, the app writes a completion record and returns a
   short-lived signed completion token.
6. Qualtrics verifies completion, presents closing information and the debrief,
   and closes the study.

Study 1 has no AI recommendation, artifact assignment, experimental condition,
or second application phase. The same application serves multiple experts while
keeping their sessions and randomized orders isolated.

## Study 2 Flow

1. Qualtrics records consent and eligibility.
2. Qualtrics assigns one of eight between-subject conditions.
3. Qualtrics launches the application permanently assigned to that condition
   with the HAI query parameters; the app rejects a mismatched `cond` value.
4. The app presents neutral instructions, the complete role description, and
   the complete recruitment policy before unlocking the first candidate. It
   then randomizes and persists one six-profile order.
5. Every trial follows the same sequence:
   - profile and source materials;
   - unaided decision and confidence;
   - cognitive-forcing requirement re-entry when assigned, while the AI output
     remains hidden;
   - bounded agent plan, configured evidence retrieval, evaluation, and complete
     recommendation under the assigned rendering;
   - optional bounded examination of supporting evidence, caution, mandatory-
     rule application, or missing information;
   - final aided decision and confidence;
   - neutral evidence-recall prompt.
6. The app records completion and returns to Qualtrics with `PROLIFIC_PID`,
   `session_id`, `cond`, and `done=1`.
7. Qualtrics records the post-task perception measures, demographics, and
   debrief.

The assigned explanation-presence, anthropomorphic-delivery, and cognitive-forcing levels
remain fixed across all six trials.

The shared agent implementation lives in `src/xai_as_closure/` and reads only
the current `study_CHI/` materials. Its recommendation and substantive rationale
are frozen per profile; agentic execution supplies the stateful plan, retrieval,
evaluation, rendering, and audit trace without introducing condition-dependent
content drift.

Anthropomorphic delivery is also frozen. The audit payload records
`anthrokit-hiring-study2-v4` and its assigned LowA or HighA token preset, while
participant state contains the complete paired response card, condition-visible
sources, and any bounded evidence-examination history.
Study 2 uses `study2-state-v6`, `study2-event-v8`, and `study2-app-v8` so pilot
sessions created before the frozen delivery specification cannot be mixed with
the active instrument.

## Cognitive-Forcing Invariant

Cognitive forcing occurs after the unaided decision and before the recommendation
is requested or revealed. It shifts the participant into an active processing
state by requiring re-encoding of the role requirement before exposure to AI
advice.

The forcing-present task uses the same structure in all explanation and delivery
conditions. The participant opens the complete job description, initially
focused on Section 4.1, and types or pastes the mandatory certification
requirement. Submission unlocks the request for the AI recommendation. Because
the task operates on the always-available job description rather than the
recommendation or citations, its content is structurally identical across the P
and A cells. The forcing-absent workflow proceeds directly from the unaided
decision to the recommendation request.

## Event Model

Logs are append-only. Study 1 retains its pseudonymous versioned event schema.
Study 2 retains the HAI event shape, adapted to the current factors. Every Study
2 event contains:

- schema version;
- application version;
- material manifest;
- session identifier and, for Study 2, the retained Prolific participant ID;
- phase, trial identifier, and trial position;
- assigned condition and profile order;
- turn number;
- event type;
- UTC timestamp;
- client elapsed monotonic time;
- page or component identifier;
- event payload.

## Study 1 Events

Study 1 records, where applicable:

- session created and resumed;
- launch-token validation;
- every role and policy opening or revisit, paired to its return event by a
  document-visit identifier, with click-to-return and visible-document dwell
  time until the expert returns to the candidate;
- randomized profile order;
- profile and section visibility;
- candidate decision, certification classification, confidence, decisive
  evidence, ambiguity or missing-information response, realism or unintended-cue
  response, and submission;
- pre-submission response changes without storing keystroke content;
- candidate-judgment lock;
- session completion after six submitted judgments; and
- return-token issuance.

## Study 2 Events

Study 2 records, where applicable:

- condition assignment and validation;
- randomized profile order;
- material and section visibility;
- unaided decision, confidence, and timing;
- agent plan, retrieved-evidence labels, and evaluation completion;
- AI recommendation and rendering displayed;
- bounded evidence-examination selection and agent response;
- explanation presence, message-block identifiers, neutral citation locators,
  and focused complete-document links displayed;
- every reference-document and evidence-card opening, paired return,
  click-to-return time, and visible-document dwell time until the participant
  returns to the candidate;
- cognitive-forcing prompt, document access, submitted response, completion, and
  elapsed time;
- aided decision, confidence, and timing;
- evidence-recall response;
- navigation, interruption, resume, and duplicate-submission attempts;
- post-task handoff; and
- session completion.

The log stores submitted responses and meaningful state transitions. It should
not collect raw cursor paths, full keystroke streams, clipboard contents,
unrelated browser telemetry, or information that is not justified by the
research questions and consent.

## Timing

For every applicable decision-relevant screen, record:

- first render;
- first meaningful interaction;
- material opening and closing;
- recommendation reveal in Study 2;
- forcing start and completion in Study 2;
- decision submission; and
- interruption or inactive periods.

Server timestamps support ordering across systems. Client monotonic durations
support within-session latency and are not affected by clock changes.

## Storage and Reliability

Production logs are written to protected research storage, not the public code
repository. Study 2 retains the HAI `EventLogger`: one local JSONL event stream
per session and a full session-plus-events payload saved through the existing
GitHub API utility to a configured private data repository. The backup is
refreshed after each completed trial. Local directories and files use owner-only
permissions.

A session summary is derived from events but never replaces the raw append-only
trace. Data exports retain schema and material versions so analyses can be
reproduced after the interface evolves.

The migrated `session_flatten` pipeline produces participant-, trial-, and
event-level tables. The trial table retains the six-profile order, error type,
ground truth, unaided and aided decisions and confidence, appropriate reliance,
AI-following and reversal indicators, forcing timing, source count, interaction
count, and the neutral evidence-recall response.

## Merge and Quality Checks

The Study 1 analysis pipeline joins on its restricted pseudonymous identifier.
The retained Study 2 HAI pipeline validates and joins on Prolific ID and reports:

- unmatched survey records;
- unmatched application sessions;
- duplicate or resumed sessions;
- invalid or changed condition assignments;
- incomplete candidate judgments, trials, or sessions;
- out-of-order or missing required events;
- material-version mismatches; and
- Study 1 completion-token failures or Study 2 return-handoff failures.

Exclusions are based on prespecified rules. Logging failures are reported as data
quality problems rather than silently converted into participant exclusions.

## Data Minimization and Secondary Use

Rich logging means retaining research-relevant state and behavior, not collecting
everything a browser can expose. Every logged field must have a documented
purpose, consent basis, access rule, and retention period. Secondary analyses
must remain compatible with the consent language and ethics approval.
