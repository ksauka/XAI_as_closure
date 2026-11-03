"""Check that the visible build marker cannot conceal stale application imports."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import os

from streamlit.testing.v1 import AppTest
from xai_as_closure import study1_app
from xai_as_closure.cases import PROJECT_ROOT

RELEASE = '2026-11-03.3'


class Study1EntryTests(unittest.TestCase):
    def test_old_cached_app_is_stopped_before_its_launch_logic_runs(self):
        old_app = Mock(spec=['run'])
        with patch('xai_as_closure.study1_entry.import_module', return_value=old_app):
            app = AppTest.from_file(str(PROJECT_ROOT / 'apps/study1_validation_v2.py')).run()
            self.assertFalse(app.exception)
            self.assertTrue(any('Version 2' in c.value and RELEASE in c.value for c in app.caption))
            self.assertTrue(any('older Study 1 application loaded' in e.value for e in app.error))
            old_app.run.assert_not_called()

    def test_current_app_still_accepts_manual_researcher_codes(self):
        with patch.dict(os.environ, {'STUDY1_LOCAL_PREVIEW': '0'}):
            app = AppTest.from_file(str(PROJECT_ROOT / 'apps/study1_validation_v2.py')).run()
            self.assertFalse(app.exception)
            self.assertTrue(any('Version 2' in c.value and RELEASE in c.value for c in app.caption))
            self.assertEqual(app.radio(key='study1_link_type').value, 'Researcher-issued participant code')

    def test_earlier_entry_is_visibly_different(self):
        with patch.dict(os.environ, {'STUDY1_LOCAL_PREVIEW': '0'}):
            app = AppTest.from_file(str(PROJECT_ROOT / 'apps/study1_validation.py')).run()
            self.assertFalse(app.exception)
            self.assertTrue(any('Earlier Study 1 entry point' in c.value and RELEASE in c.value for c in app.caption))
            self.assertFalse(any('Version 2' in c.value for c in app.caption))


if __name__ == '__main__':
    unittest.main()
