"""Operational context engine for NexusOps AI Copilot."""

from __future__ import annotations

from analytics.incident_analysis import build_telemetry_evidence, derive_correlation_signals
from core.copilot_model import (
    AnalysisContext,
    CloudResourceContext,
    CorrelationContext,
    IncidentContext,
    OperationalContext,
    ServiceContext,
)
from core.correlation import build_hypotheses
from telemetry import TelemetrySnapshot, get_cloud_resources, get_service_profile, telemetry_seed, telemetry_unit


def build_operational_context(snapshot: TelemetrySnapshot) -> OperationalContext:
    """Build a compact, explainable operational context from existing telemetry."""
    services = _build_service_contexts(snapshot)
    incidents = _build_incident_contexts(snapshot)
    correlations, analysis = _build_correlation_and_analysis(snapshot, incidents)
    resources = _build_cloud_resource_contexts(snapshot)
    metrics = _snapshot_metrics(snapshot, incidents)

    return OperationalContext(
        environment=snapshot.environment,
        service_filter=snapshot.service,
        time_range=snapshot.time_range,
        telemetry_mode="SIMULATED TELEMETRY",
        system_health=snapshot.system_health,
        active_services=snapshot.active_services,
        open_incidents=snapshot.open_incidents,
        monthly_cost=snapshot.monthly_cost,
        operational_status=snapshot.operational_status,
        latency_ms=metrics["latency_ms"],
        error_rate=metrics["error_rate"],
        request_volume=metrics["request_volume"],
        services=services,
        active_incidents=incidents,
        correlations=correlations,
        analysis=analysis,
        cloud_resources=resources,
        data_freshness=f"Snapshot v{snapshot.time_range} window",
        demo_notice=(
            "Synthetic demo telemetry — not live production infrastructure data."
        ),
    )


def _snapshot_metrics(snapshot: TelemetrySnapshot, incidents: tuple[IncidentContext, ...]) -> dict[str, float]:
    if incidents:
        incident = next(item for item in snapshot.incidents if item.id == incidents[0].incident_id)
        evidence = build_telemetry_evidence(incident, snapshot)
        idx = evidence.incident_index
        return {
            "latency_ms": evidence.latency[min(idx, len(evidence.latency) - 1)],
            "error_rate": evidence.error_rate[min(idx, len(evidence.error_rate) - 1)],
            "request_volume": evidence.request_volume[min(idx, len(evidence.request_volume) - 1)],
        }
    peak = max(snapshot.chart_values) if snapshot.chart_values else 0.0
    return {"latency_ms": 120.0, "error_rate": 0.5, "request_volume": peak}


def _build_service_contexts(snapshot: TelemetrySnapshot) -> tuple[ServiceContext, ...]:
    from telemetry import SERVICE_LABELS

    contexts: list[ServiceContext] = []
    for slug, label in SERVICE_LABELS.items():
        seed = telemetry_seed(snapshot.environment, slug, snapshot.time_range, snapshot.service)
        profile = get_service_profile(label)
        cpu = round(28 + telemetry_unit(seed, 1) * 65 * profile["errors"], 1)
        latency = round(40 + telemetry_unit(seed, 2) * 780 * profile["latency"], 0)
        error_rate = round(0.3 + telemetry_unit(seed, 3) * 6 * profile["errors"], 2)
        health = round(max(62.0, 99.0 - cpu * 0.35 - error_rate * 2.5), 1)
        status = "Degraded" if cpu >= 75 or latency >= 500 else "Running"
        contexts.append(
            ServiceContext(
                name=label,
                slug=slug,
                health=health,
                latency_ms=latency,
                error_rate=error_rate,
                cpu=cpu,
                status=status,
            )
        )
    return tuple(contexts)


def _build_incident_contexts(snapshot: TelemetrySnapshot) -> tuple[IncidentContext, ...]:
    return tuple(
        IncidentContext(
            incident_id=item.id,
            title=item.title,
            severity=item.severity,
            status=item.status,
            service=item.service_label,
            impact=item.impact,
            description=item.description,
        )
        for item in snapshot.incidents
        if item.status != "resolved"
    )


def _build_correlation_and_analysis(
    snapshot: TelemetrySnapshot,
    incidents: tuple[IncidentContext, ...],
) -> tuple[tuple[CorrelationContext, ...], tuple[AnalysisContext, ...]]:
    if not incidents or not snapshot.incidents:
        return (), ()

    incident = snapshot.incidents[0]
    evidence = build_telemetry_evidence(incident, snapshot)
    signals = derive_correlation_signals(incident, evidence)
    hypotheses = build_hypotheses(incident.title, incident.service_label, signals)

    correlations = tuple(
        CorrelationContext(
            signal=name.replace("_", " ").title(),
            observed=value,
            detail=f"{name.replace('_', ' ')} {'detected' if value else 'not observed'} in demo telemetry.",
        )
        for name, value in signals.items()
        if value
    )
    analysis = tuple(
        AnalysisContext(
            hypothesis=item.title,
            confidence=item.confidence,
            evidence=item.evidence,
        )
        for item in hypotheses
    )
    return correlations, analysis


def _build_cloud_resource_contexts(snapshot: TelemetrySnapshot) -> tuple[CloudResourceContext, ...]:
    return tuple(
        CloudResourceContext(
            name=item["name"],
            label=item["label"],
            status=item["status"],
            cpu=item["cpu"],
            latency=item["latency"],
        )
        for item in get_cloud_resources(snapshot)
    )


def find_relevant_incident(
    context: OperationalContext,
    question: str,
) -> IncidentContext | None:
    """Identify the most relevant incident for a copilot question."""
    if not context.active_incidents:
        return None

    q = question.lower()
    for incident in context.active_incidents:
        if incident.service.lower() in q or incident.title.lower() in q:
            return incident
        if "payment" in q and "payment" in incident.service.lower():
            return incident

    ranked = sorted(
        context.active_incidents,
        key=lambda item: {"critical": 3, "warning": 2, "info": 1}.get(item.severity, 0),
        reverse=True,
    )
    return ranked[0]
