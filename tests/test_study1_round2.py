"""Second-round isolation, recovery and complete participant-flow checks."""
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest
from xai_as_closure.cases import CaseRepository, PROJECT_ROOT, material_manifest
from xai_as_closure.storage import SessionStore
from xai_as_closure.study1 import Study1Session, WorkflowError
from xai_as_closure.study1_round2_support import check_round2_materials, recover_round2_checkpoint, round2_archive_path, validation_cases

SID = 's1_' + 'a' * 24
PID = 'b' * 24
LINK = 'c' * 64


class Round2Tests(unittest.TestCase):
    def make_session(self, round='round2'):
        return Study1Session.create(session_id=SID, linkage_hash=LINK,
            seed='round2-check', cases=validation_cases("round2"), validation_round=round)

    def test_instrument_separation_and_material_lock(self):
        self.assertEqual(self.make_session().state['instrument_version'], 'study1-instrument-v7')
        self.assertEqual(self.make_session('initial').state['instrument_version'], 'study1-instrument-v6')
        state = self.make_session().state
        state['instrument_version'] = 'study1-instrument-v6'
        with self.assertRaises(WorkflowError):
            Study1Session.restore(state, validation_cases("round2"))
        check_round2_materials()
        with patch('xai_as_closure.study1_round2_support.material_manifest', return_value={'manifest_sha256': 'wrong'}):
            with self.assertRaises(WorkflowError):
                check_round2_materials()

    def test_recovery_preserves_events_and_rejects_identity_mismatch(self):
        with tempfile.TemporaryDirectory() as original, tempfile.TemporaryDirectory() as restored:
            session = self.make_session()
            first = SessionStore(original)
            first.append_event(session.state, 'session_created', phase='screening')
            payload = dict(session.state, participant_id=PID, events=first.read_events(SID),
                           material_manifest=session.cases.material_manifest)
            response = Mock(status_code=200)
            response.json.return_value = {'content': base64.b64encode(json.dumps(payload).encode()).decode()}
            kwargs = dict(store=SessionStore(restored), cases=validation_cases("round2"), repo='test/private',
                          token='test-only', session_id=SID, participant_id=PID, linkage_hash=LINK)
            with patch('xai_as_closure.study1_round2_support.requests.get', return_value=response):
                state = recover_round2_checkpoint(**kwargs)
                self.assertEqual(state['profile_order'], session.state['profile_order'])
                self.assertEqual(kwargs['store'].read_events(SID), payload['events'])
                payload['participant_id'] = 'wrong'
                response.json.return_value = {'content': base64.b64encode(json.dumps(payload).encode()).decode()}
                with self.assertRaises(WorkflowError):
                    recover_round2_checkpoint(**kwargs)

    def test_failed_lookup_cannot_silently_create_fresh_session(self):
        with tempfile.TemporaryDirectory() as directory:
            kwargs = dict(store=SessionStore(directory), cases=validation_cases("round2"), repo='test/private',
                          token='test-only', session_id=SID, participant_id=PID, linkage_hash=LINK)
            with patch('xai_as_closure.study1_round2_support.requests.get', return_value=Mock(status_code=503)):
                with self.assertRaises(WorkflowError):
                    recover_round2_checkpoint(**kwargs)
            with patch('xai_as_closure.study1_round2_support.requests.get', return_value=Mock(status_code=404)):
                self.assertIsNone(recover_round2_checkpoint(**kwargs))

    def test_incomplete_or_reordered_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SessionStore(directory)
            session = self.make_session()
            store.append_event(session.state, 'session_created', phase='screening')
            events = store.read_events(SID)
            events[0]['event_sequence'] = 2
            with self.assertRaises(ValueError):
                store.restore_archive(session.state, events)
        with self.assertRaises(WorkflowError):
            round2_archive_path('../../unsafe')

    def test_preview_full_journey_and_reload_never_writes_remote(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
                'STUDY1_LOCAL_PREVIEW': '1', 'STUDY1_PREVIEW_DATA_ROOT': directory,
                'STUDY1_PREVIEW_ID': 'LOCAL_PREVIEW_ROUND2_AUTOTEST'}), \
                patch('xai_as_closure.study1_app.save_to_github') as save, \
                patch('xai_as_closure.study1_app.test_github_connection') as connect, \
                patch('xai_as_closure.study1_round2_support.requests.get') as recover:
            app_path = str(PROJECT_ROOT / 'apps/study1_validation_v2_six_profiles_archive.py')
            app = AppTest.from_file(app_path, default_timeout=15).run()
            self.assertFalse(app.exception)
            for label in ('Open job description', 'Open recruitment policy'):
                next(button for button in app.button if button.label == label).click().run()
                self.assertFalse(app.exception)
                next(button for button in app.button if button.label == 'Back to candidate').click().run()
            for _ in range(6):
                session = app.session_state['_study1_session']
                reference = session.current_reference()
                app.radio(key=f'screening_decision_{reference}').set_value('Reject candidate')
                app.radio(key=f'screening_hard_criterion_{reference}').set_value('No')
                app.text_input(key=f'screening_evidence_{reference}').set_value('Synthetic software check only')
                next(button for button in app.button if button.label == 'Lock and submit judgment').click().run()
                self.assertFalse(app.exception)
            self.assertEqual(app.session_state['_study1_session'].phase, 'post_study')
            # A new browser session restores the local snapshot and the six locked responses.
            resumed = AppTest.from_file(app_path, default_timeout=15).run()
            self.assertEqual(len(resumed.session_state['_study1_session'].state['responses']), 6)
            for key in ('role_requirement_clarity', 'candidate_profile_realism',
                        'qualification_difference_plausibility', 'mandatory_information_identifiability',
                        'information_sufficiency', 'task_ecological_validity'):
                resumed.radio(key=f'post_study_{key}').set_value(4)
            resumed.radio(key='post_study_professional_disagreement').set_value('No')
            next(button for button in resumed.button if button.label == 'Submit final materials review').click().run()
            self.assertFalse(resumed.exception)
            self.assertTrue(resumed.session_state['_study1_session'].complete)
            records = list((Path(directory) / 'sessions').glob('*.json'))
            self.assertEqual(len(records), 1)
            state = json.loads(records[0].read_text())
            self.assertTrue(state['is_preview'])
            self.assertEqual(state['validation_round'], 'round2')
            self.assertEqual(len(state['responses']), 6)
            events = SessionStore(directory).read_events(state['session_id'])
            self.assertEqual(sum(e['event_type'] == 'candidate_judgment_submitted' for e in events), 6)
            opened = [e for e in events if e['event_type'] == 'document_opened']
            closed = [e for e in events if e['event_type'] == 'document_closed']
            self.assertEqual(len(opened), 2)
            self.assertEqual([e['payload']['document_visit_id'] for e in opened],
                             [e['payload']['document_visit_id'] for e in closed])
            self.assertTrue(all(e['payload']['dwell_seconds'] >= 0 for e in closed))
            self.assertTrue(all(e['is_preview'] and e['validation_round'] == 'round2' for e in events))
            save.assert_not_called()
            connect.assert_not_called()
            recover.assert_not_called()

    def test_backup_failure_blocks_completion_until_saved(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
                'STUDY1_LOCAL_PREVIEW': '0', 'STUDY1_ROUND2_DATA_ROOT': directory}):
            linkage = hashlib.sha256(PID.encode()).hexdigest()
            cases = validation_cases("round2")
            identity = f'{linkage}\0{cases.case_set_id}\0study1-instrument-v7\0round2'
            session_id = 's1_' + hashlib.sha256(identity.encode()).hexdigest()[:24]
            session = Study1Session.create(session_id=session_id, linkage_hash=linkage,
                seed=linkage, cases=cases, validation_round='round2')
            for _ in range(6):
                session.submit_judgment(dict(decision='Reject candidate', hard_criterion_judgment='No',
                    confidence=50, decisive_evidence='Synthetic check'))
            final = {key: 4 for key in ('role_requirement_clarity', 'candidate_profile_realism',
                'qualification_difference_plausibility', 'mandatory_information_identifiability',
                'information_sufficiency', 'task_ecological_validity')}
            session.submit_post_study(dict(final, professional_disagreement='No', disputed_profiles=[],
                disputed_profiles_reason='', materials_feedback=''))
            session.state['archive_pending'] = True
            SessionStore(directory).save(session.state)
            def secret(key, default=''):
                return {'GITHUB_REPO': 'test/private', 'GITHUB_TOKEN': 'test-only',
                        'STUDY1_ROUND2_DATA_ROOT': directory}.get(key, default)
            with patch('xai_as_closure.study1_app._secret', side_effect=secret), \
                    patch('xai_as_closure.study1_app.test_github_connection', return_value=(True, 'ok')), \
                    patch('xai_as_closure.study1_app.save_to_github', return_value=(False, 'synthetic failure')) as save:
                app = AppTest.from_file(str(PROJECT_ROOT / 'apps/study1_validation_v2_six_profiles_archive.py'), default_timeout=15)
                app.query_params['PROLIFIC_PID'] = PID
                app.query_params['return'] = 'https://example.qualtrics.com/jfe/form/test'
                app.run()
                self.assertFalse(app.exception)
                self.assertTrue(any('backup has not completed' in e.value for e in app.error))
                self.assertFalse(any('All 6 independent' in m.value for m in app.markdown))
                self.assertTrue(app.session_state['_study1_session'].state['archive_pending'])
                self.assertIn('/round2/', save.call_args.args[1])
                save.return_value = (True, 'ok')
                next(button for button in app.button if button.label == 'Retry saving').click().run()
                self.assertFalse(app.exception)
                self.assertTrue(any('All 6 independent' in m.value for m in app.markdown))
                self.assertFalse(app.session_state['_study1_session'].state['archive_pending'])


if __name__ == '__main__':
    unittest.main()
