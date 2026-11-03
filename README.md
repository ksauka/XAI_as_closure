# XAI as Closure

Research software for studying how explanation presence, anthropomorphic delivery, and
cognitive forcing affect verification and reliance on AI-assisted candidate
screening.

The repository contains two linked applications:

- **Study 1 — expert validation:** one shared application in which domain
  experts assess C-05 and C-06 without AI assistance in the current focused version. Earlier six-profile rounds are archived separately.
- **Study 2 — AI-assisted screening:** eight condition-locked applications in
  an explanation × anthropomorphism × cognitive-forcing design. Each participant
  evaluates the same six profiles in randomized order.

All profiles, recommendations, and participant-facing response cards are fixed
research stimuli. The Study 2 agent uses a bounded evidence-store → plan →
retrieve → evaluate → recommend → render workflow and does not use live model
generation to rewrite experimental content.

## Repository structure

```text
apps/                  Streamlit entry points for Study 1 and Study 2
src/xai_as_closure/    Application, agent, condition, logging, and analysis code
study_CHI/             Job, policy, candidate, protocol, and condition materials
docs/                  Research brief, manuscript, and bibliography
tests/                 Unit and regression tests
requirements.txt       Runtime Python dependencies
```

## Requirements

- Python 3.11
- Runtime dependencies in `requirements.txt`; test tools in `requirements-dev.txt`

## Installation

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

For tests and analysis checks in the same environment:

```bash
python -m pip install -r requirements-dev.txt
```

## Configuration

Copy the example configuration before running locally:

```bash
cp .env.example .env
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Prolific routes use `PROLIFIC_PID` (with `pid` as a legacy fallback) and the
encoded Qualtrics `return` URL. Study 1 version 2 also accepts a researcher-issued
`participant_code` for independently recruited experts, including manual entry
on its welcome page. These codes use a separate linkage namespace. Study 2 additionally uses `cond`, which must
match the condition-locked application.

For local or self-hosted deployment, `STUDY1_DATA_ROOT` and `STUDY2_DATA_ROOT`
can point to protected storage. On Streamlit Community Cloud, configure
`GITHUB_REPO` and `GITHUB_TOKEN` separately for every deployed app because its
local filesystem is ephemeral and secrets are not shared between apps. A
Study 1 launch checks for an existing checkpoint before starting, saves quietly during the task and waits for a confirmed final save at completion. Study 2 retains its private-storage launch check.

Never commit `.env`, `.streamlit/secrets.toml`, participant data, or raw logs.

## Running the applications

Study 1, revised-material expert assessment (version 2):

```bash
streamlit run apps/study1_validation_v2.py
```

Deploy this entry point as a separate Streamlit app. The previous
`apps/study1_validation.py` entry point is retained for the earlier instrument.
The unpublished candidate uses shared v8 trimmed reference documents, instrument v9 and separate `round2_focused_trimmed` records. It presents two profiles, with Q7 and optional Q8 as the final review. Study 2 still uses all six profiles. Historical v7/v6 materials and records remain separate. See [the focused launch guide](study_CHI/STUDY1_FOCUSED_LAUNCH.md) and [local checks](study_CHI/STUDY1_TRIM_CHECKS.md). Develop locally and deploy only from a deliberately promoted `live` branch outside recruitment; current cloud settings have not yet been switched from `main`.

For an isolated local rehearsal with synthetic records and no remote writes:

```bash
python tools/local_study1_round2.py
```

The default preview address is http://localhost:8509/.

Example Study 2 condition:

```bash
streamlit run apps/study2_01_lowP_lowA_noF.py
```

See `apps/README.md` for all eight Study 2 entry points and condition IDs.

## Data and logging

- Study 1 stores linked validation sessions. Round-2 private checkpoints
  retain the Prolific platform identifier for the survey merge; event logs use
  the linkage hash. Keep these records in restricted research storage.
- Study 2 writes one local JSONL event stream per session and can mirror the
  complete session to a private GitHub repository after each completed trial.
- Study 2 logs retain the Prolific ID required by the existing Qualtrics merge
  pipeline and must therefore remain in restricted research storage.
- Raw data directories and credentials are excluded from version control.

The extraction utilities in `src/xai_as_closure/session_flatten.py` produce
participant-, trial-, and event-level records for analysis.

## Testing

Run the complete test suite from the repository root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Run static checks with:

```bash
python -m ruff check src tests apps
python -m ruff format --check src tests apps
```

Before any Study 2 pilot or deployment, run the frozen-instrument audit:

```bash
PYTHONPATH=src python -m xai_as_closure.release_audit
```

The audit fails if a frozen material, recommendation, condition mapping,
explanation boundary, delivery register, or version identifier has drifted.

## Documentation

- `docs/research_brief.md` — research questions and two-study design
- `study_CHI/STUDY1_VALIDATION_PROTOCOL.md` — expert-validation procedure
- `study_CHI/STUDY2_CONDITIONS.md` — condition definitions and invariants
- `study_CHI/STUDY2_ANALYSIS_PLAN.md` — confirmatory outcomes, models, and exclusions
- `study_CHI/STUDY2_DEPLOYMENT_CHECKLIST.md` — eight-condition pilot and launch gate
- `study_CHI/STUDY2_MATERIAL_FREEZE.json` — executable material/version freeze
- `study_CHI/APPLICATION_LOGGING_ARCHITECTURE.md` — linkage, logging, and storage
- `study_CHI/HAI_MIGRATION_MAP.md` — mapping from the former HAI implementation

## Responsible use

This is a research instrument built with fictional hiring materials. It must
not be used to make real employment, screening, promotion, or hiring decisions.


## Current Study 2 analysis

The [v2 analysis plan](study_CHI/STUDY2_ANALYSIS_PLAN.md) specifies diagnostic reliance, H1/H3 confirmatory tests and H2 estimation. [Analysis tools](analysis/study2/README.md) reproduce precision planning and check operational inputs. [Operational specifications](study_CHI/STUDY2_OPERATIONAL_SPEC.json) keep unavailable final survey and pilot values explicit rather than declaring recruitment readiness.
