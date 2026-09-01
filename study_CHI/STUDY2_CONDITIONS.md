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
present, the full fixed rationale and claim-linked neutral citations are
available. `A` controls the frozen communication register. `F`
controls whether, after the unaided
decision but before the AI recommendation is requested or revealed, the
participant must type or paste both mandatory professional requirements—the
qualifying certification and current professional membership—from the complete
job description.

Before candidate screening, every condition presents the same single-screen
recruitment brief: a concise company-and-role summary, concise recruitment
guidance, the shared recruitment timeline (posted 20 July 2026, screening window
27–30 August 2026, target fill 20 September 2026), and two optional full-document buttons. This keeps the task oriented
toward screening rather than a sequence of compulsory document windows. The
complete job description and recruitment policy remain optionally available
during every trial for verification.

## Frozen anthropomorphic-delivery manipulation

The active delivery specification is `anthrokit-hiring-study2-v7`, implemented
in `src/xai_as_closure/study2_delivery.py`. It preserves the validated
AnthroKit-Hiring contrast on five dimensions: self-reference, warmth, formality,
empathic directness, and hedging.

- **Low A (`LowA`)** uses the label “AI screening system” and a complete formal,
  procedural, impersonal assessment message. Its request and progress language
  use the same register.
- **High A (`HighA`)** uses the label “AI screening assistant” and a complete
  warm, first-person, mildly hedged, adviser-like assessment card. Its request,
  progress, and recommendation language use the same register.

Explanation-present conditions use frozen procedural and anthropomorphic
templates for the advance and reject sides. C-01/C-02/C-05 share one advance
message. C-03/C-04 share one correct-reject message. C-06 has a separate frozen
false-reject message that treats its bare AIGP entry as ambiguous despite the
current IAPP membership elsewhere in the same candidate file. It invokes the
distinct ETHOS Certified AI Governance Professional as an alternative meaning,
then criticises credential-documentation precision and attention to detail. This
is deliberately the AI's erroneous reasoning, not a fact added to the supplied
knowledge documents. Claim-level citations use neutral locators such as `CV(4)`
and `CV(6)`. Each
citation opens the complete source document inside the AI-assessment page,
automatically positions the cited passage in view, and highlights that passage
without extracting or interpreting it. Citation placement, document treatment,
and highlighting are identical in both registers. Explanation-absent conditions use a corresponding
frozen LowA/HighA verdict-only pair. Persona names, gender, emoji, humor,
embodiment, emotional or lived-experience claims, protected-attribute inference,
and live LLM rewriting are excluded. `A` cannot alter explanation presence, and
explanation assignment cannot alter the delivery register.

The false advance on C-05 is a certification-currentness error. The candidate's
AIGP term ended on 31 May 2026, before the screening window, but the fixed
recommendation treats it as current. The shared advance citation set for
C-01/C-02/C-05 includes `CV(4)`, `JD(4.1)`, `JD(4.2)`, `POL(2.1)`, and
`POL(2.3)` so the evidence needed to overturn C-05 remains within the cited
documents without giving the error trial a distinctive citation pattern.

The false reject on C-06 is a whole-file reconciliation error. Its Certifications
section records a current `AIGP` term without expanding the issuer. Its later
Professional Memberships section records current International Association of
Privacy Professionals (IAPP) membership with the same 18 June 2025–30 June 2027
term. Read together under policy Section 2.3,
these passages establish the current IAPP AIGP in job-description Section 4.1
and the separate membership required by Section 4.2. The fixed recommendation
instead treats `AIGP` as potentially referring to another provider and rejects
the candidate. Its explanation cites the certification, membership, relevant
experience, role requirements, and governing policy, so the error remains
recoverable by reconciling the complete cited evidence.

## Current agent boundary

The migrated agent plans, retrieves, evaluates, recommends, and renders the
frozen assessment. After the unaided decision, the participant moves to a
separate assessment page; the CV is no longer continuously displayed but remains
available as an optional source document and through explanation citations.
Citation traversal does not replace the assessment page: the focused complete
document opens in-page and closes back to the unchanged assessment and final
decision form.

The recommendation is invariant across all eight conditions. The complete
rationale is invariant across explanation-present delivery cells and is omitted
by design when explanation is absent.

## Local verification, one entry point per condition

Each condition is a fixed, standalone Streamlit entry point under `apps/`; there
is no shared runtime toggle between conditions. To confirm all eight locally,
run each on its own port and open it directly (add `?PROLIFIC_PID=<anything>`
to skip the manual-entry gate; use a different ID per condition, since the same
ID resumes an in-progress session and a condition mismatch is rejected):

```bash
streamlit run apps/study2_01_lowP_lowA_noF.py --server.port 8602
streamlit run apps/study2_02_lowP_lowA_F.py   --server.port 8603
streamlit run apps/study2_03_lowP_highA_noF.py --server.port 8604
streamlit run apps/study2_04_lowP_highA_F.py   --server.port 8605
streamlit run apps/study2_05_highP_lowA_noF.py --server.port 8606
streamlit run apps/study2_06_highP_lowA_F.py   --server.port 8607
streamlit run apps/study2_07_highP_highA_noF.py --server.port 8608
streamlit run apps/study2_08_highP_highA_F.py   --server.port 8609
```

| Entry point | Condition ID | Explanation | Delivery | Forcing |
|---|---|---|---|---|
| `study2_01_lowP_lowA_noF.py` | `P0_A0_F0` | Absent | Procedural | Absent |
| `study2_02_lowP_lowA_F.py` | `P0_A0_F1` | Absent | Procedural | Present |
| `study2_03_lowP_highA_noF.py` | `P0_A1_F0` | Absent | Anthropomorphic | Absent |
| `study2_04_lowP_highA_F.py` | `P0_A1_F1` | Absent | Anthropomorphic | Present |
| `study2_05_highP_lowA_noF.py` | `P1_A0_F0` | Present | Procedural | Absent |
| `study2_06_highP_lowA_F.py` | `P1_A0_F1` | Present | Procedural | Present |
| `study2_07_highP_highA_noF.py` | `P1_A1_F0` | Present | Anthropomorphic | Absent |
| `study2_08_highP_highA_F.py` | `P1_A1_F1` | Present | Anthropomorphic | Present |

What distinguishes each manipulation on screen:

- **Explanation (P).** Absent (`P0`, ports 8602-8605): the recommendation shows
  a verdict with no clickable evidence. Present (`P1`, ports 8606-8609): an
  "Inspect evidence used" row appears below the recommendation with `[CV · …]`
  / `[Role(…)]` / `[Policy(…)]` chips that open the real cited passage.
- **Delivery (A).** Procedural (`A0`): speaker label "AI screening system",
  structured "Recommendation: **X**." text. Anthropomorphic (`A1`): speaker
  label "AI screening assistant", first-person prose ("I'd recommend...").
- **Forcing (F).** Present (`F1`): after the unaided decision, the participant
  must re-encode both mandatory professional requirements from the role
  description before the recommendation unlocks. Absent (`F0`): the recommendation is available
  immediately on request.
