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

Both studies use dedicated applications. Qualtrics manages consent, eligibility,
participant linkage, questionnaire measures, and completion routing. The Study 1
validation app presents and randomizes the expert-validation materials, locks
independent judgments, and records profile-level evidence and timing. The Study 2
experimental app delivers the assigned condition across six repeated trials.
Survey and application records are joined using a pseudonymous study linkage
identifier rather than a directly identifying recruitment ID.

Canonical CHI sources:

```text
docs/research_brief.md                         Current two-study research brief
docs/CHI2027/PROJECT_HANDOFF.md                Cross-machine status and remaining-work handoff
docs/CHI2027/                                  CHI 2027 manuscript and bibliography
study_CHI/STUDY1_VALIDATION_PROTOCOL.md        Expert-validation procedure
study_CHI/APPLICATION_LOGGING_ARCHITECTURE.md  Qualtrics, app, and event architecture
study_CHI/                                     Locked role, policy, profile, and case set
```

## Environment

The project uses the `esd_platform` Conda environment with Python 3.12.
Recreate it from the repository root with:

```bash
conda env create -f environment.yml
conda activate esd_platform
```

For the existing local environment, run project commands with
`/home/kudzai/miniconda3/envs/esd_platform/bin/python` when Conda activation is
not available in the shell.

## Run Study 1

Launch the dedicated validation app with:

    streamlit run apps/study1_validation.py

Local runs permit pilot mode. Production must set `STUDY1_ALLOW_PILOT=false`, provide `STUDY_LINK_SECRET`, and pass a signed Qualtrics launch token. Logs default to the Git-ignored `study_CHI/data/raw/study1/` directory; set `STUDY1_DATA_ROOT` to protected research storage for deployment.

## Copied HAI Source Snapshot

This repository was initialized from a complete local copy of the earlier HAI project so useful implementation and study-design elements could be inspected and adopted without depending on another repository. The copied snapshot remains under `docs/HAI/`, `study_HAI/`, `src/agentic_hiring/`, the eight legacy condition apps, and the inherited analysis files.

There is no Git submodule, second remote, sibling-checkout import, or runtime link to the old HAI repository. A clean clone of `XAI_as_closure` must contain everything needed for CHI development.

When adopting an HAI component:

1. Copy the relevant code, material, or pattern into a CHI-owned location such as `src/xai_as_closure/` or `study_CHI/`.
2. Adapt it to the current CHI protocol and terminology.
3. Add CHI-specific tests and documentation.
4. Keep the copied legacy source only as provenance; do not make active CHI code import from it.

The copied HAI snapshot is inactive and is not the CHI source of truth. Its historical documentation belongs under `docs/HAI/` and `study_HAI/`, not in the active CHI setup instructions.

## Research Use

This software is a research instrument using fictional hiring materials. It is designed to study recommendation following, overreliant advancement, and verification uptake; it should not be used to support real hiring, screening, promotion, or employment decisions.

## Data Boundary

Participant-level data, interaction logs, generated outputs, vector stores,
credentials, and local environment files are excluded from Git. They may remain
in the private local workspace for reproducibility and secondary analysis, but
the public code repository contains only de-identified documentation, schemas,
instruments, source code, and approved aggregate artifacts.
