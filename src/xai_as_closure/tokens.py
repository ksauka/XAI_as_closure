"""Signed launch and completion tokens for Qualtrics handoffs."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import parse_qsl, unquote, urlencode, urlparse, urlunparse


class TokenError(ValueError):
    pass


MAX_TOKEN_LENGTH = 8192
ALLOWED_STUDIES = frozenset({"study1", "study2"})
INSECURE_DEPLOYMENT_SECRETS = frozenset(
    {"replace-with-a-long-random-secret", "local-pilot-secret"}
)


def require_deployment_secret(secret: str) -> None:
    """Reject missing, placeholder, or obviously weak deployment secrets."""
    if len(secret) < 32 or secret in INSECURE_DEPLOYMENT_SECRETS:
        raise TokenError(
            "STUDY_LINK_SECRET must be a non-placeholder value of at least 32 characters."
        )


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_token(payload: dict[str, Any], secret: str) -> str:
    if not secret:
        raise TokenError("A token secret is required.")
    body = _encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = _encode(
        hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    )
    return f"{body}.{signature}"


def verify_token(
    token: str,
    secret: str,
    *,
    expected_type: str = "launch",
    expected_study: str = "study1",
    now: int | None = None,
) -> dict[str, Any]:
    if not secret:
        raise TokenError("A token secret is required.")
    if not token or len(token) > MAX_TOKEN_LENGTH or token.count(".") != 1:
        raise TokenError("Malformed launch token.")
    body, supplied_signature = token.split(".")
    if not body or not supplied_signature:
        raise TokenError("Malformed launch token.")
    expected_signature = _encode(
        hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    )
    if not hmac.compare_digest(supplied_signature, expected_signature):
        raise TokenError("Invalid launch-token signature.")
    try:
        payload = json.loads(_decode(body))
    except (
        binascii.Error,
        UnicodeDecodeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        raise TokenError("Invalid launch-token payload.") from exc
    if not isinstance(payload, dict):
        raise TokenError("Invalid launch-token payload.")
    timestamp = int(time.time() if now is None else now)
    if payload.get("typ") != expected_type:
        raise TokenError("Unexpected token type.")
    if payload.get("study") != expected_study:
        raise TokenError("Token is for a different study.")
    try:
        issued_at = int(payload["iat"])
        expires_at = int(payload["exp"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TokenError("Launch token has invalid timestamps.") from exc
    if issued_at > expires_at or issued_at > timestamp + 300:
        raise TokenError("Launch token has invalid timestamps.")
    if expires_at <= timestamp:
        raise TokenError("Launch token has expired.")
    if expected_type == "launch" and not str(payload.get("linkage_id", "")).strip():
        raise TokenError("Token does not contain a linkage identifier.")
    if expected_type == "completion":
        if not str(payload.get("session_id", "")).strip():
            raise TokenError("Completion token does not contain a session identifier.")
        if not str(payload.get("linkage_hash", "")).strip():
            raise TokenError("Completion token does not contain a linkage hash.")
    return payload


def create_completion_token(
    *,
    session_id: str,
    linkage_hash: str,
    secret: str,
    study: str = "study1",
    ttl_seconds: int = 1800,
) -> str:
    if study not in ALLOWED_STUDIES:
        raise TokenError("Unknown study identifier.")
    if not session_id.strip() or not linkage_hash.strip():
        raise TokenError("Completion-token identifiers are required.")
    if not 0 < ttl_seconds <= 86400:
        raise TokenError(
            "Completion-token lifetime must be between 1 and 86400 seconds."
        )
    issued = int(time.time())
    return create_token(
        {
            "typ": "completion",
            "study": study,
            "session_id": session_id,
            "linkage_hash": linkage_hash,
            "iat": issued,
            "exp": issued + ttl_seconds,
        },
        secret,
    )


def safe_qualtrics_return_url(
    raw_url: str, completion_token: str, *, study: str = "study1"
) -> str | None:
    if not raw_url or study not in ALLOWED_STUDIES:
        return None
    decoded = unquote(raw_url)
    if not decoded.startswith("https://"):
        decoded = "https://" + decoded
    parsed = urlparse(decoded)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or parsed.username or parsed.password:
        return None
    if not (hostname == "qualtrics.com" or hostname.endswith(".qualtrics.com")):
        return None
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query[f"{study}_complete"] = "1"
    query["completion_token"] = completion_token
    return urlunparse(parsed._replace(query=urlencode(query)))
