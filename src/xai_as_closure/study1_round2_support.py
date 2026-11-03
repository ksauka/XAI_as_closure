"""Round-2 material identity and private archive paths."""
from __future__ import annotations

import json
import re

from .background_save import ARCHIVE_ID_PATTERN
from .cases import PROJECT_ROOT, CaseRepository, material_manifest
from .study1 import (
    FOCUSED_ROUND,
    LEGACY_FOCUSED_ROUND,
    WorkflowError,
    instrument_version,
)

ROUND2_FREEZE = PROJECT_ROOT / 'study_CHI/STUDY1_ROUND2_MATERIALS.json'


ARCHIVED_ROUND2_CASES = PROJECT_ROOT / 'study_CHI/materials_review/archive/pre_c05_dual_expiry_2026-11-03/study_CHI/six_profiles_case_set.json'
FOCUSED_FREEZE = PROJECT_ROOT / 'study_CHI/STUDY1_FOCUSED_MATERIALS.json'


def validation_cases(validation_round: str) -> CaseRepository:
    if validation_round == 'round2':
        return CaseRepository(ARCHIVED_ROUND2_CASES)
    if validation_round == LEGACY_FOCUSED_ROUND:
        return CaseRepository(PROJECT_ROOT / 'study_CHI/materials_review/archive/pre_reading_trim_2026-11-03/study_CHI/six_profiles_case_set.json')
    return CaseRepository()


def check_round2_materials(validation_round: str = 'round2') -> None:
    try:
        path = FOCUSED_FREEZE if validation_round == FOCUSED_ROUND else ROUND2_FREEZE
        if validation_round == LEGACY_FOCUSED_ROUND:
            path = PROJECT_ROOT / 'study_CHI/materials_review/archive/pre_reading_trim_2026-11-03/study_CHI/STUDY1_FOCUSED_MATERIALS.json'
        expected = json.loads(path.read_text(encoding='utf-8'))
        cases = validation_cases(validation_round)
        current = material_manifest(cases.path)
        expected_instrument = instrument_version(validation_round)
        if (expected['case_set_id'] != cases.case_set_id
                or expected['material_manifest_sha256'] != current['manifest_sha256']
                or expected['validation_round'] != validation_round
                or expected['instrument_version'] != expected_instrument):
            raise ValueError('Validation material identity differs.')
    except (OSError, ValueError, KeyError) as exc:
        raise WorkflowError('The study materials could not be verified. Please contact the researcher.') from exc


def round2_archive_path(session_id: str, validation_round: str = 'round2', archive_id: str | None = None) -> str:
    """Each new session writes its own file; sessions saved before archive IDs keep their path."""
    if not re.fullmatch(r's1_[0-9a-f]{24}', session_id) or validation_round not in {'round2', LEGACY_FOCUSED_ROUND, FOCUSED_ROUND}:
        raise WorkflowError('Invalid saved-session identifier or validation round.')
    if archive_id is not None and not ARCHIVE_ID_PATTERN.fullmatch(archive_id):
        raise WorkflowError('Invalid saved-session archive identifier.')
    name = f'{session_id}_{archive_id}' if archive_id else session_id
    return f'sessions/xai_as_closure/study1/{validation_round}/{name}.json'
