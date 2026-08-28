"""Streamlit application for the CHI 2027 six-profile Study 2 experiment."""

from __future__ import annotations

import hashlib
import os
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse
from uuid import uuid4

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from .cases import POLICY_PATH, ROLE_PATH, CaseRepository
from .conditions import get_study2_condition
from .config import read_project_storage_config
from .decision_agent import Study2DecisionAgent
from .document_renderer import (
    citation_document_frame_html,
    cv_document_html,
    reference_document_html,
    render_reference_document,
)
from .document_renderer import (
    render_cv_document as show_cv_document,
)
from .github_saver import test_github_connection
from .logger import DEFAULT_LOG_DIR, EventLogger, load_state, restored_logger
from .recommendation_component import render_recommendation_passage
from .study2 import Study2Session, Study2WorkflowError
from .study2_delivery import (
    HIGH_ANTHROPOMORPHISM,
    LOW_ANTHROPOMORPHISM,
)
from .theme import apply_anthrokit_theme, show_study_banner


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


def _elapsed() -> float:
    started = st.session_state.get("_study2_started", time.perf_counter())
    return round(time.perf_counter() - started, 3)


def _read_qualtrics_params() -> None:
    """Retain the working HAI Prolific/Qualtrics URL integration."""
    pid = _query("PROLIFIC_PID") or _query("pid")
    if "prolific_pid" not in st.session_state and pid:
        st.session_state["prolific_pid"] = pid
    if "study_cond" not in st.session_state and _query("cond"):
        st.session_state["study_cond"] = _query("cond")
    if "return_raw" not in st.session_state and _query("return"):
        st.session_state["return_raw"] = _query("return")


def _prolific_gate() -> None:
    """Use the original HAI manual fallback when no Prolific ID is supplied."""
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
    status_key = "_study2_github_storage_ready"
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
    """Decode and allow-list a Qualtrics return URL from the existing flow."""
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
    raw_return: str,
    prolific_pid: str,
    session_id: str,
    condition_id: str,
) -> str | None:
    """Build the original Qualtrics return with completion linkage fields."""
    safe_return = _safe_qualtrics_return(raw_return)
    if not safe_return:
        return None
    parsed = urlparse(safe_return)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("PROLIFIC_PID", prolific_pid)
    query.setdefault("session_id", session_id)
    query.setdefault("cond", condition_id)
    query.setdefault("done", "1")
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


def _log(
    event_type: str,
    *,
    reference: str | None = None,
    phase: str | None = None,
    component: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    session: Study2Session = st.session_state["_study2_session"]
    logger: EventLogger = st.session_state["_study2_logger"]
    position = (
        session.state["profile_order"].index(reference) + 1 if reference else None
    )
    logger.log(
        event_type,
        trial_reference=reference,
        trial_position=position,
        phase=phase or session.phase,
        component=component,
        elapsed_seconds=_elapsed(),
        payload=payload,
    )
    session.state["turn_id"] = logger.turn_id
    logger.save_state(session.state)


def _sync_github() -> None:
    """Use the original HAI private-GitHub session-log backup."""
    repo = _secret("GITHUB_REPO") or _secret("GITHUB_DATA_REPO")
    token = _secret("GITHUB_TOKEN") or _secret("GITHUB_DATA_TOKEN")
    if not repo or not token:
        return
    session: Study2Session = st.session_state["_study2_session"]
    logger: EventLogger = st.session_state["_study2_logger"]
    logger.session_meta = {
        **session.state,
        "qualtrics_returned": bool(st.session_state.get("return_raw")),
        "survey_linkage_id": session.state["session_id"],
    }
    success = logger.push_to_github(repo=repo, github_token=token)
    if not success:
        st.warning(
            "The private GitHub backup could not be updated. The local HAI event "
            "log remains available; please notify the researcher."
        )


def _initialize(locked_condition_id: str) -> None:
    if "_study2_session" in st.session_state:
        return
    condition = get_study2_condition(locked_condition_id)
    query_condition = str(st.session_state.get("study_cond", ""))
    if query_condition and query_condition != locked_condition_id:
        raise Study2WorkflowError(
            "The Qualtrics condition does not match this condition-locked application."
        )
    participant_id = str(st.session_state["prolific_pid"])
    data_root = _secret("STUDY2_DATA_ROOT")
    log_dir = Path(data_root) if data_root else DEFAULT_LOG_DIR
    cases = CaseRepository()
    session_id = hashlib.sha256(
        f"{participant_id.strip()}\0{cases.case_set_id}".encode()
    ).hexdigest()
    stored_state = load_state(session_id, log_dir)
    if stored_state and stored_state.get("condition_id") not in (
        None,
        locked_condition_id,
    ):
        raise Study2WorkflowError(
            "This participant's saved session belongs to a different condition."
        )
    if stored_state:
        session = Study2Session.restore(stored_state, cases)
        logger = restored_logger(condition, stored_state, log_dir)
        event = "session_resumed"
    else:
        logger = EventLogger(
            condition, participant_id, session_id=session_id, log_dir=log_dir
        )
        session = Study2Session.create(
            session_id=session_id,
            participant_id=participant_id,
            prolific_pid=participant_id,
            condition=condition,
            seed=participant_id,
            cases=cases,
        )
        event = "session_created"
    st.session_state["_study2_started"] = time.perf_counter()
    st.session_state["_study2_session"] = session
    st.session_state["_study2_logger"] = logger
    st.session_state["_study2_agent"] = Study2DecisionAgent(
        condition=condition, cases=cases
    )
    st.session_state["_study2_pilot"] = not bool(
        _query("PROLIFIC_PID") or _query("pid")
    )
    _log(
        event,
        component="launch",
        payload={
            "prolific_id_from_url": not st.session_state["_study2_pilot"],
            "pilot_mode": st.session_state["_study2_pilot"],
            "condition_id": condition.condition_id,
            "case_set_id": cases.case_set_id,
        },
    )


def _header(session: Study2Session) -> None:
    show_study_banner(st)
    st.caption("STUDY 2 · AI-ASSISTED CANDIDATE SCREENING")
    if session.complete:
        st.progress(1.0, text="All six candidate trials complete")
        return
    if session.state.get("introduction_step") != "complete":
        st.progress(0.0, text="Study introduction")
        return
    position = int(session.state["trial_index"]) + 1
    st.progress((position - 1) / 6, text=f"Candidate {position} of 6")


def _document_view(session: Study2Session) -> bool:
    view = st.session_state.get("_study2_document")
    if not view:
        return False
    visit = st.session_state.get("_study2_document_visit") or {}
    if not isinstance(visit.get("clicked_at_monotonic"), (int, float)):
        legacy_opened_at = st.session_state.get("_study2_document_opened_at")
        if isinstance(legacy_opened_at, (int, float)):
            visit["clicked_at_monotonic"] = legacy_opened_at
    if not isinstance(visit.get("viewed_at_monotonic"), (int, float)):
        visit["viewed_at_monotonic"] = time.perf_counter()
    st.session_state["_study2_document_visit"] = visit
    if view in {"role", "policy"}:
        document_type, path = (
            ("Job description", ROLE_PATH)
            if view == "role"
            else ("Recruitment policy", POLICY_PATH)
        )
        focus = str(st.session_state.get("_study2_document_focus") or "")
        render_reference_document(
            st,
            path,
            document_type=document_type,
            role=session.cases.role,
            company=session.cases.company,
            timeline=session.cases.timeline,
            focus=focus,
        )
    elif view == "cv":
        reference = session.current_reference()
        if reference is None:
            raise Study2WorkflowError("There is no active candidate document.")
        show_cv_document(
            st,
            session.cases.participant_case(reference),
            role=session.cases.role,
            company=session.cases.company,
            timeline=session.cases.timeline,
            focus=str(st.session_state.get("_study2_document_focus") or ""),
        )
    if session.state.get("introduction_step") != "complete":
        back_label = "Back to study introduction"
        return_target = "study_introduction"
    elif session.phase == "unaided":
        back_label = "Back to candidate"
        return_target = "candidate"
    elif session.phase == "forcing":
        back_label = "Back to requirement check"
        return_target = "requirement_check"
    elif session.phase in {"agent", "aided"}:
        back_label = "Back to AI assessment"
        return_target = "ai_assessment"
    else:
        back_label = "Back to assessment question"
        return_target = "assessment_question"
    if st.button(back_label, type="primary"):
        reference = (
            session.current_reference()
            if session.state.get("introduction_step") == "complete"
            else None
        )
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
        active_source = st.session_state.get("_study2_active_source") or {}
        _log(
            "document_closed",
            reference=reference,
            component=view,
            payload={
                "document_visit_id": visit.get("document_visit_id"),
                "document": view,
                "origin": visit.get("origin"),
                "citation_id": active_source.get("citation"),
                "citation": active_source.get("citation"),
                "return_target": return_target,
                "click_to_return_seconds": click_to_return_seconds,
                "dwell_seconds": dwell_seconds,
            },
        )
        st.session_state["_study2_document"] = None
        st.session_state["_study2_document_focus"] = None
        st.session_state["_study2_active_source"] = None
        st.session_state["_study2_document_opened_at"] = None
        st.session_state["_study2_document_visit"] = None
        _sync_github()
        st.rerun()
    return True


def _sidebar(session: Study2Session) -> None:
    active_reference = (
        session.current_reference()
        if session.state.get("introduction_step") == "complete"
        else None
    )
    with st.sidebar:
        st.subheader("Source documents")
        st.caption(
            "Optional full documents for checking details beyond the recruitment brief."
        )
        document_active = bool(
            st.session_state.get("_study2_document")
            or st.session_state.get("_study2_citation_document")
        )
        if document_active:
            st.caption("Close the open source document before opening another.")
        if st.button(
            "View full job description",
            use_container_width=True,
            disabled=document_active,
        ):
            visit = {
                "document_visit_id": uuid4().hex,
                "document": "role",
                "origin": "sidebar_reference_documents",
                "clicked_at_monotonic": time.perf_counter(),
            }
            st.session_state["_study2_document"] = "role"
            st.session_state["_study2_document_focus"] = None
            st.session_state["_study2_active_source"] = None
            st.session_state["_study2_document_opened_at"] = visit[
                "clicked_at_monotonic"
            ]
            st.session_state["_study2_document_visit"] = visit
            _log(
                "document_opened",
                reference=active_reference,
                component="role",
                payload={
                    key: value
                    for key, value in visit.items()
                    if not key.endswith("_monotonic")
                },
            )
            _sync_github()
            st.rerun()
        if st.button(
            "View full recruitment policy",
            use_container_width=True,
            disabled=document_active,
        ):
            visit = {
                "document_visit_id": uuid4().hex,
                "document": "policy",
                "origin": "sidebar_reference_documents",
                "clicked_at_monotonic": time.perf_counter(),
            }
            st.session_state["_study2_document"] = "policy"
            st.session_state["_study2_document_focus"] = None
            st.session_state["_study2_active_source"] = None
            st.session_state["_study2_document_opened_at"] = visit[
                "clicked_at_monotonic"
            ]
            st.session_state["_study2_document_visit"] = visit
            _log(
                "document_opened",
                reference=active_reference,
                component="policy",
                payload={
                    key: value
                    for key, value in visit.items()
                    if not key.endswith("_monotonic")
                },
            )
            _sync_github()
            st.rerun()
        if (
            active_reference
            and session.phase != "unaided"
            and st.button(
                "View candidate CV",
                use_container_width=True,
                disabled=document_active,
            )
        ):
            _open_reference_document("cv", "sidebar_source_documents")
        st.divider()
        st.caption("The AI is advisory. You make every final screening decision.")
        if st.session_state.get("_study2_pilot"):
            st.warning(f"Pilot mode · {session.condition.condition_id}")


def _introduction(session: Study2Session) -> None:
    """Render one concise recruitment brief before the first candidate trial."""
    step = str(session.state["introduction_step"])
    presented_key = "_study2_recruitment_brief_presented"
    if not st.session_state.get(presented_key):
        _log(
            "introduction_presented",
            phase="introduction",
            component="recruitment_brief",
            payload={"step": step, "presentation": "single_screen_summary"},
        )
        st.session_state[presented_key] = True
    if step not in {"instructions", "role", "policy"}:
        return

    st.header("AI-assisted screening task")
    st.info(
        "This is a fictional research scenario. Do not use this assistant "
        "for real employment decisions."
    )
    st.markdown(
        "You will screen six candidates for the fictional AI Governance Lead "
        "role. For each candidate, you will first make an unaided decision. "
        "The AI will then provide an advisory assessment before you make your "
        "final decision."
    )
    st.markdown("### Recruitment brief")
    with st.container(border=True):
        st.markdown("#### Company and role")
        st.write(
            "Suvh Trust Bank is a mid-sized retail and commercial bank expanding "
            "its use of AI in lending, investment advice, and risk analytics. The "
            "AI Governance Lead oversees risk and conformity assessments, "
            "governance controls, regulatory compliance, and cross-functional "
            "advice for high-risk AI systems."
        )
        timeline = session.cases.timeline
        st.markdown(
            f"**Posted:** {timeline.posted_label} · "
            f"**Screening window:** {timeline.screening_window_label} · "
            f"**Target fill:** {timeline.target_fill_label}"
        )
    with st.container(border=True):
        st.markdown("#### Recruitment guidance")
        st.write(
            "Use the job description, recruitment policy, and candidate CV as the "
            "sources for screening. Choose either **Advance candidate to human "
            "interview** or **Reject candidate**. The AI assessment is advisory; "
            "the recruiter records the screening decision."
        )
    st.info(
        "For detailed role requirements and recruitment guidelines, recruiters "
        "are advised to consult the complete documents when needed."
    )
    role_column, policy_column = st.columns(2)
    with role_column:
        if st.button(
            "View full job description",
            key="introduction_full_role",
            use_container_width=True,
        ):
            _open_reference_document("role", "introduction_summary")
    with policy_column:
        if st.button(
            "View full recruitment policy",
            key="introduction_full_policy",
            use_container_width=True,
        ):
            _open_reference_document("policy", "introduction_summary")

    if st.button("Begin candidate screening", type="primary", use_container_width=True):
        previous_step = step
        try:
            next_step = step
            while next_step != "complete":
                next_step = session.advance_introduction()
        except Study2WorkflowError as exc:
            st.error(str(exc))
            return
        _log(
            "introduction_advanced",
            phase="introduction",
            component="recruitment_brief",
            payload={"from_step": previous_step, "to_step": next_step},
        )
        st.rerun()


def _open_reference_document(document: str, origin: str) -> None:
    """Open an optional source document and start visit timing."""
    if document not in {"role", "policy", "cv"}:
        raise Study2WorkflowError("Unknown source document.")
    visit = {
        "document_visit_id": uuid4().hex,
        "document": document,
        "origin": origin,
        "clicked_at_monotonic": time.perf_counter(),
    }
    st.session_state["_study2_document"] = document
    st.session_state["_study2_document_focus"] = None
    st.session_state["_study2_active_source"] = None
    st.session_state["_study2_document_opened_at"] = visit["clicked_at_monotonic"]
    st.session_state["_study2_document_visit"] = visit
    _log(
        "document_opened",
        component=document,
        payload={
            key: value for key, value in visit.items() if not key.endswith("_monotonic")
        },
    )
    _sync_github()
    st.rerun()


def _source_chip_label(source: dict[str, Any]) -> str:
    """Return a neutral participant-facing document locator."""
    citation = str(source.get("citation", "Document"))
    return f"[{citation}]"


def _render_candidate(session: Study2Session, reference: str) -> None:
    show_cv_document(
        st,
        session.cases.participant_case(reference),
        role=session.cases.role,
        company=session.cases.company,
        timeline=session.cases.timeline,
    )


def _render_phase_heading(session: Study2Session, reference: str) -> None:
    """Make each post-CV workflow stage a visibly separate study page."""
    if session.phase == "forcing":
        st.header("Requirement check")
    elif session.phase in {"agent", "aided"}:
        st.header("AI assessment")
    elif session.phase == "recall":
        st.header("Assessment reflection")
    st.caption(f"Candidate {reference}")


def _handle_inline_citation(
    session: Study2Session,
    reference: str,
    blocks: list[dict[str, Any]],
    click: dict[str, str] | None,
) -> None:
    if not click:
        return
    nonce = str(click.get("nonce", ""))
    token = str(click.get("token", ""))
    if not nonce or st.session_state.get("_study2_processed_citation_nonce") == nonce:
        return
    try:
        source, block_index, citation_index = _resolve_inline_citation(
            session, reference, blocks, token
        )
    except Study2WorkflowError:
        st.error("The selected citation is unavailable.")
        return
    identity = (
        str(source.get("citation", "")),
        str(source.get("document", "")),
        str(source.get("focus", "")),
    )
    st.session_state["_study2_processed_citation_nonce"] = nonce
    visit = {
        "document_visit_id": uuid4().hex,
        "document": identity[1],
        "origin": "ai_message_citation",
        "clicked_at_monotonic": time.perf_counter(),
    }
    if st.session_state.get("_study2_citation_document"):
        _close_citation_document(
            reference,
            return_target="another_citation",
            close_reason="citation_replaced",
        )
    st.session_state["_study2_citation_document"] = {
        "source": dict(source),
        "visit": visit,
    }
    citation = _source_chip_label(source)
    _log(
        "citation_clicked",
        reference=reference,
        component="message_citation",
        payload={
            "document_visit_id": visit["document_visit_id"],
            "citation_id": identity[0],
            "citation": citation,
            "document": identity[1],
            "focus": identity[2],
            "origin": visit["origin"],
            "message_block_index": block_index,
            "citation_index": citation_index,
        },
    )
    _log(
        "document_opened",
        reference=reference,
        component=identity[1],
        payload={
            "document_visit_id": visit["document_visit_id"],
            "citation_id": identity[0],
            "citation": citation,
            "document": identity[1],
            "focus": identity[2],
            "origin": visit["origin"],
            "presentation": "inline_complete_document",
        },
    )
    _sync_github()
    st.rerun()


def _resolve_inline_citation(
    session: Study2Session,
    reference: str,
    blocks: list[dict[str, Any]],
    token: str,
) -> tuple[dict[str, Any], int, int]:
    """Resolve only a registered citation addressed by its rendered block position."""
    match = re.fullmatch(r"(\d+):(\d+)", token)
    if match is None:
        raise Study2WorkflowError("Invalid citation token.")
    block_index, citation_index = (int(value) for value in match.groups())
    try:
        source = blocks[block_index]["citations"][citation_index]
    except (IndexError, KeyError, TypeError) as exc:
        raise Study2WorkflowError("Unknown citation token.") from exc
    if not isinstance(source, dict):
        raise Study2WorkflowError("Invalid citation source.")
    identity = (
        str(source.get("citation", "")),
        str(source.get("document", "")),
        str(source.get("focus", "")),
    )
    registered = {
        (passage.citation, passage.document, passage.focus)
        for passage in session.cases.assessment_sources(reference)
    }
    if identity not in registered:
        raise Study2WorkflowError("Unregistered citation source.")
    return source, block_index, citation_index


def _citation_document_html(
    session: Study2Session,
    reference: str,
    source: dict[str, Any],
) -> str:
    """Return the complete registered source document with one focused passage."""
    document = str(source.get("document", ""))
    focus = str(source.get("focus", ""))
    if document == "cv":
        rendered = cv_document_html(
            session.cases.participant_case(reference),
            role=session.cases.role,
            company=session.cases.company,
            timeline=session.cases.timeline,
            focus=focus,
        )
    elif document in {"role", "policy"}:
        document_type, path = (
            ("Job description", ROLE_PATH)
            if document == "role"
            else ("Recruitment policy", POLICY_PATH)
        )
        rendered = reference_document_html(
            path.read_text(encoding="utf-8"),
            document_type=document_type,
            role=session.cases.role,
            company=session.cases.company,
            timeline=session.cases.timeline,
            focus=focus,
        )
    else:
        raise Study2WorkflowError("Unknown citation document.")
    if 'id="cited-passage"' not in rendered:
        raise Study2WorkflowError("The cited passage is unavailable in its document.")
    return citation_document_frame_html(rendered)


def _close_citation_document(
    reference: str,
    *,
    return_target: str,
    close_reason: str,
) -> None:
    """Close and time the currently displayed inline complete document."""
    drawer = st.session_state.get("_study2_citation_document")
    if not isinstance(drawer, dict):
        return
    source = drawer.get("source") or {}
    visit = drawer.get("visit") or {}
    closed_at = time.perf_counter()
    clicked_at = visit.get("clicked_at_monotonic")
    viewed_at = visit.get("viewed_at_monotonic")
    click_to_return_seconds = (
        round(closed_at - float(clicked_at), 3)
        if isinstance(clicked_at, (int, float))
        else None
    )
    dwell_seconds = (
        round(closed_at - float(viewed_at), 3)
        if isinstance(viewed_at, (int, float))
        else None
    )
    _log(
        "document_closed",
        reference=reference,
        phase="aided",
        component=str(source.get("document", "")),
        payload={
            "document_visit_id": visit.get("document_visit_id"),
            "document": source.get("document"),
            "origin": visit.get("origin"),
            "citation_id": source.get("citation"),
            "citation": _source_chip_label(source),
            "focus": source.get("focus"),
            "presentation": "inline_complete_document",
            "return_target": return_target,
            "close_reason": close_reason,
            "click_to_return_seconds": click_to_return_seconds,
            "dwell_seconds": dwell_seconds,
        },
    )
    st.session_state["_study2_citation_document"] = None


def _render_citation_document(session: Study2Session, reference: str) -> None:
    """Render a complete cited source in-page without leaving the assessment."""
    drawer = st.session_state.get("_study2_citation_document")
    if not isinstance(drawer, dict):
        return
    source = drawer.get("source") or {}
    visit = drawer.get("visit") or {}
    if not isinstance(source, dict) or not isinstance(visit, dict):
        st.session_state["_study2_citation_document"] = None
        return
    if not isinstance(visit.get("viewed_at_monotonic"), (int, float)):
        visit["viewed_at_monotonic"] = time.perf_counter()
        drawer["visit"] = visit
        st.session_state["_study2_citation_document"] = drawer
    citation = _source_chip_label(source)
    with st.container(border=True):
        st.markdown(f"**Source document · {citation}**")
        st.caption(
            "Complete source document. The passage linked by the citation is highlighted."
        )
        try:
            frame = _citation_document_html(session, reference, source)
        except Study2WorkflowError as exc:
            st.error(str(exc))
        else:
            st.iframe(frame, height=620, tab_index=0)
        if st.button(
            "Close source document",
            key=f"close_citation_document_{reference}",
            type="primary",
        ):
            _close_citation_document(
                reference,
                return_target="ai_assessment",
                close_reason="participant_closed",
            )
            _sync_github()
            st.rerun()


def _render_agent_output(session: Study2Session, reference: str) -> None:
    output = session.current_trial().get("agent_output")
    if not output:
        return
    with st.container(border=True):
        st.caption(str(output["speaker_label"]))
        blocks = output.get("message_blocks", [])
        if blocks and session.condition.explanation:
            click = render_recommendation_passage(
                blocks,
                anthropomorphic=session.condition.anthropomorphic,
                key=f"recommendation_passage_{reference}",
            )
            _handle_inline_citation(session, reference, blocks, click)
        elif blocks:
            st.markdown(" ".join(str(block["text"]).strip() for block in blocks))
        else:
            st.markdown(str(output["text"]))
    _render_citation_document(session, reference)


def _unaided(session: Study2Session, reference: str) -> None:
    st.info("Make your initial decision before requesting the AI assessment.")
    with st.form(f"unaided_{reference}"):
        st.subheader("Initial screening decision")
        decision = st.radio(
            "Initial screening decision",
            ["Advance candidate to human interview", "Reject candidate"],
            index=None,
            label_visibility="collapsed",
        )
        st.subheader("Rate your confidence about your decision")
        confidence = st.slider(
            "Rate your confidence about your decision",
            0,
            100,
            50,
            format="%d%%",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Lock initial decision", type="primary")
    if submitted:
        try:
            session.submit_unaided({"decision": decision, "confidence": confidence})
        except Study2WorkflowError as exc:
            st.error(str(exc))
            return
        _log(
            "unaided_decision_submitted",
            reference=reference,
            phase="unaided",
            component="unaided_form",
            payload=session.current_trial()["unaided"],
        )
        st.rerun()


def _agent(session: Study2Session, reference: str) -> None:
    st.info("Your initial decision is locked. You can now request the AI assessment.")
    preset = (
        HIGH_ANTHROPOMORPHISM
        if session.condition.anthropomorphic
        else LOW_ANTHROPOMORPHISM
    )
    if st.button(preset.request_label, type="primary", use_container_width=True):
        agent: Study2DecisionAgent = st.session_state["_study2_agent"]
        try:
            with st.spinner(preset.spinner_label):
                output = session.request_agent_assessment(agent)
        except (KeyError, RuntimeError, Study2WorkflowError, ValueError) as exc:
            st.error(str(exc))
            return
        _log(
            "agent_assessment_presented",
            reference=reference,
            phase="agent",
            component="agent_output",
            payload=output.audit_payload(),
        )
        st.rerun()


def _forcing(session: Study2Session, reference: str) -> None:
    st.warning(
        "Before the AI assessment is revealed, check the candidate's file "
        "against the job description's mandatory requirement, and enter what "
        "you find here."
    )
    if st.button(
        "Open complete job description",
        key=f"forcing_role_{reference}",
        use_container_width=True,
    ):
        visit = {
            "document_visit_id": uuid4().hex,
            "document": "role",
            "origin": "cognitive_forcing_prompt",
            "clicked_at_monotonic": time.perf_counter(),
        }
        st.session_state["_study2_document"] = "role"
        st.session_state["_study2_document_focus"] = ""
        st.session_state["_study2_active_source"] = None
        st.session_state["_study2_document_opened_at"] = visit["clicked_at_monotonic"]
        st.session_state["_study2_document_visit"] = visit
        _log(
            "document_opened",
            reference=reference,
            phase="forcing",
            component="role",
            payload={
                "document_visit_id": visit["document_visit_id"],
                "document": "role",
                "origin": visit["origin"],
                "focus_section": "",
            },
        )
        _sync_github()
        st.rerun()
    with st.form(f"forcing_{reference}"):
        mandatory_requirement = st.text_area(
            "Type or paste the strength from the CV that meets the job's "
            'mandatory requirement, or type "None" if none does.',
            max_chars=1000,
        )
        submitted = st.form_submit_button(
            "Confirm requirement and continue", type="primary"
        )
    if submitted:
        try:
            session.submit_forcing({"mandatory_requirement": mandatory_requirement})
        except Study2WorkflowError as exc:
            _log(
                "cognitive_forcing_attempt_failed",
                reference=reference,
                phase="forcing",
                component="forcing_form",
                payload={
                    "attempt_count": session.current_trial()["forcing"].get(
                        "attempt_count"
                    ),
                    "submitted_text": mandatory_requirement.strip(),
                    "is_correct": False,
                },
            )
            st.error(str(exc))
            return
        _log(
            "cognitive_forcing_submitted",
            reference=reference,
            phase="forcing",
            component="forcing_form",
            payload=session.current_trial()["forcing"],
        )
        st.rerun()


def _aided(session: Study2Session, reference: str) -> None:
    with st.form(f"aided_{reference}"):
        st.subheader("Final screening decision")
        decision = st.radio(
            "Final screening decision",
            ["Advance candidate to human interview", "Reject candidate"],
            index=None,
            label_visibility="collapsed",
        )
        st.subheader("Rate your confidence about your decision")
        confidence = st.slider(
            "Rate your confidence about your decision",
            0,
            100,
            50,
            format="%d%%",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Lock final decision", type="primary")
    if submitted:
        try:
            session.submit_aided({"decision": decision, "confidence": confidence})
        except Study2WorkflowError as exc:
            st.error(str(exc))
            return
        _close_citation_document(
            reference,
            return_target="final_decision",
            close_reason="decision_submitted",
        )
        _log(
            "aided_decision_submitted",
            reference=reference,
            phase="aided",
            component="aided_form",
            payload=session.current_trial()["aided"],
        )
        st.rerun()


def _recall(session: Study2Session, reference: str) -> None:
    with st.form(f"recall_{reference}"):
        response = st.text_area(
            "What information most influenced your final assessment?",
            max_chars=1500,
        )
        submitted = st.form_submit_button("Submit and continue", type="primary")
    if submitted:
        try:
            completed_reference = session.submit_evidence_recall(response)
        except Study2WorkflowError as exc:
            st.error(str(exc))
            return
        completed_trial = session.state["trials"][completed_reference]
        _log(
            "evidence_recall_submitted",
            reference=completed_reference,
            phase="recall",
            component="recall_form",
            payload=completed_trial["evidence_recall"],
        )
        if session.complete:
            _log(
                "session_completed",
                component="completion",
                payload={
                    "trial_count": 6,
                    "total_duration_seconds": session.state["total_duration_seconds"],
                },
            )
        _sync_github()
        st.rerun()


def _complete(session: Study2Session) -> None:
    st.success("All six candidate trials are complete.")
    return_url = _build_final_return(
        str(st.session_state.get("return_raw", "")),
        str(session.state["prolific_pid"]),
        str(session.state["session_id"]),
        str(session.state["condition_id"]),
    )
    if return_url:
        st.link_button("Return to survey", return_url, type="primary")
    else:
        st.info("Please return to your survey tab and continue.")


def run(locked_condition_id: str) -> None:
    st.set_page_config(
        page_title="Study 2 AI-assisted screening",
        layout="centered",
        initial_sidebar_state="expanded",
    )
    apply_anthrokit_theme(st)
    _read_qualtrics_params()
    _prolific_gate()
    _check_private_storage()
    try:
        _initialize(locked_condition_id)
    except (Study2WorkflowError, ValueError) as exc:
        st.error(f"Study link unavailable: {exc}")
        st.stop()
    session: Study2Session = st.session_state["_study2_session"]
    _header(session)
    _sidebar(session)
    if _document_view(session):
        return
    if session.state.get("introduction_step") != "complete":
        _introduction(session)
        return
    if session.complete:
        _complete(session)
        return
    reference = session.current_reference()
    if reference is None:
        raise Study2WorkflowError("There is no active candidate trial.")
    presented_key = f"_study2_presented_{reference}"
    if session.phase == "unaided" and not st.session_state.get(presented_key):
        _log(
            "profile_presented",
            reference=reference,
            phase="unaided",
            component="candidate",
            payload={
                "visible_cv_section_count": len(
                    session.cases.participant_case(reference).sections
                )
            },
        )
        st.session_state[presented_key] = True
    if session.phase == "unaided":
        _render_candidate(session, reference)
    else:
        _render_phase_heading(session, reference)
    if session.phase == "aided":
        _render_agent_output(session, reference)
    if session.phase == "unaided":
        _unaided(session, reference)
    elif session.phase == "agent":
        _agent(session, reference)
    elif session.phase == "forcing":
        _forcing(session, reference)
    elif session.phase == "aided":
        _aided(session, reference)
    elif session.phase == "recall":
        _recall(session, reference)
