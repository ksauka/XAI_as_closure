"""Study 1 initial entry point, release 2026-11-03.3."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xai_as_closure.study1_entry import run_entry

run_entry(validation_round="initial", expected_release="2026-11-03.3")
