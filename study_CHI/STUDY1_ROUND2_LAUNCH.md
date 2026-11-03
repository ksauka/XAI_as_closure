# Study 1: second expert assessment

Prepared on 3 November 2026. No second-round expert responses have been collected by preparing or testing this application.

The standalone application is `apps/study1_validation_v2.py`. Deploy it as its own Streamlit app, separately from the earlier Study 1 app and all eight Study 2 apps. Participants receive only its own study link. The researcher hub is not a participant entry point.

## Materials and procedure

The app reads the same canonical v6 job description, recruitment policy and six candidate profiles as Study 2. `STUDY1_ROUND2_MATERIALS.json` records their hashes; the app stops if the files change. JD 4.2.1 now provides the explicit certification-identity rule. Policy 2.3 covers whole-file assessment and currency. C-05 still has the expired AIGP certification; C-06 still has a bare AIGP entry and current IAPP membership. The intended decisions have not changed.

Every expert assesses all six profiles in a participant-specific random order. C-05 and C-06 receive no special labels, hints or feedback. The app shows no AI advice. For each profile it records the screening decision, mandatory-requirements judgement, confidence and decisive evidence. The final materials review remains unchanged, including conditional questions about professional disagreement.

Instrument v7 broadens the decisive-evidence question from information in the candidate file alone to the relevant requirement and candidate evidence. The same question is asked for every profile. Record this change alongside the governing-document revision; do not describe the two rounds as identical instruments.

## Local rehearsal

Run `python tools/local_study1_round2.py` in the repository's installed Python environment. The default address is `http://localhost:8509/`. Each launch creates a new temporary folder and synthetic participant identifier. Preview mode ignores incoming participant and return parameters and makes no remote backup writes. Test records are marked `is_preview: true`; do not import them into research results. The researcher hub links to this local address.

## Production deployment

1. Use a separate Streamlit deployment with main file `apps/study1_validation_v2.py` and the repository's pinned requirements. Include the canonical materials, source module and round-2 manifest in the deployed revision.
2. Configure private data storage through `GITHUB_REPO` and `GITHUB_TOKEN`, or the existing `GITHUB_DATA_REPO` and `GITHUB_DATA_TOKEN` alternatives. The repository must be private. Give the deployment credential only the required access to this data repository. Never put credential values in source files or participant URLs.
3. Leave `STUDY1_LOCAL_PREVIEW` unset. A production launch requires a valid participant identifier and working private storage. Experts may enter either a researcher-issued participant code or their Prolific ID; Prolific recruitment is not required. Round-2 local snapshots use `study_CHI/data/raw/study1_round2`; `STUDY1_ROUND2_DATA_ROOT` can override this. If the older generic `STUDY1_DATA_ROOT` is used, the new app adds a `round2` subfolder.
4. For Prolific recruitment, pass `PROLIFIC_PID` through the task URL. For independently recruited experts, pass `participant_code`, or let them enter their researcher-issued code on the welcome page. Use one route, not both. Researcher codes contain 3–64 letters, numbers, hyphens or underscores; issue a unique pseudonymous code to each expert and keep any identity mapping separately. Do not use names or email addresses. Codes are case-sensitive. An optional `return` parameter may contain a URL-encoded HTTPS Qualtrics return URL. Verify the full consent-to-task-to-closing flow using a clearly identified pilot before recruiting. The task has no built-in consent or eligibility survey. Configure these in Qualtrics rather than sending experts directly into the task.
5. Check the private saved record, including the six judgements, final review, round, instrument version, material hashes and event sequence. Test a refresh and a return after the local snapshot is unavailable. The app checks its stable private checkpoint before creating a new session. Do not run two simultaneous copies of the task for one participant.
6. Confirm completion in the saved record. The URL parameter `done=1` is a routing indicator, not independent proof of completion. Configure the survey's completion verification against the saved completed session before issuing credit or payment automatically.

Production records retain the participant identifier and recruitment source in the private checkpoint. Only Prolific-linked records populate `prolific_pid`; independently recruited experts use the separate researcher-code namespace. They do not request names or email addresses. This is a clarification of the older protocol's stronger statement that the app receives no raw platform identifier. Reflect the actual linkage arrangement in the approved privacy information and restrict access to it. Events use the linkage hash and session identifier.

Remote checkpoints are stored under `sessions/xai_as_closure/study1/round2/<session_id>.json`. They contain both the state and the ordered event history. Local round-2 records and private checkpoints are separate from the earlier batches. A failed backup blocks further progress or the completion return until saving succeeds.

## Fix before expert recruitment

Use fresh experts: exclude every earlier Study 1 participant and pilot, and exclude these experts from Study 2. Fix eligibility, sample size, compensation, missing-response exclusions, agreement thresholds, intended-reason coding and adjudication before opening recruitment. The earlier protocol's sample target is not evidence that the revised-round recruitment settings have been finalised. Pilot the duration before setting time and payment; this app does not promise a ten-minute completion time.

Analyse this round separately from the original batches. Report profile-level decisions and mandatory-requirements judgements, uncertainty, intended-reason coding and professional-disagreement explanations. For C-05, distinguish noticing expiry from rejecting for another reason. For C-06, distinguish applying JD 4.2.1 from guessing the issuer or overriding the stated rule. Document access and viewing intervals show access behaviour, not comprehension. Do not change the manifest or threshold after observing responses without recording a new material revision and its reason.

This application prepares the new expert assessment. It does not declare the revised materials validated or release Study 2 for recruitment.


## Participant links and repeated testing

A participant can open the bare app address and choose a researcher-issued code or Prolific ID. For survey integration, use `?participant_code=EXP-007` for a researcher-issued code, or the existing `?PROLIFIC_PID=...` for a Prolific-issued ID. Do not place the example code in a real recruitment invitation; issue each expert a unique code. Qualtrics must fill its embedded field before the participant opens the task. Literal `${e://Field/...}` values are rejected with an explicit message rather than saved as participant IDs.

Researcher-code returns include `participant_code`, `session_id` and `done=1`; Prolific returns retain `PROLIFIC_PID`, `session_id` and `done=1`. Configure the corresponding embedded field in the closing survey. Neither route treats `done=1` alone as independent completion verification.

The same ID or code restores the same session, including a completed one. A restored completion now explicitly says that a previous completed session was loaded. Incognito does not reset server records. Use the isolated local preview for repeated software testing; do not remove real responses or reuse one code across experts. Changing identity within a live tab is blocked to prevent mixing two participants' responses. Close that tab and open the intended link in a new tab.

The linkage update changes application metadata, not the six materials, questions, ground truth or experimental design. Instrument v7 and the shared v6 material hashes remain unchanged. The round-2 application event version is `study1-round2-app-v3`.


## Checking the running release

The version-2 entry point now displays `Study 1 · Version 2 · second expert assessment · Build 2026-11-03.3` before any participant-ID check. The earlier entry point instead says `Earlier Study 1 entry point`. If neither marker is present, the visible page has not executed these entry-point files.

An entry-point/shared-module mismatch now stops with an explicit older-code message before the cached launch function can run. This check does not reset participant records or restart the service. The researcher controls any necessary deployment restart. The repository disables automatic source watching, so a browser refresh alone does not guarantee that imported server modules are refreshed.

The exact older message `The supplied Prolific ID is invalid.` is absent from the current Study 1 modules. Study 2 retains a Prolific-only check, so seeing that sentence alone is not sufficient to identify which app or release is running. Confirm the visible Study 1 version-2 marker before diagnosing participant-link behaviour.
