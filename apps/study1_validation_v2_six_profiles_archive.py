"""Study 1 round2 entry point, release 2026-11-03.5."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xai_as_closure.study1_entry import run_entry

run_entry(validation_round="round2", expected_release="2026-11-03.5")
