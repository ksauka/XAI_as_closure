"""Focused revalidation, material provenance and historical-record isolation."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest
from xai_as_closure.cases import CaseRepository, PROJECT_ROOT
from xai_as_closure.storage import SessionStore
from xai_as_closure.study1 import FOCUSED_ROUND, Study1Session, WorkflowError
from xai_as_closure.study1_round2_support import check_round2_materials, round2_archive_path, validation_cases

SID='s1_'+'c'*24
LINK='d'*64
PID='e'*24

def judgment():
    return dict(decision='Reject candidate', hard_criterion_judgment='No',confidence=65,decisive_evidence='Synthetic test only')

def review():
    return dict(professional_disagreement='No', disputed_profiles=[],
                disputed_profiles_reason='', materials_feedback='')

class FocusedValidationTests(unittest.TestCase):
    def session(self):
        return Study1Session.create(session_id=SID,linkage_hash=LINK,seed='focused',cases=CaseRepository(),validation_round=FOCUSED_ROUND)

    def test_only_two_profiles_randomised_without_removing_study2_cases(self):
        orders=set()
        for seed in map(str,range(20)):
            session=Study1Session.create(session_id=SID,linkage_hash=LINK,seed=seed,cases=CaseRepository(),validation_round=FOCUSED_ROUND)
            self.assertEqual(set(session.state['profile_order']),{'C-05','C-06'})
            self.assertEqual(session.state['instrument_version'],'study1-instrument-v9')
            orders.add(tuple(session.state['profile_order']))
        self.assertEqual(len(orders),2)
        self.assertEqual(len(CaseRepository().references),6)
        check_round2_materials(FOCUSED_ROUND)
        check_round2_materials('round2')

    def test_current_shared_profile_differs_only_in_C05_membership_cv(self):
        old=validation_cases('round2'); current=CaseRepository()
        before=json.loads(old.path.read_text())['profiles']; after=json.loads(current.path.read_text())['profiles']
        self.assertEqual(old.case_set_id,'ai_governance_lead_six_profiles_v6')
        self.assertEqual(current.case_set_id,'ai_governance_lead_six_profiles_v8')
        for a,b in zip(before,after):
            self.assertEqual(a['ground_truth'],b['ground_truth'])
            self.assertEqual(a['fixed_assessment']['recommendation'],b['fixed_assessment']['recommendation'])
            for x,y in zip(a['candidate_cv']['sections'],b['candidate_cv']['sections']):
                if a['reference']=='C-05' and x['id']=='cv_memberships':
                    self.assertIn('31 December 2026',x['text']); self.assertIn('31 May 2026',y['text'])
                else: self.assertEqual(x,y)

    def test_two_judgments_required_and_unshown_disputes_rejected(self):
        session=self.session()
        session.submit_judgment(judgment())
        self.assertEqual(session.phase,'screening')
        session.submit_judgment(judgment())
        self.assertEqual(session.phase,'post_study')
        with self.assertRaises(WorkflowError): session.submit_judgment(judgment())
        bad=dict(review(),professional_disagreement='Yes',disputed_profiles=['C-01'],disputed_profiles_reason='Not shown')
        with self.assertRaises(WorkflowError): session.submit_post_study(bad)
        session.submit_post_study(review())
        self.assertTrue(Study1Session.restore(session.state,CaseRepository()).complete)
        corrupt=deepcopy(session.state); corrupt['profile_order'].append('C-01')
        with self.assertRaises(WorkflowError): Study1Session.restore(corrupt,CaseRepository())

    def test_focused_round_has_its_own_archive_namespace(self):
        self.assertNotEqual(round2_archive_path(SID),round2_archive_path(SID,FOCUSED_ROUND))

    def test_local_app_two_case_journey_resume_review_and_completion(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'STUDY1_LOCAL_PREVIEW':'1',
                'STUDY1_PREVIEW_DATA_ROOT':directory,'STUDY1_PREVIEW_ID':'LOCAL_FOCUSED_TEST'}),\
                patch('xai_as_closure.study1_app.save_to_github') as save,\
                patch('xai_as_closure.background_save.test_github_connection') as connect:
            path=str(PROJECT_ROOT/'apps/study1_validation_v2.py')
            app=AppTest.from_file(path,default_timeout=15).run()
            self.assertFalse(app.exception)
            self.assertTrue(any('focused expert assessment' in c.value for c in app.caption))
            for i in range(2):
                s=app.session_state['_study1_session']; ref=s.current_reference()
                self.assertIn(ref,{'C-05','C-06'})
                app.radio(key=f'screening_decision_{ref}').set_value('Reject candidate')
                app.radio(key=f'screening_hard_criterion_{ref}').set_value('No')
                app.text_input(key=f'screening_evidence_{ref}').set_value('Synthetic local check')
                next(b for b in app.button if b.label=='Lock and submit judgment').click().run()
                self.assertFalse(app.exception)
            resumed=AppTest.from_file(path,default_timeout=15).run()
            self.assertEqual(resumed.session_state['_study1_session'].phase,'post_study')
            self.assertEqual(set(resumed.multiselect(key='post_study_disputed_profiles').options),{'C-05','C-06'})
            for key,value in review().items():
                if key in ('disputed_profiles','disputed_profiles_reason','materials_feedback'): continue
                resumed.radio(key='post_study_'+key).set_value(value)
            next(b for b in resumed.button if b.label=='Submit final materials review').click().run()
            self.assertFalse(resumed.exception)
            self.assertTrue(resumed.session_state['_study1_session'].complete)
            self.assertTrue(any('All 2 independent' in m.value for m in resumed.markdown))
            session=resumed.session_state['_study1_session']
            events=SessionStore(directory).read_events(session.state['session_id'])
            self.assertEqual(sum(e['event_type']=='candidate_judgment_submitted' for e in events),2)
            self.assertEqual([e['payload']['judgment_count'] for e in events if e['event_type']=='session_completed'],[2])
            self.assertTrue(all(e['validation_round']==FOCUSED_ROUND for e in events))
            save.assert_not_called(); connect.assert_not_called()

    def test_production_save_uses_focused_path_and_new_material_hash(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'STUDY1_LOCAL_PREVIEW':'0'}):
            def secret(key,default=''):
                return {'GITHUB_REPO':'test/private','GITHUB_TOKEN':'test-only','STUDY1_FOCUSED_DATA_ROOT':directory}.get(key,default)
            with patch('xai_as_closure.study1_app._secret',side_effect=secret),\
                 patch('xai_as_closure.background_save.test_github_connection',return_value=(True,'ok')),\
                 patch('requests.get',return_value=Mock(status_code=404)),\
                 patch('xai_as_closure.study1_app.save_to_github',return_value=(True,'ok')) as save:
                app=AppTest.from_file(str(PROJECT_ROOT/'apps/study1_validation_v2.py'),default_timeout=15)
                app.query_params['PROLIFIC_PID']=PID; app.run()
                self.assertFalse(app.exception)
                job = app.session_state.filtered_state.get('_study1_backup_job')
                if job:
                    job[0].result(timeout=3)
                self.assertIn('/round2_focused_trimmed/',save.call_args.args[1])
                payload=json.loads(save.call_args.args[2])
                self.assertEqual(payload['material_manifest'],CaseRepository().material_manifest)
                self.assertEqual(set(payload['profile_order']),{'C-05','C-06'})
                self.assertFalse(payload['is_preview'])

if __name__=='__main__': unittest.main()
