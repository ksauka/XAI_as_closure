"""Round-2 material identity and private checkpoint recovery."""
from __future__ import annotations

import base64
import json
import re

import requests

from .cases import PROJECT_ROOT, CaseRepository, material_manifest
from .storage import SessionStore
from .study1 import FOCUSED_ROUND, Study1Session, WorkflowError

ROUND2_FREEZE = PROJECT_ROOT / 'study_CHI/STUDY1_ROUND2_MATERIALS.json'


ARCHIVED_ROUND2_CASES = PROJECT_ROOT / 'study_CHI/materials_review/archive/pre_c05_dual_expiry_2026-11-03/study_CHI/six_profiles_case_set.json'
FOCUSED_FREEZE = PROJECT_ROOT / 'study_CHI/STUDY1_FOCUSED_MATERIALS.json'


def validation_cases(validation_round: str) -> CaseRepository:
    return CaseRepository(ARCHIVED_ROUND2_CASES) if validation_round == 'round2' else CaseRepository()


def check_round2_materials(validation_round: str = 'round2') -> None:
    try:
        path = FOCUSED_FREEZE if validation_round == FOCUSED_ROUND else ROUND2_FREEZE
        expected = json.loads(path.read_text(encoding='utf-8'))
        cases = validation_cases(validation_round)
        current = material_manifest(cases.path)
        expected_instrument = 'study1-instrument-v8' if validation_round == FOCUSED_ROUND else 'study1-instrument-v7'
        if (expected['case_set_id'] != cases.case_set_id
                or expected['material_manifest_sha256'] != current['manifest_sha256']
                or expected['validation_round'] != validation_round
                or expected['instrument_version'] != expected_instrument):
            raise ValueError('Validation material identity differs.')
    except (OSError, ValueError, KeyError) as exc:
        raise WorkflowError('The study materials could not be verified. Please contact the researcher.') from exc


def round2_archive_path(session_id: str, validation_round: str = 'round2') -> str:
    if not re.fullmatch(r's1_[0-9a-f]{24}', session_id) or validation_round not in {'round2', FOCUSED_ROUND}:
        raise WorkflowError('Invalid saved-session identifier or validation round.')
    return f'sessions/xai_as_closure/study1/{validation_round}/{session_id}.json'


def recover_round2_checkpoint(*, store: SessionStore, cases: CaseRepository,
                              repo: str, token: str, session_id: str,
                              participant_id: str, linkage_hash: str, recruitment_source: str = "prolific", validation_round: str = "round2") -> dict | None:
    """A failed lookup is not treated as permission to overwrite a checkpoint."""
    path = round2_archive_path(session_id, validation_round)
    try:
        response = requests.get(
            f'https://api.github.com/repos/{repo}/contents/{path}',
            headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'},
            timeout=15,
        )
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise ValueError('Checkpoint lookup failed.')
        payload = json.loads(base64.b64decode(response.json()['content'], validate=False))
        if (payload.get('session_id') != session_id
                or payload.get('participant_id') != participant_id
                or payload.get('linkage_hash') != linkage_hash
                or payload.get('recruitment_source', 'prolific') != recruitment_source
                or payload.get('validation_round') != validation_round
                or payload.get('material_manifest', {}).get('manifest_sha256') != cases.material_manifest['manifest_sha256']):
            raise ValueError('Checkpoint identity differs.')
        events = payload['events']
        state = {key: value for key, value in payload.items()
                 if key not in {'events', 'participant_id', 'prolific_pid', 'saved_at_utc'}}
        Study1Session.restore(state, cases)
        store.restore_archive(state, events)
        return state
    except (requests.RequestException, OSError, ValueError, KeyError, TypeError) as exc:
        raise WorkflowError('Your saved session could not be checked. Please retry or contact the researcher.') from exc
