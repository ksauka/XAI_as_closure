"""Study 2 condition 8: high provenance, high anthropomorphism, forcing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xai_as_closure.study2_app import run

run("P1_A1_F1")
