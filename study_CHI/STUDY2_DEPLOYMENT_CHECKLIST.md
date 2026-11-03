# Study 2 Deployment and Technical-Pilot Checklist

**Internal release checklist — do not open recruitment until every required
item is signed off**

## 1. External research gates

The analysis authority is STUDY2_ANALYSIS_PLAN.md (v2): diagnostic outcomes, H1/H3 Holm tests, H2 estimation, and profile fixed effects.

- [ ] Operational specification is complete; `python analysis/study2/readiness.py` reports no unresolved inputs.
- [ ] Acceptable H2 interval width and selected analysable target (ceiling 400) are documented against archived simulation output.
- [ ] Final questionnaire item IDs, response ranges, reverse keys, scoring and export hash are frozen.
- [ ] Evidence-coding manual, seeded independent subset, blinding and adjudication procedure are frozen.
- [ ] Analysis exports use study2-analysis-v2 and agreement trials have no reliance score.
- [ ] All eight cells have technical-pilot timings; the derived allowance and input hash are recorded, with no automatic submission.


- [ ] Ethics approval covers six repeated candidate trials, an initial unaided
      decision, AI exposure, final aided decision, interaction logging, and the
      post-task measures.
- [ ] The final Qualtrics consent, eligibility, PPBE, ANT, TRUST, forcing-only PCE, pre-task AI-use frequency, interpersonal trust, generosity,
      attention, demographics, debrief, and completion logic are frozen.
- [ ] Study 1 expert Prolific IDs are blocked from Study 2 recruitment.
- [ ] The reproducible power simulation and its output are archived.
- [ ] Compensation is recalculated from the slowest credible technical-pilot
      completion time, not from the fastest completion.
- [ ] The final time allowance permits document verification in all eight
      conditions and does not automatically submit a decision.

## 2. Automated release gate

Run from the repository root in the Python 3.11 `dsagent` environment:

```bash
PYTHONPATH=src python -m xai_as_closure.release_audit
PYTHONPATH=src python -m unittest discover -s tests -v
python -m ruff check src tests apps
python -m ruff format --check src tests apps
```

Required result:

- [ ] release audit passes;
- [ ] all tests pass;
- [ ] Ruff lint passes;
- [ ] Ruff formatting check passes; and
- [ ] `git status --short` contains no unintended tracked changes.

The release audit compares the runtime materials and message specification with
`STUDY2_MATERIAL_FREEZE.json`; verifies all eight condition-locked entry points;
and checks recommendation, explanation-visibility, and delivery-register
invariants.

## 3. Deployment configuration

Configure and verify separately for every Streamlit Community Cloud app:

- [ ] `GITHUB_REPO` names the restricted study-data repository;
- [ ] `GITHUB_TOKEN` has only the permissions required to write study logs;
- [ ] the token and repository name are absent from the public repository and
      application output;
- [ ] the app's source branch and entry point match the table below;
- [ ] the application is publicly viewable without Streamlit, GitHub, Google,
      institutional, or email-invitation login; and
- [ ] the deployment uses the frozen commit recorded for launch.

| Cell | Condition | Entry point | Explanation | Delivery | Forcing |
|---:|---|---|---|---|---|
| 1 | `P0_A0_F0` | `apps/study2_01_lowP_lowA_noF.py` | Absent | Procedural | Absent |
| 2 | `P0_A0_F1` | `apps/study2_02_lowP_lowA_F.py` | Absent | Procedural | Present |
| 3 | `P0_A1_F0` | `apps/study2_03_lowP_highA_noF.py` | Absent | Anthropomorphic | Absent |
| 4 | `P0_A1_F1` | `apps/study2_04_lowP_highA_F.py` | Absent | Anthropomorphic | Present |
| 5 | `P1_A0_F0` | `apps/study2_05_highP_lowA_noF.py` | Present | Procedural | Absent |
| 6 | `P1_A0_F1` | `apps/study2_06_highP_lowA_F.py` | Present | Procedural | Present |
| 7 | `P1_A1_F0` | `apps/study2_07_highP_highA_noF.py` | Present | Anthropomorphic | Absent |
| 8 | `P1_A1_F1` | `apps/study2_08_highP_highA_F.py` | Present | Anthropomorphic | Present |

## 4. Signed-out access test

Test every deployed URL in a new signed-out incognito browser with
`embed=true`.

- [ ] the task opens without authentication;
- [ ] the Streamlit/GitHub toolbar is absent;
- [ ] the “You do not have access to this app” page never appears;
- [ ] the fictional-research disclosure and recruitment brief render;
- [ ] no repository identity, researcher email, secret, stack trace, or private
      storage detail is visible; and
- [ ] a deliberately mismatched `cond` value is rejected.

Use researcher-controlled pilot identifiers that cannot be mistaken for real
participant records. Record them in the private exclusion list, not this public
repository. Use a different identifier for every condition because the same
identifier deterministically resumes its existing condition.

## 5. Eight-condition visual and workflow audit

Complete all six trials in every cell. For each cell, confirm:

- [ ] profile order is randomized and remains stable after refresh;
- [ ] the CV is visible for the initial decision and is not continuously shown
      on the post-decision assessment page;
- [ ] job description, policy, and CV remain optionally accessible;
- [ ] the initial decision and confidence are locked before AI exposure;
- [ ] the fixed AI verdict is C-01 Advance, C-02 Advance, C-03 Reject,
      C-04 Reject, C-05 Advance, and C-06 Reject;
- [ ] the final decision, confidence, and neutral evidence-recall response are
      required before advancing;
- [ ] refresh or interruption resumes the same profile, phase, and condition;
- [ ] six trials are required before completion; and
- [ ] the valid Qualtrics route appears only as **Return to survey**; without a
      valid route, the page says only “Please return to your survey tab and
      continue.”

### Explanation absent (`P0`)

- [ ] only the frozen verdict is shown;
- [ ] no rationale, citation, source chip, or explanatory metadata is visible;
      and
- [ ] complete documents remain independently available.

### Explanation present (`P1`)

- [ ] the complete frozen rationale is shown;
- [ ] every citation is inline with its claim;
- [ ] every citation opens the complete source inside the assessment page;
- [ ] the cited passage is positioned and neutrally highlighted;
- [ ] closing returns to the unchanged assessment and final-decision form; and
- [ ] procedural and anthropomorphic cells expose the same citation set.

### Procedural delivery (`A0`)

- [ ] speaker is “AI screening system”;
- [ ] wording is impersonal, formal, and structured; and
- [ ] no first-person adviser language appears.

### Anthropomorphic delivery (`A1`)

- [ ] speaker is “AI screening assistant”;
- [ ] wording uses the frozen warm first-person adviser register; and
- [ ] no avatar, chatbot icon, persona name, emoji, humor, lived-experience
      claim, or authority reminder appears.

### Cognitive forcing present (`F1`)

- [ ] forcing occurs after the initial decision and before AI exposure;
- [ ] the task is identical for every candidate and every `P`/`A` cell;
- [ ] it asks for the two role requirements, not a candidate classification;
- [ ] the complete job description opens focused at Section 4.1 while retaining
      the complete document;
- [ ] an incomplete or incorrect response never unlocks the AI, regardless of
      the number of attempts; and
- [ ] a response containing a current qualifying certification and current
      relevant professional membership unlocks the AI.

## 6. Error-profile audit

### C-05 — false advance

- [ ] participant CV shows IAPP AIGP ending 31 May 2026;
- [ ] current IAPP membership remains separate and does not revive the expired
      certification;
- [ ] AI verdict remains Advance in all eight cells;
- [ ] explanation-present citations expose the dated certification, membership,
      governing requirements, and relevant policy; and
- [ ] no participant-facing text reveals “false advance” or ground truth.

### C-06 — false reject

- [ ] Certifications shows current `AIGP` without expanding the issuer;
- [ ] Professional Memberships shows current IAPP membership with the same term;
- [ ] AI verdict remains Reject in all eight cells;
- [ ] explanation-present citations expose both separated CV sections and the
      whole-file evidence rule; and
- [ ] the frozen AI text confidently invokes the alternative ETHOS reading
      without adding ETHOS to the source documents.

## 7. Private logging and resume audit

For one complete pilot session in every condition, verify the private archive
contains:

- [ ] `study2-state-v9`, `study2-event-v11`, and `study2-app-v12`;
- [ ] `anthrokit-hiring-study2-v7` and case set v5;
- [ ] condition factors and stable randomized profile order;
- [ ] initial and final decisions, confidence, and timestamps;
- [ ] forcing attempts, validated response, and elapsed time where assigned;
- [ ] AI plan, retrieval, evaluation, verdict, rendering, and visible-source
      audit fields;
- [ ] citation click, document open, focus, dwell, close reason, and return
      target where applicable;
- [ ] evidence-recall response and total session duration;
- [ ] a durable private-GitHub checkpoint after every completed workflow step;
      and
- [ ] no names, email addresses, Qualtrics Response IDs, credentials, or
      unrelated browser telemetry.

Interrupt at least one pilot session after each of these points and confirm
resume: introduction, initial decision, forcing, AI reveal, final decision, and
between candidate trials.

## 8. Qualtrics round trip

- [ ] Qualtrics assigns one condition and opens its matching locked app;
- [ ] the launch includes `PROLIFIC_PID`, `cond`, encoded HTTPS `return`, and
      `embed=true`;
- [ ] a non-Qualtrics or HTTP return route is rejected;
- [ ] completion overwrites any conflicting return-query linkage fields with
      the actual participant, session, condition, and `done=1` values;
- [ ] the returned record joins to exactly one private application session; and
- [ ] the Qualtrics debrief discloses that some AI recommendations were
      deliberately incorrect.

## 9. Pilot acceptance record

Record privately:

- frozen Git commit;
- deployment URLs and condition mapping;
- test date, browser, viewport, and tester;
- one private session ID per condition;
- automated audit/test output;
- observed median, upper-percentile, and maximum completion times by condition;
- defects found and their resolution; and
- final ethics, power, Qualtrics, timing, and launch sign-offs.

## 10. Rollback

If any release invariant, route, storage check, or pilot workflow fails:

1. do not recruit or pause recruitment;
2. preserve affected session records and version identifiers;
3. correct the defect on a new application/schema/material version as required;
4. rerun the complete automated and eight-condition audit; and
5. do not combine incompatible sessions without an explicit documented rule.


## 11. Local preparation update, 30 October 2026

The researcher review hub is apps/local_review.py, outside the frozen eight-app entry-point set. Use tools/local_study2.py for isolated local previews. Never enable STUDY2_LOCAL_PREVIEW on a production host.

- [ ] Validate v12 stable private checkpoints at sessions/xai_as_closure/study2/checkpoints/<session_id>.json. Do not mix old dated pilot archives with this release.
- [ ] Complete a live server-restart recovery test with local files absent; check state, condition, profile order and full event history.
- [ ] Simulate a storage write outage and verify that progress/return is blocked until retry succeeds.
- [ ] Verify the configured data repository is private. Initial checkpoint write must succeed before task progression.
- [ ] Test parallel participants, duplicate tabs, API-rate limits and realistic checkpoint payload sizes on the selected deployment.
- [ ] Verify the return route resumes the original Qualtrics response; do not trust a client-supplied done=1 as proof of completion.

PPBE, ANT, TRUST and forcing-only PCE use researcher-confirmed 1–7 agreement endpoints. Pre-task response options and final survey export mapping are still pending. Production recovery is covered by mocked tests; this does not replace live hosting verification.
