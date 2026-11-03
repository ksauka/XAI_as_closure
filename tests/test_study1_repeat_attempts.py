"""Synthetic production-path tests: no network or participant records."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest
from xai_as_closure.cases import PROJECT_ROOT

PID = 'a' * 24
PATH = str(PROJECT_ROOT / 'apps/study1_validation_v2.py')
RETURN = 'https://uva.fra1.qualtrics.com/jfe/form/SV_3axCYUYXLkOkvsy?stage=post'


def complete(app):
    while app.session_state['_study1_session'].phase == 'screening':
        ref = app.session_state['_study1_session'].current_reference()
        app.radio(key=f'screening_decision_{ref}').set_value('Reject candidate')
        app.radio(key=f'screening_hard_criterion_{ref}').set_value('No')
        app.text_input(key=f'screening_evidence_{ref}').set_value('Synthetic test only')
        next(b for b in app.button if b.label == 'Lock and submit judgment').click().run()
        assert not app.exception
    app.radio(key='post_study_professional_disagreement').set_value('No')
    next(b for b in app.button if b.label == 'Submit final materials review').click().run()
    assert not app.exception


class RepeatAttemptTests(unittest.TestCase):
    def test_same_prolific_id_repeats_without_overwriting_and_refresh_resumes(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'STUDY1_LOCAL_PREVIEW': '1', 'STUDY1_PREVIEW_DATA_ROOT': directory, 'STUDY1_PREVIEW_ID': PID}):
            def secret(key, default=''):
                return {'GITHUB_REPO': 'test/private', 'GITHUB_TOKEN': 'test-only',
                        'STUDY1_FOCUSED_DATA_ROOT': directory}.get(key, default)
            with patch('xai_as_closure.study1_app._secret', side_effect=secret), \
                 patch('xai_as_closure.background_save.test_github_connection', return_value=(True, 'ok')), \
                 patch('requests.get', return_value=Mock(status_code=404)), \
                 patch('xai_as_closure.study1_app.save_to_github', return_value=(True, None)) as save:
                app = AppTest.from_file(PATH, default_timeout=20)
                app.query_params['PROLIFIC_PID'] = PID
                app.query_params['return'] = RETURN
                app.run()
                self.assertFalse(app.exception)
                original = app.session_state['_study1_session'].state['session_id']
                complete(app)
                original_path = Path(directory) / 'sessions' / f'{original}.json'
                original_bytes = original_path.read_bytes()
                app.button(key='study1_repeat_attempt').click().run()
                self.assertFalse(app.exception)
                session = app.session_state['_study1_session']
                repeat = session.state['session_id']
                token = app.query_params['attempt'][0]
                self.assertNotEqual(original, repeat)
                self.assertEqual(session.state['responses'], {})
                self.assertEqual(session.state['participant_session_id'], original)
                self.assertEqual(session.state['attempt_id'], token)
                self.assertTrue(session.state['repeat_attempt'])
                self.assertEqual(app.query_params['PROLIFIC_PID'], [PID])
                self.assertEqual(app.query_params['return'], [RETURN])
                self.assertEqual(original_path.read_bytes(), original_bytes)
                for ref in ('C-05', 'C-06'):
                    if session.current_reference() == ref:
                        self.assertIsNone(app.radio(key=f'screening_decision_{ref}').value)
                        self.assertEqual(app.text_input(key=f'screening_evidence_{ref}').value, '')
                save.assert_not_called()
                refreshed = AppTest.from_file(PATH, default_timeout=20)
                refreshed.query_params.update({'PROLIFIC_PID': PID, 'return': RETURN, 'attempt': token})
                refreshed.run()
                self.assertFalse(refreshed.exception)
                self.assertEqual(refreshed.session_state['_study1_session'].state['session_id'], repeat)
                complete(refreshed)
                repeat_path = Path(directory) / 'sessions' / f'{repeat}.json'
                repeat_bytes = repeat_path.read_bytes()
                refreshed.button(key='study1_repeat_attempt').click().run()
                self.assertFalse(refreshed.exception)
                third = refreshed.session_state['_study1_session'].state['session_id']
                self.assertNotIn(third, (original, repeat))
                self.assertEqual(repeat_path.read_bytes(), repeat_bytes)
                self.assertEqual(original_path.read_bytes(), original_bytes)
                self.assertEqual(len(list((Path(directory) / 'sessions').glob('*.json'))), 3)


if __name__ == '__main__':
    unittest.main()
