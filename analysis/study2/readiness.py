"""Report unresolved operational inputs without fabricating a launch approval."""

import json
from pathlib import Path


def unresolved(spec):
    issues = []
    validation = spec.get("material_validation", {})
    if validation and (validation.get("status") != "complete" or validation.get("validated_case_set_id") != validation.get("case_set_id")):
        issues.append("second expert assessment of the revised shared material version")
    if not spec.get("selected_analysable_target"):
        issues.append("selected analysable target and documented precision decision")
    if not spec.get("h2_maximum_log_ci_width"):
        issues.append("substantively acceptable H2 precision criterion")
    if not spec["timing"].get("soft_allowance_seconds") or not spec["timing"].get(
        "pilot_input_sha256"
    ):
        issues.append("complete eight-cell pilot and derived timing value")
    if spec.get("precision_decision") is None:
        issues.append("documented precision decision linked to simulation artifact")
    if spec["timing"].get("automatic_submission"):
        issues.append("automatic submission must remain disabled")
    survey = spec["questionnaire"]
    if not survey.get("survey_export_sha256"):
        issues.append("final Qualtrics export hash")
    for name in survey.get(
        "active_constructs",
        ["PPBE", "ANT", "PCE", "TRUST", "TRUST_PROPENSITY", "RISK_AVERSION"],
    ):
        scale = survey["scales"][name]
        missing = []
        if not scale.get("items"):
            missing.append("item wording/IDs")
        elif set(scale.get("item_text", {})) != set(scale["items"]):
            missing.append("verbatim item text")
        if (
            scale.get("response_min") is None
            or scale.get("response_max") is None
            or not scale.get("endpoint_labels")
        ):
            missing.append("response range/endpoints")
        if scale.get("reverse_item_ids") is None:
            missing.append("reverse-scoring keys")
        if not scale.get("qualtrics_export_map"):
            missing.append("verified Qualtrics mapping")
        if scale.get("status") != "frozen":
            missing.append("scale freeze")
        if missing:
            issues.append(name + ": " + ", ".join(missing))
    if (
        spec["attention_rule"].get("status") != "frozen"
        or not spec["attention_rule"].get("item_id")
        or spec["attention_rule"].get("pass_value") is None
    ):
        issues.append("prespecified Qualtrics attention item and pass value")
    return issues


def main():
    root = Path(__file__).resolve().parents[2]
    spec = json.loads((root / "study_CHI/STUDY2_OPERATIONAL_SPEC.json").read_text())
    issues = unresolved(spec)
    print(
        "Study 2 operational readiness: "
        + (
            "INCOMPLETE"
            if issues
            else "specified; verify external ethics/deployment gates separately"
        )
    )
    for issue in issues:
        print("- " + issue)
    return 2 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
