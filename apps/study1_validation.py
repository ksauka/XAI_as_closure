"""Entry point for the CHI 2027 Study 1 expert-validation application."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from xai_as_closure.study1_app import run

run()
