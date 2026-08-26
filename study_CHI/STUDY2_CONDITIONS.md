# Study 2 Condition Matrix

Study 2 uses eight condition-locked applications over one shared implementation.
Qualtrics assigns exactly one condition before launch, routes the participant to
the corresponding application, and includes the same identifier in the `cond`
query parameter. The application rejects mismatched assignments and keeps its condition fixed
across all six candidate trials.

| Condition ID | Explanation | Delivery | Cognitive forcing |
|---|---|---|---|
| `P0_A0_F0` | Absent | Procedural | Absent |
| `P0_A0_F1` | Absent | Procedural | Present |
| `P0_A1_F0` | Absent | Anthropomorphic | Absent |
| `P0_A1_F1` | Absent | Anthropomorphic | Present |
| `P1_A0_F0` | Present | Procedural | Absent |
| `P1_A0_F1` | Present | Procedural | Present |
| `P1_A1_F0` | Present | Anthropomorphic | Absent |
| `P1_A1_F1` | Present | Anthropomorphic | Present |

The legacy `P0`/`P1` routing key is retained so deployed app and Qualtrics URLs
remain stable. Semantically, it records explanation absent/present. When
explanation is absent, only the frozen verdict is shown and participants must
inspect the always-available documents independently. When explanation is
present, the full fixed rationale, claim-linked neutral citations, and bounded
evidence examination are available. `A` controls the frozen communication
register. `F` controls whether, after the unaided
decision but before the AI recommendation is requested or revealed, the
participant must type or paste the mandatory certification requirement from the
complete job description.

## Frozen anthropomorphic-delivery manipulation

The active delivery specification is `anthrokit-hiring-study2-v4`, implemented
in `src/xai_as_closure/study2_delivery.py`. It preserves the validated
AnthroKit-Hiring contrast on five dimensions: self-reference, warmth, formality,
empathic directness, and hedging.

- **Low A (`LowA`)** uses the label “AI screening system” and a complete formal,
  procedural, impersonal assessment message. Its request, progress, and evidence-
  examination language use the same register.
- **High A (`HighA`)** uses the label “AI screening assistant” and a complete
  warm, first-person, mildly hedged, adviser-like assessment card. Its request,
  progress and evidence-examination language use the same register.

Explanation-present conditions use frozen procedural and anthropomorphic
templates for the advance and reject sides. C-01/C-02/C-05 share one advance
message. C-03/C-04 share one correct-reject message. C-06 has a separate frozen
false-reject message that makes the comparative, more-than-the-minimum rationale
explicit. Claim-level citations use neutral locators such as `CV §4`, open the
complete document at that location, and have the same placement and visual
treatment in both registers. Explanation-absent conditions use a corresponding
frozen LowA/HighA verdict-only pair. Persona names, gender, emoji, humor,
embodiment, emotional or lived-experience claims, protected-attribute inference,
and live LLM rewriting are excluded. `A` cannot alter explanation presence, and
explanation assignment cannot alter the delivery register.

## Condition-bounded agentic interaction

When explanation is present, after the recommendation is shown and before the
aided decision is locked, participants can use an optional bounded
evidence-examination action.
The recruiter can ask for the strongest support, strongest caution, application
of the mandatory rule, or missing/uncertain information. The migrated HAI agent
retrieves and renders a pre-authored candidate-specific response, appends it to
the conversation, and logs the interaction. The answer cannot change the frozen
verdict. The action is absent in no-explanation conditions so those participants
receive only the verdict and must verify against the source documents
independently. Within explanation-present conditions, semantic content is held
constant and `A` controls only response register.

The recommendation is invariant across all eight conditions. The complete
rationale is invariant across explanation-present delivery cells and is omitted
by design when explanation is absent.
