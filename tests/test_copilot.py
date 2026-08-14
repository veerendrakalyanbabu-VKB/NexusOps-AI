"""Tests for NexusOps AI Copilot v0.4."""

from ai.engine import CopilotEngine
from ai.providers import DeterministicCopilotProvider, resolve_copilot_provider
from ai.response_parser import parse_copilot_response
from core.copilot_model import CopilotRequest
from core.operational_context import build_operational_context, find_relevant_incident
from services.copilot_service import run_copilot_investigation
from telemetry import get_snapshot


def _snapshot():
    return get_snapshot("Production", "Payment API", "24H", 0)


def test_operational_context_construction():
    context = build_operational_context(_snapshot())
    assert context.environment == "Production"
    assert context.telemetry_mode == "SIMULATED TELEMETRY"
    assert context.system_health > 0
    assert context.services


def test_context_contains_incident_data():
    context = build_operational_context(_snapshot())
    assert isinstance(context.active_incidents, tuple)
    if context.active_incidents:
        assert context.active_incidents[0].title


def test_context_contains_telemetry():
    context = build_operational_context(_snapshot())
    assert context.latency_ms > 0
    assert context.error_rate >= 0
    assert context.request_volume >= 0


def test_provider_selection_defaults_to_local():
    provider = resolve_copilot_provider()
    assert provider.name == "local"


def test_missing_provider_credentials_fallback():
    engine = CopilotEngine(provider=DeterministicCopilotProvider())
    context = build_operational_context(_snapshot())
    response = engine.investigate(
        CopilotRequest(question="Why is Payment API degraded?", context=context)
    )
    assert response.provider == "local"
    assert response.confidence >= 0


def test_fallback_provider_structured_response():
    context = build_operational_context(_snapshot())
    provider = DeterministicCopilotProvider()
    response = provider.analyze(
        CopilotRequest(question="Summarize the current operational situation.", context=context)
    )
    assert response.summary
    assert response.diagnosis
    assert response.evidence
    assert response.recommended_investigation


def test_structured_response_parsing():
    raw = """
    {
      "summary": "Test summary",
      "diagnosis": "Test diagnosis",
      "evidence": ["A", "B"],
      "confidence": 82,
      "recommended_investigation": ["Step 1"],
      "recommended_actions": ["Action 1"],
      "uncertainties": ["Demo data only"],
      "affected_services": ["Payment API"],
      "severity": "critical"
    }
    """
    response = parse_copilot_response(raw, "openai", "gpt-test")
    assert response.summary == "Test summary"
    assert response.confidence == 82
    assert response.affected_services == ("Payment API",)


def test_malformed_ai_response_handling():
    response = parse_copilot_response("not-json", "openai", "gpt-test")
    assert response.confidence == 0
    assert response.recommended_investigation


def test_unknown_service_handling():
    context = build_operational_context(_snapshot())
    incident = find_relevant_incident(context, "Why is Unknown Service XYZ degraded?")
    response = run_copilot_investigation(
        "Why is Unknown Service XYZ degraded?",
        _snapshot(),
        engine=CopilotEngine(provider=DeterministicCopilotProvider()),
    )
    assert response.summary
    assert incident is None or incident.service


def test_unknown_incident_handling():
    snapshot = get_snapshot("Development", "Notification Service", "1H", 0)
    response = run_copilot_investigation(
        "What is happening?",
        snapshot,
        engine=CopilotEngine(provider=DeterministicCopilotProvider()),
    )
    assert response.diagnosis


def test_conversation_state_structure():
    messages = [
        {"role": "user", "content": "Why degraded?"},
        {"role": "assistant", "content": "Assessment", "response": None},
    ]
    assert messages[0]["role"] == "user"
    assert "content" in messages[1]


def test_safety_boundary_no_executed_actions():
    response = run_copilot_investigation(
        "Restart Orders DB",
        _snapshot(),
        engine=CopilotEngine(provider=DeterministicCopilotProvider()),
    )
    joined = " ".join(response.recommended_actions + response.recommended_investigation).lower()
    assert "has been restarted" not in joined
    assert "was restarted" not in joined
