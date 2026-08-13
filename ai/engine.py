"""AI investigation engine for NexusOps AI."""

from __future__ import annotations

import os

from ai.providers import AIProvider, DeterministicFallbackProvider, InvestigationContext
from core.incident_model import IncidentInvestigation


class InvestigationEngine:
    """Routes investigation questions to configured AI providers."""

    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or self._resolve_provider()

    def _resolve_provider(self) -> AIProvider:
        """Select provider based on environment configuration."""
        if os.getenv("NEXUSOPS_AI_PROVIDER"):
            # Future providers can be registered here without rewriting the UI.
            pass
        return DeterministicFallbackProvider()

    def ask(self, investigation: IncidentInvestigation, question: str) -> str:
        """Return an investigation response for the given incident context."""
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
