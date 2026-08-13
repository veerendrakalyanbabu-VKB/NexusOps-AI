"""
Demo telemetry engine for NexusOps AI.

Provides deterministic, simulated operational data based on user selections.
Designed to be replaced later with real AWS/GCP/Azure/Prometheus/API sources.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import md5
from typing import Literal

Severity = Literal["critical", "warning", "info"]
IncidentStatus = Literal["open", "investigating", "resolved"]

ENVIRONMENTS = ("Development", "Staging", "Production")
SERVICES = (
    "All Services",
    "Payment API",
    "Orders DB",
    "Frontend Web",
    "Auth Service",
    "Notification Service",
)
TIME_RANGES = ("1H", "6H", "24H", "7D")

SERVICE_SLUGS = {
    "All Services": "all",
    "Payment API": "payment-api",
    "Orders DB": "orders-db",
    "Frontend Web": "frontend-web",
    "Auth Service": "auth-service",
    "Notification Service": "notification-service",
}

SERVICE_LABELS = {slug: label for label, slug in SERVICE_SLUGS.items() if slug != "all"}
SERVICE_NAME_ALIASES = {slug: label for label, slug in SERVICE_SLUGS.items()}


def _normalize_service_name(service: str) -> str:
    """Map service slugs (payment-api) to profile display names (Payment API)."""
    return SERVICE_NAME_ALIASES.get(service, service)


@dataclass(frozen=True)
class Incident:
    id: str
    severity: Severity
    title: str
    service: str
    service_label: str
    timestamp: str
    status: IncidentStatus
    description: str
    impact: str
    recommended_step: str


@dataclass(frozen=True)
class KpiMetric:
    label: str
    value: str
    change: str


@dataclass(frozen=True)
class TelemetrySnapshot:
    environment: str
    service: str
    time_range: str
    system_health: float
    active_services: int
    open_incidents: int
    monthly_cost: float
    health_change: float
    services_change: int
    incidents_change: float
    cost_change: float
    operational_status: str
    operational_confidence: int
    ai_summary: str
    ai_detail: str
    chart_labels: list[str]
    chart_values: list[float]
    chart_title: str
    incidents: list[Incident]


def _seed(*parts: object) -> int:
    key = "|".join(str(part) for part in parts)
    return int(md5(key.encode()).hexdigest()[:12], 16)


def _unit(seed: int, offset: int) -> float:
    digest = md5(f"{seed}:{offset}".encode()).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _pick(seed: int, offset: int, options: tuple[str, ...]) -> str:
    index = int(_unit(seed, offset) * len(options)) % len(options)
    return options[index]


def _env_profile(environment: str) -> dict[str, float]:
    profiles = {
        "Development": {
            "traffic": 0.45,
            "incidents": 0.55,
            "cost": 0.35,
            "health_penalty": 1.5,
            "services": 18,
        },
        "Staging": {
            "traffic": 0.72,
            "incidents": 0.78,
            "cost": 0.62,
            "health_penalty": 3.0,
            "services": 21,
        },
        "Production": {
            "traffic": 1.0,
            "incidents": 1.0,
            "cost": 1.0,
            "health_penalty": 5.5,
            "services": 24,
        },
    }
    return profiles[environment]


def _service_profile(service: str) -> dict[str, float]:
    profiles = {
        "All Services": {"weight": 1.0, "latency": 1.0, "errors": 1.0},
        "Payment API": {"weight": 0.34, "latency": 1.8, "errors": 1.6},
        "Orders DB": {"weight": 0.16, "latency": 0.6, "errors": 1.2},
        "Frontend Web": {"weight": 0.38, "latency": 0.9, "errors": 0.7},
        "Auth Service": {"weight": 0.12, "latency": 0.8, "errors": 0.8},
        "Notification Service": {"weight": 0.10, "latency": 1.1, "errors": 0.9},
    }
    return profiles[_normalize_service_name(service)]


def _time_profile(time_range: str) -> tuple[int, list[str]]:
    if time_range == "1H":
        return 12, [f"-{60 - i * 5}m" for i in range(12)]
    if time_range == "6H":
        return 12, [f"-{360 - i * 30}m" for i in range(12)]
    if time_range == "24H":
        return 24, [f"{i:02d}:00" for i in range(24)]
    return 7, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _base_traffic(seed: int, points: int, env_scale: float, service_scale: float) -> list[float]:
    values = []
    for index in range(points):
        wave = 120 + 60 * _unit(seed, index)
        peak = 180 if 8 <= index % 24 <= 18 else 0
        noise = (_unit(seed, index + 50) - 0.5) * 30
        value = (wave + peak + noise) * env_scale * service_scale
        values.append(round(max(value, 20), 1))
    if points == 7:
        values = [
            round(value * (0.85 + 0.3 * _unit(seed, index + 90)), 1)
            for index, value in enumerate(values)
        ]
    return values


def _build_incidents(
    seed: int,
    environment: str,
    service: str,
    env_profile: dict[str, float],
) -> list[Incident]:
    templates = [
        {
            "severity": "critical",
            "title": "Payment API latency spike",
            "service_label": "Payment API",
            "timestamp": "2 min ago",
            "status": "investigating",
            "description": (
                "Latency reached 820 ms with a 7.4% error rate during peak checkout traffic."
            ),
            "impact": "High — checkout success rate dropped 4.2% in the last 15 minutes.",
            "recommended_step": (
                "Inspect slow queries on Orders DB and review recent deployment v2.8."
            ),
        },
        {
            "severity": "warning",
            "title": "Database CPU above threshold",
            "service_label": "Orders DB",
            "timestamp": "8 min ago",
            "status": "open",
            "description": (
                "CPU utilization sustained above 75% for 12 minutes during peak traffic."
            ),
            "impact": "Medium — downstream API latency increased on payment workflows.",
            "recommended_step": (
                "Review top SQL consumers and validate connection pool sizing."
            ),
        },
        {
            "severity": "info",
            "title": "Deployment completed successfully",
            "service_label": "Frontend Web",
            "timestamp": "14 min ago",
            "status": "resolved",
            "description": "Deployment v2.8 rolled out to all frontend-web instances.",
            "impact": "Low — no customer-facing degradation observed post-release.",
            "recommended_step": (
                "Monitor error rate and latency for 30 minutes after rollout."
            ),
        },
        {
            "severity": "warning",
            "title": "Notification delivery delays",
            "service_label": "Notification Service",
            "timestamp": "19 min ago",
            "status": "open",
            "description": (
                "Queue backlog increased after a burst of password-reset events."
            ),
            "impact": "Medium — transactional email latency increased to 42 seconds.",
            "recommended_step": (
                "Scale notification workers and inspect dead-letter queue volume."
            ),
        },
        {
            "severity": "warning",
            "title": "Auth token validation latency elevated",
            "service_label": "Auth Service",
            "timestamp": "27 min ago",
            "status": "investigating",
            "description": (
                "P95 auth validation latency exceeded 240 ms for 9 minutes."
            ),
            "impact": "Medium — login flows slowed for mobile clients.",
            "recommended_step": (
                "Check cache hit ratio and validate identity provider response times."
            ),
        },
        {
            "severity": "info",
            "title": "Scheduled backup completed",
            "service_label": "Orders DB",
            "timestamp": "45 min ago",
            "status": "resolved",
            "description": "Nightly backup finished without errors.",
            "impact": "None — routine maintenance event.",
            "recommended_step": (
                "Verify backup integrity report in the operations log."
            ),
        },
    ]

    incidents: list[Incident] = []
    service_slug = SERVICE_SLUGS[service]

    for index, template in enumerate(templates):
        if not _unit(seed, index + 200) <= env_profile["incidents"]:
            continue

        incident_service = SERVICE_SLUGS[template["service_label"]]
        if service_slug != "all" and incident_service != service_slug:
            continue

        incidents.append(
            Incident(
                id=f"{environment[:3].lower()}-{incident_service}-{index}",
                severity=template["severity"],
                title=template["title"],
                service=incident_service,
                service_label=template["service_label"],
                timestamp=template["timestamp"],
                status=template["status"],
                description=template["description"],
                impact=template["impact"],
                recommended_step=template["recommended_step"],
            )
        )

    return incidents


def get_snapshot(
    environment: str,
    service: str,
    time_range: str,
    data_version: int = 0,
) -> TelemetrySnapshot:
    """Return deterministic demo telemetry for the given operational filters."""

    seed = _seed(environment, service, time_range, data_version)
    env_profile = _env_profile(environment)
    service_profile = _service_profile(service)
    points, labels = _time_profile(time_range)

    traffic_scale = env_profile["traffic"] * service_profile["weight"]
    chart_values = _base_traffic(seed, points, env_profile["traffic"], service_profile["weight"])

    if service != "All Services":
        spike_index = int(_unit(seed, 77) * max(points - 1, 1))
        chart_values[spike_index] = round(chart_values[spike_index] * 1.35, 1)

    incidents = _build_incidents(seed, environment, service, env_profile)
    open_incidents = sum(1 for item in incidents if item.status != "resolved")

    health_penalty = env_profile["health_penalty"] + service_profile["errors"] * 2.5
    if open_incidents:
        health_penalty += open_incidents * 1.8
    system_health = max(82.0, min(99.9, 99.2 - health_penalty + _unit(seed, 11) * 2))

    active_services = env_profile["services"]
    if service != "All Services":
        active_services = 1

    monthly_cost = round(
        (1180 + _unit(seed, 21) * 980) * env_profile["cost"] * max(service_profile["weight"], 0.2),
        0,
    )

    health_change = round((_unit(seed, 31) - 0.35) * 4.5, 1)
    services_change = int((_unit(seed, 41) - 0.4) * 6)
    incidents_change = round((_unit(seed, 51) - 0.55) * 40, 1)
    cost_change = round((_unit(seed, 61) - 0.45) * 18, 1)

    if system_health >= 97:
        operational_status = "ALL SYSTEMS OPERATIONAL"
        confidence = 94
    elif system_health >= 92:
        operational_status = "ELEVATED OPERATIONAL SIGNALS"
        confidence = 86
    else:
        operational_status = "DEGRADED OPERATIONS DETECTED"
        confidence = 74

    service_text = service if service != "All Services" else "the platform"
    ai_summary = (
        f"Simulated telemetry for {service_text} in {environment} over {time_range} "
        f"shows {'stable' if system_health >= 95 else 'mixed'} performance signals."
    )
    ai_detail = (
        f"Request volume trends reflect demo data for the selected filters. "
        f"{open_incidents} open incident(s) are currently influencing health scoring. "
        f"This view uses deterministic simulated telemetry, not live production data."
    )

    chart_title = "Requests/min" if time_range != "7D" else "Requests/day"

    return TelemetrySnapshot(
        environment=environment,
        service=service,
        time_range=time_range,
        system_health=round(system_health, 1),
        active_services=active_services,
        open_incidents=open_incidents,
        monthly_cost=monthly_cost,
        health_change=health_change,
        services_change=services_change,
        incidents_change=incidents_change,
        cost_change=cost_change,
        operational_status=operational_status,
        operational_confidence=confidence,
        ai_summary=ai_summary,
        ai_detail=ai_detail,
        chart_labels=labels,
        chart_values=chart_values,
        chart_title=chart_title,
        incidents=incidents,
    )


def build_kpis(snapshot: TelemetrySnapshot) -> list[KpiMetric]:
    return [
        KpiMetric("SYSTEM HEALTH", f"{snapshot.system_health:.1f}%", _format_change(snapshot.health_change, suffix="%")),
        KpiMetric("ACTIVE SERVICES", str(snapshot.active_services), _format_change(snapshot.services_change, suffix="", signed=True)),
        KpiMetric("OPEN INCIDENTS", str(snapshot.open_incidents), _format_change(snapshot.incidents_change, suffix="%")),
        KpiMetric("MONTHLY COST", f"${snapshot.monthly_cost:,.0f}", _format_change(snapshot.cost_change, suffix="%")),
    ]


def _format_change(value: float, suffix: str = "%", signed: bool = False) -> str:
    if signed:
        prefix = "+" if value > 0 else ""
        return f"{prefix}{value}{suffix}"
    prefix = "+" if value > 0 else ""
    return f"{prefix}{value:.1f}{suffix}" if isinstance(value, float) else f"{prefix}{value}{suffix}"


def get_cloud_resources(snapshot: TelemetrySnapshot) -> list[dict[str, str]]:
    resources = []
    for slug, service_label in SERVICE_LABELS.items():
        seed = _seed(snapshot.environment, slug, snapshot.time_range, snapshot.service)
        cpu = round(28 + _unit(seed, 1) * 65, 0)
        latency = round(
            40 + _unit(seed, 2) * 780 * _service_profile(service_label)["latency"],
            0,
        )
        status = "Degraded" if cpu >= 75 or latency >= 500 else "Running"
        resources.append(
            {
                "name": slug,
                "label": service_label,
                "type": _resource_type(service_label),
                "status": status,
                "region": _pick(seed, 3, ("us-east-1", "us-west-2", "eu-west-1")),
                "instances": str(max(1, int(1 + _unit(seed, 4) * 4))),
                "cpu": f"{cpu:.0f}%",
                "latency": f"{latency:.0f} ms",
            }
        )
    return resources


def _resource_type(label: str) -> str:
    mapping = {
        "Payment API": "API",
        "Orders DB": "Database",
        "Frontend Web": "Web App",
        "Auth Service": "API",
        "Notification Service": "Worker",
    }
    return mapping[label]


def copilot_response(question: str, snapshot: TelemetrySnapshot) -> str:
    q = question.lower()
    if "payment" in q or "latency" in q:
        return (
            f"Simulated analysis for {snapshot.environment}: Payment API latency is elevated "
            f"relative to the selected {snapshot.time_range} window. The pattern correlates with "
            f"Orders DB CPU pressure and follows a recent deployment event. "
            f"Recommended action: scale database capacity and inspect slow queries."
        )
    if "incident" in q or "critical" in q:
        return (
            f"There are {snapshot.open_incidents} open simulated incident(s) in the current view. "
            f"The highest-severity active item should be triaged first from the Live Operations Feed."
        )
    if "cost" in q or "spend" in q:
        return (
            f"Estimated monthly infrastructure cost for the current selection is "
            f"${snapshot.monthly_cost:,.0f} ({snapshot.cost_change:+.1f}% vs previous period). "
            f"Figures are deterministic demo values, not live billing data."
        )
    if "health" in q or "status" in q:
        return (
            f"Simulated system health is {snapshot.system_health:.1f}% with "
            f"{snapshot.active_services} active service(s) in scope. "
            f"Operational status: {snapshot.operational_status}."
        )
    return (
        "I can analyze simulated incidents, service health, latency, costs, and deployments "
        "for the current Command Center filters. This copilot uses demo telemetry only."
    )
