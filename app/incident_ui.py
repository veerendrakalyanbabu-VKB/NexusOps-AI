"""Incident Intelligence UI rendering."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from ai.engine import InvestigationEngine
from core.incident_model import IncidentInvestigation


def _chart_layout(title: str, y_title: str) -> dict:
    return dict(
        height=260,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"),
        xaxis=dict(title="Time", gridcolor="rgba(255,255,255,.05)"),
        yaxis=dict(title=y_title, gridcolor="rgba(255,255,255,.05)"),
        showlegend=False,
        title=dict(text=title, font=dict(size=14, color="#e5e7eb")),
    )


def _add_incident_marker(fig: go.Figure, evidence, labels: list[str]) -> None:
    if not labels:
        return
    index = min(evidence.incident_index, len(labels) - 1)
    fig.add_vline(
        x=labels[index],
        line_width=1,
        line_dash="dash",
        line_color="#f87171",
    )


def render_incident_intelligence(investigation: IncidentInvestigation) -> None:
    """Render the full Incident Intelligence investigation experience."""
    severity = investigation.severity.upper()
    st.html(f"""
<div class="section">INCIDENT COMMAND</div>
<div class="detail-card">
<div class="ai-title">{severity}</div>
<div class="ai-heading">{investigation.title}</div>
<p class="ai-text"><strong style="color:white;">Service:</strong> {investigation.service_label}</p>
<p class="ai-text"><strong style="color:white;">Status:</strong> {investigation.status.title()}</p>
<p class="ai-text"><strong style="color:white;">Detected:</strong> {investigation.detected_at}</p>
<p class="ai-text"><strong style="color:white;">Impact:</strong> {investigation.impact}</p>
<p class="ai-text" style="color:#7f8a9d;font-size:12px;">{investigation.demo_notice}</p>
</div>
""")

    st.html('<div class="section">Executive Impact</div>')
    metrics = investigation.executive_metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Error Rate", f"{metrics.error_rate:.1f}%")
    col2.metric("Latency", f"{metrics.latency_ms:.0f} ms")
    col3.metric("Traffic", f"{metrics.traffic_per_min:,.0f}/min")
    col4.metric("Business Impact", metrics.business_impact_summary[:28] + "...")
    col5.metric("Affected Services", metrics.affected_services)

    st.html('<div class="section">Incident Timeline</div>')
    for event in investigation.timeline:
        st.html(f"""
<div class="incident info">
<strong style="color:#5eead4;">{event.time}</strong>
<span style="color:#d1d5db;"> — {event.label}</span>
<br><small style="color:#7f8a9d;">{event.category}</small>
</div>
""")

    st.html('<div class="section">Telemetry Evidence</div>')
    evidence = investigation.evidence
    labels = list(evidence.labels)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        latency_fig = go.Figure()
        latency_fig.add_trace(
            go.Scatter(x=labels, y=list(evidence.latency), mode="lines", line=dict(width=2))
        )
        _add_incident_marker(latency_fig, evidence, labels)
        latency_fig.update_layout(**_chart_layout("API Latency", "ms"))
        st.plotly_chart(latency_fig, width="stretch")

        error_fig = go.Figure()
        error_fig.add_trace(
            go.Scatter(x=labels, y=list(evidence.error_rate), mode="lines", line=dict(width=2))
        )
        _add_incident_marker(error_fig, evidence, labels)
        error_fig.update_layout(**_chart_layout("Error Rate", "%"))
        st.plotly_chart(error_fig, width="stretch")

    with chart_col2:
        traffic_fig = go.Figure()
        traffic_fig.add_trace(
            go.Scatter(
                x=labels,
                y=list(evidence.request_volume),
                mode="lines",
                fill="tozeroy",
                line=dict(width=2),
            )
        )
        _add_incident_marker(traffic_fig, evidence, labels)
        traffic_fig.update_layout(**_chart_layout("Request Volume", "req/min"))
        st.plotly_chart(traffic_fig, width="stretch")

        cpu_fig = go.Figure()
        cpu_fig.add_trace(
            go.Scatter(x=labels, y=list(evidence.database_cpu), mode="lines", line=dict(width=2))
        )
        _add_incident_marker(cpu_fig, evidence, labels)
        cpu_fig.update_layout(**_chart_layout("Database CPU", "%"))
        st.plotly_chart(cpu_fig, width="stretch")

    st.html('<div class="section">Service Correlation</div>')
    for service in investigation.related_services:
        st.html(f"""
<div class="incident warning">
<strong style="color:white;">{service.name}</strong>
<span style="color:#7f8a9d;"> — {service.relationship}</span>
<br>
<small style="color:#7f8a9d;">
Health {service.health:.1f}% · Latency {service.latency_ms:.0f} ms ·
Error {service.error_rate:.1f}% · CPU {service.cpu:.1f}%
</small>
</div>
""")

    st.html('<div class="section">Root Cause Analysis</div>')
    for hypothesis in investigation.hypotheses:
        rank_label = hypothesis.rank.upper()
        evidence_items = "".join(f"<li>{item}</li>" for item in hypothesis.evidence)
        st.html(f"""
<div class="detail-card">
<div class="ai-title">{rank_label} HYPOTHESIS</div>
<div class="ai-heading">{hypothesis.title}</div>
<p style="color:#5eead4;">Confidence: {hypothesis.confidence}%</p>
<p class="ai-text"><strong style="color:white;">Evidence:</strong></p>
<ul class="ai-text">{evidence_items}</ul>
<p class="ai-text" style="font-size:12px;color:#7f8a9d;">
Correlation-based hypothesis from simulated telemetry. Not machine-learned root-cause analysis.
</p>
</div>
""")

    st.html('<div class="section">Business Impact</div>')
    impact = investigation.business_impact
    st.html(f"""
<div class="detail-card">
<p class="ai-text"><strong style="color:white;">Technical signal:</strong> {impact.technical_signal}</p>
<p class="ai-text"><strong style="color:white;">Business interpretation:</strong> {impact.business_interpretation}</p>
<p class="ai-text"><strong style="color:white;">Checkout success impact (est.):</strong> ↓ {impact.checkout_success_delta:.1f}%</p>
<p class="ai-text"><strong style="color:white;">Affected transactions (est.):</strong> {impact.affected_transactions:,}</p>
<p class="ai-text"><strong style="color:white;">Severity:</strong> {impact.severity_level}</p>
<p class="ai-text"><strong style="color:white;">Customer impact:</strong> {impact.customer_impact}</p>
<p class="ai-text"><strong style="color:white;">Estimated risk:</strong> {impact.estimated_hourly_risk}</p>
</div>
""")

    st.html('<div class="section">Recommended Actions</div>')
    for item in investigation.recommendations:
        st.html(f"""
<div class="incident info">
<strong style="color:white;">{item.step}. {item.action}</strong>
<br><small style="color:#7f8a9d;">Why: {item.reason}</small>
</div>
""")

    st.html('<div class="section">Ask NexusOps</div>')
    _render_ai_investigation_panel(investigation)


def _render_ai_investigation_panel(investigation: IncidentInvestigation) -> None:
    engine = InvestigationEngine()
    message_key = f"investigation_messages_{investigation.incident_id}"

    if message_key not in st.session_state:
        st.session_state[message_key] = [
            {
                "role": "assistant",
                "content": (
                    f"Incident intelligence loaded for '{investigation.title}'. "
                    f"Ask why the service is degraded, what the business impact is, "
                    f"or what to do next. {investigation.demo_notice}"
                ),
            }
        ]

    for message in st.session_state[message_key]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if prompt := st.chat_input("Ask NexusOps about this incident...", key=f"investigate_{investigation.incident_id}"):
        st.session_state[message_key].append({"role": "user", "content": prompt})
        response = engine.ask(investigation, prompt)
        st.session_state[message_key].append({"role": "assistant", "content": response})
        st.rerun()
