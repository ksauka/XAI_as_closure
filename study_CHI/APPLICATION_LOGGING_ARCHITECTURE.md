# Qualtrics, Application, and Logging Architecture

## System Boundary

The project uses two dedicated research applications connected to separate
Qualtrics study flows:

- Study 1 expert-validation application;
- Study 2 six-profile experimental application.

Qualtrics is the recruitment-facing survey and routing layer. The applications
are the controlled task and behavioral-logging layer. Neither application should
depend on Qualtrics page timing as its primary interaction record.

## Pseudonymous Linkage

Qualtrics creates a study-specific random linkage identifier. It passes a signed,
short-lived launch token to the application containing only:

- linkage identifier;
- study identifier;
- permitted application phase;
- Study 2 condition assignment, when applicable;
- issued and expiry times; and
- return-route identifier.

The application verifies the signature and expiry before starting a session.
Direct Prolific IDs, names, email addresses, and Qualtrics Response IDs are not
written to the event log. The restricted linkage table remains in the protected
survey-data workspace.

## Study 1 Flow

1. Qualtrics records consent, eligibility, and expert background.
2. Qualtrics launches the validation app with a signed Study 1 token.
3. The app randomizes and persists one six-profile order.
4. The expert completes all locked Phase A judgments.
5. The app opens Phase B only after Phase A is complete.
6. The expert assesses assigned recommendation artifacts.
7. The app writes a completion record and returns a one-time completion token.
8. Qualtrics verifies completion, collects final feedback, and closes the study.

## Study 2 Flow

1. Qualtrics records consent and eligibility.
2. Qualtrics assigns one of eight between-subject conditions.
3. Qualtrics launches the experimental app with a signed condition token.
4. The app randomizes and persists one six-profile order.
5. Every trial follows the same sequence:
   - profile and source materials;
   - unaided decision and confidence;
   - complete AI assessment, recommendation, and assigned rendering;
   - cognitive-forcing task when assigned;
   - final aided decision and confidence;
   - neutral evidence-recall prompt.
6. The app records post-task readiness and returns a one-time completion token.
7. Qualtrics records the post-task perception measures, demographics, and
   debrief.

The assigned provenance, anthropomorphic-delivery, and cognitive-forcing levels
remain fixed across all six trials.

## Cognitive-Forcing Invariant

Cognitive forcing occurs after the recommendation and its assigned explanation
are visible and before the final aided decision. It therefore asks participants
to interrogate an actual recommendation rather than reason about an output they
have not seen.

The forcing-present task uses the same structure in all provenance and delivery
conditions. It asks for evidence supporting the recommendation and evidence that
could count against it without naming the mandatory certification or revealing
the intended error. The forcing-absent workflow proceeds directly to the final
decision.

## Event Model

Logs are append-only. Every event contains:

- schema version;
- application version and Git commit;
- material manifest and profile version;
- session identifier and pseudonymous linkage identifier;
- study, phase, trial identifier, and trial position;
- assigned condition and profile order;
- event sequence number;
- event type;
- server UTC timestamp;
- client elapsed monotonic time;
- page or component identifier;
- payload version; and
- write status.

## Study 1 Events

Study 1 records, where applicable:

- session created and resumed;
- launch-token validation;
- role and policy opened or revisited;
- randomized profile order;
- profile and section visibility;
- Phase A decision, certification classification, confidence, decisive evidence,
  ambiguity response, and submission;
- pre-submission response changes without storing keystroke content;
- Phase A lock;
- Phase B artifact assignment and rendering version;
- artifact ratings and comments;
- phase and session completion; and
- return-token issuance.

## Study 2 Events

Study 2 records, where applicable:

- condition assignment and validation;
- randomized profile order;
- material and section visibility;
- unaided decision, confidence, and timing;
- AI recommendation and rendering displayed;
- provenance source labels and passage links displayed;
- link opening, passage visibility, return, and dwell;
- cognitive-forcing prompt, response, revisions, and completion;
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

For every decision-relevant screen, record:

- first render;
- first meaningful interaction;
- material opening and closing;
- recommendation reveal;
- forcing start and completion;
- decision submission; and
- interruption or inactive periods.

Server timestamps support ordering across systems. Client monotonic durations
support within-session latency and are not affected by clock changes.

## Storage and Reliability

Production logs are written to protected research storage, not the public code
repository. Writes use idempotent event identifiers. The app maintains a
temporary retry queue when storage is unavailable and does not report completion
until required events and final state are durably acknowledged.

A session summary is derived from events but never replaces the raw append-only
trace. Data exports retain schema and material versions so analyses can be
reproduced after the interface evolves.

## Merge and Quality Checks

The analysis pipeline joins Qualtrics and application records by the restricted
pseudonymous linkage identifier and reports:

- unmatched survey records;
- unmatched application sessions;
- duplicate or resumed sessions;
- invalid or changed condition assignments;
- incomplete trials and phases;
- out-of-order or missing required events;
- material-version mismatches; and
- completion-token failures.

Exclusions are based on prespecified rules. Logging failures are reported as data
quality problems rather than silently converted into participant exclusions.

## Data Minimization and Secondary Use

Rich logging means retaining research-relevant state and behavior, not collecting
everything a browser can expose. Every logged field must have a documented
purpose, consent basis, access rule, and retention period. Secondary analyses
must remain compatible with the consent language and ethics approval.
