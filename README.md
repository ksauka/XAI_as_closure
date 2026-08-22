# XAI as Closure

Independent research workspace for the redesigned CHI 2027 project on how
provenance-based explainability, anthropomorphic delivery, and cognitive forcing
shape verification, decision revision, and appropriate reliance on agentic AI
advice.

## CHI 2027 Research Design

The project contains two linked studies:

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

## HAI Legacy Implementation

This history-free workspace was created from the complete local HAI project so
useful application, Qualtrics, logging, and analysis components can be migrated
deliberately. HAI materials remain under `docs/HAI/` and `study_HAI/`; the
original HAI application remains under `src/agentic_hiring/` and `apps/`.

The original HAI artifact and its history remain in the separate
`ksauka/Agentic-AI-interogative-agendas` repository. New CHI development
belongs here.

### Original HAI Overview

Research prototype for a controlled agentic hiring-support study on explanation, anthropomorphic delivery, trust, overreliance, and verification in agentic AI decision support. The project implements a Streamlit workflow in which the hiring case remains fixed while provenance cues, conversational style, and Human Intervention Checkpoints (interrogative agendas) vary across conditions.

## Overview

The application evaluates a fictional candidate against internal hiring materials: company context, role requirements, and screening policy. It is designed as an experimental research instrument, not as a real hiring or screening system.

The study uses a 2 x 2 x 2 condition structure:

- Explainability: low or high provenance visibility
- Anthropomorphic cues: low or high
- Human Intervention Checkpoints: absent or present

## Repository Structure

```text
apps/                  Streamlit entry points for the eight study conditions
scripts/               Dataset and knowledge-base preparation utilities
src/agentic_hiring/    Shared retrieval, recommendation, rendering, and logging code
study/                 Study materials, measures, protocol, and local data workspace
tests/                 Automated validation tests
outputs/               Generated analysis outputs and reports
```

## Setup

```bash
python -m pip install -r requirements.txt
cp .env.example .env
```

Add your OpenAI API key to `.env` or your deployment secrets:

```bash
OPENAI_API_KEY=your-api-key
AGENTIC_REQUIRE_LIVE_RAG=true
```

For study deployment, keep `AGENTIC_REQUIRE_LIVE_RAG=true` so sessions cannot continue without the live retrieval and generation backend.

## Prepare the Knowledge Base

```bash
PYTHONPATH=src python scripts/build_internal_knowledge_base.py
```

This indexes the internal company context, role description, and screening policy used by the study assistant. Candidate CVs are handled as session-specific inputs.

## Run an App

Launch one assigned condition, for example:

```bash
python -m streamlit run apps/app_01_lowE_lowA_noIA.py
```

The eight app entry points in `apps/` correspond to the full condition matrix.

## Test

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Research Use

This software is a research instrument using fictional hiring materials. It is designed to study recommendation following, overreliant advancement, and verification uptake; it should not be used to support real hiring, screening, promotion, or employment decisions.

## Data Boundary

Participant-level data, interaction logs, generated outputs, vector stores,
credentials, and local environment files are excluded from Git. They may remain
in the private local workspace for reproducibility and secondary analysis, but
the public code repository contains only de-identified documentation, schemas,
instruments, source code, and approved aggregate artifacts.
