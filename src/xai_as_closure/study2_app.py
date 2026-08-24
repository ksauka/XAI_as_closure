"""Streamlit application for the CHI 2027 six-profile Study 2 experiment."""

from __future__ import annotations

import hashlib
import os
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from .cases import POLICY_PATH, ROLE_PATH, CaseRepository
from .conditions import get_study2_condition
from .decision_agent import Study2DecisionAgent
from .github_saver import test_github_connection
from .logger import DEFAULT_LOG_DIR, EventLogger, load_state, restored_logger
from .study2 import Study2Session, Study2WorkflowError
from .study2_delivery import (
    CHALLENGE_LABELS,
    HIGH_ANTHROPOMORPHISM,
    LOW_ANTHROPOMORPHISM,
)
from .theme import apply_anthrokit_theme, show_study_banner


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
    session_id = hashlib.sha256(participant_id.strip().encode("utf-8")).hexdigest()
    cases = CaseRepository()
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
    if view in {"role", "policy"}:
        title, path = (
            ("AI Governance Lead job description", ROLE_PATH)
            if view == "role"
            else ("Recruitment policy", POLICY_PATH)
        )
        st.subheader(title)
        if view == "role" and st.session_state.get("_study2_document_focus") == "4.1":
            st.caption(
                "Complete job description · current focus: Section 4.1 Mandatory Certification"
            )
        st.markdown(path.read_text(encoding="utf-8"))
    elif view == "source":
        source = st.session_state.get("_study2_active_source", {})
        st.subheader(str(source.get("label", "Evidence passage")))
        st.caption("Highlighted passage used in the AI assessment")
        st.info(f"**{source.get('heading', '')}**\n\n{source.get('text', '')}")
        st.markdown("#### Complete source document")
        label = str(source.get("label", ""))
        if label.startswith("Job description"):
            st.markdown(ROLE_PATH.read_text(encoding="utf-8"))
        elif label.startswith("Recruitment policy"):
            st.markdown(POLICY_PATH.read_text(encoding="utf-8"))
        elif label.startswith("Candidate "):
            case = session.cases.participant_case(
                session.current_reference() or str(source.get("reference", ""))
            )
            for section in case.sections:
                if section.heading == source.get("heading"):
                    st.warning(f"**{section.heading}**\n\n{section.text}")
                else:
                    st.markdown(f"**{section.heading}**")
                    st.write(section.text)
    back_label = (
        "Back to candidate"
        if session.state.get("introduction_step") == "complete"
        else "Back to study introduction"
    )
    if st.button(back_label, type="primary"):
        reference = (
            session.current_reference()
            if session.state.get("introduction_step") == "complete"
            else None
        )
        opened_at = st.session_state.get("_study2_document_opened_at")
        dwell_seconds = (
            round(time.perf_counter() - float(opened_at), 3)
            if isinstance(opened_at, (int, float))
            else None
        )
        active_source = st.session_state.get("_study2_active_source") or {}
        _log(
            "document_closed",
            reference=reference,
            component=view,
            payload={
                "document": view,
                "source_label": active_source.get("label"),
                "dwell_seconds": dwell_seconds,
            },
        )
        st.session_state["_study2_document"] = None
        st.session_state["_study2_document_focus"] = None
        st.session_state["_study2_active_source"] = None
        st.session_state["_study2_document_opened_at"] = None
        st.rerun()
    return True


def _sidebar(session: Study2Session) -> None:
    active_reference = (
        session.current_reference()
        if session.state.get("introduction_step") == "complete"
        else None
    )
    with st.sidebar:
        st.subheader("Reference documents")
        st.caption("Available throughout every candidate trial.")
        if st.button("Open job description", use_container_width=True):
            st.session_state["_study2_document"] = "role"
            st.session_state["_study2_document_focus"] = None
            st.session_state["_study2_document_opened_at"] = time.perf_counter()
            _log(
                "document_opened",
                reference=active_reference,
                component="role",
            )
            st.rerun()
        if st.button("Open recruitment policy", use_container_width=True):
            st.session_state["_study2_document"] = "policy"
            st.session_state["_study2_document_opened_at"] = time.perf_counter()
            _log(
                "document_opened",
                reference=active_reference,
                component="policy",
            )
            st.rerun()
        st.divider()
        st.caption("The AI is advisory. You make every final screening decision.")
        if st.session_state.get("_study2_pilot"):
            st.warning(f"Pilot mode · {session.condition.condition_id}")


def _introduction(session: Study2Session) -> None:
    """Render the neutral HAI introduction before the first candidate trial."""
    step = str(session.state["introduction_step"])
    presented_key = f"_study2_introduction_presented_{step}"
    if not st.session_state.get(presented_key):
        _log(
            "introduction_presented",
            phase="introduction",
            component=step,
            payload={"step": step},
        )
        st.session_state[presented_key] = True
    if step == "instructions":
        st.header("AI-assisted screening task")
        st.info(
            "This is a fictional research scenario. Do not use this assistant "
            "for real employment decisions."
        )
        st.markdown(
            "You will screen six candidates for the fictional AI Governance Lead "
            "role. For each candidate, you will first make an unaided decision. "
            "The AI will then provide an advisory assessment before you make your "
            "final decision. **The final screening decision is always yours.**"
        )
        st.markdown(
            "The complete job description and recruitment policy remain available "
            "from the sidebar throughout the task."
        )
        button_label = "Continue to role description"
    elif step == "role":
        st.header("Role description")
        st.markdown(ROLE_PATH.read_text(encoding="utf-8"))
        button_label = "Continue to recruitment policy"
    elif step == "policy":
        st.header("Recruitment policy")
        st.markdown(POLICY_PATH.read_text(encoding="utf-8"))
        button_label = "Begin candidate screening"
    else:
        return
    if st.button(button_label, type="primary", use_container_width=True):
        previous_step = step
        try:
            next_step = session.advance_introduction()
        except Study2WorkflowError as exc:
            st.error(str(exc))
            return
        _log(
            "introduction_advanced",
            phase="introduction",
            component=previous_step,
            payload={"from_step": previous_step, "to_step": next_step},
        )
        st.rerun()


def _source_chip_label(source: dict[str, Any]) -> str:
    """Return the compact citation labels used by the original HAI interface."""
    label = str(source.get("label", ""))
    section = re.search(r"Section (\d+\.\d+)", label)
    if label.startswith("Job description"):
        return f"[Role §{section.group(1)}]" if section else "[Role]"
    if label.startswith("Recruitment policy"):
        return f"[Policy §{section.group(1)}]" if section else "[Policy]"
    heading = str(source.get("heading", "CV evidence"))
    return f"[CV · {heading}]"


def _render_candidate(session: Study2Session, reference: str) -> None:
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


def _render_agent_output(session: Study2Session, reference: str) -> None:
    output = session.current_trial().get("agent_output")
    if not output:
        return
    with st.chat_message("assistant"):
        st.caption(str(output["speaker_label"]))
        st.markdown(str(output["text"]))
        sources = output.get("visible_sources", [])
        if sources:
            st.markdown("**Inspect evidence used**")
            columns = st.columns(min(len(sources), 3))
            for index, source in enumerate(sources):
                with columns[index % len(columns)]:
                    if st.button(
                        _source_chip_label(source),
                        key=f"source_{reference}_{index}",
                        help=str(source["label"]),
                        use_container_width=True,
                    ):
                        st.session_state["_study2_active_source"] = source
                        st.session_state["_study2_document"] = "source"
                        st.session_state["_study2_document_opened_at"] = (
                            time.perf_counter()
                        )
                        _log(
                            "citation_clicked",
                            reference=reference,
                            component="source_passage",
                            payload={
                                "citation_id": source["label"],
                                "document": _source_chip_label(source),
                                "source_label": source["label"],
                                "source_index": index,
                            },
                        )
                        st.rerun()
        for challenge in output.get("challenge_history", []):
            st.divider()
            st.markdown(f"**{challenge['prompt_label']}**")
            st.write(str(challenge["response_text"]))


def _unaided(session: Study2Session, reference: str) -> None:
    st.info("Make your initial decision before requesting the AI assessment.")
    with st.form(f"unaided_{reference}"):
        decision = st.radio(
            "Initial screening decision",
            ["Advance candidate to human interview", "Reject candidate"],
            index=None,
        )
        confidence = st.slider("Initial confidence", 0, 100, 50, format="%d%%")
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
        "Before the AI assessment is revealed, consult the job description and "
        "re-enter its mandatory certification requirement."
    )
    if st.button(
        "Open complete job description",
        key=f"forcing_role_{reference}",
        use_container_width=True,
    ):
        st.session_state["_study2_document"] = "role"
        st.session_state["_study2_document_focus"] = "4.1"
        st.session_state["_study2_document_opened_at"] = time.perf_counter()
        _log(
            "document_opened",
            reference=reference,
            phase="forcing",
            component="role",
            payload={"document": "role", "focus_section": "4.1"},
        )
        st.rerun()
    with st.form(f"forcing_{reference}"):
        mandatory_requirement = st.text_area(
            "Type or paste the mandatory certification requirement from the job description.",
            max_chars=1000,
        )
        submitted = st.form_submit_button(
            "Confirm requirement and continue", type="primary"
        )
    if submitted:
        try:
            session.submit_forcing({"mandatory_requirement": mandatory_requirement})
        except Study2WorkflowError as exc:
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
    preset = (
        HIGH_ANTHROPOMORPHISM
        if session.condition.anthropomorphic
        else LOW_ANTHROPOMORPHISM
    )
    with st.expander(preset.examination_intro):
        kind = st.selectbox(
            "Select an area to examine",
            options=list(CHALLENGE_LABELS),
            format_func=lambda value: CHALLENGE_LABELS[value],
            index=None,
            key=f"challenge_kind_{reference}",
        )
        if st.button(
            preset.examination_button,
            key=f"challenge_submit_{reference}",
            use_container_width=True,
        ):
            if kind is None:
                st.info("Select an area before continuing.")
            else:
                agent: Study2DecisionAgent = st.session_state["_study2_agent"]
                try:
                    response = session.examine_agent_assessment(agent, kind)
                except (KeyError, RuntimeError, Study2WorkflowError, ValueError) as exc:
                    st.error(str(exc))
                else:
                    _log(
                        "agent_evidence_examined",
                        reference=reference,
                        phase="aided",
                        component="agent_challenge",
                        payload=response,
                    )
                    st.rerun()
    with st.form(f"aided_{reference}"):
        decision = st.radio(
            "Final screening decision",
            ["Advance candidate to human interview", "Reject candidate"],
            index=None,
        )
        confidence = st.slider("Final confidence", 0, 100, 50, format="%d%%")
        submitted = st.form_submit_button("Lock final decision", type="primary")
    if submitted:
        try:
            session.submit_aided({"decision": decision, "confidence": confidence})
        except Study2WorkflowError as exc:
            st.error(str(exc))
            return
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
        st.info("You may now return to the survey tab.")


def run(locked_condition_id: str) -> None:
    st.set_page_config(
        page_title="Study 2 AI-assisted screening",
        page_icon=":material/smart_toy:",
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
    if not st.session_state.get(presented_key):
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
    _render_candidate(session, reference)
    if session.phase in {"aided", "recall"}:
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
