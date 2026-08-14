"""Parsing and validation for structured Copilot responses."""

from __future__ import annotations

import json
import re
from typing import Any

from core.copilot_model import CopilotResponse


def parse_copilot_response(
    raw_text: str,
    provider: str,
    model: str,
    fallback: CopilotResponse | None = None,
) -> CopilotResponse:
    """Parse model output into a validated CopilotResponse."""
    payload = _extract_json(raw_text)
    if payload is None:
        if fallback is not None:
            return fallback
        return _minimal_fallback_response(provider, model, raw_text)

    try:
        return _from_payload(payload, provider, model)
    except (KeyError, TypeError, ValueError):
        if fallback is not None:
            return fallback
        return _minimal_fallback_response(provider, model, raw_text)


def _extract_json(raw_text: str) -> dict[str, Any] | None:
    text = raw_text.strip()
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _from_payload(payload: dict[str, Any], provider: str, model: str) -> CopilotResponse:
    return CopilotResponse(
        summary=str(payload.get("summary", "Operational assessment unavailable.")),
        diagnosis=str(payload.get("diagnosis", "No diagnosis provided.")),
        evidence=_as_tuple(payload.get("evidence")),
        confidence=_clamp_confidence(payload.get("confidence", 0)),
        recommended_investigation=_as_tuple(payload.get("recommended_investigation")),
        recommended_actions=_as_tuple(payload.get("recommended_actions")),
        uncertainties=_as_tuple(payload.get("uncertainties")),
        affected_services=_as_tuple(payload.get("affected_services")),
        severity=str(payload.get("severity", "none")),
        provider=provider,
        model=model,
    )


def _as_tuple(value: Any) -> tuple[str, ...]:
    if not value:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(item) for item in value)


def _clamp_confidence(value: Any) -> int:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, number))


def _minimal_fallback_response(provider: str, model: str, raw_text: str) -> CopilotResponse:
    summary = raw_text.strip()[:500] if raw_text.strip() else "Malformed AI response received."
    return CopilotResponse(
        summary=summary,
        diagnosis="Unable to parse structured AI output. Showing safe fallback summary.",
        evidence=(),
        confidence=0,
        recommended_investigation=("Review operational context manually.",),
        recommended_actions=("Retry the investigation after verifying provider configuration.",),
        uncertainties=("Structured AI response could not be validated.",),
        affected_services=(),
        severity="none",
        provider=provider,
        model=model,
    )
