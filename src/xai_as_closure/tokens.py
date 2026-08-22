"""Signed launch and completion tokens for Qualtrics handoffs."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse


class TokenError(ValueError):
    pass


@dataclass(frozen=True)
class LaunchContext:
    linkage_id: str
    return_route: str
    pilot: bool = False


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_token(payload: dict[str, Any], secret: str) -> str:
    if not secret:
        raise TokenError("A token secret is required.")
    body = _encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature = _encode(hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest())
    return f"{body}.{signature}"


def verify_token(
    token: str,
    secret: str,
    *,
    expected_type: str = "launch",
    expected_study: str = "study1",
    now: int | None = None,
) -> dict[str, Any]:
    try:
        body, supplied_signature = token.split(".", 1)
    except ValueError as exc:
        raise TokenError("Malformed launch token.") from exc
    expected_signature = _encode(
        hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    )
    if not hmac.compare_digest(supplied_signature, expected_signature):
        raise TokenError("Invalid launch-token signature.")
    try:
        payload = json.loads(_decode(body))
    except (ValueError, json.JSONDecodeError) as exc:
        raise TokenError("Invalid launch-token payload.") from exc
    timestamp = int(time.time() if now is None else now)
    if payload.get("typ") != expected_type:
        raise TokenError("Unexpected token type.")
    if payload.get("study") != expected_study:
        raise TokenError("Token is for a different study.")
    if int(payload.get("exp", 0)) < timestamp:
        raise TokenError("Launch token has expired.")
    if not str(payload.get("linkage_id", "")).strip():
        raise TokenError("Token does not contain a linkage identifier.")
    return payload


def create_completion_token(
    *, session_id: str, linkage_hash: str, secret: str, ttl_seconds: int = 1800
) -> str:
    issued = int(time.time())
    return create_token(
        {
            "typ": "completion",
            "study": "study1",
            "session_id": session_id,
            "linkage_hash": linkage_hash,
            "iat": issued,
            "exp": issued + ttl_seconds,
        },
        secret,
    )


def safe_qualtrics_return_url(raw_url: str, completion_token: str) -> str | None:
    if not raw_url:
        return None
    decoded = unquote(raw_url)
    if not decoded.startswith(("https://", "http://")):
        decoded = "https://" + decoded
    parsed = urlparse(decoded)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"}:
        return None
    if not (hostname == "qualtrics.com" or hostname.endswith(".qualtrics.com")):
        return None
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["study1_complete"] = "1"
    query["completion_token"] = completion_token
    return urlunparse(parsed._replace(query=urlencode(query)))
