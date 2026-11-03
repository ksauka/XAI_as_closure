"""Check the entry-point release before calling shared Study 1 application code."""
from __future__ import annotations

from importlib import import_module
import streamlit as st


def run_entry(validation_round: str, expected_release: str) -> None:
    st.set_page_config(page_title='Study 1 expert validation',
                       page_icon=':material/fact_check:', layout='centered',
                       initial_sidebar_state='expanded')
    labels = {'round2_focused': 'Version 2 · focused expert assessment · C-05 and C-06', 'round2': 'Archived six-profile second expert assessment'}
    label = labels.get(validation_round, 'Earlier Study 1 entry point')
    st.caption(f'Study 1 · {label} · Build {expected_release}')
    app = import_module('xai_as_closure.study1_app')
    loaded_release = getattr(app, 'STUDY1_APP_RELEASE', None)
    if loaded_release != expected_release:
        st.error('The entry point has updated, but this server still has an older Study 1 application loaded.')
        st.info('Researcher: restart this deployment from Streamlit Manage app. Refreshing the browser alone will not reload the server code.')
        st.stop()
    app.run(validation_round=validation_round)
