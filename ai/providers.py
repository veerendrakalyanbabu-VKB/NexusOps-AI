"""AI provider abstractions for NexusOps AI."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai.prompts import SYSTEM_PROMPT, build_user_prompt
from ai.response_parser import parse_copilot_response
from core.copilot_model import CopilotRequest, CopilotResponse
from core.incident_model import IncidentInvestigation
from core.operational_context import find_relevant_incident


# ---------------------------------------------------------------------------
# v0.3 incident investigation providers (preserved)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InvestigationContext:
    investigation: IncidentInvestigation
    question: str


class AIProvider(ABC):
    """Base class for incident-scoped AI providers."""

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


# ---------------------------------------------------------------------------
# v0.4 copilot providers
# ---------------------------------------------------------------------------


class CopilotProvider(ABC):
    """Base class for operational Copilot providers."""

    name: str = "local"
    model: str = "deterministic"

    @abstractmethod
    def analyze(self, request: CopilotRequest) -> CopilotResponse:
        raise NotImplementedError


class DeterministicCopilotProvider(CopilotProvider):
    """Evidence-based structured responses using NexusOps operational context."""

    name = "local"
    model = "deterministic-fallback"

    def analyze(self, request: CopilotRequest) -> CopilotResponse:
        context = request.context
        question = request.question.lower()
        incident = find_relevant_incident(context, request.question)
        primary_analysis = context.analysis[0] if context.analysis else None

        if "critical" in question or "most critical" in question:
            return self._critical_issue_response(context, incident)

        if "cascad" in question or "contribut" in question:
            return self._cascade_response(context, incident)

        if "summar" in question or "situation" in question:
            return self._summary_response(context, incident)

        if "investigate first" in question or "first" in question:
            return self._investigation_priority_response(context, incident)

        if "why" in question or "degraded" in question or "latency" in question:
            return self._degradation_response(context, incident, primary_analysis)

        return self._summary_response(context, incident)

    def _degradation_response(self, context, incident, primary_analysis) -> CopilotResponse:
        service = incident.service if incident else context.service_filter
        evidence = self._collect_evidence(context, incident, primary_analysis)
        confidence = primary_analysis.confidence if primary_analysis else 62
        diagnosis = (
            f"Simulated assessment: {service} shows degraded operational signals in the "
            f"{context.environment} environment over {context.time_range}."
        )
        if primary_analysis:
            diagnosis += f" Leading hypothesis: {primary_analysis.hypothesis}."

        return CopilotResponse(
            summary=f"Operational degradation detected for {service} in simulated telemetry.",
            diagnosis=diagnosis,
            evidence=evidence,
            confidence=confidence,
            recommended_investigation=self._investigation_steps(context, incident),
            recommended_actions=self._action_steps(context, incident),
            uncertainties=(
                "Confidence is based on deterministic correlation, not ML root-cause analysis.",
                context.demo_notice,
            ),
            affected_services=self._affected_services(context, incident),
            severity=incident.severity if incident else "warning",
            provider=self.name,
            model=self.model,
        )

    def _critical_issue_response(self, context, incident) -> CopilotResponse:
        if not context.active_incidents:
            return self._empty_incidents_response(context)
        top = incident or context.active_incidents[0]
        return CopilotResponse(
            summary=f"Most critical open issue: {top.title}",
            diagnosis=(
                f"{top.severity.upper()} incident on {top.service} is the highest-priority "
                f"operational signal in the current simulated context."
            ),
            evidence=(top.description, top.impact),
            confidence=88 if top.severity == "critical" else 72,
            recommended_investigation=self._investigation_steps(context, incident),
            recommended_actions=self._action_steps(context, incident),
            uncertainties=(context.demo_notice,),
            affected_services=(top.service,),
            severity=top.severity,
            provider=self.name,
            model=self.model,
        )

    def _cascade_response(self, context, incident) -> CopilotResponse:
        degraded = [item.name for item in context.services if item.status == "Degraded"]
        evidence = tuple(
            f"{item.signal}: {item.detail}" for item in context.correlations[:4]
        ) or ("No strong cascade pattern in current demo telemetry.",)
        return CopilotResponse(
            summary="Potential dependency cascade under review.",
            diagnosis=(
                "Correlated signals suggest upstream/downstream degradation may be linked. "
                f"Degraded services in scope: {', '.join(degraded) if degraded else 'none detected'}."
            ),
            evidence=evidence,
            confidence=76 if degraded else 48,
            recommended_investigation=self._investigation_steps(context, incident),
            recommended_actions=self._action_steps(context, incident),
            uncertainties=(
                "Cascade inference is correlation-based on simulated telemetry.",
                context.demo_notice,
            ),
            affected_services=tuple(degraded) if degraded else self._affected_services(context, incident),
            severity=incident.severity if incident else "warning",
            provider=self.name,
            model=self.model,
        )

    def _summary_response(self, context, incident) -> CopilotResponse:
        return CopilotResponse(
            summary=(
                f"{context.environment} operational status: {context.operational_status}. "
                f"{context.open_incidents} open incident(s), system health {context.system_health:.1f}%."
            ),
            diagnosis=(
                f"Simulated telemetry for {context.service_filter} over {context.time_range} "
                f"shows latency {context.latency_ms:.0f} ms and error rate {context.error_rate:.1f}%."
            ),
            evidence=self._collect_evidence(context, incident, context.analysis[0] if context.analysis else None),
            confidence=70,
            recommended_investigation=self._investigation_steps(context, incident),
            recommended_actions=self._action_steps(context, incident),
            uncertainties=(context.demo_notice,),
            affected_services=self._affected_services(context, incident),
            severity=incident.severity if incident else "none",
            provider=self.name,
            model=self.model,
        )

    def _investigation_priority_response(self, context, incident) -> CopilotResponse:
        steps = self._investigation_steps(context, incident)
        return CopilotResponse(
            summary="Prioritized investigation plan generated from current operational context.",
            diagnosis="Start with the highest-severity incident and its upstream dependencies.",
            evidence=self._collect_evidence(context, incident, context.analysis[0] if context.analysis else None),
            confidence=80 if incident else 55,
            recommended_investigation=steps,
            recommended_actions=self._action_steps(context, incident),
            uncertainties=(context.demo_notice,),
            affected_services=self._affected_services(context, incident),
            severity=incident.severity if incident else "none",
            provider=self.name,
            model=self.model,
        )

    def _empty_incidents_response(self, context) -> CopilotResponse:
        return CopilotResponse(
            summary="No open incidents in the current simulated operational context.",
            diagnosis="Platform signals appear stable for the selected filters.",
            evidence=(f"System health: {context.system_health:.1f}%.",),
            confidence=65,
            recommended_investigation=("Monitor latency and error-rate trends.",),
            recommended_actions=("Continue routine operational monitoring.",),
            uncertainties=(context.demo_notice,),
            affected_services=(),
            severity="none",
            provider=self.name,
            model=self.model,
        )

    def _collect_evidence(self, context, incident, primary_analysis) -> tuple[str, ...]:
        evidence: list[str] = [
            f"System health {context.system_health:.1f}% in {context.environment}.",
            f"Latency {context.latency_ms:.0f} ms, error rate {context.error_rate:.1f}%.",
        ]
        if incident:
            evidence.append(f"Incident: {incident.title} ({incident.severity}).")
            evidence.append(incident.impact)
        if primary_analysis:
            evidence.extend(primary_analysis.evidence[:2])
        for item in context.correlations[:2]:
            evidence.append(item.detail)
        return tuple(evidence)

    def _investigation_steps(self, context, incident) -> tuple[str, ...]:
        steps = [
            "Review the highest-severity open incident and its timeline.",
            "Compare latency and error-rate trends against the selected time window.",
            "Inspect upstream database and dependency health signals.",
        ]
        if incident:
            steps.insert(0, f"Triage incident '{incident.title}' on {incident.service}.")
        return tuple(steps[:4])

    def _action_steps(self, context, incident) -> tuple[str, ...]:
        actions = [
            "Inspect slow queries and connection pool utilization on dependent databases.",
            "Review recent deployment changes correlated in the incident timeline.",
            "Monitor payment and checkout error rates after mitigation steps.",
        ]
        if incident and incident.severity == "critical":
            actions.insert(0, "Escalate critical incident response and assign an incident commander.")
        return tuple(actions[:4])

    def _affected_services(self, context, incident) -> tuple[str, ...]:
        if incident:
            services = {incident.service}
            for item in context.services:
                if item.status == "Degraded":
                    services.add(item.name)
            return tuple(services)
        return tuple(item.name for item in context.services if item.status == "Degraded")


class ExternalJSONCopilotProvider(CopilotProvider):
    """Shared JSON-based provider logic for external LLM APIs."""

    def __init__(self, name: str, model: str, call_model) -> None:
        self.name = name
        self.model = model
        self._call_model = call_model

    def analyze(self, request: CopilotRequest) -> CopilotResponse:
        fallback = DeterministicCopilotProvider().analyze(request)
        try:
            raw = self._call_model(SYSTEM_PROMPT, build_user_prompt(request))
            return parse_copilot_response(raw, self.name, self.model, fallback=fallback)
        except Exception:
            return fallback


def resolve_copilot_provider() -> CopilotProvider:
    """Select the configured Copilot provider with safe fallback."""
    provider_name = os.getenv("NEXUSOPS_AI_PROVIDER", "local").strip().lower()

    if provider_name == "claude":
        claude = _build_claude_provider()
        if claude is not None:
            return claude

    if provider_name == "gemini":
        gemini = _build_gemini_provider()
        if gemini is not None:
            return gemini

    if provider_name == "openai":
        openai_provider = _build_openai_provider()
        if openai_provider is not None:
            return openai_provider

    return DeterministicCopilotProvider()


def provider_status() -> dict[str, str]:
    """Return provider availability metadata for the UI."""
    configured = os.getenv("NEXUSOPS_AI_PROVIDER", "local").strip().lower() or "local"
    provider = resolve_copilot_provider()
    return {
        "configured": configured,
        "active": provider.name,
        "model": provider.model,
        "availability": "READY",
        "mode": "Decision Support",
    }


def _build_claude_provider() -> CopilotProvider | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
    except ImportError:
        return None

    model = os.getenv("NEXUSOPS_CLAUDE_MODEL", "claude-3-5-sonnet-latest")
    client = anthropic.Anthropic(api_key=api_key)

    def call_model(system_prompt: str, user_prompt: str) -> str:
        message = client.messages.create(
            model=model,
            max_tokens=1200,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text

    return ExternalJSONCopilotProvider("claude", model, call_model)


def _build_gemini_provider() -> CopilotProvider | None:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
    except ImportError:
        return None

    model = os.getenv("NEXUSOPS_GEMINI_MODEL", "gemini-2.0-flash")
    client = genai.Client(api_key=api_key)

    def call_model(system_prompt: str, user_prompt: str) -> str:
        response = client.models.generate_content(
            model=model,
            contents=f"{system_prompt}\n\n{user_prompt}",
        )
        return response.text or ""

    return ExternalJSONCopilotProvider("gemini", model, call_model)


def _build_openai_provider() -> CopilotProvider | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
    except ImportError:
        return None

    model = os.getenv("NEXUSOPS_OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    def call_model(system_prompt: str, user_prompt: str) -> str:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""

    return ExternalJSONCopilotProvider("openai", model, call_model)
