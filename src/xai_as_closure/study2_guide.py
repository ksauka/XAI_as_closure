"""Non-recording Study 2 tour rendered inside each condition app."""

from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from .conditions import get_study2_condition


_IMAGE = re.compile(r"!\[(?P<alt>[^]]+)]\((?P<path>[^)]+)\)")


def _condition_description(condition_id: str) -> str:
    condition = get_study2_condition(condition_id)
    explanation = (
        "provenance-based explanation"
        if condition.explanation
        else "no explanation"
    )
    delivery = (
        "anthropomorphic delivery"
        if condition.anthropomorphic
        else "procedural delivery"
    )
    forcing = (
        "cognitive forcing"
        if condition.forcing
        else "no cognitive forcing"
    )
    return f"{explanation}; {delivery}; {forcing}"


def render_guide_navigation(active: str) -> None:
    """Render stable tab-like navigation without initialising a study session."""
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
        f'<a class="{tour_class}" href="?guide=true&amp;view=tour">Tour Guide</a>'
        f'<a class="{demo_class}" href="?guide=true&amp;view=demo">Interactive Study Platform</a>'
        "</div>",
        unsafe_allow_html=True,
    )


def render_study2_guide(condition_id: str) -> None:
    """Render the public guide without initialising or saving a study session."""
    root = Path(__file__).resolve().parents[2]
    guide_path = root / "study_CHI" / "STUDY2_STUDY_GUIDE.md"
    markdown = guide_path.read_text(encoding="utf-8")
    if markdown.startswith("# Study Guide"):
        markdown = markdown.removeprefix("# Study Guide").lstrip()

    st.title("Tour Guide")
    st.caption(f"Condition: {_condition_description(condition_id)}")

    cursor = 0
    for match in _IMAGE.finditer(markdown):
        st.markdown(markdown[cursor : match.start()])
        image_path = root / "study_CHI" / match.group("path")
        st.image(
            str(image_path),
            caption=match.group("alt"),
            use_container_width=True,
        )
        cursor = match.end()
    st.markdown(markdown[cursor:])
