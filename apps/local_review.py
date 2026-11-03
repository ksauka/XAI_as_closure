"""Researcher-only local review hub; never a participant recruitment entry point."""

import importlib.util
import json
import os
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
st.set_page_config(page_title="FAccT study rehearsal", layout="wide")
if os.getenv("STUDY2_LOCAL_PREVIEW") != "1":
    st.error("This researcher preview must be started locally in preview mode.")
    st.stop()

from xai_as_closure.materials_review import render_materials_review


def playground():
    st.title("FAccT study rehearsal")
    st.info(
        "Local review only. The task apps use synthetic identifiers and isolated logs. Remote saving is disabled. This hub is not a Qualtrics survey or a recruitment link."
    )
    st.page_link(materials_page, label="Review and improve C-05 and C-06")
    spec = json.loads((ROOT / "study_CHI/STUDY2_OPERATIONAL_SPEC.json").read_text())
    st.header("Study 1: second expert assessment")
    st.link_button("Open Study 1 version 2", "http://localhost:8509/", use_container_width=True)
    st.header("Study 2: open a condition")
    for index in range(8):
        p, a, f = index // 4, (index // 2) % 2, index % 2
        label = f"{index + 1}. Explanation {'present' if p else 'absent'} · {'Anthropomorphic' if a else 'Procedural'} · Forcing {'present' if f else 'absent'}"
        st.link_button(label, f"http://localhost:{8501 + index}/?embed=true", use_container_width=True)
    st.header("Questionnaire preview")
    forcing = st.checkbox("Preview a participant assigned to cognitive forcing", value=True)
    st.caption(
        "Item wording and 1–7 agreement endpoints are confirmed. Pre-task response options, final survey mapping and branching still need implementation checks. No questionnaire responses are saved by this review page."
    )
    for name in spec["questionnaire"]["active_constructs"]:
        scale = spec["questionnaire"]["scales"][name]
        if name == "PCE" and not forcing:
            continue
        with st.expander(name + " · " + scale["timing"]):
            for key, text in scale["item_text"].items():
                if scale.get("response_min") == 1:
                    st.radio(text, list(range(1, 8)), index=None, horizontal=True, key=key)
                    st.caption("1 = Strongly disagree; 7 = Strongly agree")
                else:
                    st.write(text)
                    st.caption("Response options pending")
    st.header("What remains before recruitment")
    module_spec = importlib.util.spec_from_file_location("study_readiness", ROOT / "analysis/study2/readiness.py")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    for issue in module.unresolved(spec):
        st.write("• " + issue)
    st.caption(
        "Passing the software tests does not establish ethics approval, public deployment readiness or adequate statistical precision."
    )


materials_page = st.Page(render_materials_review, title="C-05 and C-06 profiles", url_path="case-review")
st.navigation([
    st.Page(playground, title="Study 2 playground", default=True),
    materials_page,
], position="top").run()
