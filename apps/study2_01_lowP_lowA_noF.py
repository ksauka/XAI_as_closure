"""Study 2 condition 1: low provenance, low anthropomorphism, no forcing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xai_as_closure.study2_app import run

run("P0_A0_F0")
