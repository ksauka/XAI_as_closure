"""Verify that trimming never changes a rule, recommendation or citation target."""
import json
from pathlib import Path
import unittest
from xai_as_closure.cases import PROJECT_ROOT, CaseRepository, ArtifactVariant, _clauses
from xai_as_closure.study1 import Study1Session, FOCUSED_ROUND, LEGACY_FOCUSED_ROUND, instrument_version
from xai_as_closure.study1_round2_support import validation_cases, check_round2_materials, round2_archive_path

ARCHIVE = PROJECT_ROOT / 'study_CHI/materials_review/archive/pre_reading_trim_2026-11-03/study_CHI'

class TrimTests(unittest.TestCase):
    def test_only_uncited_sections_removed_and_all_kept_clauses_unchanged(self):
        for name, retained in [('job_description.md', 7), ('recruitment_policy.md', 5)]:
            before, after = _clauses(ARCHIVE/name), _clauses(PROJECT_ROOT/'study_CHI'/name)
            self.assertTrue(after)
            self.assertEqual(after, {k:v for k,v in before.items() if int(k.split('.')[0]) <= retained})

    def test_all_profiles_outputs_and_cited_passages_match_the_previous_version(self):
        old = CaseRepository(ARCHIVE/'six_profiles_case_set.json')
        new = CaseRepository()
        a, b = json.loads(old.path.read_text()), json.loads(new.path.read_text())
        a.pop('case_set_id'); b.pop('case_set_id')
        self.assertEqual(a, b)
        count = 0
        for reference in new.references:
            for anthropomorphic in (False, True):
                before = old.artifact(reference, ArtifactVariant(True, anthropomorphic))
                after = new.artifact(reference, ArtifactVariant(True, anthropomorphic))
                self.assertEqual(before, after)
                count += len(after.sources)
        self.assertEqual(count, 156)  # (3*12 + 3*14) in each delivery register

    def test_long_document_round_can_still_be_restored_separately(self):
        old = validation_cases(LEGACY_FOCUSED_ROUND)
        new = validation_cases(FOCUSED_ROUND)
        check_round2_materials(LEGACY_FOCUSED_ROUND)
        check_round2_materials(FOCUSED_ROUND)
        self.assertNotEqual(old.case_set_id, new.case_set_id)
        self.assertNotEqual(old.material_manifest, new.material_manifest)
        self.assertNotEqual(instrument_version(LEGACY_FOCUSED_ROUND), instrument_version(FOCUSED_ROUND))
        sid = 's1_'+'a'*24
        self.assertNotEqual(round2_archive_path(sid,LEGACY_FOCUSED_ROUND), round2_archive_path(sid,FOCUSED_ROUND))
        session = Study1Session.create(session_id=sid,linkage_hash='a'*64,seed='old',cases=old,validation_round=LEGACY_FOCUSED_ROUND)
        self.assertEqual(Study1Session.restore(session.state,old).state, session.state)

if __name__ == '__main__':
    unittest.main()
