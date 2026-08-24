# Study 2 Condition Matrix

Study 2 uses eight condition-locked applications over one shared implementation.
Qualtrics assigns exactly one condition before launch, routes the participant to
the corresponding application, and includes the same identifier in the `cond`
query parameter. The application rejects mismatched assignments and keeps its condition fixed
across all six candidate trials.

| Condition ID | Provenance | Anthropomorphic delivery | Cognitive forcing |
|---|---|---|---|
| `P0_A0_F0` | Low | Low | Absent |
| `P0_A0_F1` | Low | Low | Present |
| `P0_A1_F0` | Low | High | Absent |
| `P0_A1_F1` | Low | High | Present |
| `P1_A0_F0` | High | Low | Absent |
| `P1_A0_F1` | High | Low | Present |
| `P1_A1_F0` | High | High | Absent |
| `P1_A1_F1` | High | High | Present |

`P` controls whether inspectable source mappings are shown. `A` controls only
the frozen communication register. `F` controls whether, after the unaided
decision but before the AI recommendation is requested or revealed, the
participant must type or paste the mandatory certification requirement from the
complete job description.

## Frozen anthropomorphic-delivery manipulation

The active delivery specification is `anthrokit-hiring-study2-v2`, implemented
in `src/xai_as_closure/study2_delivery.py`. It preserves the validated
AnthroKit-Hiring contrast on five dimensions: self-reference, warmth, formality,
empathic directness, and hedging.

- **Low A (`LowA`)** uses the label “AI screening system” and a complete formal,
  procedural, impersonal assessment card. Its request, progress, evidence-
  examination, and authority language use the same register.
- **High A (`HighA`)** uses the label “AI screening assistant” and a complete
  warm, first-person, mildly hedged, adviser-like assessment card. Its request,
  progress, evidence-examination, and authority language use the same register.

There are twelve deterministic main cards: a complete LowA/HighA pair for each
of the six profiles. Each pair expresses the same registered verdict and three
semantic claims and is length-controlled, but the whole discourse is rewritten
in the assigned register rather than placing invariant prose inside a cosmetic
wrapper. Persona names,
gender, emoji, humor, embodiment, emotional or lived-experience claims,
protected-attribute inference, and live LLM rewriting are excluded. The same
card is used at both provenance levels, so `A` cannot alter source visibility
and `P` cannot alter delivery register.

## Constant agentic interaction

After the recommendation is shown and before the aided decision is locked, all
eight conditions provide the same optional bounded evidence-examination action.
The recruiter can ask for the strongest support, strongest caution, application
of the mandatory rule, or missing/uncertain information. The migrated HAI agent
retrieves and renders a pre-authored candidate-specific response, appends it to
the conversation, and logs the interaction. The answer cannot change the frozen
verdict. Availability and semantic content are held constant across conditions;
`P` controls only source visibility and `A` controls only response register.

The recommendation and substantive rationale for a profile are invariant across
all eight conditions.
