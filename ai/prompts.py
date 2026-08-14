"""Prompt construction for NexusOps AI Copilot."""

from __future__ import annotations

import json

from core.copilot_model import CopilotRequest, OperationalContext

SYSTEM_PROMPT = """You are NexusOps AI Copilot, an operational decision-support assistant.

Rules:
- Reason only from the supplied operational evidence.
- Clearly distinguish evidence from inference.
- Do not invent telemetry, incidents, deployments, or executed actions.
- Identify uncertainty explicitly.
- Provide a confidence score from 0 to 100.
- Prioritize severity and business impact.
- Recommend safe investigation steps only.
- Never claim an infrastructure action was executed.
- Never expose secrets or request credentials.
- Prefer: Evidence -> reasoning -> recommendation.

Respond with valid JSON only using this schema:
{
  "summary": "string",
  "diagnosis": "string",
  "evidence": ["string"],
  "confidence": 0,
  "recommended_investigation": ["string"],
  "recommended_actions": ["string"],
  "uncertainties": ["string"],
  "affected_services": ["string"],
  "severity": "critical|warning|info|none"
}
"""


def build_user_prompt(request: CopilotRequest) -> str:
    """Serialize operational context and user question for the model."""
    context_payload = _context_to_dict(request.context)
    return (
        f"User question: {request.question}\n\n"
        f"Operational context (simulated demo telemetry):\n"
        f"{json.dumps(context_payload, indent=2)}"
    )


def _context_to_dict(context: OperationalContext) -> dict:
    return {
        "system": {
            "environment": context.environment,
            "service_filter": context.service_filter,
            "time_range": context.time_range,
            "telemetry_mode": context.telemetry_mode,
            "system_health": context.system_health,
            "active_services": context.active_services,
            "open_incidents": context.open_incidents,
            "monthly_cost": context.monthly_cost,
            "operational_status": context.operational_status,
            "latency_ms": context.latency_ms,
            "error_rate": context.error_rate,
            "request_volume": context.request_volume,
            "data_freshness": context.data_freshness,
        },
        "services": [service.__dict__ for service in context.services],
        "active_incidents": [incident.__dict__ for incident in context.active_incidents],
        "correlations": [item.__dict__ for item in context.correlations],
        "analysis": [
            {
                "hypothesis": item.hypothesis,
                "confidence": item.confidence,
                "evidence": list(item.evidence),
            }
            for item in context.analysis
        ],
        "cloud_resources": [resource.__dict__ for resource in context.cloud_resources],
        "demo_notice": context.demo_notice,
    }
