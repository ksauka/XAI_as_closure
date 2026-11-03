"""Participant linkage for Prolific and independently recruited experts."""
from __future__ import annotations

from dataclasses import dataclass
import re

from .study1 import WorkflowError


@dataclass(frozen=True)
class ParticipantLink:
    participant_id: str
    recruitment_source: str

    @property
    def hash_input(self) -> str:
        # Keep existing Prolific session identifiers recoverable. Independent
        # codes use a separate namespace, even if a code resembles a Prolific ID.
        if self.recruitment_source == "researcher":
            return "researcher\0" + self.participant_id
        return self.participant_id


def validate_participant(value: str, source: str) -> ParticipantLink:
    value = value.strip()
    if "${" in value:
        raise WorkflowError(
            "The link contains an unfilled Qualtrics field. Open the task from "
            "the survey after its participant ID or participant code has been filled in."
        )
    if source == "prolific":
        if not re.fullmatch(r"[0-9a-fA-F]{24}", value):
            raise WorkflowError(
                "Enter the 24-character participant ID supplied by Prolific. "
                "If you were recruited outside Prolific, use the researcher-issued participant-code option."
            )
    elif source == "researcher":
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{2,63}", value):
            raise WorkflowError(
                "Enter the participant code supplied by the researcher: 3–64 letters, "
                "numbers, hyphens or underscores. Do not enter a name or email address."
            )
    else:
        raise WorkflowError("Unknown participant-link type.")
    return ParticipantLink(value, source)


def read_participant_link(*, prolific_pid: str = "", participant_code: str = "",
                          legacy_pid: str = "") -> ParticipantLink | None:
    prolific_pid, participant_code, legacy_pid = (
        prolific_pid.strip(), participant_code.strip(), legacy_pid.strip()
    )
    if prolific_pid and legacy_pid and prolific_pid != legacy_pid:
        raise WorkflowError("The study link contains conflicting participant IDs.")
    platform_id = prolific_pid or legacy_pid
    if platform_id and participant_code:
        raise WorkflowError("Use either a Prolific ID or a researcher-issued participant code in the study link.")
    if platform_id:
        return validate_participant(platform_id, "prolific")
    if participant_code:
        return validate_participant(participant_code, "researcher")
    return None
