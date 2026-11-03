"""Local researcher workspace for reviewing C-05 and C-06, not recruitment."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from xai_as_closure.cases import CASE_SET_PATH, POLICY_PATH, ROLE_PATH, CaseRepository


def profile_markdown(profile: dict) -> str:
    lines = [f"# Candidate {profile['reference']}"]
    for section in profile["candidate_cv"]["sections"]:
        lines.extend([f"## {section['heading']}", section["text"]])
    return "\n\n".join(lines) + "\n"


def render_materials_review() -> None:
    st.title("C-05 and C-06: profile review")
    st.caption("Shared materials for Study 1 and Study 2. Current profiles are on the left; editable working drafts are on the right.")
    cases = CaseRepository()
    source = json.loads(CASE_SET_PATH.read_text(encoding="utf-8"))
    source_hash = hashlib.sha256(CASE_SET_PATH.read_bytes()).hexdigest()
    profiles = {p["reference"]: p for p in source["profiles"]}
    draft_root = CASE_SET_PATH.parent / "materials_review" / "drafts"
    st.write(f"**Role:** {cases.role}, {cases.company} · **Screening:** {cases.timeline.screening_window_label}")
    st.info("The completed second expert assessment used the installed v6 materials. The left pane shows that assessed version; the right pane shows the shared working draft for the next Study 1 assessment and Study 2. Saving here does not replace the installed version.")
    tabs = st.tabs(["C-05 · certification and membership currency", "C-06 · credential identity", "Job description", "Recruitment policy"])
    for tab, path, label in ((tabs[2], ROLE_PATH, "job_description"),
                             (tabs[3], POLICY_PATH, "recruitment_policy")):
        with tab:
            review_document = draft_root / path.name
            document_path = review_document if review_document.exists() else path
            if document_path == review_document:
                st.caption("Shared working revision for the next Study 1 assessment and Study 2.")
            document = document_path.read_text(encoding="utf-8")
            st.markdown(document)
            st.download_button("Download full document", document, file_name=f"{label}.md", key=f"download_{label}")
    for reference, tab in zip(("C-05", "C-06"), tabs[:2]):
        with tab:
            profile = profiles[reference]
            current = profile_markdown(profile)
            target = draft_root / f"{reference}.md"
            note_path = draft_root / f"{reference}.json"
            saved = json.loads(note_path.read_text(encoding="utf-8")) if note_path.exists() else {}
            if saved.get("source_sha256") and saved["source_sha256"] != source_hash:
                st.warning("This saved draft started from an earlier case file. Compare it with the current profile before continuing.")
            st.write(f"**Current intended decision:** {profile['ground_truth']} · **Current AI advice:** {profile['fixed_assessment']['recommendation']}")
            if reference == "C-05":
                st.write("Assessed v6: the AIGP certification ended on 31 May 2026; IAPP membership is recorded as current through 31 December 2026. The author-requested working draft changes membership to end on 31 May 2026 as well. Both would then be expired during screening on 27–30 August 2026. This further revision has not been assessed.")
            else:
                st.write("Assessed v6: the bare AIGP entry and current IAPP membership have matching terms. JD 4.2.1 gives the certification-identity rule. Preserve the bare AIGP entry when reviewing this profile; it is resolved by reading the candidate file against that rule.")
            left, right = st.columns(2, gap="large")
            with left:
                st.subheader("Current profile")
                with st.container(height=670, border=True):
                    st.markdown(current)
                st.download_button("Download current profile", current, file_name=f"{reference}_current.md", key=f"download_current_{reference}")
            with right:
                st.subheader("Working draft")
                draft = st.text_area("Edit the profile", value=target.read_text(encoding="utf-8") if target.exists() else current,
                                     height=670, key=f"profile_draft_{reference}", label_visibility="collapsed")
                rationale = st.text_area("Why are we changing it?", value=saved.get("rationale", ""), key=f"profile_rationale_{reference}")
                if st.button("Save working draft", key=f"save_{reference}", type="primary"):
                    if not draft.strip():
                        st.error("The draft is empty. Enter the profile before saving.")
                    else:
                        draft_root.mkdir(parents=True, exist_ok=True)
                        target.write_text(draft, encoding="utf-8")
                        note_path.write_text(json.dumps({
                            "status": "review_draft_not_study_material",
                            "applies_to": ["study1", "study2"],
                            "reference": reference,
                            "source_case_set": cases.case_set_id,
                            "source_sha256": source_hash,
                            "saved_at_utc": datetime.now(timezone.utc).isoformat(),
                            "rationale": rationale,
                        }, indent=2) + "\n", encoding="utf-8")
                        st.success(f"{reference} working draft saved in the repository.")
                st.download_button("Download working draft", draft, file_name=f"{reference}_draft.md", key=f"download_draft_{reference}")
                st.caption("One shared draft is saved for both studies in study_CHI/materials_review/drafts. Study 2 AI wording and citations must be checked against the same profiles before release.")
