"""Incident analysis: timeline, telemetry evidence, and business impact."""

from __future__ import annotations

from core.incident_model import (
    BusinessImpact,
    ExecutiveMetrics,
    Recommendation,
    TelemetryEvidence,
    TimelineEvent,
)
from telemetry import Incident, TelemetrySnapshot, get_service_profile, telemetry_seed, telemetry_unit


def _analysis_seed(incident: Incident, snapshot: TelemetrySnapshot) -> int:
    return telemetry_seed(
        incident.id,
        snapshot.environment,
        snapshot.service,
        snapshot.time_range,
    )


def build_timeline(incident: Incident, snapshot: TelemetrySnapshot) -> tuple[TimelineEvent, ...]:
    """Build a deterministic incident timeline from demo telemetry context."""
    seed = _analysis_seed(incident, snapshot)
    base_hour = 13
    events: list[TimelineEvent] = []

    if incident.severity in ("critical", "warning"):
        events.extend(
            [
                TimelineEvent(f"{base_hour:02d}:02", "Deployment v2.8 detected", "deployment"),
                TimelineEvent(f"{base_hour:02d}:05", "Orders DB CPU increased", "telemetry"),
                TimelineEvent(
                    f"{base_hour:02d}:07",
                    f"{incident.service_label} latency crossed threshold",
                    "telemetry",
                ),
                TimelineEvent(f"{base_hour:02d}:09", "Error rate increased", "telemetry"),
                TimelineEvent(f"{base_hour:02d}:12", "Incident declared", "incident"),
            ]
        )
    else:
        events.extend(
            [
                TimelineEvent(f"{base_hour:02d}:00", incident.title, "incident"),
                TimelineEvent(f"{base_hour:02d}:05", "Routine operational check passed", "telemetry"),
            ]
        )

    if telemetry_unit(seed, 88) > 0.7 and len(events) > 2:
        events.insert(
            2,
            TimelineEvent(f"{base_hour:02d}:06", "Traffic spike detected on checkout path", "telemetry"),
        )

    return tuple(events)


def build_telemetry_evidence(
    incident: Incident,
    snapshot: TelemetrySnapshot,
) -> TelemetryEvidence:
    """Generate deterministic telemetry series around the incident window."""
    seed = _analysis_seed(incident, snapshot)
    labels = snapshot.chart_labels or tuple(f"T-{10 - i}" for i in range(10))
    points = len(labels)
    profile = get_service_profile(incident.service_label)
    incident_index = max(1, min(points - 2, int(telemetry_unit(seed, 5) * (points - 1))))

    latency: list[float] = []
    error_rate: list[float] = []
    request_volume: list[float] = []
    database_cpu: list[float] = []

    base_latency = 120 * profile["latency"]
    base_error = 0.4 * profile["errors"]
    base_cpu = 42 + profile["errors"] * 8

    snapshot_values = list(snapshot.chart_values) if snapshot.chart_values else [100.0] * points

    for index in range(points):
        position_factor = index / max(points - 1, 1)
        spike = 0.0
        if index >= incident_index - 1:
            spike = (index - incident_index + 2) * 0.22

        latency.append(round(base_latency * (1 + spike + telemetry_unit(seed, index) * 0.08), 1))
        error_rate.append(round(base_error * (1 + spike * 1.6 + telemetry_unit(seed, index + 30) * 0.05), 2))
        request_volume.append(
            round(snapshot_values[index] if index < len(snapshot_values) else 100 + index * 8, 1)
        )
        database_cpu.append(
            round(min(99.0, base_cpu + spike * 38 + telemetry_unit(seed, index + 60) * 10), 1)
        )

    return TelemetryEvidence(
        labels=tuple(labels),
        latency=tuple(latency),
        error_rate=tuple(error_rate),
        request_volume=tuple(request_volume),
        database_cpu=tuple(database_cpu),
        incident_index=incident_index,
    )


def build_executive_metrics(
    incident: Incident,
    evidence: TelemetryEvidence,
) -> ExecutiveMetrics:
    """Summarize executive impact cards from telemetry evidence."""
    idx = evidence.incident_index
    latency = evidence.latency[min(idx, len(evidence.latency) - 1)]
    error_rate = evidence.error_rate[min(idx, len(evidence.error_rate) - 1)]
    traffic = evidence.request_volume[min(idx, len(evidence.request_volume) - 1)]

    return ExecutiveMetrics(
        error_rate=error_rate,
        latency_ms=latency,
        traffic_per_min=traffic,
        business_impact_summary=incident.impact,
        affected_services=2 if incident.severity == "critical" else 1,
    )


def build_business_impact(
    incident: Incident,
    evidence: TelemetryEvidence,
    snapshot: TelemetrySnapshot,
) -> BusinessImpact:
    """Translate infrastructure signals into estimated business impact."""
    seed = _analysis_seed(incident, snapshot)
    idx = evidence.incident_index
    latency = evidence.latency[min(idx, len(evidence.latency) - 1)]
    error_rate = evidence.error_rate[min(idx, len(evidence.error_rate) - 1)]

    checkout_delta = round(error_rate * 0.55 + (latency / 1000) * 2.8, 1)
    affected_txns = int(180 + telemetry_unit(seed, 19) * 420)

    severity_map = {
        "critical": "High",
        "warning": "Medium",
        "info": "Low",
    }
    customer_map = {
        "critical": "Checkout and payment flows likely affected for a subset of users.",
        "warning": "Partial degradation possible for dependent workflows.",
        "info": "Minimal or no customer-facing impact expected.",
    }

    hourly_risk = int(1200 + telemetry_unit(seed, 29) * 4800)

    return BusinessImpact(
        technical_signal=f"{incident.service_label} latency = {latency:.0f} ms · error rate = {error_rate:.1f}%",
        business_interpretation=(
            "Checkout conversion degradation detected."
            if incident.severity == "critical"
            else "Operational risk elevated for dependent workflows."
        ),
        checkout_success_delta=checkout_delta,
        affected_transactions=affected_txns,
        severity_level=severity_map.get(incident.severity, "Low"),
        customer_impact=customer_map.get(incident.severity, "Monitor only."),
        estimated_hourly_risk=f"${hourly_risk:,} / hour (estimated demo value)",
    )


def build_recommendations(
    incident: Incident,
    hypotheses: tuple,
) -> tuple[Recommendation, ...]:
    """Generate ordered remediation recommendations with rationale."""
    items: list[Recommendation] = [
        Recommendation(
            step=1,
            action="Inspect slow queries on Orders DB",
            reason="Database pressure appears before API latency in the correlated demo timeline.",
        ),
        Recommendation(
            step=2,
            action="Compare database CPU against normal baseline",
            reason="CPU saturation is a leading signal in the incident evidence window.",
        ),
        Recommendation(
            step=3,
            action="Review deployment v2.8 changes",
            reason="A recent deployment precedes degradation in the synthetic timeline.",
        ),
        Recommendation(
            step=4,
            action="Check connection pool saturation",
            reason="Traffic growth during the incident window can exhaust pooled connections.",
        ),
    ]

    if incident.severity == "critical":
        items.append(
            Recommendation(
                step=5,
                action="Evaluate rollback if deployment correlation strengthens",
                reason="Rollback reduces risk when deployment and error signals align.",
            )
        )
        items.append(
            Recommendation(
                step=6,
                action=f"Continue monitoring {incident.service_label} error rate",
                reason="Sustained error-rate improvement confirms remediation effectiveness.",
            )
        )
    else:
        items.append(
            Recommendation(
                step=5,
                action=incident.recommended_step,
                reason="Incident-specific guidance from the operational playbook.",
            )
        )

    if hypotheses:
        primary = hypotheses[0]
        items[0] = Recommendation(
            step=1,
            action=items[0].action,
            reason=f"Primary hypothesis ({primary.confidence}% confidence): {primary.title}.",
        )

    return tuple(items)


def derive_correlation_signals(
    incident: Incident,
    evidence: TelemetryEvidence,
) -> dict[str, bool]:
    """Derive boolean correlation signals from telemetry evidence."""
    idx = evidence.incident_index
    latency_before = evidence.latency[max(0, idx - 2)]
    latency_at = evidence.latency[min(idx, len(evidence.latency) - 1)]
    cpu_at = evidence.database_cpu[min(idx, len(evidence.database_cpu) - 1)]
    error_at = evidence.error_rate[min(idx, len(evidence.error_rate) - 1)]
    traffic_at = evidence.request_volume[min(idx, len(evidence.request_volume) - 1)]
    traffic_before = evidence.request_volume[max(0, idx - 2)]

    return {
        "latency_spike": latency_at > latency_before * 1.35,
        "error_rate_spike": error_at > 1.0,
        "traffic_increase": traffic_at > traffic_before * 1.1,
        "cpu_saturation": cpu_at >= 75,
        "database_pressure": cpu_at >= 68,
        "deployment_recent": incident.severity in ("critical", "warning"),
        "dependent_degradation": incident.service_label in ("Payment API", "Frontend Web"),
    }
