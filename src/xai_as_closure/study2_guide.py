"""Non-recording Study 2 research artifact rendered inside each condition app."""

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


def render_study2_guide(condition_id: str) -> None:
    """Render the public guide without initialising or saving a study session."""
    root = Path(__file__).resolve().parents[2]
    guide_path = root / "study_CHI" / "STUDY2_STUDY_GUIDE.md"
    markdown = guide_path.read_text(encoding="utf-8")
    if markdown.startswith("# Study Guide"):
        markdown = markdown.removeprefix("# Study Guide").lstrip()

    st.title("Study Guide")
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
