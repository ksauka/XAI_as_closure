# XAI as Closure

Independent research workspace for the redesigned CHI 2027 project on how
provenance-based explainability, anthropomorphic delivery, and cognitive forcing
shape verification, decision revision, and appropriate reliance on agentic AI
advice.

## CHI 2027 Research Design

The project contains two studies in one research programme:

1. **Study 1: expert validation.** Domain experts independently evaluate six
   candidate profiles against a locked job description and recruitment policy.
   This establishes the profile-level ground truth used in Study 2.
2. **Study 2: six-profile experiment.** Participants complete unaided and
   AI-assisted decisions for six profiles in random order. They are randomly
   assigned to one of eight between-subject conditions in a 2 x 2 x 2 design:
   provenance traceability, anthropomorphic delivery, and cognitive forcing.

Both studies use dedicated applications. In Study 1, one shared validation app
serves multiple experts, presents all six candidates in a randomized order, and
records the six required judgment fields without showing any AI output.
Qualtrics provides only consent, pseudonymous linkage, and completion or closing
routing for this study. Eight condition-locked Study 2 applications deliver the
eight agentic-AI conditions across six repeated trials, with Qualtrics routing
each participant to the assigned application and supporting the questionnaires.
Study 1 uses its pseudonymous linkage flow. Study 2 retains the working HAI
integration: Qualtrics passes `PROLIFIC_PID`, the assigned `cond`, and the
encoded `return` URL to the condition-locked application.

In forcing-present Study 2 conditions, the participant records the unaided
decision, re-enters the mandatory certification requirement from the complete
job description while the AI output remains hidden, and only then requests the
AI recommendation.

Study 2's LowA and HighA communication registers are frozen in
`src/xai_as_closure/study2_delivery.py`. They implement the validated
AnthroKit-Hiring contrast as twelve complete paired assessment cards, with
condition-sensitive request, progress, evidence-examination, and human-authority
language. The migrated HAI agent retains the evidence store, planner, retriever,
evaluator, recommender, renderer, bounded follow-up interaction, logging, private
GitHub backup, theme, Qualtrics cleaning, and session-flattening pipeline. No live
model rewrites the experimental text.

Canonical CHI sources:

```text
docs/research_brief.md                         Current two-study research brief
docs/CHI2027/                                  CHI 2027 manuscript and bibliography
study_CHI/STUDY1_VALIDATION_PROTOCOL.md        Expert-validation procedure
study_CHI/APPLICATION_LOGGING_ARCHITECTURE.md  Qualtrics, app, and event architecture
study_CHI/                                     Locked role, policy, profile, and case set
```

## Environment

The project uses the `dsagent` Conda environment with Python 3.11.
Recreate it from the repository root with:

```bash
conda env create -f environment.yml
conda activate dsagent
```

When shell activation is unavailable but Conda is installed, commands can be
run with `conda run -n dsagent <command>`.

## Run Study 1

Launch the dedicated validation app with:

    streamlit run apps/study1_validation.py

Pilot mode is disabled unless explicitly enabled with
`STUDY1_ALLOW_PILOT=true`. Production must leave it disabled, provide a unique
`STUDY_LINK_SECRET` of at least 32 characters, and pass a signed Qualtrics launch
token. Logs default to the Git-ignored `study_CHI/data/raw/study1/` directory;
set `STUDY1_DATA_ROOT` to protected research storage for deployment.

## Run Study 2

Study 2 has eight active entry points, one permanently locked to each condition.
For example, launch condition 1 with:

    streamlit run apps/study2_01_lowP_lowA_noF.py

The remaining seven entry points are listed in `apps/README.md`. Study 2 uses
the established HAI query parameters: `PROLIFIC_PID` (or legacy `pid`), `cond`,
and an encoded Qualtrics `return` URL. A supplied `cond` must match the entry
point's hard-coded condition. When no participant ID is supplied, the original
manual Prolific-ID gate supports local pilots. JSONL logs default to the
Git-ignored `study_CHI/data/raw/study2/interaction_logs/` directory; set
`STUDY2_DATA_ROOT` to a protected log directory for deployment. When
`GITHUB_REPO` and `GITHUB_TOKEN` are configured, the HAI logger saves the full
session and event stream to that private data repository after each completed
trial.

## Self-Contained Active Source

All active Study 1 and Study 2 implementation code lives under
`src/xai_as_closure/`, with current materials under `study_CHI/`. There is no
submodule, second remote, sibling-checkout import, or external project runtime
dependency; a clean clone is sufficient to set up, test, and run the CHI
applications.

## Research Use

This software is a research instrument using fictional hiring materials. It is designed to study recommendation following, overreliant advancement, and verification uptake; it should not be used to support real hiring, screening, promotion, or employment decisions.

## Data Boundary

Participant-level data, interaction logs, generated outputs, credentials, and
local environment files are excluded from Git. They may remain
in the private local workspace for reproducibility and secondary analysis, but
the public code repository contains only de-identified documentation, schemas,
instruments, source code, and approved aggregate artifacts.

## Test

The source-layout test suite uses the standard library test runner:

    PYTHONPATH=src python3 -m unittest discover -s tests -v
