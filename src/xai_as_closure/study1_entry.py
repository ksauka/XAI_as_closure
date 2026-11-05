"""Check the entry-point release before calling shared Study 1 application code."""
from __future__ import annotations

from importlib import import_module
import streamlit as st
import os

from .study1_guide import render_guide_navigation, render_study1_guide


def run_entry(validation_round: str, expected_release: str) -> None:
    st.set_page_config(page_title='Study 1 expert validation',
                       page_icon=':material/fact_check:', layout='centered',
                       initial_sidebar_state='expanded')
    labels = {'round2_focused_trimmed': 'Version 2 · focused expert assessment · C-05 and C-06 · shortened documents', 'round2_focused': 'Version 2 · focused expert assessment · C-05 and C-06', 'round2': 'Archived six-profile second expert assessment'}
    label = labels.get(validation_round, 'Earlier Study 1 entry point')
    if os.getenv('STUDY1_LOCAL_PREVIEW') == '1':
        st.caption(f'Study 1 · {label} · Build {expected_release}')
    guide_value = st.query_params.get("guide", "")
    if isinstance(guide_value, list):
        guide_value = guide_value[0] if guide_value else ""
    guide_mode = str(guide_value).strip().lower() in {"1", "true", "yes"}
    if guide_mode:
        view_value = st.query_params.get("view", "")
        if isinstance(view_value, list):
            view_value = view_value[0] if view_value else ""
        view = "demo" if str(view_value).strip().lower() == "demo" else "tour"
        render_guide_navigation(view)
        if view == "tour":
            render_study1_guide()
            return
    app = import_module('xai_as_closure.study1_app')
    loaded_release = getattr(app, 'STUDY1_APP_RELEASE', None)
    if loaded_release != expected_release:
        if os.getenv('STUDY1_LOCAL_PREVIEW') == '1':
            st.error('The entry point has updated, but this server still has an older Study 1 application loaded.')
        else:
            st.info('The task is reconnecting. Please refresh this page in a moment.')
        st.stop()
    app.run(
        validation_round="initial" if guide_mode else validation_round,
        artifact_demo=guide_mode,
    )
