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

Study 1 uses the same proven Prolific-ID and validated Qualtrics-return flow as
the current application, deriving a deterministic pseudonymous session ID for
resume and storage. Study 2 retains the previously working HAI linkage.
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

1. Qualtrics records consent; eligibility and professional background may
   already have been verified during recruitment.
2. Qualtrics launches the validation app with the Prolific ID and a validated
   return route.
3. The app randomizes and persists one six-profile order.
4. The expert submits one locked ground-truth judgment for each candidate.
5. After the sixth judgment, the expert submits the short final materials
   review; only then does the app write a completion record.
6. Qualtrics receives completion, collects the basic-demographics block,
   presents closing information and the debrief, and closes the study.

Study 1 has no AI recommendation, artifact assignment, experimental condition,
or AI-task phase. The final materials review belongs to the same streamlined
validation workflow. The same application serves multiple experts while keeping
their sessions and randomized orders isolated.

## Study 2 Flow

1. Qualtrics records consent and eligibility.
2. Qualtrics assigns one of eight between-subject conditions.
3. Qualtrics launches the application permanently assigned to that condition
   with the HAI query parameters; the app rejects a mismatched `cond` value.
4. On one recruitment-brief screen, the app presents neutral instructions, a
   concise company-and-role summary, and concise recruitment guidance before
   unlocking the first candidate. Two optional buttons open the complete
   governing documents, which also remain available during every trial. The app
   then randomizes and persists one six-profile order.
5. Every trial follows the same sequence:
   - profile and source materials;
   - unaided decision and confidence;
   - cognitive-forcing requirement re-entry when assigned, while the AI output
     remains hidden;
   - bounded agent plan, configured evidence retrieval, evaluation, and complete
     recommendation under the assigned rendering;
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

Explanation-present recommendations use the local
`recommendation_component_frontend/` HTML/JavaScript component. Citation buttons
are embedded directly after their claims. The component returns only a block and
citation position; Python validates that position against the registered case
evidence before opening the complete source in an in-page document frame. The
frame positions and highlights the registered passage without leaving the AI
assessment. Open, focus, dwell, close-reason, and return-target events are
recorded. The recommendation component loads no remote scripts and does not
render untrusted HTML.

Anthropomorphic delivery is also frozen. The audit payload records
`anthrokit-hiring-study2-v7` and its assigned LowA or HighA token preset, while
participant state contains the complete paired response card, condition-visible
sources.
Study 2 uses `study2-state-v8`, `study2-event-v10`, and `study2-app-v10` so pilot
sessions created before the revised case set and frozen delivery specification
cannot be mixed with the active instrument. The state records the `v3` case-set
identifier and rejects prior material versions; resumability remains available
within the same current material version.

## Cognitive-Forcing Invariant

Cognitive forcing occurs after the unaided decision and before the recommendation
is requested or revealed. It shifts the participant into an active processing
state by requiring re-encoding of the role requirement before exposure to AI
advice.

The forcing-present task uses the same structure in all explanation and delivery
conditions. The participant opens the complete job description, initially
focused on Sections 4.1–4.2, and types or pastes both mandatory professional
requirements. Submission unlocks the request for the AI recommendation. Because
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
- candidate decision, direct hard-criterion judgment, confidence, short decisive
  evidence, and submission;
- pre-submission response changes without storing keystroke content;
- candidate-judgment lock;
- final materials-review presentation and submission, including the six Likert
  items, disputed-profile response, and optional combined feedback;
- session completion only after six judgments and the final review; and
- validated return-route handoff.

## Study 2 Events

Study 2 records, where applicable:

- condition assignment and validation;
- randomized profile order;
- material and section visibility;
- unaided decision, confidence, and timing;
- agent plan, retrieved-evidence labels, and evaluation completion;
- AI recommendation and rendering displayed;
- explanation presence, message-block identifiers, neutral citation locators,
  and focused complete-document links displayed;
- every sidebar reference-document and in-page citation-document opening,
  paired close/return, click-to-return time, visible-document dwell time,
  presentation mode, close reason, and return target;
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
