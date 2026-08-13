"""AI provider abstractions for NexusOps AI."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from core.incident_model import IncidentInvestigation


@dataclass(frozen=True)
class InvestigationContext:
    investigation: IncidentInvestigation
    question: str


class AIProvider(ABC):
    """Base class for future AI providers (Gemini, Claude, OpenAI, etc.)."""

    @abstractmethod
    def investigate(self, context: InvestigationContext) -> str:
        raise NotImplementedError


class DeterministicFallbackProvider(AIProvider):
    """Rule-based investigation responses that require no API credentials."""

    def investigate(self, context: InvestigationContext) -> str:
        inv = context.investigation
        question = context.question.lower()
        primary = inv.hypotheses[0] if inv.hypotheses else None

        if "why" in question or "degraded" in question or "latency" in question:
            hypothesis_text = (
                f"The leading hypothesis is '{primary.title}' ({primary.confidence}% confidence)."
                if primary
                else "No strong hypothesis was generated from the available demo signals."
            )
            return (
                f"Simulated investigation for {inv.service_label}: {inv.description} "
                f"{hypothesis_text} "
                f"Observed evidence includes latency at {inv.executive_metrics.latency_ms:.0f} ms "
                f"and error rate at {inv.executive_metrics.error_rate:.1f}%. "
                f"{inv.demo_notice}"
            )

        if "impact" in question or "business" in question:
            impact = inv.business_impact
            return (
                f"Estimated business impact: {impact.business_interpretation} "
                f"Checkout success delta ~{impact.checkout_success_delta:.1f}%. "
                f"Affected transactions (demo estimate): {impact.affected_transactions:,}. "
                f"Customer impact: {impact.customer_impact} "
                f"{inv.demo_notice}"
            )

        if "recommend" in question or "action" in question or "next" in question:
            steps = "; ".join(
                f"{item.step}. {item.action}" for item in inv.recommendations[:3]
            )
            return (
                f"Recommended next actions: {steps}. "
                f"These are deterministic playbook suggestions, not automated remediations. "
                f"{inv.demo_notice}"
            )

        if primary:
            evidence = " ".join(primary.evidence[:2])
            return (
                f"Investigation summary for '{inv.title}': {evidence} "
                f"Confidence for primary hypothesis: {primary.confidence}%. "
                f"{inv.demo_notice}"
            )

        return (
            f"I analyzed the simulated incident context for {inv.service_label}. "
            f"Status: {inv.status}. Impact: {inv.impact} "
            f"Ask about degradation, business impact, or recommended actions. "
            f"{inv.demo_notice}"
        )
