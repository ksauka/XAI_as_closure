"""Non-recording Study 1 tour with the complete material set."""

from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from .cases import CaseRepository
from .document_renderer import render_cv_document, render_reference_document


_IMAGE = re.compile(r"!\[(?P<alt>[^]]+)]\((?P<path>[^)]+)\)")


def render_guide_navigation(active: str) -> None:
    """Render stable tab-like navigation without creating a study session."""
    tour_class = "artifact-tab artifact-tab--active" if active == "tour" else "artifact-tab"
    demo_class = "artifact-tab artifact-tab--active" if active == "demo" else "artifact-tab"
    st.markdown(
        """
        <style>
        .artifact-tabs { display:flex; gap:.4rem; margin:.2rem 0 1rem; border-bottom:1px solid #d9dde5; }
        .artifact-tab { display:inline-block; padding:.65rem 1rem; color:#344054 !important;
          text-decoration:none !important; border:1px solid transparent; border-bottom:0;
          border-radius:.45rem .45rem 0 0; }
        .artifact-tab:hover { background:#f2f4f7; }
        .artifact-tab--active { background:#fff; border-color:#d9dde5; font-weight:700; margin-bottom:-1px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="artifact-tabs">'
        f'<a class="{tour_class}" href="?guide=true&amp;view=tour" target="_self">Tour Guide</a>'
        f'<a class="{demo_class}" href="?guide=true&amp;view=demo" target="_self">Interactive Study Platform</a>'
        "</div>",
        unsafe_allow_html=True,
    )


def _render_markdown_with_images(markdown: str, root: Path) -> None:
    cursor = 0
    for match in _IMAGE.finditer(markdown):
        st.markdown(markdown[cursor : match.start()])
        st.image(
            str(root / "study_CHI" / match.group("path")),
            caption=match.group("alt"),
            use_container_width=True,
        )
        cursor = match.end()
    st.markdown(markdown[cursor:])


def render_study1_guide() -> None:
    """Render the public guide without initialising or saving a study session."""
    root = Path(__file__).resolve().parents[2]
    guide_path = root / "study_CHI" / "STUDY1_STUDY_GUIDE.md"
    markdown = guide_path.read_text(encoding="utf-8")
    if markdown.startswith("# Study 1 Guide"):
        markdown = markdown.removeprefix("# Study 1 Guide").lstrip()

    st.title("Tour Guide")
    _render_markdown_with_images(markdown, root)

    cases = CaseRepository()
    st.header("Governing documents")
    role_tab, policy_tab = st.tabs(["Job description", "Recruitment policy"])
    with role_tab:
        render_reference_document(
            st,
            cases.role_path,
            document_type="Job description",
            role=cases.role,
            company=cases.company,
            timeline=cases.timeline,
        )
    with policy_tab:
        render_reference_document(
            st,
            cases.policy_path,
            document_type="Recruitment policy",
            role=cases.role,
            company=cases.company,
            timeline=cases.timeline,
        )

    st.header("Candidate profiles")
    profile_tabs = st.tabs(list(cases.references))
    for reference, tab in zip(cases.references, profile_tabs):
        with tab:
            render_cv_document(
                st,
                cases.participant_case(reference),
                role=cases.role,
                company=cases.company,
                timeline=cases.timeline,
            )

