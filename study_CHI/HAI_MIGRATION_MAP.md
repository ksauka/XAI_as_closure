# HAI-to-Study-2 Migration Map

The former `src/agentic_hiring` implementation is the baseline for the active
Study 2 system. It was not discarded and rebuilt as a minimal wrapper. Its
working responsibilities were migrated into `src/xai_as_closure` and adapted to
the six validated profiles and the current explanation × anthropomorphism ×
cognitive-forcing design.

## Active migrated modules

| Former HAI responsibility | Active module | Adaptation |
|---|---|---|
| Agent orchestration and state | `decision_agent.py`, `schemas.py` | Retains evidence-store → plan → retrieve → evaluate → recommend → render → examine lifecycle; uses six candidate-scoped states and fixed error trials. |
| Evidence parsing and retrieval | `cases.py`, `evidence_store.py`, `retriever.py` | Reads the current recruitment policy, job description, and embedded CV sections; registered evidence sets replace the historical single-CV store. |
| Evaluation and recommendation policy | `evaluator.py`, `recommender.py` | Preserves the six pre-registered AI verdicts, including the intended false advance and false reject; interaction cannot mutate a verdict. |
| AnthroKit configuration and response cards | `anthrokit_hiring.yaml`, `anthrokit_prompts.py`, `study2_delivery.py` | Retains the five operative LowA/HighA dimensions and guardrails. Frozen advance/reject templates and bounded candidate-specific follow-up cards replace the historical single-candidate scripts. |
| Rendering and citation presentation | `renderer.py`, `study2_app.py`, `theme.py` | Retains the instructions → role → policy introduction, conversational rendering, chat presentation, full-document navigation, dwell logging, condition-sensitive controls, and the HAI visual system. Explanation-present cells attach neutral CV/JD/POL locators directly to their claims and open the complete document at that focus; explanation-absent cells show the verdict only. |
| Interaction | `decision_agent.py`, `study2.py`, `study2_app.py` | Retains post-recommendation evidence examination for support, caution, policy application, and missing information when explanation is present. It is omitted with the rationale in explanation-absent cells. Old HIC assignment is not a factor and cannot change the recommendation. |
| Logging and GitHub persistence | `logger.py`, `github_saver.py`, `github_loader.py` | Retains the HAI `EventLogger`, local per-session JSONL stream, Prolific linkage fields, and private-GitHub session backup. Writes use owner-only permissions and the backup runs after each completed trial. No parallel Study 2 storage abstraction is used. |
| Session extraction | `session_flatten.py` | Retains JSON/JSONL loading and CSV writing; now emits participant-, six-trial-, and event-level rows for appropriate-reliance analysis. |
| Qualtrics cleaning and merge | `qualtrics_clean.py`, `qualtrics_merge.py` | Retained for linkage validation, deduplication, and joining app exports to survey measures. |
| Configuration | `config.py` | Retained for deployment compatibility. Experimental text does not depend on an OpenAI key. |

The canonical modules are imported directly. Compatibility wrappers such as
`study2_conditions.py`, `study2_storage.py`, `study2_agent.py`, and
`study2_schemas.py` are intentionally absent because they duplicate the migrated
HAI modules without changing behavior.

## Intentionally changed or inactive legacy paths

These exclusions are design-preserving, not omissions:

- The historical `engine.py` was a second, competing implementation of the
  agent. It is not retained because `decision_agent.py` is now the single
  canonical pipeline; two engines could diverge on a registered stimulus.
- The historical `streamlit_app.py` encoded one candidate and the obsolete
  E×A×HIC screen order. Its proven theme, chat, citation, document-navigation,
  persistence, and interaction patterns were integrated into `study2_app.py`,
  whose six-trial explanation × anthropomorphism × forcing state machine is
  necessarily different. Stable `P0`/`P1` route IDs are retained for deployment.
- Historical arbitrary CV upload and `documents.py` ingestion are excluded
  because Study 2 must show exactly the six expert-validated CVs. Accepting an
  uploaded seventh profile would violate the case-set contract.
- HIC Stage 1 steering and its ability to change a recommendation are excluded
  because HIC is no longer an experimental factor and current verdicts must stay
  fixed. The post-recommendation examination mechanism is retained equally in
  every condition.
- Open-ended LLM rewriting in `anthrokit_stylizer.py` is retained only as
  compatibility code and is not called by the instrument. The active app uses
  pre-authored cards so wording cannot drift between participants.
- `semantic_search.py` is retained as a fallback utility but is not used for
  participant-authored arbitrary questions. The active examination choices are
  bounded, deterministic, and auditable.
- Historical Study HAI materials and its single candidate are not active data
  sources. Current retrieval is limited to the three `study_CHI` sources and six
  validated profiles.

## Active invariants

- Eight condition-locked applications; six trials per participant.
- Recommendation and registered semantic claims fixed per profile.
- Explanation is absent or present: absent shows the verdict only; present shows
  the full frozen rationale, citations, and bounded evidence examination.
- Anthropomorphism changes the complete delivery register and interaction
  language, not the substantive claims or evidence set.
- Cognitive forcing occurs after the unaided decision and before recommendation
  reveal, using the complete job description focused initially on Section 4.1.
- Bounded post-recommendation interaction is available when explanation is
  present and cannot change the verdict.
