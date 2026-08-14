"""Copilot orchestration service."""

from __future__ import annotations

import streamlit as st

from ai.engine import CopilotEngine
from core.copilot_model import CopilotRequest, CopilotResponse
from core.operational_context import build_operational_context
from telemetry import TelemetrySnapshot


@st.cache_data(show_spinner=False)
def load_operational_context(
    environment: str,
    service: str,
    time_range: str,
    data_version: int,
):
    from telemetry import get_snapshot

    snapshot = get_snapshot(environment, service, time_range, data_version)
    return snapshot, build_operational_context(snapshot)


def run_copilot_investigation(
    question: str,
    snapshot: TelemetrySnapshot,
    engine: CopilotEngine | None = None,
) -> CopilotResponse:
    """Construct context and run a Copilot investigation."""
    context = build_operational_context(snapshot)
    request = CopilotRequest(question=question.strip(), context=context)
    copilot = engine or CopilotEngine()
    return copilot.investigate(request)
