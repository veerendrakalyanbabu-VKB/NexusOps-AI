"""Tests for NexusOps AI incident intelligence."""

from analytics.incident_analysis import (
    build_business_impact,
    build_telemetry_evidence,
    build_timeline,
    derive_correlation_signals,
)
from core.correlation import build_hypotheses, evaluate_signals
from core.incident_model import severity_weight
from services.incident_service import build_investigation, find_incident
from telemetry import Incident, get_snapshot


def _sample_incident() -> Incident:
    return Incident(
        id="dev-payment-api-0",
        severity="critical",
        title="Payment API latency spike",
        service="payment-api",
        service_label="Payment API",
        timestamp="2 min ago",
        status="investigating",
        description="Latency reached 820 ms with a 7.4% error rate.",
        impact="High — checkout success rate dropped 4.2%.",
        recommended_step="Inspect slow queries on Orders DB.",
    )


def _sample_snapshot():
    return get_snapshot("Development", "All Services", "24H", 0)


def test_incident_model_creation():
    investigation = build_investigation(_sample_incident(), _sample_snapshot())
    assert investigation is not None
    assert investigation.incident_id == "dev-payment-api-0"
    assert investigation.title == "Payment API latency spike"
    assert investigation.executive_metrics.latency_ms > 0


def test_severity_classification():
    assert severity_weight("critical") == 3
    assert severity_weight("warning") == 2
    assert severity_weight("info") == 1


def test_correlation_scoring():
    signals = {
        "latency_spike": True,
        "error_rate_spike": True,
        "cpu_saturation": True,
        "deployment_recent": True,
    }
    scores = evaluate_signals(signals)
    assert scores["latency_spike"] == 28
    assert scores["cpu_saturation"] == 22


def test_root_cause_confidence_calculation():
    signals = {
        "latency_spike": True,
        "error_rate_spike": True,
        "cpu_saturation": True,
        "database_pressure": True,
        "deployment_recent": True,
        "traffic_increase": True,
        "dependent_degradation": True,
    }
    hypotheses = build_hypotheses("Payment API latency spike", "Payment API", signals)
    assert hypotheses
    assert hypotheses[0].rank == "primary"
    assert 0 < hypotheses[0].confidence <= 95
    assert hypotheses[0].evidence


def test_incident_timeline_generation():
    incident = _sample_incident()
    snapshot = _sample_snapshot()
    timeline = build_timeline(incident, snapshot)
    assert len(timeline) >= 4
    assert timeline[-1].category == "incident"
    assert timeline[0].time.startswith("13:")


def test_business_impact_calculation():
    incident = _sample_incident()
    snapshot = _sample_snapshot()
    evidence = build_telemetry_evidence(incident, snapshot)
    impact = build_business_impact(incident, evidence, snapshot)
    assert impact.checkout_success_delta > 0
    assert impact.affected_transactions > 0
    assert impact.severity_level == "High"
    assert "demo" in impact.estimated_hourly_risk.lower()


def test_find_incident_and_deterministic_investigation():
    snapshot = _sample_snapshot()
    incident = find_incident(snapshot, snapshot.incidents[0].id if snapshot.incidents else None)
    if incident:
        first = build_investigation(incident, snapshot)
        second = build_investigation(incident, snapshot)
        assert first is not None and second is not None
        assert first.executive_metrics.latency_ms == second.executive_metrics.latency_ms
        assert len(first.timeline) == len(second.timeline)


def test_correlation_signals_from_evidence():
    incident = _sample_incident()
    snapshot = _sample_snapshot()
    evidence = build_telemetry_evidence(incident, snapshot)
    signals = derive_correlation_signals(incident, evidence)
    assert isinstance(signals["latency_spike"], bool)
    assert isinstance(signals["deployment_recent"], bool)
