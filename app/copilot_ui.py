"""AI Copilot UI for NexusOps AI v0.4."""

from __future__ import annotations

import streamlit as st

from ai.engine import CopilotEngine
from ai.providers import provider_status
from core.copilot_model import CopilotResponse
from services.copilot_service import run_copilot_investigation
from telemetry import TelemetrySnapshot

EXAMPLE_PROMPTS = (
    "Why is the Payment API degraded?",
    "What is the most critical issue right now?",
    "What services are most likely contributing to the current incident?",
    "Summarize the current operational situation.",
    "What should an engineer investigate first?",
    "Are there signs of a cascading failure?",
)


def init_copilot_session_state() -> None:
    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = []
    if "copilot_engine" not in st.session_state:
        st.session_state.copilot_engine = CopilotEngine()


def clear_copilot_conversation() -> None:
    st.session_state.copilot_messages = []


def render_copilot_status(snapshot: TelemetrySnapshot) -> None:
    status = provider_status()
    st.html(f"""
<div class="detail-card">
<div class="ai-title">AI COPILOT</div>
<div class="ai-heading">● {status['availability']}</div>
<p class="ai-text"><strong style="color:white;">Provider:</strong> {status['active']}</p>
<p class="ai-text"><strong style="color:white;">Model:</strong> {status['model']}</p>
<p class="ai-text"><strong style="color:white;">Context:</strong> LIVE (simulated operational snapshot)</p>
<p class="ai-text"><strong style="color:white;">Telemetry:</strong> SIMULATED TELEMETRY</p>
<p class="ai-text"><strong style="color:white;">Mode:</strong> {status['mode']}</p>
<p class="ai-text"><strong style="color:white;">Environment:</strong> {snapshot.environment} · {snapshot.service} · {snapshot.time_range}</p>
</div>
""")


def render_copilot_response_card(response: CopilotResponse) -> None:
    evidence_items = "".join(f"<li>{item}</li>" for item in response.evidence)
    investigation_items = "".join(
        f"<li>{index + 1}. {item}</li>"
        for index, item in enumerate(response.recommended_investigation)
    )
    action_items = "".join(
        f"<li>{index + 1}. {item}</li>"
        for index, item in enumerate(response.recommended_actions)
    )
    uncertainty_items = "".join(f"<li>{item}</li>" for item in response.uncertainties)
    affected = ", ".join(response.affected_services) if response.affected_services else "None identified"

    st.html(f"""
<div class="detail-card">
<div class="ai-title">AI OPERATIONS ASSESSMENT</div>
<div class="ai-heading">{response.summary}</div>
<p class="ai-text"><strong style="color:white;">Diagnosis</strong><br>{response.diagnosis}</p>
<p class="ai-text"><strong style="color:white;">Evidence</strong></p>
<ul class="ai-text">{evidence_items or '<li>No evidence available.</li>'}</ul>
<p style="color:#5eead4;"><strong>Confidence:</strong> {response.confidence}%</p>
<p class="ai-text"><strong style="color:white;">Severity:</strong> {response.severity.upper()}</p>
<p class="ai-text"><strong style="color:white;">Affected Services:</strong> {affected}</p>
<p class="ai-text"><strong style="color:white;">Recommended Investigation</strong></p>
<ol class="ai-text">{investigation_items or '<li>Review operational context manually.</li>'}</ol>
<p class="ai-text"><strong style="color:white;">Recommended Actions</strong></p>
<ol class="ai-text">{action_items or '<li>Continue monitoring.</li>'}</ol>
<p class="ai-text"><strong style="color:white;">Uncertainty</strong></p>
<ul class="ai-text">{uncertainty_items or '<li>No major uncertainties identified.</li>'}</ul>
<p class="ai-text" style="font-size:12px;color:#7f8a9d;">
Provider: {response.provider} · Model: {response.model} · Decision support only. No actions executed.
</p>
</div>
""")


def render_copilot_page(snapshot: TelemetrySnapshot) -> None:
    init_copilot_session_state()

    st.html("""
<div class="section">AI Copilot</div>
<div class="ai-card">
<div class="ai-title">NEXUS INTELLIGENCE</div>
<div class="ai-heading">Operational Decision Support</div>
<p class="ai-text">
Ask NexusOps about infrastructure health, incidents, correlations, and investigation priorities.
Responses are built from the current simulated operational context.
</p>
</div>
""")

    render_copilot_status(snapshot)

    st.caption("Example investigation prompts")
    prompt_cols = st.columns(2)
    selected_prompt: str | None = None
    for index, prompt in enumerate(EXAMPLE_PROMPTS):
        with prompt_cols[index % 2]:
            if st.button(prompt, key=f"copilot_prompt_{index}", width="stretch"):
                selected_prompt = prompt

    control_col1, control_col2 = st.columns(2)
    with control_col1:
        if st.button("New Investigation", width="stretch"):
            clear_copilot_conversation()
            st.rerun()
    with control_col2:
        if st.button("Clear Conversation", width="stretch"):
            clear_copilot_conversation()
            st.rerun()

    for message in st.session_state.copilot_messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and "response" in message:
                render_copilot_response_card(message["response"])
            else:
                st.write(message.get("content", ""))

    question = selected_prompt
    if prompt := st.chat_input("Ask NexusOps about your infrastructure..."):
        question = prompt

    if question:
        st.session_state.copilot_messages.append({"role": "user", "content": question})
        with st.spinner("Analyzing operational context..."):
            response = run_copilot_investigation(
                question,
                snapshot,
                engine=st.session_state.copilot_engine,
            )
        st.session_state.copilot_messages.append(
            {"role": "assistant", "content": response.summary, "response": response}
        )
        st.rerun()
