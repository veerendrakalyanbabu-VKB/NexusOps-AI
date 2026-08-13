"""Incident investigation service."""

from __future__ import annotations

from analytics.incident_analysis import (
    build_business_impact,
    build_executive_metrics,
    build_recommendations,
    build_telemetry_evidence,
    build_timeline,
    derive_correlation_signals,
)
from core.correlation import build_hypotheses
from core.incident_model import IncidentInvestigation, RelatedService
from telemetry import Incident, TelemetrySnapshot, get_service_profile, telemetry_seed, telemetry_unit


SERVICE_DEPENDENCIES = {
    "payment-api": ("orders-db", "frontend-web"),
    "orders-db": (),
    "frontend-web": ("auth-service",),
    "auth-service": (),
    "notification-service": (),
}


def build_investigation(
    incident: Incident | None,
    snapshot: TelemetrySnapshot,
) -> IncidentInvestigation | None:
    """Build a full incident investigation from demo telemetry."""
    if incident is None:
        return None

    evidence = build_telemetry_evidence(incident, snapshot)
    executive_metrics = build_executive_metrics(incident, evidence)
    timeline = build_timeline(incident, snapshot)
    signals = derive_correlation_signals(incident, evidence)
    hypotheses = build_hypotheses(incident.title, incident.service_label, signals)
    business_impact = build_business_impact(incident, evidence, snapshot)
    recommendations = build_recommendations(incident, hypotheses)
    related_services = _build_related_services(incident, snapshot, evidence)

    return IncidentInvestigation(
        incident_id=incident.id,
        title=incident.title,
        severity=incident.severity,
        status=incident.status,
        service=incident.service,
        service_label=incident.service_label,
        detected_at=incident.timestamp,
        description=incident.description,
        impact=incident.impact,
        executive_metrics=executive_metrics,
        timeline=timeline,
        evidence=evidence,
        related_services=related_services,
        hypotheses=hypotheses,
        business_impact=business_impact,
        recommendations=recommendations,
    )


def find_incident(snapshot: TelemetrySnapshot, incident_id: str | None) -> Incident | None:
    """Return an incident from the snapshot by id, if present."""
    if not incident_id:
        return None
    for incident in snapshot.incidents:
        if incident.id == incident_id:
            return incident
    return None


def _build_related_services(
    incident: Incident,
    snapshot: TelemetrySnapshot,
    evidence,
) -> tuple[RelatedService, ...]:
    """Build related service correlation cards."""
    seed = telemetry_seed(incident.id, snapshot.environment, "related")
    chain = [incident.service, *SERVICE_DEPENDENCIES.get(incident.service, ())]

    related: list[RelatedService] = []
    for index, slug in enumerate(chain):
        from telemetry import SERVICE_LABELS

        label = SERVICE_LABELS.get(slug, slug)
        profile = get_service_profile(label)
        cpu = round(38 + telemetry_unit(seed, index + 1) * 55 * profile["errors"], 1)
        latency = round(60 + telemetry_unit(seed, index + 10) * 760 * profile["latency"], 1)
        error_rate = round(0.3 + telemetry_unit(seed, index + 20) * 6 * profile["errors"], 2)
        health = round(max(62.0, 99.0 - cpu * 0.35 - error_rate * 2.5), 1)

        if index == 0:
            relationship = "Primary affected service"
        elif index == 1:
            relationship = "Upstream dependency"
        else:
            relationship = "Downstream dependent"

        related.append(
            RelatedService(
                name=label,
                slug=slug,
                health=health,
                latency_ms=latency,
                error_rate=error_rate,
                cpu=cpu,
                relationship=relationship,
            )
        )

    return tuple(related)
