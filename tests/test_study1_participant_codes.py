"""Independent expert linkage, platform compatibility and completion recovery."""
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from streamlit.testing.v1 import AppTest
from xai_as_closure.cases import PROJECT_ROOT
from xai_as_closure.study1 import WorkflowError
from xai_as_closure.study1_app import _build_final_return
from xai_as_closure.study1_launch import read_participant_link, validate_participant


class ParticipantCodeTests(unittest.TestCase):
    def test_both_sources_are_explicit_and_namespaced(self):
        self.assertIsNone(read_participant_link())
        platform = read_participant_link(prolific_pid='a' * 24)
        external = read_participant_link(participant_code='a' * 24)
        self.assertEqual(platform.hash_input, 'a' * 24)
        self.assertNotEqual(platform.hash_input, external.hash_input)
        self.assertEqual(external.recruitment_source, 'researcher')
        self.assertEqual(read_participant_link(legacy_pid='a' * 24), platform)
        self.assertEqual(validate_participant(' EXP-007 ', 'researcher').participant_id, 'EXP-007')

    def test_ambiguous_and_unexpanded_links_are_rejected(self):
        for params in ({'prolific_pid': '${e://Field/PROLIFIC_PID}'},
                       {'participant_code': '${e://Field/participant_code}'},
                       {'prolific_pid': 'a' * 24, 'participant_code': 'EXP-007'},
                       {'prolific_pid': 'a' * 24, 'legacy_pid': 'b' * 24}):
            with self.assertRaises(WorkflowError):
                read_participant_link(**params)
        for value in ('', 'a', 'name@example.com', '../EXP-007', '<script>', 'code with spaces'):
            with self.assertRaises(WorkflowError):
                validate_participant(value, 'researcher')
        with self.assertRaises(WorkflowError):
            validate_participant('EXP-007', 'prolific')

    def test_external_survey_return_does_not_claim_a_prolific_id(self):
        url = _build_final_return(
            'https://uva.fra1.qualtrics.com/jfe/form/SV_9zP4nU7SuKhcZOC?stage=post&PROLIFIC_PID=stale&pid=stale',
            'EXP-007', 's1_' + 'a' * 24, recruitment_source='researcher')
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        self.assertEqual(query['participant_code'], ['EXP-007'])
        self.assertEqual(query['stage'], ['post'])
        self.assertEqual(query['done'], ['1'])
        self.assertNotIn('PROLIFIC_PID', query)
        self.assertNotIn('pid', query)
        self.assertTrue(parsed.path.endswith('SV_9zP4nU7SuKhcZOC'))
        platform = _build_final_return('https://example.qualtrics.com/jfe/form/test?participant_code=stale',
            'a' * 24, 's1_' + 'b' * 24)
        query = parse_qs(urlparse(platform).query)
        self.assertEqual(query['PROLIFIC_PID'], ['a' * 24])
        self.assertNotIn('participant_code', query)

    def mocked_production(self, directory):
        stack = ExitStack()
        stack.enter_context(patch.dict(os.environ, {'STUDY1_LOCAL_PREVIEW': '0',
            'STUDY1_ROUND2_DATA_ROOT': directory}))
        def secret(key, default=''):
            return {'GITHUB_REPO': 'test/private', 'GITHUB_TOKEN': 'test-only',
                    'STUDY1_ROUND2_DATA_ROOT': directory}.get(key, default)
        stack.enter_context(patch('xai_as_closure.study1_app._secret', side_effect=secret))
        stack.enter_context(patch('xai_as_closure.study1_app.test_github_connection', return_value=(True, 'ok')))
        save = stack.enter_context(patch('xai_as_closure.study1_app.save_to_github', return_value=(True, 'ok')))
        lookup = stack.enter_context(patch('xai_as_closure.study1_round2_support.requests.get', return_value=Mock(status_code=404)))
        return stack, save, lookup

    def app(self):
        return AppTest.from_file(str(PROJECT_ROOT / 'apps/study1_validation_v2_six_profiles_archive.py'), default_timeout=15)

    def test_manual_external_expert_completes_and_reopens_saved_session(self):
        with tempfile.TemporaryDirectory() as directory:
            stack, save, lookup = self.mocked_production(directory)
            with stack:
                app = self.app().run()
                self.assertFalse(app.exception)
                self.assertEqual(app.radio(key='study1_link_type').value, 'Researcher-issued participant code')
                app.text_input(key='study1_link_value').set_value('EXP-007')
                next(b for b in app.button if b.label == 'Begin study task').click().run()
                self.assertFalse(app.exception)
                session = app.session_state['_study1_session']
                original_id = session.state['session_id']
                self.assertEqual(session.state['recruitment_source'], 'researcher')
                self.assertEqual(session.state['linkage_hash'], hashlib.sha256(b'researcher\0EXP-007').hexdigest())
                for _ in range(6):
                    reference = app.session_state['_study1_session'].current_reference()
                    app.radio(key=f'screening_decision_{reference}').set_value('Reject candidate')
                    app.radio(key=f'screening_hard_criterion_{reference}').set_value('No')
                    app.text_input(key=f'screening_evidence_{reference}').set_value('Synthetic software test only')
                    next(b for b in app.button if b.label == 'Lock and submit judgment').click().run()
                for key in ('role_requirement_clarity', 'candidate_profile_realism',
                    'qualification_difference_plausibility', 'mandatory_information_identifiability',
                    'information_sufficiency', 'task_ecological_validity'):
                    app.radio(key=f'post_study_{key}').set_value(4)
                app.radio(key='post_study_professional_disagreement').set_value('No')
                next(b for b in app.button if b.label == 'Submit final materials review').click().run()
                self.assertFalse(app.exception)
                self.assertTrue(app.session_state['_study1_session'].complete)
                checkpoint = json.loads(save.call_args.args[2])
                self.assertEqual(checkpoint['participant_id'], 'EXP-007')
                self.assertEqual(checkpoint['prolific_pid'], '')
                self.assertEqual(checkpoint['recruitment_source'], 'researcher')
                resumed = self.app()
                resumed.query_params['participant_code'] = 'EXP-007'
                resumed.run()
                self.assertFalse(resumed.exception)
                self.assertEqual(resumed.session_state['_study1_session'].state['session_id'], original_id)
                self.assertTrue(resumed.session_state['_study1_session'].complete)
                self.assertTrue(any('already has a completed session' in item.value for item in resumed.info))
                self.assertEqual(len(list((Path(directory) / 'sessions').glob('*.json'))), 1)

    def test_placeholder_stops_before_storage_and_no_silent_participant_switch(self):
        with tempfile.TemporaryDirectory() as directory:
            stack, save, lookup = self.mocked_production(directory)
            with stack:
                app = self.app()
                app.query_params['PROLIFIC_PID'] = '${e://Field/PROLIFIC_PID}'
                app.run()
                self.assertFalse(app.exception)
                self.assertTrue(any('unfilled Qualtrics field' in item.value for item in app.error))
                save.assert_not_called()
                lookup.assert_not_called()
                app = self.app()
                app.query_params['participant_code'] = 'EXP-007'
                app.run()
                self.assertFalse(app.exception)
                original_id = app.session_state['_study1_session'].state['session_id']
                app.query_params['participant_code'] = 'EXP-008'
                app.run()
                self.assertFalse(app.exception)
                self.assertTrue(any('linked to another participant' in item.value for item in app.error))
                self.assertEqual(app.session_state['_study1_session'].state['session_id'], original_id)
                self.assertEqual(len(list((Path(directory) / 'sessions').glob('*.json'))), 1)


if __name__ == '__main__':
    unittest.main()
