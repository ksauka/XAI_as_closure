"""Time each app's first screen for a Prolific participant while GitHub is slow.

Usage: python tools/time_first_screen.py [delay_seconds]
Every GitHub GET/PUT is replaced by a fake that waits <delay> seconds.
"""
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

root = Path(__file__).resolve().parents[1]
delay = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
sys.path.insert(0, str(root / "src"))
os.environ["STUDY1_LOCAL_PREVIEW"] = "0"
os.environ["STUDY2_LOCAL_PREVIEW"] = "0"

from streamlit.testing.v1 import AppTest  # noqa: E402

calls = []


def slow(method):
    def fake(url, *args, **kwargs):
        calls.append(method)
        time.sleep(delay)
        if url.rstrip("/").count("/") == 5:  # repos/<owner>/<repo>: connection test
            return Mock(status_code=200, json=lambda: {"private": True, "permissions": {"push": True}})
        return Mock(status_code=404 if method == "GET" else 201)
    return fake


apps = [
    ("Study 1", "apps/study1_validation_v2.py", {}, "STUDY1_FOCUSED_DATA_ROOT"),
    ("Study 2", "apps/study2_01_lowP_lowA_noF.py", {"cond": "P0_A0_F0"}, "STUDY2_DATA_ROOT"),
]
with patch("requests.get", side_effect=slow("GET")), patch("requests.put", side_effect=slow("PUT")):
    for name, path, query, root_key in apps:
        with tempfile.TemporaryDirectory() as data:
            calls.clear()
            app = AppTest.from_file(str(root / path), default_timeout=180)
            app.query_params = {"PROLIFIC_PID": "000000000000000000000abc", **query}
            app.secrets = {"GITHUB_REPO": "test/private", "GITHUB_TOKEN": "test-only", root_key: data}
            started = time.monotonic()
            app.run()
            elapsed = time.monotonic() - started
            status = "exception" if app.exception else "ok"
            print(f"{name}: first screen after {elapsed:5.1f}s, "
                  f"{len(calls)} GitHub call(s) waited on or started ({status})")
