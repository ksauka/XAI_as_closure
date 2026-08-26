# HAI Streamlit-to-Study-2 Comparison

This comparison was made directly between the historical
`src/agentic_hiring/streamlit_app.py` in Git history and the active
`src/xai_as_closure/study2_app.py`. It governs which interface behavior is
ported and why a historical behavior is changed or excluded.

| Historical HAI behavior | Active Study 2 disposition | Reason |
|---|---|---|
| Prolific ID entry and raw query-parameter gate | Ported | Study 2 retains `PROLIFIC_PID`/`pid`, `cond`, and `return`; the manual ID gate remains as the pilot fallback. A supplied condition must match the condition-locked app. |
| Welcome, fictional-scenario disclosure, advisory AI statement, role screen, policy screen | Ported as a required instructions → complete role → complete policy introduction | The current protocol requires the role to be shown at the start and available throughout. |
| One fixed candidate screen | Adapted to six randomized, stateful candidate trials | Current within-subjects design uses all six validated profiles. |
| HAI theme, banner, reading column, chat presentation, button and citation styles | Ported through `theme.py` and the shared Study 2 app | Condition-neutral presentation remains useful and tested. |
| Condition-sensitive recommendation button, spinner, prompt, and conversational response language | Ported and expanded | LowA/HighA now governs complete main cards and bounded evidence-examination language, not only a wrapper. |
| HIC Stage 1 priority steering before recommendation | Excluded | HIC is not a current factor; steering could alter a pre-registered verdict and confound the explanation × anthropomorphism × forcing design. |
| Full plan → retrieve → evaluate → recommend → render agent lifecycle | Ported, with candidate-scoped evidence stores | Agenticity is retained while outputs remain reproducible across the six fixed trials. |
| Citation controls | Ported as neutral claim-linked CV/JD/POL locators | In explanation-present cells, each citation sits directly after its conversational claim and opens the complete document at that location. In explanation-absent cells, only the verdict is shown; stable `P0`/`P1` IDs remain deployment keys. |
| Citation opens complete document with cited section highlighted; click and dwell are logged | Ported | Supports evidence traversal and the false-advance/false-reject detection asymmetry. |
| HIC Stage 2 selectable evidence challenge | Adapted as constant interaction in all eight conditions | Retains genuine post-recommendation agent interaction without making it a fourth factor. The four bounded options are support, caution, rule application, and missing information. |
| HIC Stage 2 free-text question and live LLM fallback | Excluded | Arbitrary generation would produce participant-specific wording and evidence, weakening stimulus invariance and auditability. |
| HIC could change the recommendation to Hold | Excluded | Study 2 has two fixed outcomes and pre-registered verdicts, including two intentional errors. |
| Judgement-settledness item before final decision | Excluded | It is not part of the current registered measures and would add an unplanned repeated outcome. |
| Three final actions including Hold and conditional hold reasons | Replaced by Advance candidate to human interview/Reject candidate plus confidence | The locked recruitment policy and Study 1 ground truth use the current two-outcome rule. |
| Recommendation dwell and final-decision timing | Ported | Study 2 records recommendation presentation and aided-submission times per trial. |
| Single-candidate completion metrics | Excluded | They do not map to a six-trial task and could expose or overemphasize one trial. |
| Local JSONL logger and end-of-task GitHub save | Ported and extended to six trials | The canonical `EventLogger` retains local JSONL and the existing private-GitHub saver. It includes the six-trial state in the session payload and backs up after each completed trial. |
| Direct Qualtrics return URL with `PROLIFIC_PID`, session, condition, and done fields | Ported and hardened | The same handoff fields are retained; host validation now requires an actual `qualtrics.com` host or subdomain. |
| Participant/session and event flattening | Ported and adapted | Exports now include participant, six-trial, and event levels needed for mixed-effects appropriate-reliance analysis. |

The resulting interface is not a new minimal app. It is the HAI interaction
model adapted to the current materials, conditions, outcome space, and six-trial
procedure while preserving the working HAI deployment infrastructure.
