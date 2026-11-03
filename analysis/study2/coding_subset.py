"""Create a seeded, profile-stratified blind coding sheet from trial exports."""

import argparse
import csv
import hashlib
import math
import random
from pathlib import Path


def select_subset(rows, seed=20261022):
    by_profile = {f"C-0{i}": [] for i in range(1, 7)}
    seen = set()
    for row in rows:
        key = row["session_id"] + ":" + row["reference"]
        if key in seen:
            raise ValueError("Duplicate session/profile; consolidate archives first")
        seen.add(key)
        reference = row["reference"]
        if reference not in by_profile:
            raise ValueError("Unknown profile")
        by_profile[reference].append(
            {
                "response_id": hashlib.sha256(key.encode()).hexdigest()[:24],
                "reference": reference,
                "response": row.get("evidence_recall", ""),
                "coder_1": "",
                "coder_2": "",
                "adjudicated_code": "",
                "adjudication_note": "",
            }
        )
    selected = []
    for reference, records in sorted(by_profile.items()):
        records.sort(key=lambda r: r["response_id"])
        count = min(len(records), max(20, math.ceil(len(records) * 0.25)))
        selected.extend(random.Random(f"{seed}:{reference}").sample(records, count))
    return sorted(selected, key=lambda r: (r["reference"], r["response_id"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261022)
    args = parser.parse_args()
    with args.input.open(newline="") as handle:
        rows = select_subset(list(csv.DictReader(handle)), args.seed)
    if not rows:
        raise ValueError("No trial records")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
