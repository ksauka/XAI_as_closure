"""Streamlit application for the two-phase Study 1 expert validation."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import streamlit as st

from .cases import POLICY_PATH, ROLE_PATH, CaseRepository
from .storage import SessionStore, pseudonymize_linkage, stable_session_id
from .study1 import Study1Session, WorkflowError
from .tokens import (
    TokenError,
    create_completion_token,
    safe_qualtrics_return_url,
    verify_token,
)


def _secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return str(value or os.getenv(name, default))


def _query(name: str) -> str:
    try:
        value = st.query_params.get(name, "")
    except Exception:
        return ""
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value)


def _apply_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #fbfcfd; color: #20252b; }
        .block-container {
            max-width: 920px;
            padding: 1.5rem 2rem 3rem;
        }
        h1 { font-size: 1.85rem; letter-spacing: 0; }
        h2 { font-size: 1.28rem; letter-spacing: 0; margin-top: 1.25rem; }
        h3 { font-size: 1.05rem; letter-spacing: 0; }
        [data-testid="stSidebar"] {
            background: #f4f6f8;
            border-right: 1px solid #dce1e6;
        }
        [data-testid="stForm"] {
            background: #ffffff;
            border: 1px solid #dce1e6;
            border-radius: 6px;
            padding: 1.25rem;
        }
        [data-testid="stAlert"] { border-radius: 6px; }
        [data-testid="stButton"] button,
        [data-testid="stFormSubmitButton"] button {
            border-radius: 5px;
        }
        .study-kicker {
            color: #53606d;
            font-size: .85rem;
            font-weight: 650;
            margin-bottom: .2rem;
        }
        .recommendation-panel {
            background: #ffffff;
            border: 1px solid #cbd3dc;
            border-left: 5px solid #176b87;
            border-radius: 6px;
            padding: 1rem 1.15rem;
            margin: 1rem 0;
        }
        .recommendation-panel p { margin: .35rem 0; line-height: 1.55; }
        .source-passage {
            background: #f7f9fb;
            border: 1px solid #dce1e6;
            padding: .9rem 1rem;
            margin: .5rem 0 1rem;
        }
        .completion-panel {
            background: #f2f8f4;
            border: 1px solid #9cc7a8;
            border-radius: 6px;
            padding: 1rem 1.15rem;
        }
        footer, #MainMenu { visibility: hidden; }
        @media (max-width: 640px) {
            .block-container { padding: 1rem .85rem 2rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _elapsed() -> float:
    return round(time.perf_counter() - st.session_state.get("_study1_started", time.perf_counter()), 3)


def _position(session: Study1Session, reference: str) -> int:
    return session.state["profile_order"].index(reference) + 1


def _log(
    event_type: str,
    *,
    reference: str | None = None,
    component: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    session: Study1Session = st.session_state["_study1_session"]
    store: SessionStore = st.session_state["_study1_store"]
    store.append_event(
        session.state,
        event_type,
        phase=session.phase,
        trial_reference=reference,
        trial_position=_position(session, reference) if reference else None,
        component=component,
        elapsed_seconds=_elapsed(),
        payload=payload,
    )


def _load_launch() -> tuple[str, str, str, bool]:
    secret = _secret("STUDY_LINK_SECRET")
    token = _query("token")
    if token:
        if not secret:
            raise TokenError("The study server is missing its launch-token secret.")
        payload = verify_token(token, secret)
        phase = str(payload.get("phase", "both"))
        if phase not in {"both", "phase_a"}:
            raise TokenError("This token is not permitted to start Study 1.")
        return (
            str(payload["linkage_id"]),
            str(payload.get("return_route", "")),
            secret,
            False,
        )
    allow_pilot = _secret("STUDY1_ALLOW_PILOT", "true").lower() in {"1", "true", "yes"}
    if not allow_pilot:
        raise TokenError("A valid Qualtrics launch token is required.")
    pilot_id = st.session_state.setdefault("_study1_pilot_id", os.urandom(16).hex())
    return pilot_id, _query("return"), secret or "local-pilot-secret", True


def _initialize() -> None:
    if "_study1_session" in st.session_state:
        return
    linkage_id, return_route, secret, pilot = _load_launch()
    linkage_hash = pseudonymize_linkage(linkage_id, secret)
    session_id = stable_session_id(linkage_hash)
    data_root = _secret("STUDY1_DATA_ROOT")
    store = SessionStore(Path(data_root) if data_root else None) if data_root else SessionStore()
    cases = CaseRepository()
    stored = store.load(session_id)
    if stored:
        session = Study1Session.restore(stored, cases)
        event = "session_resumed"
    else:
        session = Study1Session.create(
            session_id=session_id,
            linkage_hash=linkage_hash,
            seed=linkage_hash,
            cases=cases,
        )
        store.save(session.state)
        event = "session_created"
    st.session_state["_study1_started"] = time.perf_counter()
    st.session_state["_study1_session"] = session
    st.session_state["_study1_store"] = store
    st.session_state["_study1_secret"] = secret
    st.session_state["_study1_return"] = return_route
    st.session_state["_study1_pilot"] = pilot
    _log(
        event,
        component="launch",
        payload={
            "launch_token_validated": not pilot,
            "pilot_mode": pilot,
            "case_set_id": cases.case_set_id,
        },
    )


def _header(session: Study1Session) -> None:
    st.markdown('<div class="study-kicker">STUDY 1 · EXPERT VALIDATION</div>', unsafe_allow_html=True)
    st.title("Candidate screening task")
    if session.phase == "phase_a":
        count = len(session.state["phase_a_responses"])
        st.progress(count / 6, text=f"Independent judgments: {count} of 6 submitted")
    elif session.phase == "phase_b":
        count = len(session.state["phase_b_responses"])
        st.progress(count / 6, text=f"Recommendation artifacts: {count} of 6 reviewed")
    else:
        st.progress(1.0, text="Task complete")


def _document_navigation(session: Study1Session) -> bool:
    view = st.session_state.get("_study1_document")
    if view:
        title, path = (
            ("AI Governance Lead job description", ROLE_PATH)
            if view == "role"
            else ("Recruitment policy", POLICY_PATH)
        )
        st.subheader(title)
        st.markdown(path.read_text(encoding="utf-8"))
        if st.button("Back to candidate", type="primary", key=f"back_{view}"):
            _log("document_closed", component=view, payload={"document": view})
            st.session_state["_study1_document"] = None
            st.rerun()
        return True

    with st.sidebar:
        st.subheader("Reference documents")
        st.caption("These documents remain available throughout the task.")
        if st.button("Open job description", use_container_width=True):
            st.session_state["_study1_document"] = "role"
            _log("document_opened", component="role", payload={"document": "role"})
            st.rerun()
        if st.button("Open recruitment policy", use_container_width=True):
            st.session_state["_study1_document"] = "policy"
            _log("document_opened", component="policy", payload={"document": "policy"})
            st.rerun()
        st.divider()
        st.caption("Fictional materials for research. Do not use for real hiring decisions.")
        if st.session_state.get("_study1_pilot"):
            st.warning("Pilot mode")
    return False


def _render_cv(reference: str) -> None:
    session: Study1Session = st.session_state["_study1_session"]
    case = session.cases.phase_a_case(reference) if session.phase == "phase_a" else session.cases.phase_a_case(reference)
    st.subheader(f"Candidate {case.reference}")
    for section in case.sections:
        st.markdown(f"#### {section.heading}")
        st.write(section.text)


def _mark_presented(phase: str, reference: str, payload: dict[str, Any]) -> None:
    key = f"_presented_{phase}_{reference}"
    if not st.session_state.get(key):
        _log("profile_presented" if phase == "phase_a" else "artifact_presented", reference=reference, component="candidate", payload=payload)
        st.session_state[key] = True


def _phase_a(session: Study1Session) -> None:
    reference = session.current_reference()
    if reference is None:
        st.rerun()
    assert reference is not None
    _mark_presented(
        "phase_a",
        reference,
        {"visible_cv_section_count": len(session.cases.phase_a_case(reference).sections)},
    )
    st.info(
        "Judge the candidate independently against the job description and recruitment policy. "
        "A submitted judgment cannot be changed."
    )
    _render_cv(reference)

    with st.form(f"phase_a_{reference}", clear_on_submit=False):
        decision = st.radio(
            "Screening decision",
            ["Advance to Hire", "Reject"],
            index=None,
            key=f"phase_a_decision_{reference}",
        )
        certification = st.radio(
            "Which accepted mandatory certification is shown in the profile?",
            [
                "IAPP AIGP",
                "ISO/IEC 42001 Lead Implementer",
                "Neither accepted certification",
            ],
            index=None,
            key=f"phase_a_certification_{reference}",
        )
        confidence = st.slider(
            "Confidence in this decision", 0, 100, 50, format="%d%%",
            key=f"phase_a_confidence_{reference}",
        )
        decisive_evidence = st.text_area(
            "What evidence was decisive for your judgment?",
            max_chars=1500,
            key=f"phase_a_evidence_{reference}",
        )
        ambiguity = st.text_area(
            "Describe any ambiguity, missing information, or realism concern. Enter “None” if there is none.",
            max_chars=1500,
            key=f"phase_a_ambiguity_{reference}",
        )
        suitability = st.selectbox(
            "Optional: overall suitability apart from the mandatory criterion",
            [
                "Not assessed",
                "Very unsuitable",
                "Unsuitable",
                "Neither unsuitable nor suitable",
                "Suitable",
                "Very suitable",
            ],
            key=f"phase_a_suitability_{reference}",
        )
        submitted = st.form_submit_button(
            "Lock and submit judgment", type="primary", use_container_width=True
        )

    if submitted:
        try:
            locked_reference = session.submit_phase_a(
                {
                    "decision": decision,
                    "certification": certification,
                    "confidence": confidence,
                    "decisive_evidence": decisive_evidence.strip(),
                    "ambiguity": ambiguity.strip(),
                    "overall_suitability": suitability,
                }
            )
        except WorkflowError as exc:
            st.error(str(exc))
            return
        _log(
            "phase_a_judgment_submitted",
            reference=locked_reference,
            component="judgment_form",
            payload=session.state["phase_a_responses"][locked_reference],
        )
        if session.phase == "phase_b":
            _log("phase_a_locked", component="phase_transition", payload={"judgment_count": 6})
            st.session_state["_show_phase_b_transition"] = True
        st.rerun()


def _render_source(reference: str, source_index: int) -> None:
    session: Study1Session = st.session_state["_study1_session"]
    artifact = session.recommendation_artifact()
    source = artifact.sources[source_index]
    st.markdown(
        f'<div class="source-passage"><strong>{source.label}</strong><br>{source.text}</div>',
        unsafe_allow_html=True,
    )
    if st.button("Close source passage", key=f"close_source_{reference}_{source_index}"):
        _log(
            "provenance_source_closed",
            reference=reference,
            component="source_passage",
            payload={"source_label": source.label, "source_index": source_index},
        )
        st.session_state["_study1_source"] = None
        st.rerun()


def _phase_b(session: Study1Session) -> None:
    if st.session_state.pop("_show_phase_b_transition", False):
        st.success(
            "All independent judgments are now locked. The next phase evaluates whether "
            "the displayed AI outputs are realistic and clear; it does not reopen your decisions."
        )

    reference = session.current_reference()
    if reference is None:
        st.rerun()
    assert reference is not None
    artifact = session.recommendation_artifact()
    assignment = session.state["artifact_assignments"][reference]
    _mark_presented(
        "phase_b",
        reference,
        {
            "artifact_variant": assignment["variant"],
            "provenance": assignment["provenance"],
            "anthropomorphic": assignment["anthropomorphic"],
            "internal_assessment": session.cases.internal_assessment_for_log(reference),
        },
    )

    st.info(
        "Evaluate whether this is a plausible AI screening output. Plausibility is "
        "separate from whether you agree with the recommendation."
    )
    _render_cv(reference)
    st.markdown(
        f'<div class="recommendation-panel"><p>{artifact.lead}</p>'
        f'<p><strong>Assessment rationale</strong><br>{artifact.rationale}</p></div>',
        unsafe_allow_html=True,
    )

    if artifact.sources:
        st.markdown("#### Evidence used")
        for index, source in enumerate(artifact.sources):
            if st.button(source.label, key=f"source_{reference}_{index}"):
                st.session_state["_study1_source"] = index
                _log(
                    "provenance_source_opened",
                    reference=reference,
                    component="source_passage",
                    payload={"source_label": source.label, "source_index": index},
                )
                st.rerun()
        active_source = st.session_state.get("_study1_source")
        if active_source is not None:
            _render_source(reference, int(active_source))
            return

    scale = [
        "1 · Not at all",
        "2",
        "3",
        "4 · Moderately",
        "5",
        "6",
        "7 · Completely",
    ]
    with st.form(f"phase_b_{reference}"):
        ai_plausibility = st.select_slider(
            "How plausible is it that an AI screening assistant could produce this output?",
            options=scale,
            value="4 · Moderately",
            key=f"phase_b_plausibility_{reference}",
        )
        rationale_realism = st.select_slider(
            "How realistic and coherent is the rationale?",
            options=scale,
            value="4 · Moderately",
            key=f"phase_b_realism_{reference}",
        )
        clarity = st.select_slider(
            "How clear is the recommendation and its basis?",
            options=scale,
            value="4 · Moderately",
            key=f"phase_b_clarity_{reference}",
        )
        reveals_error = st.radio(
            "Does the wording make any intended system error too obvious or artificial?",
            ["No", "Unsure", "Yes"],
            index=None,
            key=f"phase_b_reveals_{reference}",
        )
        evidence_accuracy = st.radio(
            "Does the output invent or misstate evidence from the available materials?",
            [
                "No unsupported or misstated evidence",
                "Unsure",
                "Contains unsupported or misstated evidence",
            ],
            index=None,
            key=f"phase_b_accuracy_{reference}",
        )
        comments = st.text_area(
            "Optional: note any wording or interface issue that reduces realism.",
            max_chars=1500,
            key=f"phase_b_comments_{reference}",
        )
        submitted = st.form_submit_button(
            "Submit artifact review", type="primary", use_container_width=True
        )

    if submitted:
        try:
            reviewed_reference = session.submit_phase_b(
                {
                    "ai_plausibility": scale.index(ai_plausibility) + 1,
                    "rationale_realism": scale.index(rationale_realism) + 1,
                    "clarity": scale.index(clarity) + 1,
                    "reveals_error": reveals_error,
                    "evidence_accuracy": evidence_accuracy,
                    "comments": comments.strip(),
                    "artifact_variant": assignment["variant"],
                }
            )
        except WorkflowError as exc:
            st.error(str(exc))
            return
        _log(
            "phase_b_artifact_submitted",
            reference=reviewed_reference,
            component="artifact_form",
            payload=session.state["phase_b_responses"][reviewed_reference],
        )
        if session.complete:
            _log("session_completed", component="completion", payload={"phase_a_count": 6, "phase_b_count": 6})
        st.session_state["_study1_source"] = None
        st.rerun()


def _complete(session: Study1Session) -> None:
    st.markdown(
        '<div class="completion-panel"><strong>Task complete</strong><br>'
        "All independent judgments and recommendation-artifact reviews were recorded.</div>",
        unsafe_allow_html=True,
    )
    secret = st.session_state["_study1_secret"]
    completion_token = create_completion_token(
        session_id=session.state["session_id"],
        linkage_hash=session.state["linkage_hash"],
        secret=secret,
    )
    return_url = safe_qualtrics_return_url(
        st.session_state.get("_study1_return", ""), completion_token
    )
    if return_url:
        st.link_button("Return to survey", return_url, type="primary", use_container_width=True)
    else:
        st.info("You may now return to the survey tab. No valid Qualtrics return route was supplied.")


def run() -> None:
    st.set_page_config(
        page_title="Study 1 expert validation",
        page_icon=":material/fact_check:",
        layout="centered",
        initial_sidebar_state="expanded",
    )
    _apply_theme()
    try:
        _initialize()
    except TokenError as exc:
        st.error(f"Study link unavailable: {exc}")
        st.stop()

    session: Study1Session = st.session_state["_study1_session"]
    _header(session)
    if _document_navigation(session):
        return
    if session.phase == "phase_a":
        _phase_a(session)
    elif session.phase == "phase_b":
        _phase_b(session)
    else:
        _complete(session)
