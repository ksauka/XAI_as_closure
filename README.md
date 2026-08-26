# XAI as Closure

Research software for studying how explanation presence, anthropomorphic delivery, and
cognitive forcing affect verification and reliance on AI-assisted candidate
screening.

The repository contains two linked applications:

- **Study 1 — expert validation:** one shared application in which domain
  experts evaluate six candidate profiles without AI assistance.
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
environment.yml        Conda environment definition
requirements.txt       Runtime Python dependencies
```

## Requirements

- Conda or Miniconda
- Python 3.11

## Installation

From the repository root:

```bash
conda env create -f environment.yml
conda activate dsagent
```

To update an existing environment:

```bash
conda env update -n dsagent -f environment.yml --prune
```

## Configuration

Copy the example configuration before running locally:

```bash
cp .env.example .env
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Both studies use `PROLIFIC_PID` (with `pid` as a legacy fallback) and the
encoded Qualtrics `return` URL. Study 2 additionally uses `cond`, which must
match the condition-locked application.

For local or self-hosted deployment, `STUDY1_DATA_ROOT` and `STUDY2_DATA_ROOT`
can point to protected storage. On Streamlit Community Cloud, configure
`GITHUB_REPO` and `GITHUB_TOKEN` separately for every deployed app because its
local filesystem is ephemeral and secrets are not shared between apps. A
production launch checks access to the private data repository before allowing
the study to begin.

Never commit `.env`, `.streamlit/secrets.toml`, participant data, or raw logs.

## Running the applications

Study 1:

```bash
streamlit run apps/study1_validation.py
```

Example Study 2 condition:

```bash
streamlit run apps/study2_01_lowP_lowA_noF.py
```

See `apps/README.md` for all eight Study 2 entry points and condition IDs.

## Data and logging

- Study 1 stores pseudonymously linked validation sessions.
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

## Documentation

- `docs/research_brief.md` — research questions and two-study design
- `study_CHI/STUDY1_VALIDATION_PROTOCOL.md` — expert-validation procedure
- `study_CHI/STUDY2_CONDITIONS.md` — condition definitions and invariants
- `study_CHI/APPLICATION_LOGGING_ARCHITECTURE.md` — linkage, logging, and storage
- `study_CHI/HAI_MIGRATION_MAP.md` — mapping from the former HAI implementation

## Responsible use

This is a research instrument built with fictional hiring materials. It must
not be used to make real employment, screening, promotion, or hiring decisions.
