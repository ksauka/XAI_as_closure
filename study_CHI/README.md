# CHI 2027 Study Materials

This directory contains the current study materials for the CHI 2027 paper.

## Canonical materials

- `job_description.md`: locked AI Governance Lead role and mandatory certification criterion.
- `recruitment_policy.md`: locked screening policy and two-outcome decision rule.
- `six_candidate_profiles.md`: human-readable six-profile trial set.
- `six_profiles_case_set.json`: structured implementation source for the six trials.

## Application architecture

Study 1 and Study 2 each require a dedicated application:

- The **Study 1 validation app** receives experts from Qualtrics, presents the
  role and policy, randomizes the six profiles, records independent ground-truth
  judgments, and locks those judgments before displaying any AI recommendation.
  A second phase then validates the realism and plausibility of the exact
  recommendation artifacts intended for Study 2.
- The **Study 2 experimental app** receives the assigned between-subjects
  condition from Qualtrics and delivers six randomized unaided-then-aided
  candidate trials under that fixed condition.

Qualtrics remains the consent, eligibility, linkage, questionnaire, and
completion-routing layer. Both applications generate pseudonymous event logs.

The Markdown and JSON materials above supersede unresolved or provisional design
language in `Methodology_CHI2027_SUPERSEDED.docx`. The DOCX is retained only as
design history and must not be used as the implementation or manuscript source of
truth.

The current manuscript source is `../docs/CHI2027/CHI_draft.tex`.
