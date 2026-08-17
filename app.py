import time

import plotly.graph_objects as go
import streamlit as st

from app.copilot_ui import render_copilot_page
from app.incident_ui import render_incident_intelligence
from services.incident_service import build_investigation, find_incident
from telemetry import (
    ENVIRONMENTS,
    Incident,
    SERVICES,
    TIME_RANGES,
    TelemetrySnapshot,
    build_kpis,
    get_cloud_resources,
    get_snapshot,
)

st.set_page_config(
    page_title="NexusOps AI",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

AUTO_REFRESH_SECONDS = 30


def init_session_state() -> None:
    defaults = {
        "environment": "Development",
        "service": "All Services",
        "time_range": "24H",
        "auto_refresh": False,
        "data_version": 0,
        "selected_incident_id": None,
        "show_investigation": False,
        "investigation_incident_id": None,
        "messages": None,
        "last_auto_refresh": time.time(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_data(show_spinner=False)
def load_snapshot(
    environment: str,
    service: str,
    time_range: str,
    data_version: int,
) -> TelemetrySnapshot:
    return get_snapshot(environment, service, time_range, data_version)


@st.cache_data(show_spinner=False)
def load_investigation(
    environment: str,
    service: str,
    time_range: str,
    data_version: int,
    incident_id: str | None,
):
    snapshot = get_snapshot(environment, service, time_range, data_version)
    incident = find_incident(snapshot, incident_id)
    return build_investigation(incident, snapshot)


def open_incident_investigation(incident_id: str) -> None:
    st.session_state.show_investigation = True
    st.session_state.investigation_incident_id = incident_id
    st.session_state.selected_incident_id = incident_id


def render_investigation_panel(incident_id: str | None) -> None:
    if not st.session_state.show_investigation or not incident_id:
        return

    investigation = load_investigation(
        st.session_state.environment,
        st.session_state.service,
        st.session_state.time_range,
        st.session_state.data_version,
        incident_id,
    )
    if investigation is None:
        st.warning("Unable to load incident intelligence for the selected incident.")
        return

    st.divider()
    render_incident_intelligence(investigation)


def render_styles() -> None:
    st.html("""
<style>
    .stApp {
        background:
            radial-gradient(
                circle at 15% 10%,
                rgba(59,130,246,.12),
                transparent 30%
            ),
            radial-gradient(
                circle at 85% 80%,
                rgba(20,184,166,.10),
                transparent 30%
            ),
            #050914;
        color: #e5e7eb;
    }

    [data-testid="stSidebar"] {
        background: #080d18;
        border-right: 1px solid rgba(255,255,255,.07);
    }

    .block-container {
        max-width: 1500px;
        padding-top: 2rem;
    }

    .hero {
        padding: 15px 0 25px;
    }

    .brand {
        font-size: 46px;
        font-weight: 800;
        letter-spacing: -2px;
        color: #ffffff;
    }

    .brand span {
        color: #5eead4;
    }

    .subtitle {
        color: #8b95a7;
        font-size: 16px;
        margin-top: 4px;
    }

    .status {
        display: inline-block;
        margin-top: 15px;
        padding: 7px 14px;
        border-radius: 30px;
        background: rgba(34,197,94,.08);
        border: 1px solid rgba(34,197,94,.25);
        color: #4ade80;
        font-size: 12px;
        font-weight: 600;
    }

    .status-warning {
        background: rgba(245,158,11,.08);
        border: 1px solid rgba(245,158,11,.25);
        color: #fbbf24;
    }

    .status-critical {
        background: rgba(239,68,68,.08);
        border: 1px solid rgba(239,68,68,.25);
        color: #f87171;
    }

    .metric {
        background: rgba(15,23,42,.72);
        border: 1px solid rgba(255,255,255,.07);
        border-radius: 18px;
        padding: 20px;
        min-height: 125px;
        box-shadow: 0 12px 40px rgba(0,0,0,.18);
    }

    .metric-label {
        color: #7f8a9d;
        font-size: 11px;
        letter-spacing: 1.3px;
        font-weight: 600;
    }

    .metric-value {
        color: white;
        font-size: 30px;
        font-weight: 750;
        margin-top: 8px;
    }

    .metric-change {
        color: #4ade80;
        font-size: 12px;
        margin-top: 5px;
    }

    .section {
        color: white;
        font-size: 20px;
        font-weight: 700;
        margin: 28px 0 12px;
    }

    .ai-card {
        background:
            linear-gradient(
                135deg,
                rgba(59,130,246,.12),
                rgba(20,184,166,.07)
            );
        border: 1px solid rgba(94,234,212,.16);
        border-radius: 20px;
        padding: 24px;
        min-height: 320px;
    }

    .ai-title {
        color: #5eead4;
        font-size: 13px;
        letter-spacing: 1px;
        font-weight: 700;
    }

    .ai-heading {
        color: white;
        font-size: 23px;
        font-weight: 700;
        margin-top: 8px;
    }

    .ai-text {
        color: #a8b1c2;
        line-height: 1.7;
    }

    .incident {
        background: rgba(15,23,42,.60);
        border: 1px solid rgba(255,255,255,.06);
        border-radius: 13px;
        padding: 14px 16px;
        margin-bottom: 9px;
    }

    .critical {
        border-left: 4px solid #ef4444;
    }

    .warning {
        border-left: 4px solid #f59e0b;
    }

    .info {
        border-left: 4px solid #38bdf8;
    }

    .detail-card {
        background: rgba(15,23,42,.72);
        border: 1px solid rgba(94,234,212,.16);
        border-radius: 18px;
        padding: 20px;
        margin-top: 12px;
    }

    .footer {
        color: #596579;
        text-align: center;
        padding: 30px 0 10px;
        font-size: 12px;
    }
</style>
""")


def render_footer() -> None:
    st.html("""
<div class="footer">
NexusOps AI · Intelligent Operations Platform · Project 3
</div>
""")


def status_class(status: str) -> str:
    if "DEGRADED" in status:
        return "status status-critical"
    if "ELEVATED" in status:
        return "status status-warning"
    return "status"


def render_metric_cards(snapshot: TelemetrySnapshot) -> None:
    columns = st.columns(4)
    for column, metric in zip(columns, build_kpis(snapshot)):
        with column:
            arrow = "↗" if metric.change.startswith("+") else "↘"
            st.html(f"""
<div class="metric">
<div class="metric-label">{metric.label}</div>
<div class="metric-value">{metric.value}</div>
<div class="metric-change">{arrow} {metric.change} vs previous period</div>
</div>
""")


def build_traffic_chart(snapshot: TelemetrySnapshot) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=snapshot.chart_labels,
            y=snapshot.chart_values,
            mode="lines",
            fill="tozeroy",
            line=dict(width=3),
            name="Requests",
        )
    )
    fig.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"),
        xaxis=dict(
            title=snapshot.time_range,
            gridcolor="rgba(255,255,255,.05)",
        ),
        yaxis=dict(
            title=snapshot.chart_title,
            gridcolor="rgba(255,255,255,.05)",
        ),
        showlegend=False,
    )
    return fig


def render_incident_card(incident: Incident, selected: bool = False) -> None:
    border = "border:1px solid rgba(94,234,212,.35);" if selected else ""
    st.html(f"""
<div class="incident {incident.severity}" style="{border}">
<strong style="color:white;">{incident.severity.upper()}</strong>
<span style="color:#d1d5db;">— {incident.title}</span>
<br>
<small style="color:#7f8a9d;">{incident.service_label} · {incident.timestamp} · {incident.status}</small>
</div>
""")


def render_incident_detail(incident: Incident) -> None:
    st.html(f"""
<div class="detail-card">
<div class="ai-title">INCIDENT DETAIL</div>
<div class="ai-heading">{incident.title}</div>
<p class="ai-text"><strong style="color:white;">Severity:</strong> {incident.severity.upper()}</p>
<p class="ai-text"><strong style="color:white;">Service:</strong> {incident.service_label}</p>
<p class="ai-text"><strong style="color:white;">Status:</strong> {incident.status}</p>
<p class="ai-text"><strong style="color:white;">Description:</strong> {incident.description}</p>
<p class="ai-text"><strong style="color:white;">Impact:</strong> {incident.impact}</p>
<p style="color:#5eead4;"><strong>Recommended next step:</strong> {incident.recommended_step}</p>
</div>
""")


def render_ai_brief(snapshot: TelemetrySnapshot) -> None:
    st.html(f"""
<div class="ai-card">
<div class="ai-title">NEXUS INTELLIGENCE</div>
<div class="ai-heading">AI Operations Brief</div>
<p class="ai-text">{snapshot.ai_summary}</p>
<p class="ai-text">{snapshot.ai_detail}</p>
<p style="color:#5eead4;">● Operational confidence: {snapshot.operational_confidence}%</p>
</div>
""")


def handle_auto_refresh() -> None:
    if not st.session_state.auto_refresh:
        return
    elapsed = time.time() - st.session_state.last_auto_refresh
    if elapsed >= AUTO_REFRESH_SECONDS:
        st.session_state.data_version += 1
        st.session_state.last_auto_refresh = time.time()
        st.rerun()


def render_operations_controls() -> None:
    st.caption("OPERATIONS CONTROL")

    st.session_state.environment = st.selectbox(
        "Environment",
        ENVIRONMENTS,
        index=ENVIRONMENTS.index(st.session_state.environment),
    )
    st.session_state.service = st.selectbox(
        "Service",
        SERVICES,
        index=SERVICES.index(st.session_state.service),
    )
    st.session_state.time_range = st.selectbox(
        "Time range",
        TIME_RANGES,
        index=TIME_RANGES.index(st.session_state.time_range),
    )
    st.session_state.auto_refresh = st.toggle(
        "Auto-refresh",
        value=st.session_state.auto_refresh,
        help=f"Refresh simulated telemetry every {AUTO_REFRESH_SECONDS} seconds.",
    )
    if st.button("Refresh Data", width="stretch"):
        st.session_state.data_version += 1
        st.session_state.last_auto_refresh = time.time()
        st.rerun()

    st.caption("Demo telemetry only — not live production data.")


init_session_state()
render_styles()
handle_auto_refresh()

snapshot = load_snapshot(
    st.session_state.environment,
    st.session_state.service,
    st.session_state.time_range,
    st.session_state.data_version,
)

with st.sidebar:
    st.markdown("## ◈ NexusOps AI")
    st.caption("Intelligent Operations Command Center")
    st.divider()

    page = st.radio(
        "NAVIGATION",
        [
            "Command Center",
            "Incidents",
            "Analytics",
            "AI Copilot",
            "Cloud Resources",
        ],
    )

    st.divider()
    render_operations_controls()
    st.divider()

    st.caption("SYSTEM STATUS")
    st.success("● Platform Online")
    st.caption("Active environment")
    st.write(st.session_state.environment)
    st.caption("Region")
    st.write("Global")

if page == "Command Center":
    status_css = status_class(snapshot.operational_status)
    st.html(f"""
<div class="hero">
<div class="brand">Nexus<span>Ops</span> AI</div>
<div class="subtitle">
Intelligent cloud operations, analytics & AI decision support
</div>
<div class="{status_css}">
● {snapshot.operational_status}
</div>
</div>
""")

    st.caption(
        f"Viewing simulated telemetry for {snapshot.service} · "
        f"{snapshot.environment} · {snapshot.time_range}"
    )

    render_metric_cards(snapshot)

    st.html('<div class="section">Operations Overview</div>')
    left, right = st.columns([1.65, 1])

    with left:
        if snapshot.chart_values:
            st.plotly_chart(build_traffic_chart(snapshot), width="stretch")
        else:
            st.info("No chart data available for the selected filters.")

    with right:
        render_ai_brief(snapshot)

    st.html('<div class="section">Live Operations Feed</div>')

    if not snapshot.incidents:
        st.info("No incidents match the current environment and service filters.")
    else:
        incident_ids = [incident.id for incident in snapshot.incidents]
        if st.session_state.selected_incident_id not in incident_ids:
            st.session_state.selected_incident_id = incident_ids[0]

        selected_id = st.radio(
            "Select incident",
            incident_ids,
            format_func=lambda incident_id: next(
                item.title for item in snapshot.incidents if item.id == incident_id
            ),
            key="incident_selector",
        )
        st.session_state.selected_incident_id = selected_id

        for incident in snapshot.incidents:
            render_incident_card(
                incident,
                selected=incident.id == st.session_state.selected_incident_id,
            )

        selected_incident = next(
            item for item in snapshot.incidents if item.id == st.session_state.selected_incident_id
        )
        render_incident_detail(selected_incident)

        if st.button("Open Incident Intelligence", type="primary", width="stretch"):
            open_incident_investigation(selected_incident.id)
            st.rerun()

        render_investigation_panel(st.session_state.investigation_incident_id)

    render_footer()

elif page == "Incidents":
    st.html('<div class="section">Incident Management</div>')
    st.caption(
        f"Simulated incidents for {snapshot.environment} · {snapshot.service} · {snapshot.time_range}"
    )

    filter_col, stats_col = st.columns([2, 1])
    with filter_col:
        severity_filter = st.multiselect(
            "Filter by severity",
            ["CRITICAL", "WARNING", "INFO"],
            default=["CRITICAL", "WARNING", "INFO"],
        )
    with stats_col:
        critical_count = sum(1 for item in snapshot.incidents if item.severity == "critical")
        warning_count = sum(1 for item in snapshot.incidents if item.severity == "warning")
        st.metric("Open Incidents", snapshot.open_incidents)
        st.caption(f"{critical_count} critical · {warning_count} warning")

    filtered = [
        item for item in snapshot.incidents
        if item.severity.upper() in severity_filter
    ]

    if not filtered:
        st.info("No incidents match the selected severity filters.")
    else:
        incident_ids = [item.id for item in filtered]
        if st.session_state.investigation_incident_id not in incident_ids:
            st.session_state.investigation_incident_id = incident_ids[0]

        selected_id = st.selectbox(
            "Select incident to investigate",
            incident_ids,
            format_func=lambda incident_id: next(
                item.title for item in filtered if item.id == incident_id
            ),
            key="incidents_page_selector",
        )

        for incident in filtered:
            render_incident_card(
                incident,
                selected=incident.id == selected_id,
            )

        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button("Open Incident Intelligence", type="primary", width="stretch"):
                open_incident_investigation(selected_id)
                st.rerun()
        with action_col2:
            if st.button("Close Investigation", width="stretch"):
                st.session_state.show_investigation = False
                st.rerun()

        selected_incident = next(item for item in filtered if item.id == selected_id)
        with st.expander(f"Quick summary — {selected_incident.service_label}", expanded=False):
            render_incident_detail(selected_incident)

        render_investigation_panel(st.session_state.investigation_incident_id)

    render_footer()

elif page == "Analytics":
    st.html('<div class="section">Operational Analytics</div>')
    st.caption(
        f"Analytics for {snapshot.service} · {snapshot.environment} · {snapshot.time_range}"
    )

    if snapshot.chart_values:
        fig = build_traffic_chart(snapshot)
        fig.update_layout(height=380)
        st.plotly_chart(fig, width="stretch")

        col1, col2, col3 = st.columns(3)
        col1.metric("Peak Traffic", f"{max(snapshot.chart_values):,.0f}")
        col2.metric("Average", f"{sum(snapshot.chart_values) / len(snapshot.chart_values):,.0f}")
        col3.metric("Lowest", f"{min(snapshot.chart_values):,.0f}")
    else:
        st.info("No analytics data available for the selected filters.")

    render_footer()

elif page == "AI Copilot":
    render_copilot_page(snapshot)
    render_footer()

elif page == "Cloud Resources":
    st.html('<div class="section">Cloud Resources</div>')
    st.caption(
        f"Simulated resource inventory for {snapshot.environment} · {snapshot.time_range}"
    )

    search = st.text_input("Search services", placeholder="Filter by service name...")
    resources = get_cloud_resources(snapshot)
    filtered_resources = [
        resource for resource in resources
        if search.lower() in resource["name"].lower()
        or search.lower() in resource["label"].lower()
    ]

    st.html("""
<div style="color:#7f8a9d;font-size:11px;letter-spacing:1.3px;font-weight:600;margin-bottom:8px;">
SERVICE · TYPE · STATUS · REGION · INSTANCES · CPU · LATENCY
</div>
""")

    status_colors = {
        "Running": "#4ade80",
        "Degraded": "#f59e0b",
    }

    if not filtered_resources:
        st.info("No cloud resources match your search.")
    else:
        for resource in filtered_resources:
            color = status_colors.get(resource["status"], "#38bdf8")
            st.html(f"""
<div class="incident info">
<strong style="color:white;">{resource["name"]}</strong>
<span style="color:#d1d5db;"> · {resource["type"]} · </span>
<span style="color:{color};">{resource["status"]}</span>
<br>
<small style="color:#7f8a9d;">
{resource["region"]} · {resource["instances"]} instances · CPU {resource["cpu"]} · Latency {resource["latency"]}
</small>
</div>
""")

    st.caption(f"Showing {len(filtered_resources)} of {len(resources)} resources")

    render_footer()
