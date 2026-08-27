"""Lightweight config helpers — no heavy dependencies (no chromadb, no langchain)."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def _read_permitted_config(
    permitted: set[str], env_path: Path | str = PROJECT_ENV_PATH
) -> dict[str, str]:
    """Read an allow-listed subset of a local dotenv file without dependencies."""
    path = Path(env_path)
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in raw_line or raw_line.lstrip().startswith("#"):
            continue
        key, value = raw_line.split("=", 1)
        key = key.strip()
        if key in permitted:
            values[key] = value.strip().strip('"').strip("'")
    return values


def load_project_openai_config(env_path: Path | str = PROJECT_ENV_PATH) -> None:
    """Load only agent-related settings from a local .env."""
    values = _read_permitted_config(
        {"OPENAI_API_KEY", "AGENTIC_REQUIRE_LIVE_RAG"}, env_path
    )
    for key, value in values.items():
        os.environ.setdefault(key, value)


def read_project_storage_config(
    env_path: Path | str = PROJECT_ENV_PATH,
) -> dict[str, str]:
    """Read only local private-storage settings for an explicit pilot fallback."""
    return _read_permitted_config(
        {
            "GITHUB_REPO",
            "GITHUB_TOKEN",
            "GITHUB_DATA_REPO",
            "GITHUB_DATA_TOKEN",
        },
        env_path,
    )
