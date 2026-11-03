"""Standalone entry point for Study 1's second expert-assessment round."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xai_as_closure.study1_app import run
run(validation_round="round2")
