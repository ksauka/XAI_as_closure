# Study 2: local preparation and launch sequence

30 October 2026. This is a preparation specification, not a published study or an approved survey export.

## Agreed study

Eight between-participant conditions cross explanation presence, procedural/anthropomorphic delivery, and fixed requirement re-entry. Each participant completes six profiles in stable random order. Preserve the frozen profile text, recommendation mapping, citations and delivery wording. The HAI poster is the predecessor, not the operational specification for this experiment.

## Local software

The existing WSL Ubuntu dsagent environment has Python 3.11, Streamlit 1.62.0, Requests 2.34.2, pytest, Ruff, NumPy and SciPy. Dependency consistency passed. The experiment uses the frozen agent pipeline; its core participant route does not require new live LLM calls, LangChain or a vector-database service. No new software installation was needed. Tested runtime versions are pinned in requirements.txt; development/analysis tools are in requirements-dev.txt. Existing broader environment packages need not be upgraded.

From `/home/suvh/projects/XAI_as_closure`, using `/home/suvh/miniconda3/envs/dsagent/bin/python`:

```sh
python tools/local_study2.py
STUDY2_LOCAL_PREVIEW=1 python -m streamlit run apps/local_review.py --server.address 127.0.0.1 --server.port 8500
```

The first command runs all eight conditions on ports 8501–8508. The second opens a researcher review page at http://localhost:8500. Keep the processes running. Ctrl+C stops them. Preview logs are synthetic, isolated under a fresh temporary directory and excluded from research data; remote saving is disabled. Preview sessions resume, so refreshing does not restart a completed participant. Restart the launcher to create fresh preview sessions. Do not deploy the review hub or enable STUDY2_LOCAL_PREVIEW in production. Local addresses are not Prolific recruitment links.

## Survey flow to implement in Qualtrics

1. Capture PROLIFIC_PID, STUDY_ID and SESSION_ID in embedded data. Obtain the approved consent. Implement non-consent and eligibility routes before treatment exposure.
2. Record occupational eligibility and the three pre-task items: AI-use frequency, interpersonal trust propensity, general generosity. Their wording is confirmed in STUDY2_QUESTIONNAIRE.md; response options still need confirmation. Do not replace generosity with risk aversion or add NCS6 from an older plan.
3. Assign one of the eight conditions once, with equal allocation, and retain that assignment on resume. Pass only the matching condition to its locked app. Keep study and submission IDs in the survey for joining; the app's own session_id is a different identifier.
4. Open the corresponding HTTPS app with PROLIFIC_PID, cond, embed=true and the encoded return route. Use the existing two-tab approach unless a tested Qualtrics integration supports another approach. A survey URL with arbitrary query parameters is not proof that the original Qualtrics response resumes: test preservation of the response, assignment and pre-task answers explicitly.
5. After all six candidate trials, link the returned app session_id and condition to exactly one archived complete session. A client-supplied done=1 flag is not sufficient evidence of completion. Implement a verifiable hand-off or reconciliation procedure before recruitment.
6. Administer PPBE (5), ANT (5) and TRUST (9) to all participants. Administer PCE (3 candidate adapted items) only to F1 participants. All four use 1–7, Strongly disagree to Strongly agree, confirmed by the researcher. Preserve exact wording and PPBE_5 reversal. No response should be preselected.
7. Non-forcing PCE is structurally not applicable. It is not zero or a failed manipulation check. PCE does not support a between-condition comparison or causal mediation claim. Completion, attempts and timing are the implementation checks.
8. Add the prospectively agreed attention item, demographics and approved debrief. Disclose deliberate AI errors. Only the completed survey should return participants to the correct Prolific completion URL/code. Provide a recovery/contact route if the hand-off fails.
9. Export the final QSF and a synthetic CSV. Verify actual export keys, branching, values and missing codes; record hashes and freeze the mapping. A written specification is not a substitute for this round trip.

## Tests and acceptance evidence

- Automated: full test suite, all eight six-trial app journeys, incomplete-forcing blocking, fresh-session resume, ordered event records, completion counts, remote-write isolation, analysis outcome scoring, release audit, lint, formatting, dependency check and whitespace check.
- Browser: both delivery styles, explanation present/absent, forcing present/absent, citation opening and full source positioning, document close, retention of form values, no text overflow at the intended desktop/laptop viewport. Perform signed-out checks again on deployed URLs.
- Storage: private repository verification, durable checkpoints, recovery after a browser refresh AND a server restart with local files removed, storage outage before and after a decision, duplicate tabs, simultaneous participants, GitHub write conflicts/rate limits, and restoration without changing assignment or losing event history.
- Survey: consent exits, eligibility exits, all eight assignments, return to the original response, joining exactly once, forcing-only PCE branch, completion-code routing and broken-link recovery.
- Human technical pilot: the operational rule calls for at least five complete sessions in each cell, separate from confirmatory data. Automated walkthroughs do not count as human timing data. Pilot the full survey plus task, not the task alone. Record interruptions and item comprehension.

## Production issues still requiring resolution

Release v12 now restores a validated stable remote checkpoint when the host has lost its local files. It restores both state and event history, rejects corrupt/mismatched records, and blocks new sessions on recovery errors. A failed production save blocks progression until retry succeeds. The connection check rejects public repositories and explicitly denied write permission; the initial checkpoint write is the effective write test. These behaviours have automated mocked tests. They still require live deployment verification before recruitment. Stable checkpoints are at `sessions/xai_as_closure/study2/checkpoints/<session_id>.json`; older dated pilot archives must not be silently mixed with this release.
Do not infer Prolific-scale capacity from eight single-user local walkthroughs. Test realistic simultaneous traffic and storage API usage on the selected deployment. Archive the final code commit, material manifest, software versions, URLs, export mapping and pilot evidence.

## Research decisions still pending

Final analysable target within the ceiling of 400; justified H1/H3 planning effects and acceptable H2 precision; pilot-derived timing; pre-task response options; attention item; final survey export; ethics coverage/sign-off; private Study 1/prior-sample and pilot exclusion lists; deployment/storage choice and support contact. These fields remain visibly unresolved rather than filled with invented values.

## Prolific preparation

Prepare a study draft with the approved eligibility criteria, desktop/laptop requirements, working HTTPS survey URL, exclusions, pilot-based duration and compensation, contact route and completion paths. Keep pilot and full-study records separate. Do not publish or incur recruitment costs during local preparation.

Prolific recommends piloting the full flow before main recruitment: https://researcher-help.prolific.com/en/articles/445167-how-do-i-run-a-pilot-study-on-prolific . The project's five-per-cell rule is its own operational rule, not a Prolific requirement.

Its Qualtrics integration guidance covers participant IDs and completion routing: https://researcher-help.prolific.com/en/articles/445194-qualtrics-integration-guide .

Current payment guidance states a minimum £6/$8 per hour and recommends £9/$12 per hour; actual compensation and total budget remain unset until full-flow timing and account currency/fees are known: https://researcher-help.prolific.com/en/articles/445129-study-cost . Prolific sets the platform maximum time automatically; distinguish that from the app's planned soft allowance. The app must not automatically submit decisions.
