"""Generate pilot timing value without pretending a pilot has occurred."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def derive_timing(rows):
    expected = {f"P{p}_A{a}_F{f}" for p in (0, 1) for a in (0, 1) for f in (0, 1)}
    cells = {key: [] for key in expected}
    seen = set()
    for row in rows:
        if row["session_id"] in seen:
            raise ValueError("Duplicate pilot session")
        seen.add(row["session_id"])
        cell = row["condition_id"]
        if cell not in cells:
            raise ValueError("Unknown condition")
        if str(row.get("complete", "")).lower() not in {"1", "true"}:
            continue
        duration = float(row["total_duration_seconds"])
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("Invalid duration")
        cells[cell].append(duration)
    if any(len(values) < 5 for values in cells.values()):
        raise ValueError("Need five complete pilot sessions in each of all eight cells")
    q95 = {
        key: float(np.quantile(values, 0.95)) for key, values in sorted(cells.items())
    }
    return {
        "soft_allowance_seconds": math.ceil(1.25 * max(q95.values()) / 60) * 60,
        "cell_q95_seconds": q95,
        "cell_counts": {key: len(values) for key, values in sorted(cells.items())},
        "automatic_submission": False,
        "hard_timeout_seconds": None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.input.open(newline="") as handle:
        result = derive_timing(list(csv.DictReader(handle)))
    result["pilot_input_sha256"] = hashlib.sha256(args.input.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
