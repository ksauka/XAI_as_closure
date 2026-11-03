"""Researcher test IDs may repeat the task; participant IDs keep one session."""
import os
import tempfile
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from test_study1_freeze import final_review, judgments

from xai_as_closure.cases import PROJECT_ROOT
from xai_as_closure.config import parse_test_ids
from xai_as_closure.session_flatten import select_first_completed_attempts

TESTER = '6718c5a3008e8aa945d5e7d1'
PARTICIPANT = '5f8e3c2a1b9d4e6f7a8b9c0d'


def production(directory, study):
    stack = ExitStack()
    stack.enter_context(patch.dict(os.environ, {f'{study}_LOCAL_PREVIEW': '0'}))
    stack.enter_context(patch('xai_as_closure.background_save.test_github_connection',
                              return_value=(True, 'ok')))
    stack.enter_context(patch(f'xai_as_closure.{study.lower()}_app.save_to_github',
                              return_value=(True, None)))
    return stack


def secrets(directory):
    return {'GITHUB_REPO': 'test/private', 'GITHUB_TOKEN': 'test-only',
            'STUDY1_FOCUSED_DATA_ROOT': directory, 'STUDY2_DATA_ROOT': directory,
            'STUDY_TEST_IDS': f' {TESTER} , OTHER-TESTER '}


def study1(directory, pid):
    app = AppTest.from_file(str(PROJECT_ROOT / 'apps/study1_validation_v2.py'), default_timeout=20)
    app.secrets = secrets(directory)
    app.query_params['PROLIFIC_PID'] = pid
    return app.run()


class Study1TestIdTests(unittest.TestCase):
    def finish_then_reopen(self, pid):
        with tempfile.TemporaryDirectory() as directory, production(directory, 'STUDY1'):
            first = study1(directory, pid)
            judgments(first)
            final_review(first)
            first_session = first.session_state['_study1_session']
            self.assertTrue(first_session.complete)
            again = study1(directory, pid)
            self.assertFalse(again.exception)
            return first_session, again

    def test_test_id_starts_a_fresh_flagged_attempt_after_finishing(self):
        first, again = self.finish_then_reopen(TESTER)
        session = again.session_state['_study1_session']
        self.assertTrue(first.state['test_participant'])
        self.assertNotEqual(session.state['session_id'], first.state['session_id'])
        self.assertEqual(session.phase, 'screening')
        self.assertTrue(session.state['test_participant'])
        self.assertEqual(again.query_params['attempt'], [session.state['attempt_id']])

    def test_participant_id_still_sees_the_completed_session(self):
        first, again = self.finish_then_reopen(PARTICIPANT)
        session = again.session_state['_study1_session']
        self.assertFalse(first.state['test_participant'])
        self.assertEqual(session.state['session_id'], first.state['session_id'])
        self.assertTrue(session.complete)


class Study2TestIdTests(unittest.TestCase):
    def open_two_conditions(self, pid):
        with tempfile.TemporaryDirectory() as directory, production(directory, 'STUDY2'):
            apps = []
            for path, cond in (('apps/study2_01_lowP_lowA_noF.py', 'P0_A0_F0'),
                               ('apps/study2_02_lowP_lowA_F.py', 'P0_A0_F1')):
                app = AppTest.from_file(str(PROJECT_ROOT / path), default_timeout=20)
                app.secrets = secrets(directory)
                app.query_params.update({'PROLIFIC_PID': pid, 'cond': cond})
                apps.append(app.run())
            return apps

    def test_test_id_can_switch_condition(self):
        first, second = self.open_two_conditions(TESTER)
        self.assertFalse(second.exception)
        self.assertFalse(second.error)
        session = second.session_state.filtered_state['_study2_session']
        self.assertEqual(session.state['condition_id'], 'P0_A0_F1')
        self.assertTrue(session.state['test_participant'])
        self.assertNotEqual(session.state['session_id'],
                            first.session_state.filtered_state['_study2_session'].state['session_id'])

    def test_participant_id_stays_in_its_condition(self):
        _, second = self.open_two_conditions(PARTICIPANT)
        self.assertTrue(any('different condition' in e.value for e in second.error))


class TestIdAnalysisTests(unittest.TestCase):
    def test_parse_and_exclude_test_records(self):
        self.assertEqual(parse_test_ids(' a , ,b '), frozenset({'a', 'b'}))
        sessions = [{'prolific_pid': TESTER, 'test_participant': True, 'completed_at_utc': '1'},
                    {'prolific_pid': PARTICIPANT, 'completed_at_utc': '2'}]
        kept, excluded = select_first_completed_attempts(sessions)
        self.assertEqual([s['prolific_pid'] for s in kept], [PARTICIPANT])
        self.assertEqual([s['prolific_pid'] for s in excluded], [TESTER])


if __name__ == '__main__':
    unittest.main()
