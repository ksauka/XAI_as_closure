"""Non-blocking saves, unique remote archives and the duplicate-record rule."""
import os
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from xai_as_closure import background_save
from xai_as_closure.background_save import (
    ARCHIVE_ID_PATTERN,
    check_connection_once,
    new_archive_id,
    sync_in_background,
)
from xai_as_closure.cases import PROJECT_ROOT
from xai_as_closure.logger import checkpoint_path
from xai_as_closure.session_flatten import select_first_completed_attempts
from xai_as_closure.study1_round2_support import round2_archive_path

PID = '5f8e3c2a1b9d4e6f7a8b9c0d'
SID = 's1_' + '0' * 24


def wait(state, prefix='_t'):
    job = state.get(f'{prefix}_backup_job')
    if job:
        job[0].result(timeout=3)


class SyncInBackgroundTests(unittest.TestCase):
    def test_saves_once_per_revision_and_retries_after_failure(self):
        state, calls = {}, []
        outcomes = iter([(False, 'synthetic outage'), (True, None)])

        def prepare():
            calls.append('prepared')
            return lambda: next(outcomes)

        self.assertFalse(sync_in_background(state, '_t', 1, prepare))
        wait(state)
        self.assertFalse(sync_in_background(state, '_t', 1, prepare))
        self.assertNotIn('_t_backup_job', state)  # Waiting out the retry delay.
        state['_t_retry_after'] = 0
        self.assertFalse(sync_in_background(state, '_t', 1, prepare))
        wait(state)
        self.assertTrue(sync_in_background(state, '_t', 1, prepare))
        self.assertTrue(sync_in_background(state, '_t', 1, prepare))
        self.assertEqual(len(calls), 2)

    def test_newer_revisions_wait_for_the_save_in_flight(self):
        state, calls, release = {}, [], threading.Event()

        def prepare():
            calls.append('prepared')
            return lambda: (release.wait(timeout=3), None)

        self.assertFalse(sync_in_background(state, '_t', 3, prepare))
        self.assertFalse(sync_in_background(state, '_t', 4, prepare))
        self.assertEqual(len(calls), 1)
        release.set()
        wait(state)
        self.assertFalse(sync_in_background(state, '_t', 4, prepare))
        wait(state)
        self.assertTrue(sync_in_background(state, '_t', 4, prepare))

    def test_connection_is_checked_once_per_server(self):
        with patch.object(background_save, '_CHECKED_REPOS', set()), \
                patch('xai_as_closure.background_save.test_github_connection',
                      return_value=(True, 'ok')) as connect:
            for _ in range(3):
                check_connection_once('test-only', 'test/once')
            background_save._WORKERS.submit(lambda: None).result(timeout=3)
            self.assertEqual(connect.call_count, 1)


class ArchivePathTests(unittest.TestCase):
    def test_each_new_session_gets_its_own_remote_file(self):
        first, second = new_archive_id(), new_archive_id()
        self.assertRegex(first, ARCHIVE_ID_PATTERN)
        self.assertNotEqual(first, second)
        self.assertNotEqual(round2_archive_path(SID, 'round2', first),
                            round2_archive_path(SID, 'round2', second))
        self.assertNotEqual(checkpoint_path('abc123', first), checkpoint_path('abc123', second))
        # Sessions saved before archive IDs keep updating their original file.
        self.assertTrue(round2_archive_path(SID).endswith(f'/{SID}.json'))
        self.assertTrue(checkpoint_path('abc123').endswith('/abc123.json'))
        with self.assertRaises(ValueError):
            checkpoint_path('abc123', '../escape')

    def test_restart_starts_a_new_record_without_github_lookup(self):
        def secret(directory):
            return lambda key, default='': {
                'GITHUB_REPO': 'test/private', 'GITHUB_TOKEN': 'test-only',
                'STUDY1_FOCUSED_DATA_ROOT': directory}.get(key, default)

        paths = []
        for _ in range(2):  # A fresh data root stands in for a host restart.
            with tempfile.TemporaryDirectory() as directory, \
                    patch.dict(os.environ, {'STUDY1_LOCAL_PREVIEW': '0'}), \
                    patch('xai_as_closure.study1_app._secret', side_effect=secret(directory)), \
                    patch('xai_as_closure.background_save.test_github_connection',
                          return_value=(True, 'ok')), \
                    patch('requests.get', return_value=Mock(status_code=404)) as lookup, \
                    patch('xai_as_closure.study1_app.save_to_github',
                          return_value=(True, None)) as save:
                app = AppTest.from_file(str(PROJECT_ROOT / 'apps/study1_validation_v2.py'),
                                        default_timeout=15)
                app.query_params['PROLIFIC_PID'] = PID
                app.run()
                self.assertFalse(app.exception)
                wait(app.session_state.filtered_state, '_study1')
                lookup.assert_not_called()
                paths.append(save.call_args.args[1])
        self.assertNotEqual(paths[0], paths[1])


class DuplicateRuleTests(unittest.TestCase):
    def test_keeps_first_completed_attempt_and_reports_the_rest(self):
        def record(name, created, completed=None, pid=PID):
            return {'name': name, 'prolific_pid': pid, 'created_at_utc': created,
                    'completed_at_utc': completed}

        sessions = [
            record('abandoned', '2026-11-03T10:00:00'),
            record('second', '2026-11-03T10:30:00', '2026-11-03T11:30:00'),
            record('first', '2026-11-03T10:10:00', '2026-11-03T11:00:00'),
            record('only-started', '2026-11-03T09:00:00', pid='other'),
            record('later-started', '2026-11-03T09:30:00', pid='other'),
        ]
        kept, excluded = select_first_completed_attempts(sessions)
        self.assertEqual(sorted(s['name'] for s in kept), ['first', 'only-started'])
        self.assertEqual(sorted(s['name'] for s in excluded),
                         ['abandoned', 'later-started', 'second'])


if __name__ == '__main__':
    unittest.main()
