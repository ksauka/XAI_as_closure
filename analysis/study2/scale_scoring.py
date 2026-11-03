"""Fail-closed scale scoring: final item keys must be frozen before use."""

from __future__ import annotations

import math


def score_scale(response, specification):
    if specification.get("status") != "frozen":
        raise ValueError("Scale item specification is not frozen")
    items = specification.get("items", [])
    low, high = specification.get("response_min"), specification.get("response_max")
    reverse = specification.get("reverse_item_ids")
    if (
        not items
        or len(items) != len(set(items))
        or not isinstance(low, (int, float))
        or not isinstance(high, (int, float))
        or low >= high
        or not isinstance(reverse, list)
        or not set(reverse) <= set(items)
    ):
        raise ValueError("Incomplete or inconsistent scale specification")
    values = []
    for item in items:
        raw = response.get(item)
        if raw in (None, ""):
            continue
        if isinstance(raw, bool):
            raise TypeError("Boolean is not a valid scale response")
        value = float(raw)
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"Out-of-range response for {item}")
        values.append(low + high - value if item in reverse else value)
    return (
        sum(values) / len(values)
        if len(values) >= math.ceil(0.8 * len(items))
        else None
    )
