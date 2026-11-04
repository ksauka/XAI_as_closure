"""Completion never waits for GitHub; pending backups are uploaded from the local copies."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from xai_as_closure.github_saver import save_to_github
from xai_as_closure.logger import checkpoint_path
from xai_as_closure.sync_pending import sync_pending

PID = "5f8e3c2a1b9d4e6f7a8b9c0d"


def completion_page_while_github_fails():
    from unittest.mock import patch

    from xai_as_closure import study2_app

    class Session:
        state = {"prolific_pid": "5f8e3c2a1b9d4e6f7a8b9c0d", "session_id": "abc123",
                 "condition_id": "P1_A1_F1"}

    with patch.object(study2_app, "_sync_github", return_value=False):
        study2_app._complete(Session())


def write_session(directory, session_id, phase, minutes_ago, pending=True):
    updated = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat()
    state = {"session_id": session_id, "participant_id": PID, "prolific_pid": PID,
             "condition_id": "P0_A0_F0", "archive_id": "20261104T101500Z_0a1b2c3d",
             "phase": phase, "archive_pending": pending, "updated_at_utc": updated}
    Path(directory, f"{session_id}.state.json").write_text(json.dumps(state))
    Path(directory, f"{session_id}.jsonl").write_text(json.dumps({"event_type": "session_completed"}) + "\n")


class CompletionPageTests(unittest.TestCase):
    def test_return_is_offered_while_the_github_backup_is_still_failing(self):
        app = AppTest.from_function(completion_page_while_github_fails).run(timeout=20)
        self.assertFalse(app.exception)
        self.assertTrue(any("complete" in s.value for s in app.success))
        self.assertFalse(any("Saving your responses" in i.value for i in app.info))


class RateLimitTests(unittest.TestCase):
    def test_rate_limited_lookup_is_not_retried(self):
        with patch("xai_as_closure.github_saver.requests") as requests:
            requests.get.return_value = Mock(status_code=403)
            success, detail = save_to_github("owner/repo", "a.json", "{}", "m", "token")
        self.assertFalse(success)
        self.assertIn("403", detail)
        self.assertEqual(requests.get.call_count, 1)
        requests.put.assert_not_called()


class SyncPendingTests(unittest.TestCase):
    def test_uploads_settled_sessions_and_leaves_active_ones(self):
        with tempfile.TemporaryDirectory() as directory:
            write_session(directory, "done1", "complete", 5)
            write_session(directory, "active1", "aided", 5)
            write_session(directory, "gone1", "aided", 90)
            write_session(directory, "saved1", "complete", 5, pending=False)
            with patch("xai_as_closure.sync_pending.save_to_github", return_value=(True, None)) as save:
                uploaded, remaining, stop = sync_pending(Path(directory), "owner/repo", "token")
            self.assertEqual((uploaded, remaining, stop), (2, 0, None))
            paths = sorted(call.args[1] for call in save.call_args_list)
            self.assertEqual(paths, sorted(checkpoint_path(s, "20261104T101500Z_0a1b2c3d")
                                           for s in ("done1", "gone1")))
            payload = json.loads(save.call_args_list[0].args[2])
            self.assertFalse(payload["archive_pending"])
            self.assertEqual(payload["events"], [{"event_type": "session_completed"}])
            state = json.loads(Path(directory, "done1.state.json").read_text())
            self.assertFalse(state["archive_pending"])
            self.assertTrue(json.loads(Path(directory, "active1.state.json").read_text())["archive_pending"])

    def test_stops_at_the_first_rate_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            write_session(directory, "done1", "complete", 5)
            write_session(directory, "done2", "complete", 5)
            with patch("xai_as_closure.sync_pending.save_to_github",
                       return_value=(False, "Version lookup returned 403.")) as save:
                uploaded, remaining, stop = sync_pending(Path(directory), "owner/repo", "token")
            self.assertEqual((uploaded, remaining), (0, 2))
            self.assertIn("rate limited", stop)
            self.assertEqual(save.call_count, 1)


if __name__ == "__main__":
    unittest.main()
