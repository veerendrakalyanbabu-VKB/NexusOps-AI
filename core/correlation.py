"""Deterministic evidence-based correlation engine for incident intelligence."""

from __future__ import annotations

from core.incident_model import Hypothesis


SIGNAL_WEIGHTS = {
    "latency_spike": 28,
    "error_rate_spike": 24,
    "cpu_saturation": 22,
    "traffic_increase": 14,
    "deployment_recent": 18,
    "dependent_degradation": 20,
    "database_pressure": 26,
}


def evaluate_signals(signals: dict[str, bool]) -> dict[str, int]:
    """Score each correlation signal deterministically."""
    return {
        name: weight if signals.get(name) else 0
        for name, weight in SIGNAL_WEIGHTS.items()
    }


def build_hypotheses(
    incident_title: str,
    service_label: str,
    signals: dict[str, bool],
) -> tuple[Hypothesis, ...]:
    """Generate ranked root-cause hypotheses from observed signals."""
    scores = evaluate_signals(signals)

    candidates: list[tuple[str, int, tuple[str, ...]]] = []

    db_score = (
        scores["database_pressure"]
        + scores["cpu_saturation"]
        + (scores["latency_spike"] // 2)
    )
    if db_score > 0:
        evidence = []
        if signals.get("cpu_saturation"):
            evidence.append("Database CPU increased before API latency crossed threshold.")
        if signals.get("database_pressure"):
            evidence.append("Database pressure signal observed during incident window.")
        if signals.get("traffic_increase"):
            evidence.append("Payment request volume increased during peak traffic.")
        if signals.get("latency_spike"):
            evidence.append("API latency increased shortly after database pressure.")
        candidates.append(
            (
                f"{_dependent_db_name(service_label)} performance degradation",
                min(95, 52 + db_score),
                tuple(evidence or ["Correlated database pressure in demo telemetry."]),
            )
        )

    deploy_score = scores["deployment_recent"] + (scores["latency_spike"] // 3)
    if deploy_score > 0:
        evidence = []
        if signals.get("deployment_recent"):
            evidence.append("Deployment v2.8 occurred shortly before degradation.")
        if signals.get("latency_spike"):
            evidence.append("Latency increase followed the deployment window.")
        if signals.get("error_rate_spike"):
            evidence.append("Error rate rose after the deployment event.")
        candidates.append(
            (
                "Recent deployment v2.8",
                min(88, 40 + deploy_score),
                tuple(evidence or ["Deployment correlation detected in demo timeline."]),
            )
        )

    traffic_score = scores["traffic_increase"] + scores["error_rate_spike"]
    if traffic_score > 0:
        evidence = []
        if signals.get("traffic_increase"):
            evidence.append("Traffic surge detected in the incident time window.")
        if signals.get("error_rate_spike"):
            evidence.append("Error rate increased as request volume climbed.")
        candidates.append(
            (
                f"{service_label} capacity saturation under traffic surge",
                min(82, 35 + traffic_score),
                tuple(evidence or ["Traffic and error signals correlated in demo data."]),
            )
        )

    if signals.get("dependent_degradation"):
        candidates.append(
            (
                "Downstream dependency degradation",
                min(78, 38 + scores["dependent_degradation"]),
                (
                    "A dependent service showed degraded health before the incident was declared.",
                    f"Primary service '{service_label}' degraded after dependency signals.",
                ),
            )
        )

    if not candidates:
        candidates.append(
            (
                f"Investigate {service_label} service health",
                45,
                (
                    f"Observed incident: {incident_title}.",
                    "Insufficient correlated demo signals for a stronger hypothesis.",
                ),
            )
        )

    candidates.sort(key=lambda item: item[1], reverse=True)
    hypotheses: list[Hypothesis] = []
    ranks = ("primary", "secondary", "tertiary")

    for index, (title, confidence, evidence) in enumerate(candidates[:3]):
        hypotheses.append(
            Hypothesis(
                title=title,
                confidence=confidence,
                evidence=evidence,
                rank=ranks[min(index, len(ranks) - 1)],
            )
        )

    return tuple(hypotheses)


def _dependent_db_name(service_label: str) -> str:
    if service_label == "Payment API":
        return "Orders DB"
    return "Orders DB"
