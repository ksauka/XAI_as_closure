"""Streamlit application for streamlined Study 1 expert validation."""

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
from .config import read_project_storage_config
from .document_renderer import render_cv_document, render_reference_document
from .github_saver import save_to_github, test_github_connection
from .storage import SessionStore, stable_session_id
from .study1 import STUDY1_INSTRUMENT_VERSION, Study1Session, WorkflowError


def _secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name)
    except StreamlitSecretNotFoundError:
        value = None
    local_config = st.session_state.get("_project_storage_config", {})
    local_value = local_config.get(name) if isinstance(local_config, dict) else None
    return str(value or os.getenv(name) or local_value or default)


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
    if not production_launch and "_project_storage_config" not in st.session_state:
        st.session_state["_project_storage_config"] = read_project_storage_config()
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
    cases = CaseRepository()
    versioned_linkage_hash = hashlib.sha256(
        (f"{linkage_hash}\0{cases.case_set_id}\0{STUDY1_INSTRUMENT_VERSION}").encode()
    ).hexdigest()
    session_id = stable_session_id(versioned_linkage_hash)
    data_root = _secret("STUDY1_DATA_ROOT")
    store = (
        SessionStore(Path(data_root) if data_root else None)
        if data_root
        else SessionStore()
    )
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
            "instrument_version": STUDY1_INSTRUMENT_VERSION,
        },
    )


def _header(session: Study1Session) -> None:
    st.markdown(
        '<div class="study-kicker">STUDY 1 · EXPERT VALIDATION</div>',
        unsafe_allow_html=True,
    )
    st.title("Candidate screening task")
    st.caption("Designed to take no more than about 10 minutes.")
    if session.phase == "screening":
        count = len(session.state["responses"])
        st.progress(count / 6, text=f"Candidate judgments: {count} of 6 submitted")
    elif session.phase == "post_study":
        st.progress(0.9, text="Candidate judgments complete · final materials review")
    else:
        st.progress(1.0, text="Task complete")


def _document_navigation(session: Study1Session) -> bool:
    view = st.session_state.get("_study1_document")
    if view:
        visit = st.session_state.get("_study1_document_visit") or {}
        if not isinstance(visit.get("viewed_at_monotonic"), (int, float)):
            visit["viewed_at_monotonic"] = time.perf_counter()
            st.session_state["_study1_document_visit"] = visit
        document_type, path = (
            ("Job description", ROLE_PATH)
            if view == "role"
            else ("Recruitment policy", POLICY_PATH)
        )
        render_reference_document(
            st,
            path,
            document_type=document_type,
            role=session.cases.role,
            company=session.cases.company,
            timeline=session.cases.timeline,
        )
        if session.phase == "screening":
            return_target = "candidate"
            back_label = "Back to candidate"
        elif session.phase == "post_study":
            return_target = "final_materials_review"
            back_label = "Back to final materials review"
        else:
            return_target = "completion"
            back_label = "Back to task completion"
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
    render_cv_document(
        st,
        case,
        role=session.cases.role,
        company=session.cases.company,
        timeline=session.cases.timeline,
    )


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
        st.subheader("Screening decision")
        decision = st.radio(
            "Screening decision",
            ["Advance candidate to human interview", "Reject candidate"],
            index=None,
            key=f"screening_decision_{reference}",
            label_visibility="collapsed",
        )
        st.subheader("Confidence in this decision")
        confidence = st.slider(
            "Confidence in this decision",
            0,
            100,
            50,
            format="%d%%",
            key=f"screening_confidence_{reference}",
            label_visibility="collapsed",
        )
        hard_criterion_judgment = st.radio(
            "Does this candidate satisfy the mandatory professional requirements?",
            ["Yes", "No"],
            index=None,
            horizontal=True,
            key=f"screening_hard_criterion_{reference}",
        )
        decisive_evidence = st.text_input(
            "What information in the candidate file was most important for your "
            'decision? Enter "None" if no information was decisive.',
            max_chars=500,
            key=f"screening_evidence_{reference}",
        )
        submitted = st.form_submit_button(
            "Lock and submit judgment", type="primary", use_container_width=True
        )

    if submitted:
        try:
            locked_reference = session.submit_judgment(
                {
                    "decision": decision,
                    "hard_criterion_judgment": hard_criterion_judgment,
                    "confidence": confidence,
                    "decisive_evidence": decisive_evidence.strip(),
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
        if session.phase == "post_study":
            _log(
                "candidate_screening_completed",
                component="candidate_judgments",
                payload={"judgment_count": 6},
            )
        _sync_github()
        st.rerun()


def _post_study(session: Study1Session) -> None:
    if not st.session_state.get("_study1_post_study_presented"):
        _log(
            "post_study_presented",
            component="final_materials_review",
            payload={"judgment_count": len(session.state["responses"])},
        )
        st.session_state["_study1_post_study_presented"] = True

    st.info(
        "You have completed all six candidate judgments. Please now evaluate "
        "the role requirements and candidate materials as a complete set."
    )
    st.caption("For questions 1–6: 1 = Strongly disagree · 7 = Strongly agree")

    likert_questions = (
        (
            "role_requirement_clarity",
            (
                "1. The role requirements were clear enough to determine whether "
                "a candidate met the mandatory requirements."
            ),
        ),
        (
            "candidate_profile_realism",
            (
                "2. The candidate profiles were realistic representations of "
                "applicants I could encounter in recruitment practice."
            ),
        ),
        (
            "qualification_difference_plausibility",
            (
                "3. The differences between qualified and unqualified candidates "
                "were plausible rather than artificial."
            ),
        ),
        (
            "mandatory_information_identifiability",
            (
                "4. The information needed to judge the mandatory professional "
                "requirements "
                "could be identified from the candidate files."
            ),
        ),
        (
            "information_sufficiency",
            (
                "5. The candidate profiles contained enough information to make "
                "a meaningful screening decision."
            ),
        ),
        (
            "task_ecological_validity",
            (
                "6. The screening task reflected the type of judgement that "
                "could reasonably occur during CV pre-screening."
            ),
        ),
    )

    with st.form("study1_post_study", clear_on_submit=False):
        likert_responses = {
            key: st.radio(
                question,
                list(range(1, 8)),
                index=None,
                horizontal=True,
                key=f"post_study_{key}",
            )
            for key, question in likert_questions
        }
        professional_disagreement = st.radio(
            "7. Were there any candidates for whom you believed reasonable "
            "recruitment professionals could disagree about whether the candidate "
            "met the mandatory professional requirements?",
            ["Yes", "No"],
            index=None,
            horizontal=True,
            key="post_study_professional_disagreement",
        )
        disputed_profiles = st.multiselect(
            "If yes, which candidate(s)?",
            sorted(session.cases.references),
            key="post_study_disputed_profiles",
        )
        disputed_profiles_reason = st.text_area(
            "If yes, why could reasonable professionals disagree?",
            max_chars=800,
            key="post_study_disputed_profiles_reason",
        )
        materials_feedback = st.text_area(
            "8. Optional: Did any profile seem unrealistic or artificially "
            "constructed, or should anything in the role requirements or profiles "
            "be changed before the main study? Identify the candidate where "
            "relevant.",
            max_chars=1000,
            key="post_study_materials_feedback",
        )
        submitted = st.form_submit_button(
            "Submit final materials review",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return
    response = {
        **likert_responses,
        "professional_disagreement": professional_disagreement,
        "disputed_profiles": disputed_profiles,
        "disputed_profiles_reason": disputed_profiles_reason.strip(),
        "materials_feedback": materials_feedback.strip(),
    }
    try:
        session.submit_post_study(response)
    except WorkflowError as exc:
        st.error(str(exc))
        return
    _log(
        "post_study_submitted",
        component="final_materials_review",
        payload=session.state["post_study_response"],
    )
    _log(
        "session_completed",
        component="completion",
        payload={
            "judgment_count": 6,
            "post_study_submitted": True,
            "total_duration_seconds": session.state["total_duration_seconds"],
        },
    )
    _sync_github()
    st.rerun()


def _complete(session: Study1Session) -> None:
    st.markdown(
        '<div class="completion-panel"><strong>Task complete</strong><br>'
        "All six independent candidate judgments and the final materials review "
        "were recorded.</div>",
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
    elif session.phase == "post_study":
        _post_study(session)
    else:
        _complete(session)
