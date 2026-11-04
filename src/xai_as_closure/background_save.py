"""Non-blocking private-GitHub backups shared by the Study 1 and Study 2 apps."""

from __future__ import annotations

import logging
import re
import threading
import time
from collections.abc import Callable, MutableMapping
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .github_saver import test_github_connection

SaveCall = Callable[[], tuple[bool, str | None]]
ARCHIVE_ID_PATTERN = re.compile(r"^\d{8}T\d{6}Z_[0-9a-f]{8}$")

# Failed backups wait before retrying: frequent retries from many open pages exhausted the
# hourly GitHub API quota on 4 Nov 2026. Local copies remain the record in the meantime.
RETRY_DELAY_SECONDS = 30.0
_WORKERS = ThreadPoolExecutor(max_workers=4, thread_name_prefix="study-save")
_LOGGER = logging.getLogger(__name__)
_CHECKED_REPOS: set[str] = set()
_CHECK_LOCK = threading.Lock()


def new_archive_id() -> str:
    """Name one session's remote file so a later session never overwrites it."""
    return f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}"


def _timed(save: SaveCall) -> tuple[bool, str | None]:
    started = time.monotonic()
    success, detail = save()
    _LOGGER.info("GitHub save %s after %.1fs", "succeeded" if success else "failed",
                 time.monotonic() - started)
    return success, detail


def sync_in_background(
    state: MutableMapping[str, Any],
    prefix: str,
    revision: int,
    prepare: Callable[[], SaveCall],
) -> bool:
    """Return True once ``revision`` is saved; otherwise start or await one save.

    ``state`` is per-browser storage such as ``st.session_state``. ``prepare`` runs
    on the caller's thread so the snapshot is consistent, and returns the call that
    runs on a worker thread. Only one save is in flight per browser session; newer
    revisions are coalesced into the next save after it finishes.
    """
    job_key = f"{prefix}_backup_job"
    saved_key = f"{prefix}_saved_revision"
    retry_key = f"{prefix}_retry_after"
    job = state.get(job_key)
    if job is not None:
        future, job_revision = job
        if not future.done():
            return False
        del state[job_key]
        try:
            success, detail = future.result()
        except Exception as exc:  # noqa: BLE001 - a worker failure must never reach the participant.
            success, detail = False, f"The background save did not finish: {exc}"
        if success:
            state[saved_key] = job_revision
        else:
            _LOGGER.warning("%s save will retry: %s", prefix, detail)
            state[retry_key] = time.monotonic() + RETRY_DELAY_SECONDS
    if state.get(saved_key, -1) >= revision:
        return True
    if time.monotonic() < state.get(retry_key, 0):
        return False
    state[job_key] = (_WORKERS.submit(_timed, prepare()), revision)
    return False


def check_connection_once(github_token: str, repo: str) -> None:
    """Log storage reachability once per server process without delaying a page."""
    with _CHECK_LOCK:
        if repo in _CHECKED_REPOS:
            return
        _CHECKED_REPOS.add(repo)

    def check() -> None:
        started = time.monotonic()
        success, detail = test_github_connection(github_token, repo)
        log = _LOGGER.info if success else _LOGGER.error
        log("Private storage check %s after %.1fs: %s", "passed" if success else "failed",
            time.monotonic() - started, detail)

    _WORKERS.submit(check)
