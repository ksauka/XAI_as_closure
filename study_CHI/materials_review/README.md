# Shared materials for Study 1 and Study 2

Current release: shared v7, 3 November 2026. C-05 certification and IAPP membership both end on 31 May 2026. All other candidate CVs, intended decisions and AI verdicts are unchanged. Both study apps load the same canonical six-profile source. The focused expert task selects C-05/C-06 only; Study 2 keeps all six. See `../STUDY1_FOCUSED_LAUNCH.md`.

The previous v6 material set and its six-profile assessment are archived separately. This v7 update does not alter the completed records or establish successful validation. The review page shows installed v7 on the left and further editable drafts on the right. Drafts saved there do not change the installed source automatically.

## Earlier v6 release record


3 November 2026

Both study applications load `CaseRepository()` from the same module. Their canonical candidate source is `study_CHI/six_profiles_case_set.json`; both also use `study_CHI/job_description.md` and `study_CHI/recruitment_policy.md`.

The C-05 and C-06 working profiles in `study_CHI/materials_review/drafts` are a single shared revision stream for the next Study 1 expert assessment and Study 2. The job-description review draft belongs to that same material set. Do not create study-specific copies of these candidate profiles or governing documents.

The approved rule and citation revision is now installed in the shared canonical sources as `ai_governance_lead_six_profiles_v6`, with delivery specification v8 and material-freeze record v3. It adds JD 4.2.1 for certification identity and retains Policy 2.3 for whole-file assessment and currency. All six candidate CVs, intended decisions and AI verdicts are unchanged. Each advance uses the same 12 source IDs; each reject uses the same 14, including JD 3.5 and JD 7.2. Further profile edits saved through the review page remain drafts until explicitly installed and versioned.

Both studies use this shared material version. The repeat Study 1 must validate it before Study 2 recruitment; validation is recorded as pending, not completed. The prior v5 files and freeze record are preserved under `study_CHI/materials_review/archive/pre_identity_revision_2026-11-03`.

Preserve the original Study 1 material versions and observations. A shared revised set does not retrospectively change which materials the completed batches assessed. Record the new validation round and material hashes separately.

Source check: `study1_app.py` and `study2_app.py` each instantiate the same `CaseRepository`; each imports `ROLE_PATH` and `POLICY_PATH` from `cases.py`. The review page reads that same canonical candidate JSON before applying author edits to the shared review drafts.
