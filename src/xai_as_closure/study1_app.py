"""Streamlit application for streamlined Study 1 expert validation."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse
from uuid import uuid4

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from .cases import POLICY_PATH, ROLE_PATH, CaseRepository, PROJECT_ROOT, material_manifest
from .config import read_project_storage_config
from .document_renderer import render_cv_document, render_reference_document
from .github_saver import save_to_github, test_github_connection
from .storage import DEFAULT_DATA_ROOT, SessionStore, stable_session_id
from .study1 import STUDY1_INSTRUMENT_VERSION, Study1Session, WorkflowError, instrument_version, is_revalidation, FOCUSED_ROUND
from .study1_launch import ParticipantLink, read_participant_link, validate_participant
from .study1_round2_support import check_round2_materials, recover_round2_checkpoint, round2_archive_path, validation_cases


STUDY1_APP_RELEASE = "2026-11-03.4"


def _round() -> str:
    return str(st.session_state.get("_study1_validation_round", "initial"))


def _local_preview() -> bool:
    return os.getenv("STUDY1_LOCAL_PREVIEW") == "1"


def _participant_id() -> str:
    return str(st.session_state.get("_study1_participant_id", st.session_state.get("prolific_pid", "")))


def _recruitment_source() -> str:
    if _local_preview():
        return "preview"
    return str(st.session_state.get("_study1_recruitment_source", "prolific"))


def _set_participant(link: ParticipantLink) -> None:
    existing = st.session_state.get("_study1_session")
    if existing is not None and (_participant_id() != link.participant_id
            or _recruitment_source() != link.recruitment_source):
        raise WorkflowError("This tab is linked to another participant. Open your own study link in a new tab.")
    st.session_state["_study1_participant_id"] = link.participant_id
    st.session_state["_study1_recruitment_source"] = link.recruitment_source
    if link.recruitment_source == "prolific":
        st.session_state["prolific_pid"] = link.participant_id
    else:
        st.session_state.pop("prolific_pid", None)


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
        .elapsed-timer {
            align-items: baseline;
            background: #ffffff;
            border: 1px solid #c9d0d7;
            border-radius: 6px;
            display: flex;
            justify-content: space-between;
            margin: .45rem 0 .8rem;
            padding: .7rem 1rem;
        }
        .elapsed-timer__label {
            color: #53606d;
            font-size: .86rem;
            font-weight: 650;
            letter-spacing: .035em;
            text-transform: uppercase;
        }
        .elapsed-timer__value {
            color: #20252b;
            font-size: 2rem;
            font-variant-numeric: tabular-nums;
            font-weight: 700;
            letter-spacing: .02em;
            line-height: 1;
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


def _format_elapsed_time(elapsed_seconds: float) -> str:
    total_seconds = max(0, int(elapsed_seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


@st.fragment(run_every=1)
def _render_elapsed_timer() -> None:
    session: Study1Session | None = st.session_state.get("_study1_session")
    if session is None:
        return
    if session.complete:
        elapsed_seconds = float(session.state.get("total_duration_seconds") or 0)
    else:
        elapsed_seconds = _elapsed()
    formatted = _format_elapsed_time(elapsed_seconds)
    st.markdown(
        '<div class="elapsed-timer" role="timer" aria-label="Elapsed time">'
        '<span class="elapsed-timer__label">Elapsed time</span>'
        f'<span class="elapsed-timer__value">{formatted}</span>'
        "</div>",
        unsafe_allow_html=True,
    )


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
    if is_revalidation(_round()) and not _local_preview():
        session.state["archive_pending"] = True
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
    if _local_preview():
        return
    repo = _secret("GITHUB_REPO") or _secret("GITHUB_DATA_REPO")
    token = _secret("GITHUB_TOKEN") or _secret("GITHUB_DATA_TOKEN")
    if not repo or not token:
        return
    session: Study1Session = st.session_state["_study1_session"]
    store: SessionStore = st.session_state["_study1_store"]
    session_id = session.state["session_id"]
    payload = {
        "session_id": session_id,
        "participant_id": _participant_id(),
        "prolific_pid": _participant_id() if _recruitment_source() == "prolific" else "",
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        **session.state,
        "material_manifest": session.cases.material_manifest,
        "events": store.read_events(session_id),
    }
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = round2_archive_path(session_id, _round()) if is_revalidation(_round()) else f"sessions/xai_as_closure/study1/{date_str}/{session_id}.json"
    success, _error = save_to_github(
        repo,
        path,
        json.dumps(payload, indent=2, ensure_ascii=True, default=str),
        f"Session: {session_id} | study1",
        github_token=token,
    )
    if is_revalidation(_round()):
        session.state["archive_pending"] = not success
        store.save(session.state)
    if not success and not is_revalidation(_round()):
        st.warning(
            "The private GitHub backup could not be updated. The local "
            "session log remains available; please notify the researcher."
        )


def _read_launch_params() -> None:
    """Read explicit linkage without requiring Prolific recruitment."""
    if _local_preview():
        st.session_state.setdefault("prolific_pid", os.getenv("STUDY1_PREVIEW_ID", "LOCAL_PREVIEW_STUDY1_ROUND2"))
        st.session_state["return_raw"] = ""
        return
    if is_revalidation(_round()):
        link = read_participant_link(prolific_pid=_query("PROLIFIC_PID"),
            participant_code=_query("participant_code"), legacy_pid=_query("pid"))
        if link is not None:
            _set_participant(link)
        if _query("return"):
            st.session_state["return_raw"] = _query("return")
        return
    pid = _query("PROLIFIC_PID") or _query("pid")
    if "prolific_pid" not in st.session_state and pid:
        st.session_state["prolific_pid"] = pid
    if "return_raw" not in st.session_state and _query("return"):
        st.session_state["return_raw"] = _query("return")


def _prolific_gate() -> None:
    """Link experts through their recruitment platform or researcher-issued code."""
    if is_revalidation(_round()):
        if _participant_id():
            return
        st.header("Welcome to the study task")
        st.write("Use the participant code supplied by the researcher, or select Prolific if you were recruited there.")
        kind = st.radio("How were you invited?",
            ["Researcher-issued participant code", "Prolific"], key="study1_link_type")
        source = "prolific" if kind == "Prolific" else "researcher"
        value = st.text_input("Prolific ID" if source == "prolific" else "Participant code",
            max_chars=64, key="study1_link_value")
        st.caption("Do not enter your name or email address. Use the same code when returning to an unfinished task.")
        if st.button("Begin study task", type="primary"):
            try:
                _set_participant(validate_participant(value, source))
            except WorkflowError as exc:
                st.error(str(exc))
            else:
                st.rerun()
        st.stop()
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
    if _local_preview():
        return
    production_launch = is_revalidation(_round()) or bool(_query("PROLIFIC_PID") or _query("pid"))
    if not production_launch and "_project_storage_config" not in st.session_state:
        st.session_state["_project_storage_config"] = read_project_storage_config()
    if _local_preview():
        return
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
    if parsed.scheme != "https" or not (
        host == "qualtrics.com" or host.endswith(".qualtrics.com")
    ):
        return None
    return decoded


def _build_final_return(
    raw_return: str, prolific_pid: str, session_id: str, *, recruitment_source: str = "prolific"
) -> str | None:
    safe_return = _safe_qualtrics_return(raw_return)
    if not safe_return:
        return None
    parsed = urlparse(safe_return)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if recruitment_source == "researcher":
        query.pop("PROLIFIC_PID", None)
        query.pop("pid", None)
        query["participant_code"] = prolific_pid
    else:
        query.pop("participant_code", None)
        query["PROLIFIC_PID"] = prolific_pid
    query["session_id"] = session_id
    query["done"] = "1"
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


def _initialize() -> None:
    validation_round = _round()
    if "_study1_session" in st.session_state:
        if st.session_state["_study1_session"].state.get("validation_round", "initial") != validation_round:
            raise WorkflowError("This saved session belongs to a different validation round.")
        return
    prolific_id = _participant_id().strip()
    source = _recruitment_source()
    production = not _local_preview() and (is_revalidation(validation_round) or bool(_query("PROLIFIC_PID") or _query("pid")))
    hash_input = prolific_id
    if is_revalidation(validation_round) and production:
        hash_input = validate_participant(prolific_id, source).hash_input
    linkage_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
    cases = validation_cases(validation_round)
    version = instrument_version(validation_round)
    identity = f"{linkage_hash}\0{cases.case_set_id}\0{version}"
    if is_revalidation(validation_round):
        identity += "\0" + validation_round
    session_id = stable_session_id(hashlib.sha256(identity.encode()).hexdigest())
    if _local_preview():
        data_root = os.getenv("STUDY1_PREVIEW_DATA_ROOT")
        if not data_root:
            data_root = st.session_state.setdefault("_study1_preview_root", tempfile.mkdtemp(prefix="facct-study1-round2-preview-"))
        store = SessionStore(Path(data_root))
    elif is_revalidation(validation_round):
        if validation_round == FOCUSED_ROUND:
            specific = _secret("STUDY1_FOCUSED_DATA_ROOT")
            generic = _secret("STUDY1_ROUND2_DATA_ROOT") or _secret("STUDY1_DATA_ROOT")
            data_root = Path(specific) if specific else (Path(generic) / FOCUSED_ROUND if generic else DEFAULT_DATA_ROOT.parent / "study1_focused")
        else:
            specific = _secret("STUDY1_ROUND2_DATA_ROOT")
            generic = _secret("STUDY1_DATA_ROOT")
            data_root = Path(specific) if specific else (Path(generic) / "round2" if generic else DEFAULT_DATA_ROOT.parent / "study1_round2")
        store = SessionStore(data_root)
    else:
        data_root = _secret("STUDY1_DATA_ROOT")
        store = SessionStore(Path(data_root)) if data_root else SessionStore()
    stored = store.load(session_id)
    if stored is None and is_revalidation(validation_round) and production:
        stored = recover_round2_checkpoint(store=store, cases=cases,
            repo=_secret("GITHUB_REPO") or _secret("GITHUB_DATA_REPO"),
            token=_secret("GITHUB_TOKEN") or _secret("GITHUB_DATA_TOKEN"),
            session_id=session_id, participant_id=prolific_id, linkage_hash=linkage_hash, recruitment_source=source, validation_round=validation_round)
    if stored:
        stored_source = stored.get("recruitment_source", "preview" if stored.get("is_preview") else "prolific")
        if is_revalidation(validation_round) and stored_source != source:
            raise WorkflowError("The saved participant-link type does not match this session.")
        if stored.get("validation_round", "initial") != validation_round:
            raise WorkflowError("The saved validation round does not match this app.")
        session = Study1Session.restore(stored, cases)
        event = "session_resumed"
    else:
        session = Study1Session.create(session_id=session_id, linkage_hash=linkage_hash,
            seed=linkage_hash, cases=cases, validation_round=validation_round)
        session.state["is_preview"] = _local_preview()
        store.save(session.state)
        event = "session_created"
    session.state["recruitment_source"] = source
    st.session_state["_study1_resumed_complete"] = bool(stored and session.complete)
    st.session_state["_study1_started"] = time.perf_counter()
    st.session_state["_study1_session"] = session
    st.session_state["_study1_store"] = store
    st.session_state["_study1_pilot"] = _local_preview() or not production
    _log(event, component="launch", payload={
        "prolific_id_from_url": bool(_query("PROLIFIC_PID") or _query("pid")) and source == "prolific",
        "recruitment_source": source,
        "pilot_mode": st.session_state["_study1_pilot"],
        "validation_round": validation_round, "case_set_id": cases.case_set_id,
        "instrument_version": version, "is_preview": _local_preview()})


def _header(session: Study1Session) -> None:
    st.markdown(
        '<div class="study-kicker">STUDY 1 · EXPERT VALIDATION</div>',
        unsafe_allow_html=True,
    )
    st.title("Candidate screening task")
    if is_revalidation(_round()):
        st.caption("Assess each candidate independently against the supplied requirements.")
    else:
        st.caption("Designed to take no more than about 10 minutes.")
    _render_elapsed_timer()
    if session.phase == "screening":
        count = len(session.state["responses"])
        total = len(session.state["profile_order"])
        st.progress(count / total, text=f"Candidate judgments: {count} of {total} submitted")
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
            ('What information was most important for your decision? Identify the '
             'relevant requirement and candidate evidence. Enter "None" if no information was decisive.')
            if is_revalidation(_round()) else
            ('What information in the candidate file was most important for your '
             'decision? Enter "None" if no information was decisive.'),
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
                payload={"judgment_count": len(session.state["profile_order"])},
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
        f"You have completed all {len(session.state['profile_order'])} candidate judgments. Please now evaluate "
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
            sorted(session.state["profile_order"]),
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
            "judgment_count": len(session.state["profile_order"]),
            "post_study_submitted": True,
            "total_duration_seconds": session.state["total_duration_seconds"],
        },
    )
    _sync_github()
    st.rerun()


def _complete(session: Study1Session) -> None:
    if st.session_state.get("_study1_resumed_complete"):
        st.info("This participant ID or code already has a completed session. Your recorded responses have been restored.")
    st.markdown(
        '<div class="completion-panel"><strong>Task complete</strong><br>'
        f"All {len(session.state['profile_order'])} independent candidate judgments and the final materials review "
        "were recorded.</div>",
        unsafe_allow_html=True,
    )
    return_url = _build_final_return(
        str(st.session_state.get("return_raw", "")),
        _participant_id(),
        str(session.state["session_id"]),
        recruitment_source=_recruitment_source(),
    )
    if return_url:
        st.link_button(
            "Return to survey", return_url, type="primary", use_container_width=True
        )
    else:
        st.info("Please return to your survey tab and continue.")


def run(validation_round: str = "initial") -> None:
    st.set_page_config(
        page_title="Study 1 expert validation",
        page_icon=":material/fact_check:",
        layout="centered",
        initial_sidebar_state="expanded",
    )
    instrument_version(validation_round)
    st.session_state["_study1_validation_round"] = validation_round
    _apply_theme()
    if is_revalidation(validation_round):
        try:
            check_round2_materials(validation_round)
        except WorkflowError as exc:
            st.error(str(exc))
            st.stop()
    try:
        _read_launch_params()
        _prolific_gate()
    except WorkflowError as exc:
        st.error(f"Study link unavailable: {exc}")
        st.stop()
    _check_private_storage()
    try:
        _initialize()
    except WorkflowError as exc:
        st.error(f"Study link unavailable: {exc}")
        st.stop()

    session: Study1Session = st.session_state["_study1_session"]
    if is_revalidation(validation_round) and session.state.get("archive_pending") and not _local_preview():
        _sync_github()
        if session.state.get("archive_pending"):
            st.error("Your progress is saved locally, but the study backup has not completed. Please retry before continuing.")
            if st.button("Retry saving", type="primary"):
                st.rerun()
            st.stop()
    _header(session)
    if _document_navigation(session):
        return
    if session.phase == "screening":
        _screening(session)
    elif session.phase == "post_study":
        _post_study(session)
    else:
        _complete(session)
