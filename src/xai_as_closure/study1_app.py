"""Streamlit application for single-phase Study 1 expert validation."""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse
from uuid import uuid4

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from .cases import POLICY_PATH, ROLE_PATH, CaseRepository
from .github_saver import save_to_github, test_github_connection
from .storage import SessionStore, stable_session_id
from .study1 import Study1Session, WorkflowError


def _secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name)
    except StreamlitSecretNotFoundError:
        value = None
    return str(value or os.getenv(name, default))


def _query(name: str) -> str:
    value = st.query_params.get(name, "")
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
        h4 {
            font-size: 1.02rem;
            letter-spacing: 0;
            margin-top: 1.4rem;
            padding-bottom: .3rem;
            border-bottom: 1px solid #dce1e6;
        }
        h5 {
            font-size: .92rem;
            letter-spacing: 0;
            font-weight: 600;
            color: #53606d;
            margin-top: .9rem;
            margin-bottom: .1rem;
        }
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
    started = st.session_state.get("_study1_started", time.perf_counter())
    return round(time.perf_counter() - started, 3)


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


def _sync_github() -> None:
    """Back up the session state and events to the private GitHub repo.

    Streamlit Community Cloud's filesystem is ephemeral, so this mirrors
    Study 2's after-every-trial backup rather than relying on local JSONL alone.
    """
    repo = _secret("GITHUB_REPO") or _secret("GITHUB_DATA_REPO")
    token = _secret("GITHUB_TOKEN") or _secret("GITHUB_DATA_TOKEN")
    if not repo or not token:
        return
    session: Study1Session = st.session_state["_study1_session"]
    store: SessionStore = st.session_state["_study1_store"]
    session_id = session.state["session_id"]
    payload = {
        "session_id": session_id,
        "participant_id": st.session_state.get("prolific_pid", ""),
        "prolific_pid": st.session_state.get("prolific_pid", ""),
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        **session.state,
        "events": store.read_events(session_id),
    }
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = f"sessions/xai_as_closure/study1/{date_str}/{session_id}.json"
    success, _error = save_to_github(
        repo,
        path,
        json.dumps(payload, indent=2, ensure_ascii=True, default=str),
        f"Session: {session_id} | study1",
        token,
    )
    if not success:
        st.warning(
            "The private GitHub backup could not be updated. The local "
            "session log remains available; please notify the researcher."
        )


def _read_launch_params() -> None:
    """Read the Prolific-issued participant id, matching Study 2's flow."""
    pid = _query("PROLIFIC_PID") or _query("pid")
    if "prolific_pid" not in st.session_state and pid:
        st.session_state["prolific_pid"] = pid
    if "return_raw" not in st.session_state and _query("return"):
        st.session_state["return_raw"] = _query("return")


def _prolific_gate() -> None:
    """Manual fallback identical to Study 2's, for direct/local links."""
    if st.session_state.get("prolific_pid"):
        return
    st.header("Welcome to the study task")
    st.write(
        "Enter your Prolific ID to link this task to your survey responses. "
        "The ID is normally filled automatically by the study link."
    )
    prolific_id = st.text_input(
        "Prolific ID",
        placeholder="e.g., 5f8e3c2a1b9d4e6f7a8b9c0d",
        max_chars=128,
    )
    if st.button("Begin study task", type="primary"):
        if prolific_id.strip():
            st.session_state["prolific_pid"] = prolific_id.strip()
            st.rerun()
        st.error("Please enter your Prolific ID before continuing.")
    st.stop()


def _check_private_storage() -> None:
    """Require working private-GitHub storage for production launches."""
    production_launch = bool(_query("PROLIFIC_PID") or _query("pid"))
    repo = _secret("GITHUB_REPO") or _secret("GITHUB_DATA_REPO")
    token = _secret("GITHUB_TOKEN") or _secret("GITHUB_DATA_TOKEN")
    if not repo or not token:
        message = (
            "Private study-data storage is not configured. Please notify the "
            "researcher before continuing."
        )
        if production_launch:
            st.error(message)
            st.stop()
        st.warning(f"Pilot mode: {message}")
        return
    status_key = "_study1_github_storage_ready"
    if status_key not in st.session_state:
        success, _detail = test_github_connection(token, repo)
        st.session_state[status_key] = success
    if not st.session_state[status_key]:
        message = (
            "Private study-data storage could not be reached. Please notify the "
            "researcher before continuing."
        )
        if production_launch:
            st.error(message)
            st.stop()
        st.warning(f"Pilot mode: {message}")


def _safe_qualtrics_return(raw_return: str) -> str | None:
    if not raw_return:
        return None
    decoded = unquote(raw_return)
    if not decoded.startswith(("http://", "https://")):
        decoded = f"https://{decoded}"
    try:
        parsed = urlparse(decoded)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or not (
        host == "qualtrics.com" or host.endswith(".qualtrics.com")
    ):
        return None
    return decoded


def _build_final_return(
    raw_return: str, prolific_pid: str, session_id: str
) -> str | None:
    safe_return = _safe_qualtrics_return(raw_return)
    if not safe_return:
        return None
    parsed = urlparse(safe_return)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("PROLIFIC_PID", prolific_pid)
    query.setdefault("session_id", session_id)
    query.setdefault("done", "1")
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


def _initialize() -> None:
    if "_study1_session" in st.session_state:
        return
    prolific_id = str(st.session_state["prolific_pid"]).strip()
    linkage_hash = hashlib.sha256(prolific_id.encode("utf-8")).hexdigest()
    session_id = stable_session_id(linkage_hash)
    data_root = _secret("STUDY1_DATA_ROOT")
    store = (
        SessionStore(Path(data_root) if data_root else None)
        if data_root
        else SessionStore()
    )
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
    pilot = not bool(_query("PROLIFIC_PID") or _query("pid"))
    st.session_state["_study1_started"] = time.perf_counter()
    st.session_state["_study1_session"] = session
    st.session_state["_study1_store"] = store
    st.session_state["_study1_pilot"] = pilot
    _log(
        event,
        component="launch",
        payload={
            "prolific_id_from_url": not pilot,
            "pilot_mode": pilot,
            "case_set_id": cases.case_set_id,
        },
    )


def _header(session: Study1Session) -> None:
    st.markdown(
        '<div class="study-kicker">STUDY 1 · EXPERT VALIDATION</div>',
        unsafe_allow_html=True,
    )
    st.title("Candidate screening task")
    if session.phase == "screening":
        count = len(session.state["responses"])
        st.progress(count / 6, text=f"Candidate judgments: {count} of 6 submitted")
    else:
        st.progress(1.0, text="Task complete")


def _document_navigation(session: Study1Session) -> bool:
    view = st.session_state.get("_study1_document")
    if view:
        visit = st.session_state.get("_study1_document_visit") or {}
        if not isinstance(visit.get("viewed_at_monotonic"), (int, float)):
            visit["viewed_at_monotonic"] = time.perf_counter()
            st.session_state["_study1_document_visit"] = visit
        title, path = (
            ("AI Governance Lead job description", ROLE_PATH)
            if view == "role"
            else ("Recruitment policy", POLICY_PATH)
        )
        st.subheader(title)
        st.markdown(path.read_text(encoding="utf-8"))
        return_target = "candidate" if session.phase == "screening" else "completion"
        back_label = (
            "Back to candidate"
            if return_target == "candidate"
            else "Back to task completion"
        )
        if st.button(back_label, type="primary", key=f"back_{view}"):
            returned_at = time.perf_counter()
            clicked_at = visit.get("clicked_at_monotonic")
            viewed_at = visit.get("viewed_at_monotonic")
            click_to_return_seconds = (
                round(returned_at - float(clicked_at), 3)
                if isinstance(clicked_at, (int, float))
                else None
            )
            dwell_seconds = (
                round(returned_at - float(viewed_at), 3)
                if isinstance(viewed_at, (int, float))
                else None
            )
            _log(
                "document_closed",
                reference=session.current_reference(),
                component=view,
                payload={
                    "document_visit_id": visit.get("document_visit_id"),
                    "document": view,
                    "origin": visit.get("origin"),
                    "return_target": return_target,
                    "click_to_return_seconds": click_to_return_seconds,
                    "dwell_seconds": dwell_seconds,
                },
            )
            st.session_state["_study1_document"] = None
            st.session_state["_study1_document_visit"] = None
            _sync_github()
            st.rerun()
        return True

    reference = session.current_reference()
    with st.sidebar:
        st.subheader("Reference documents")
        st.caption("These documents remain available throughout the task.")
        if st.button("Open job description", use_container_width=True):
            visit = {
                "document_visit_id": uuid4().hex,
                "document": "role",
                "origin": "sidebar_reference_documents",
                "clicked_at_monotonic": time.perf_counter(),
            }
            st.session_state["_study1_document"] = "role"
            st.session_state["_study1_document_visit"] = visit
            _log(
                "document_opened",
                reference=reference,
                component="role",
                payload={
                    key: value
                    for key, value in visit.items()
                    if not key.endswith("_monotonic")
                },
            )
            _sync_github()
            st.rerun()
        if st.button("Open recruitment policy", use_container_width=True):
            visit = {
                "document_visit_id": uuid4().hex,
                "document": "policy",
                "origin": "sidebar_reference_documents",
                "clicked_at_monotonic": time.perf_counter(),
            }
            st.session_state["_study1_document"] = "policy"
            st.session_state["_study1_document_visit"] = visit
            _log(
                "document_opened",
                reference=reference,
                component="policy",
                payload={
                    key: value
                    for key, value in visit.items()
                    if not key.endswith("_monotonic")
                },
            )
            _sync_github()
            st.rerun()
        st.divider()
        st.caption(
            "Fictional materials for research. Do not use for real hiring decisions."
        )
        if st.session_state.get("_study1_pilot"):
            st.warning("Pilot mode")
    return False


def _render_cv(reference: str) -> None:
    session: Study1Session = st.session_state["_study1_session"]
    case = session.cases.participant_case(reference)
    st.subheader(f"Candidate {case.reference} Curriculum vitae")
    in_experience = False
    for section in case.sections:
        if section.id.startswith("cv_role_"):
            if not in_experience:
                st.markdown("#### Experience")
                in_experience = True
            st.markdown(f"##### {section.heading}")
        else:
            in_experience = False
            st.markdown(f"#### {section.heading}")
        st.write(section.text)


def _mark_presented(reference: str, payload: dict[str, Any]) -> None:
    key = f"_presented_{reference}"
    if not st.session_state.get(key):
        _log(
            "profile_presented",
            reference=reference,
            component="candidate",
            payload=payload,
        )
        st.session_state[key] = True


def _screening(session: Study1Session) -> None:
    reference = session.current_reference()
    if reference is None:
        raise WorkflowError("There is no active validation profile.")
    _mark_presented(
        reference,
        {
            "visible_cv_section_count": len(
                session.cases.participant_case(reference).sections
            )
        },
    )
    st.info(
        "Judge the candidate independently against the job description and recruitment policy. "
        "A submitted judgment cannot be changed."
    )
    _render_cv(reference)

    with st.form(f"screening_{reference}", clear_on_submit=False):
        decision = st.radio(
            "Screening decision",
            ["Advance candidate to human interview", "Reject candidate"],
            index=None,
            key=f"screening_decision_{reference}",
        )
        certification = st.text_input(
            "Type the accepted mandatory requirement shown in the profile, "
            "or “None” if it is not present.",
            key=f"screening_certification_{reference}",
        )
        confidence = st.slider(
            "Confidence in this decision",
            0,
            100,
            50,
            format="%d%%",
            key=f"screening_confidence_{reference}",
        )
        decisive_evidence = st.text_area(
            "What evidence was decisive for your judgment?",
            max_chars=1500,
            key=f"screening_evidence_{reference}",
        )
        ambiguity = st.text_area(
            "Describe any ambiguity or missing information. Enter “None” if there is none.",
            max_chars=1500,
            key=f"screening_ambiguity_{reference}",
        )
        realism_cues = st.text_area(
            "Does anything feel unrealistic or unintentionally signal how this "
            "candidate should be classified? Enter “None” if not.",
            max_chars=1500,
            key=f"screening_realism_cues_{reference}",
        )
        submitted = st.form_submit_button(
            "Lock and submit judgment", type="primary", use_container_width=True
        )

    if submitted:
        try:
            locked_reference = session.submit_judgment(
                {
                    "decision": decision,
                    "certification": certification.strip(),
                    "confidence": confidence,
                    "decisive_evidence": decisive_evidence.strip(),
                    "ambiguity": ambiguity.strip(),
                    "realism_cues": realism_cues.strip(),
                }
            )
        except WorkflowError as exc:
            st.error(str(exc))
            return
        _log(
            "candidate_judgment_submitted",
            reference=locked_reference,
            component="judgment_form",
            payload=session.state["responses"][locked_reference],
        )
        if session.complete:
            _log(
                "session_completed",
                component="completion",
                payload={
                    "judgment_count": 6,
                    "total_duration_seconds": session.state["total_duration_seconds"],
                },
            )
        _sync_github()
        st.rerun()


def _complete(session: Study1Session) -> None:
    st.markdown(
        '<div class="completion-panel"><strong>Task complete</strong><br>'
        "All six independent candidate judgments were recorded.</div>",
        unsafe_allow_html=True,
    )
    return_url = _build_final_return(
        str(st.session_state.get("return_raw", "")),
        str(st.session_state["prolific_pid"]),
        str(session.state["session_id"]),
    )
    if return_url:
        st.link_button(
            "Return to survey", return_url, type="primary", use_container_width=True
        )
    else:
        st.info("Please return to your survey tab and continue.")


def run() -> None:
    st.set_page_config(
        page_title="Study 1 expert validation",
        page_icon=":material/fact_check:",
        layout="centered",
        initial_sidebar_state="expanded",
    )
    _apply_theme()
    _read_launch_params()
    _prolific_gate()
    _check_private_storage()
    try:
        _initialize()
    except WorkflowError as exc:
        st.error(f"Study link unavailable: {exc}")
        st.stop()

    session: Study1Session = st.session_state["_study1_session"]
    _header(session)
    if _document_navigation(session):
        return
    if session.phase == "screening":
        _screening(session)
    else:
        _complete(session)
