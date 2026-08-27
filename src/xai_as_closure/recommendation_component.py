"""Local Streamlit component for inline, clickable recommendation citations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_COMPONENT_PATH = Path(__file__).with_name("recommendation_component_frontend")
_recommendation_component = components.declare_component(
    "xai_recommendation_passage",
    path=str(_COMPONENT_PATH),
)


def render_recommendation_passage(
    blocks: list[dict[str, Any]],
    *,
    anthropomorphic: bool,
    key: str,
) -> dict[str, str] | None:
    """Render fixed text with source buttons attached directly to each claim."""
    safe_blocks = []
    for block_index, block in enumerate(blocks):
        citations = [
            {
                "label": str(source.get("citation", "Document")),
                "token": f"{block_index}:{citation_index}",
            }
            for citation_index, source in enumerate(block.get("citations", []))
        ]
        safe_blocks.append({"text": str(block.get("text", "")), "citations": citations})
    value = _recommendation_component(
        blocks=safe_blocks,
        anthropomorphic=anthropomorphic,
        key=key,
        default=None,
    )
    return value if isinstance(value, dict) else None


__all__ = ["render_recommendation_passage"]
