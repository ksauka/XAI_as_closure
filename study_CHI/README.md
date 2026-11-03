# CHI 2027 Study Materials

This directory contains the current study materials for the CHI 2027 paper.

## Canonical materials

- `job_description.md`: locked AI Governance Lead role, recruitment timeline, and current certification-and-membership criteria.
- `recruitment_policy.md`: locked screening policy and two-outcome decision rule.
- `six_candidate_profiles.md`: human-readable six-profile trial set.
- `six_profiles_case_set.json`: structured `v6` implementation source for the six trials.
- `STUDY1_VALIDATION_PROTOCOL.md`: expert stimulus-validation procedure and initial-batch history.
- `STUDY1_ROUND2_LAUNCH.md`: setup and launch checks for the standalone version-2 app.
- `STUDY1_ROUND2_MATERIALS.json`: hashes and instrument version for the pending revised-material assessment.
- `STUDY2_CONDITIONS.md`: active 2 x 2 x 2 condition identifiers and invariants.
- `STUDY2_ANALYSIS_PLAN.md`: frozen confirmatory estimands, outcome definitions, models, exclusions, and reporting rules.
- `STUDY2_DEPLOYMENT_CHECKLIST.md`: pre-launch technical, privacy, linkage, pilot, and rollback checks for all eight applications.
- `STUDY2_MATERIAL_FREEZE.json`: machine-checkable versions and hashes for the locked Study 2 stimuli and delivery implementation.
- `APPLICATION_LOGGING_ARCHITECTURE.md`: Qualtrics linkage, app flow, and event schema.
- `HAI_MIGRATION_MAP.md`: direct mapping from the working HAI implementation to the active Study 2 modules.
- `HAI_STREAMLIT_COMPARISON.md`: screen-by-screen disposition of the historical HAI interface.
- `../src/xai_as_closure/study2_delivery.py`: frozen LowA/HighA delivery specification.

## Application architecture

The implemented entry points are `apps/study1_validation.py` and the eight
condition-locked `apps/study2_*.py` applications listed in `apps/README.md`.
Their domain, agent, state, linkage, and logging modules are under
`src/xai_as_closure/`.

Before a release, verify the frozen materials and all eight condition mappings:

```bash
PYTHONPATH=src python -m xai_as_closure.release_audit
```

The programme uses one Study 1 application and eight Study 2 applications:

- The **Study 1 validation app** is one shared application for multiple experts.
  It presents the role and policy, randomizes all six profiles, and records a
  locked independent judgment, direct hard-criterion judgment, confidence,
  and short decisive-evidence response for every candidate. A short final
  materials review then assesses the clarity, realism, discriminability,
  sufficiency, and disputed-profile status of the complete stimulus set. The
  instrument targets a completion time of no more than about 10 minutes. It never
  displays an AI recommendation or implements an experimental condition.
- Each **Study 2 experimental app** is permanently locked to one
  between-subjects condition and delivers six randomized unaided-then-aided
  candidate trials. A Qualtrics `cond` parameter must match that app's condition.
  Its bounded agent executes a plan, retrieves the configured evidence, evaluates
  the case, and renders the frozen recommendation under the assigned explanation
  and delivery conditions. Explanation-absent cells show only the verdict;
  explanation-present cells show the full rationale and inspectable evidence.
  The complete LowA/HighA cards are deterministic,
  preserve the validated AnthroKit-Hiring token contrast, and never call an LLM
  to rewrite participant-facing stimuli.
  In explanation-present conditions, citations open the relevant complete
  source document. In explanation-absent conditions, verification requires
  independent use of the complete source documents.
  Cognitive forcing, when assigned, occurs after the unaided decision and gates
  the still-hidden recommendation until the participant re-enters the mandatory
  certification and professional-membership requirements from the complete job
  description. A neutral
  evidence-recall prompt follows every trial.

For Study 1, Qualtrics is limited to consent, pseudonymous linkage, completion,
closing information, and debrief. Study 2 retains the HAI Prolific/Qualtrics
linkage and uses Qualtrics for condition assignment and questionnaire measures.
Study 2's private event log contains the Prolific ID needed by the retained
cleaning and merge pipeline.

The Markdown and JSON materials above supersede unresolved or provisional design
language in `Methodology_CHI2027_SUPERSEDED.docx`. The DOCX is retained only as
design history and must not be used as the implementation or manuscript source of
truth.

The duplicate material files formerly kept under
`new experiment material 23_08_2026/` were removed to prevent drift. That
directory retains the maintained `implementation_plan.md` and a pointer back to
the canonical participant-facing documents in this directory.

The current manuscript source is `../docs/CHI2027/CHI_draft.tex`.


## Current FAccT analysis specification (22 October 2026)

The active plan is [STUDY2_ANALYSIS_PLAN.md](STUDY2_ANALYSIS_PLAN.md): H1/H3 confirmatory with Holm adjustment, H2 interaction estimation, diagnostic disagreements only for reliance, and profile fixed effects. The sample ceiling is 400 analysable. Earlier H4–H6/N=312 passages are superseded. [STUDY2_OPERATIONAL_SPEC.json](STUDY2_OPERATIONAL_SPEC.json) records scoring, coding and timing status; [STUDY2_EVIDENCE_CODING.md](STUDY2_EVIDENCE_CODING.md) defines decisive evidence. Reproducible simulation and readiness tools are in [analysis/study2](../analysis/study2/README.md). Unset pilot and instrument fields are not evidence that launch gates have passed.
