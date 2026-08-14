"""AI engines for NexusOps AI."""

from __future__ import annotations

from ai.providers import (
    AIProvider,
    CopilotProvider,
    DeterministicCopilotProvider,
    DeterministicFallbackProvider,
    InvestigationContext,
    resolve_copilot_provider,
)
from core.copilot_model import CopilotRequest, CopilotResponse
from core.incident_model import IncidentInvestigation


class InvestigationEngine:
    """Routes incident-scoped investigation questions (v0.3 preserved)."""

    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or DeterministicFallbackProvider()

    def ask(self, investigation: IncidentInvestigation, question: str) -> str:
        if not question.strip():
            return "Please enter a question about the incident."
        context = InvestigationContext(investigation=investigation, question=question.strip())
        try:
            return self._provider.investigate(context)
        except Exception:
            return (
                "The AI investigation layer encountered an error. "
                "Deterministic incident evidence remains available in the dashboard. "
                f"{investigation.demo_notice}"
            )


class CopilotEngine:
    """Operational Copilot engine for v0.4."""

    def __init__(self, provider: CopilotProvider | None = None) -> None:
        self._provider = provider or resolve_copilot_provider()

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def model_name(self) -> str:
        return self._provider.model

    def investigate(self, request: CopilotRequest) -> CopilotResponse:
        if not request.question.strip():
            return CopilotResponse(
                summary="Please enter an operational question.",
                diagnosis="No question was provided.",
                evidence=(),
                confidence=0,
                recommended_investigation=(),
                recommended_actions=(),
                uncertainties=(),
                affected_services=(),
                severity="none",
                provider=self._provider.name,
                model=self._provider.model,
            )
        try:
            return self._provider.analyze(request)
        except Exception:
            fallback = DeterministicCopilotProvider()
            response = fallback.analyze(request)
            return CopilotResponse(
                summary=response.summary,
                diagnosis=(
                    "Primary provider unavailable. Showing deterministic fallback assessment."
                ),
                evidence=response.evidence,
                confidence=response.confidence,
                recommended_investigation=response.recommended_investigation,
                recommended_actions=response.recommended_actions,
                uncertainties=(
                    *response.uncertainties,
                    "External provider failed; deterministic fallback was used.",
                ),
                affected_services=response.affected_services,
                severity=response.severity,
                provider="local",
                model="deterministic-fallback",
            )
