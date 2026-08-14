"""Structured models for NexusOps AI Copilot."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceContext:
    name: str
    slug: str
    health: float
    latency_ms: float
    error_rate: float
    cpu: float
    status: str


@dataclass(frozen=True)
class IncidentContext:
    incident_id: str
    title: str
    severity: str
    status: str
    service: str
    impact: str
    description: str


@dataclass(frozen=True)
class CorrelationContext:
    signal: str
    observed: bool
    detail: str


@dataclass(frozen=True)
class AnalysisContext:
    hypothesis: str
    confidence: int
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class CloudResourceContext:
    name: str
    label: str
    status: str
    cpu: str
    latency: str


@dataclass(frozen=True)
class OperationalContext:
    environment: str
    service_filter: str
    time_range: str
    telemetry_mode: str
    system_health: float
    active_services: int
    open_incidents: int
    monthly_cost: float
    operational_status: str
    latency_ms: float
    error_rate: float
    request_volume: float
    services: tuple[ServiceContext, ...]
    active_incidents: tuple[IncidentContext, ...]
    correlations: tuple[CorrelationContext, ...]
    analysis: tuple[AnalysisContext, ...]
    cloud_resources: tuple[CloudResourceContext, ...]
    data_freshness: str
    demo_notice: str


@dataclass(frozen=True)
class CopilotRequest:
    question: str
    context: OperationalContext


@dataclass(frozen=True)
class CopilotResponse:
    summary: str
    diagnosis: str
    evidence: tuple[str, ...]
    confidence: int
    recommended_investigation: tuple[str, ...]
    recommended_actions: tuple[str, ...]
    uncertainties: tuple[str, ...]
    affected_services: tuple[str, ...]
    severity: str
    provider: str
    model: str

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "diagnosis": self.diagnosis,
            "evidence": list(self.evidence),
            "confidence": self.confidence,
            "recommended_investigation": list(self.recommended_investigation),
            "recommended_actions": list(self.recommended_actions),
            "uncertainties": list(self.uncertainties),
            "affected_services": list(self.affected_services),
            "severity": self.severity,
            "provider": self.provider,
            "model": self.model,
        }
