"""Incident intelligence domain models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TimelineEvent:
    time: str
    label: str
    category: str


@dataclass(frozen=True)
class RelatedService:
    name: str
    slug: str
    health: float
    latency_ms: float
    error_rate: float
    cpu: float
    relationship: str


@dataclass(frozen=True)
class Hypothesis:
    title: str
    confidence: int
    evidence: tuple[str, ...]
    rank: str


@dataclass(frozen=True)
class Recommendation:
    step: int
    action: str
    reason: str


@dataclass(frozen=True)
class BusinessImpact:
    technical_signal: str
    business_interpretation: str
    checkout_success_delta: float
    affected_transactions: int
    severity_level: str
    customer_impact: str
    estimated_hourly_risk: str


@dataclass(frozen=True)
class TelemetryEvidence:
    labels: tuple[str, ...]
    latency: tuple[float, ...]
    error_rate: tuple[float, ...]
    request_volume: tuple[float, ...]
    database_cpu: tuple[float, ...]
    incident_index: int


@dataclass(frozen=True)
class ExecutiveMetrics:
    error_rate: float
    latency_ms: float
    traffic_per_min: float
    business_impact_summary: str
    affected_services: int


@dataclass(frozen=True)
class IncidentInvestigation:
    incident_id: str
    title: str
    severity: str
    status: str
    service: str
    service_label: str
    detected_at: str
    description: str
    impact: str
    executive_metrics: ExecutiveMetrics
    timeline: tuple[TimelineEvent, ...]
    evidence: TelemetryEvidence
    related_services: tuple[RelatedService, ...]
    hypotheses: tuple[Hypothesis, ...]
    business_impact: BusinessImpact
    recommendations: tuple[Recommendation, ...]
    demo_notice: str = (
        "Synthetic demo telemetry — not live production infrastructure data."
    )


def severity_weight(severity: str) -> int:
    """Return numeric weight for severity classification."""
    return {"critical": 3, "warning": 2, "info": 1}.get(severity.lower(), 0)
