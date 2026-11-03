"""Executable release audit for the frozen Study 2 research instrument."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .cases import PROJECT_ROOT, CaseRepository, material_manifest
from .conditions import CONDITIONS
from .decision_agent import Study2DecisionAgent
from .logger import APPLICATION_VERSION, EVENT_SCHEMA_VERSION
from .study2 import STATE_SCHEMA_VERSION
from .study2_delivery import DELIVERY_SPEC_VERSION

FREEZE_PATH = PROJECT_ROOT / "study_CHI" / "STUDY2_MATERIAL_FREEZE.json"

EXPECTED_ENTRY_POINTS = {
    "study2_01_lowP_lowA_noF.py": "P0_A0_F0",
    "study2_02_lowP_lowA_F.py": "P0_A0_F1",
    "study2_03_lowP_highA_noF.py": "P0_A1_F0",
    "study2_04_lowP_highA_F.py": "P0_A1_F1",
    "study2_05_highP_lowA_noF.py": "P1_A0_F0",
    "study2_06_highP_lowA_F.py": "P1_A0_F1",
    "study2_07_highP_highA_noF.py": "P1_A1_F0",
    "study2_08_highP_highA_F.py": "P1_A1_F1",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_release(freeze_path: Path = FREEZE_PATH) -> list[str]:
    """Return release-blocking invariant failures; an empty list means pass."""
    failures: list[str] = []
    try:
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Material freeze cannot be read: {exc}"]

    versions = {
        "delivery_spec_version": DELIVERY_SPEC_VERSION,
        "study2_state_schema": STATE_SCHEMA_VERSION,
        "study2_event_schema": EVENT_SCHEMA_VERSION,
        "study2_application_version": APPLICATION_VERSION,
    }
    for key, observed in versions.items():
        if freeze.get(key) != observed:
            failures.append(
                f"{key} differs from the freeze: {observed!r} != {freeze.get(key)!r}"
            )

    manifest = material_manifest()
    if freeze.get("material_set") != manifest["material_set"]:
        failures.append("Runtime material-set identifier differs from the freeze.")
    if freeze.get("material_manifest_sha256") != manifest["manifest_sha256"]:
        failures.append("Runtime material manifest differs from the freeze.")

    files = freeze.get("files")
    if not isinstance(files, dict) or not files:
        failures.append("The material freeze has no file hashes.")
    else:
        for relative, expected_hash in files.items():
            path = PROJECT_ROOT / str(relative)
            if not path.is_file():
                failures.append(f"Frozen file is missing: {relative}")
            elif _sha256(path) != expected_hash:
                failures.append(f"Frozen file changed: {relative}")

    expected_matrix = {
        (explanation, anthropomorphic, forcing)
        for explanation in (False, True)
        for anthropomorphic in (False, True)
        for forcing in (False, True)
    }
    observed_matrix = {
        (condition.explanation, condition.anthropomorphic, condition.forcing)
        for condition in CONDITIONS.values()
    }
    if len(CONDITIONS) != 8 or observed_matrix != expected_matrix:
        failures.append(
            "The registered conditions do not form the complete 2 x 2 x 2 matrix."
        )

    app_root = PROJECT_ROOT / "apps"
    observed_apps = {path.name for path in app_root.glob("study2_*.py")}
    if observed_apps != set(EXPECTED_ENTRY_POINTS):
        failures.append("Study 2 entry points differ from the frozen eight-app set.")
    for filename, condition_id in EXPECTED_ENTRY_POINTS.items():
        path = app_root / filename
        if path.is_file() and f'run("{condition_id}")' not in path.read_text(
            encoding="utf-8"
        ):
            failures.append(f"{filename} is not locked to {condition_id}.")

    try:
        cases = CaseRepository()
    except (KeyError, TypeError, ValueError) as exc:
        failures.append(f"The case set is invalid: {exc}")
        return failures

    if cases.case_set_id != freeze.get("case_set_id"):
        failures.append("Case-set identifier differs from the freeze.")
    frozen_truth = freeze.get("ground_truth", {})
    frozen_verdicts = freeze.get("fixed_ai_verdicts", {})
    for reference in cases.references:
        labels = cases.analysis_labels(reference)
        if labels["ground_truth"] != frozen_truth.get(reference):
            failures.append(f"Ground truth changed for {reference}.")
        outputs = {
            condition_id: Study2DecisionAgent(condition=condition, cases=cases).assess(
                reference
            )
            for condition_id, condition in CONDITIONS.items()
        }
        recommendations = {output.recommendation for output in outputs.values()}
        rationales = {output.rationale for output in outputs.values()}
        if recommendations != {frozen_verdicts.get(reference)}:
            failures.append(
                f"Fixed AI verdict changed across conditions for {reference}."
            )
        if len(rationales) != 1:
            failures.append(
                f"Substantive rationale drifts across conditions for {reference}."
            )
        for condition_id, output in outputs.items():
            condition = CONDITIONS[condition_id]
            payload = output.participant_payload()
            visible_sources = payload.get("visible_sources", [])
            rationale = payload.get("rationale")
            if condition.explanation:
                if not visible_sources or not rationale:
                    failures.append(
                        f"Explanation-present output is incomplete for {reference}/{condition_id}."
                    )
            elif visible_sources or rationale is not None:
                failures.append(
                    f"Explanation-absent output leaks evidence for {reference}/{condition_id}."
                )
            expected_speaker = (
                "AI screening assistant"
                if condition.anthropomorphic
                else "AI screening system"
            )
            if payload.get("speaker_label") != expected_speaker:
                failures.append(
                    f"Delivery register is incorrect for {reference}/{condition_id}."
                )

    return failures


def main() -> int:
    failures = audit_release()
    if failures:
        print("Study 2 release audit: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Study 2 release audit: PASS")
    print("- frozen materials match")
    print("- eight condition-locked apps cover the 2 x 2 x 2 matrix")
    print("- recommendations and rationales are condition-invariant")
    print("- explanation visibility and delivery registers are correct")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
