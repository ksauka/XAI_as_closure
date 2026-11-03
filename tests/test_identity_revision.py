"""Checks for shared material v6 and a resolvable three-level JD citation."""
import json
import unittest

from xai_as_closure.cases import ArtifactVariant, CaseRepository, PROJECT_ROOT, ROLE_PATH
from xai_as_closure.document_renderer import reference_document_html
from xai_as_closure.study2_delivery import delivery_card


class IdentityRevisionTests(unittest.TestCase):
    def setUp(self):
        self.cases = CaseRepository()

    def test_new_clause_resolves_and_highlights_exactly_one_passage(self):
        for reference in self.cases.references:
            source = next(s for s in self.cases.assessment_sources(reference) if s.source_id == 'jd_4_2_1')
            self.assertEqual(source.citation, 'JD(4.2.1)')
            self.assertEqual(source.focus, '4.2.1')
            self.assertIn('shall be treated as established', source.text)
        document = reference_document_html(ROLE_PATH.read_text(), document_type='Job description',
            role=self.cases.role, company=self.cases.company, timeline=self.cases.timeline, focus='4.2.1')
        self.assertEqual(document.count('id="cited-passage"'), 1)
        self.assertIn('<h2>4.2.1 Confirming certification identity from the file</h2>', document)

    def test_all_visible_citation_sets_match_within_recommendation_side(self):
        for anthropomorphic in (False, True):
            for group in (('C-01', 'C-02', 'C-05'), ('C-03', 'C-04', 'C-06')):
                sets = [set(s.source_id for s in self.cases.artifact(r, ArtifactVariant(True, anthropomorphic)).sources) for r in group]
                self.assertEqual(sets[0], sets[1])
                self.assertEqual(sets[1], sets[2])
                self.assertTrue({'jd_4_2_1', 'pol_2_3'}.issubset(sets[0]))
                for reference, registered in zip(group, sets):
                    displayed = {s for block in delivery_card(reference, explanation=True, anthropomorphic=anthropomorphic).blocks for s in block.citation_ids}
                    self.assertEqual(displayed, registered)

    def test_revision_keeps_candidate_cvs_ground_truth_and_verdicts(self):
        prior = json.loads((PROJECT_ROOT / 'study_CHI/materials_review/archive/pre_identity_revision_2026-11-03/study_CHI/six_profiles_case_set.json').read_text())
        current = json.loads((PROJECT_ROOT / 'study_CHI/materials_review/archive/pre_c05_dual_expiry_2026-11-03/study_CHI/six_profiles_case_set.json').read_text())
        for before, after in zip(prior['profiles'], current['profiles']):
            self.assertEqual(before['reference'], after['reference'])
            self.assertEqual(before['candidate_cv'], after['candidate_cv'])
            self.assertEqual(before['ground_truth'], after['ground_truth'])
            self.assertEqual(before['fixed_assessment']['recommendation'], after['fixed_assessment']['recommendation'])
        c06 = self.cases.participant_case('C-06')
        certificate = next(s for s in c06.sections if s.id == 'cv_certifications')
        self.assertIn('- AIGP —', certificate.text)
        self.assertNotIn('IAPP', certificate.text)

    def test_currency_rule_has_no_competing_identity_rule(self):
        title, text = self.cases._policy_clauses['2.3']
        self.assertEqual(title, '2.3 Whole-File and Currency Rule')
        self.assertNotIn('identity', text.lower())
        self.assertIn('expired', text.lower())
        self.assertNotIn('Section 2.3 resolves the identity', self.cases._policy_clauses['4.1'][1])

    def test_both_studies_share_the_revised_set_and_validation_is_pending(self):
        from xai_as_closure import study1_app, study2_app
        self.assertEqual(study1_app.CaseRepository().case_set_id, 'ai_governance_lead_six_profiles_v8')
        self.assertEqual(study1_app.CaseRepository().path, study2_app.CaseRepository().path)
        self.assertEqual(study1_app.ROLE_PATH, study2_app.ROLE_PATH)
        self.assertEqual(study1_app.POLICY_PATH, study2_app.POLICY_PATH)
        freeze = json.loads((PROJECT_ROOT / 'study_CHI/STUDY2_MATERIAL_FREEZE.json').read_text())
        self.assertEqual(freeze['validation_status'], 'pending_focused_assessment')
        self.assertFalse(freeze['ready_for_confirmatory_recruitment'])


if __name__ == '__main__':
    unittest.main()
