"""Meaningful failure/recovery checks for the unpublished participant freeze."""
from contextlib import ExitStack
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

import requests
from streamlit.testing.v1 import AppTest
from xai_as_closure.cases import PROJECT_ROOT, CaseRepository
from xai_as_closure.github_saver import save_to_github
from xai_as_closure.storage import SessionStore
from xai_as_closure.study1 import Study1Session, FOCUSED_ROUND

APP = str(PROJECT_ROOT / 'apps/study1_validation_v2.py')
CODE = 'RESEARCHER-FREEZE-20261103-001'
RETURN = 'https://uva.fra1.qualtrics.com/jfe/form/SV_3axCYUYXLkOkvsy?stage=post'


def production(directory, save):
    stack = ExitStack()
    stack.enter_context(patch.dict(os.environ, {'STUDY1_LOCAL_PREVIEW': '0'}))
    stack.enter_context(patch('xai_as_closure.study1_app._secret', side_effect=lambda key, default='':
        {'GITHUB_REPO':'test/private', 'GITHUB_TOKEN':'test-only',
         'STUDY1_FOCUSED_DATA_ROOT':directory}.get(key, default)))
    stack.enter_context(patch('requests.get', return_value=Mock(status_code=404)))
    stack.enter_context(patch('xai_as_closure.study1_app.save_to_github', side_effect=save))
    return stack


def new_app():
    app = AppTest.from_file(APP, default_timeout=15)
    app.query_params.update({'participant_code': CODE, 'return': RETURN})
    return app.run()


def judgments(app):
    for _ in range(2):
        ref = app.session_state['_study1_session'].current_reference()
        app.radio(key=f'screening_decision_{ref}').set_value('Reject candidate')
        app.radio(key=f'screening_hard_criterion_{ref}').set_value('No')
        app.slider(key=f'screening_confidence_{ref}').set_value(70)
        app.text_input(key=f'screening_evidence_{ref}').set_value('Synthetic freeze check only')
        next(b for b in app.button if b.label == 'Lock and submit judgment').click().run()
        assert not app.exception


def final_review(app, disagreement=False):
    app.radio(key='post_study_professional_disagreement').set_value('Yes' if disagreement else 'No')
    if disagreement:
        app.multiselect(key='post_study_disputed_profiles').set_value(['C-06'])
        app.text_area(key='post_study_disputed_profiles_reason').set_value('Synthetic follow-up check only')
    app.text_area(key='post_study_materials_feedback').set_value('Synthetic researcher review')
    next(b for b in app.button if b.label == 'Submit final materials review').click().run()
    assert not app.exception


def drain(app):
    for _ in range(6):
        job = app.session_state.filtered_state.get('_study1_backup_job')
        if job:
            job[0].result(timeout=4)
        app.session_state['_study1_retry_after'] = 0
        app.run()
        if not app.session_state['_study1_session'].state.get('archive_pending'):
            return
    raise AssertionError('The final revision was not saved')


class GithubRetryTests(unittest.TestCase):
    def test_failed_version_lookups_never_write(self):
        with patch('xai_as_closure.github_saver.time.sleep'), \
             patch('xai_as_closure.github_saver.requests.get', side_effect=requests.Timeout('test')), \
             patch('xai_as_closure.github_saver.requests.put') as put:
            self.assertFalse(save_to_github('test/private', 'test.json', '{}', 'test', 'not-real')[0])
            put.assert_not_called()

    def test_retry_fetches_version_before_first_write(self):
        good = Mock(status_code=200)
        good.json.return_value = {'sha':'confirmed-version'}
        with patch('xai_as_closure.github_saver.time.sleep'), \
             patch('xai_as_closure.github_saver.requests.get', side_effect=[Mock(status_code=503), good]) as get, \
             patch('xai_as_closure.github_saver.requests.put', return_value=Mock(status_code=200)) as put:
            self.assertTrue(save_to_github('test/private', 'test.json', '{}', 'test', 'not-real')[0])
            self.assertEqual(get.call_count, 2)
            self.assertEqual(put.call_count, 1)
            self.assertEqual(put.call_args.kwargs['json']['sha'], 'confirmed-version')

    def test_conflict_refetches_new_version(self):
        first, second = Mock(status_code=200), Mock(status_code=200)
        first.json.return_value = {'sha':'old'}
        second.json.return_value = {'sha':'new'}
        with patch('xai_as_closure.github_saver.time.sleep'), \
             patch('xai_as_closure.github_saver.requests.get', side_effect=[first, second]) as get, \
             patch('xai_as_closure.github_saver.requests.put', side_effect=[Mock(status_code=409), Mock(status_code=200)]) as put:
            self.assertTrue(save_to_github('test/private', 'test.json', '{}', 'test', 'not-real')[0])
            self.assertEqual(get.call_count, 2)
            self.assertEqual([c.kwargs['json']['sha'] for c in put.call_args_list], ['old','new'])


class FrozenJourneyTests(unittest.TestCase):
    def test_slow_save_does_not_block_judgments_but_completion_waits(self):
        gate = threading.Event()
        uploaded = []
        def save(*args, **kwargs):
            gate.wait(timeout=10)
            uploaded.append(json.loads(args[2]))
            return True, None
        try:
            with tempfile.TemporaryDirectory() as directory, production(directory, save):
                app = new_app()
                self.assertFalse(app.exception)
                text = '\n'.join(x.value for x in app.markdown)
                self.assertNotIn('role="timer"', text)
                self.assertFalse(any('Build' in c.value for c in app.caption))
                self.assertFalse(any(b.label == 'Start another attempt' for b in app.button))
                judgments(app)
                self.assertEqual(app.session_state['_study1_session'].phase, 'post_study')
                self.assertEqual([r.key for r in app.radio], ['post_study_professional_disagreement'])
                self.assertFalse(any('Strongly disagree' in c.value for c in app.caption))
                final_review(app, disagreement=True)
                self.assertFalse(app.error)
                self.assertTrue(any('Saving your responses' in x.value for x in app.info))
                self.assertEqual(len(app.get('link_button')), 0)
                self.assertFalse(app.session_state['_study1_backup_job'][0].done())
                gate.set()
                drain(app)
                self.assertEqual(app.get('link_button')[0].proto.label, 'Return to survey')
                self.assertFalse(any(b.label == 'Start another attempt' for b in app.button))
                sid = app.session_state['_study1_session'].state['session_id']
                payload = uploaded[-1]
                self.assertEqual(payload['participant_id'], CODE)
                self.assertEqual(payload['phase'], 'complete')
                self.assertEqual(payload['post_study_review_version'], 'q7_q8_v1')
                self.assertEqual(set(payload['post_study_response']), {'professional_disagreement',
                    'disputed_profiles','disputed_profiles_reason','materials_feedback'})
                self.assertEqual(payload['event_sequence'], app.session_state['_study1_session'].state['event_sequence'])
                self.assertFalse(payload['archive_pending'])
                self.assertTrue(all(isinstance(e['elapsed_seconds'], (int,float)) for e in payload['events']))
                resumed = new_app()
                self.assertEqual(resumed.session_state['_study1_session'].state['session_id'], sid)
                self.assertTrue(resumed.session_state['_study1_session'].complete)
                drain(resumed)
                self.assertFalse(any(b.label == 'Start another attempt' for b in resumed.button))
                self.assertEqual(len(list((Path(directory)/'sessions').glob('*.json'))), 1)
        finally:
            gate.set()

    def test_failed_save_is_quiet_until_a_successful_completion_retry(self):
        result = [False]
        def save(*args, **kwargs):
            return result[0], None if result[0] else 'synthetic outage'
        with tempfile.TemporaryDirectory() as directory, production(directory, save):
            app = new_app()
            judgments(app)
            final_review(app)
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
            self.assertTrue(any('Saving your responses' in x.value for x in app.info))
            self.assertEqual(len(app.get('link_button')), 0)
            result[0] = True
            drain(app)
            self.assertEqual(app.get('link_button')[0].proto.label, 'Return to survey')

    def test_historical_full_review_is_restored_without_rewriting_it(self):
        cases = CaseRepository()
        s = Study1Session.create(session_id='s1_'+'d'*24, linkage_hash='e'*64,
                                seed='legacy', cases=cases, validation_round=FOCUSED_ROUND)
        for _ in range(2):
            s.submit_judgment(dict(decision='Reject candidate',hard_criterion_judgment='No',
                                  confidence=60,decisive_evidence='Historical synthetic fixture'))
        s.state.pop('post_study_review_version')
        s.state.update(phase='complete', post_study_response=dict(
            **{k:4 for k in ('role_requirement_clarity','candidate_profile_realism',
               'qualification_difference_plausibility','mandatory_information_identifiability',
               'information_sufficiency','task_ecological_validity')},
            professional_disagreement='No',disputed_profiles=[],disputed_profiles_reason='',materials_feedback=''),
            post_study_submitted_at_utc=s.state['updated_at_utc'],completed_at_utc=s.state['updated_at_utc'],
            total_duration_seconds=1.0)
        before = deepcopy(s.state)
        restored = Study1Session.restore(s.state, cases)
        self.assertTrue(restored.complete)
        self.assertEqual(restored.state, before)


if __name__ == '__main__':
    unittest.main()
