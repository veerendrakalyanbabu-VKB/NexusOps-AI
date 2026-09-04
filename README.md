# NexusOps AI

A portfolio implementation of an operations intelligence workspace for exploring infrastructure health, incident context, correlated signals, and evidence-backed investigation paths.

The application is built with **Python, Streamlit, Pandas, Plotly, pytest, and a provider abstraction for optional AI-assisted analysis**.

**🌐 Live Demo:** [nexusops-ai-y6cvwvktst6dq2peeudqsz.streamlit.app](https://nexusops-ai-y6cvwvktst6dq2peeudqsz.streamlit.app/)

**💻 GitHub Repository:** [github.com/veerendrakalyanbabu-VKB/nexusops-ai](https://github.com/veerendrakalyanbabu-VKB/NexusOps-AI)

---

## 🚀 Project Overview

NexusOps AI is an AI-assisted operations command center that brings infrastructure monitoring, incident intelligence, operational correlation and AI-assisted decision support into a single interface.

The platform is designed around the way modern engineering and DevOps teams investigate operational issues:

**Monitor → Detect → Investigate → Correlate → Assess → Recommend**

NexusOps transforms operational telemetry and incident signals into structured intelligence that helps engineers understand:

- What is happening?
- Which services are affected?
- What signals are correlated?
- What could be causing the issue?
- What evidence supports the assessment?
- What should be investigated next?

> **Note:** The current deployment uses simulated deterministic telemetry for portfolio demonstration. It does not represent live production infrastructure.

---

## ⚡ Core Capabilities

### 📊 Command Center

The Command Center provides a centralized operational overview including:

- System Health
- Active Services
- Open Incidents
- Monthly Cloud Cost
- Health Trends
- Service Status
- Latency Signals
- Operational Trends
- Infrastructure Health Indicators
- Operational Confidence

---

### 🚨 Incident Intelligence

Incident Intelligence helps engineers investigate operational problems using structured evidence.

Features include:

- Incident detection
- Incident severity
- Incident timeline
- Telemetry evidence
- Service impact
- Correlation signals
- Root-cause hypotheses
- Business impact assessment
- Investigation priorities
- Recommended next steps

---

### 🤖 AI Copilot

The AI Copilot provides structured operational decision support.

It can help engineers understand:

- Current operational state
- Incident context
- Investigation priorities
- Supporting evidence
- Potential causes
- Recommended actions
- Operational risk
- Confidence levels

The Copilot is designed as a **decision-support system**, rather than an autonomous infrastructure controller.

---

### 🔗 Service Correlation

NexusOps analyzes operational signals across services to identify potentially related degradation.

Correlation intelligence can help identify:

- Related service failures
- Dependency signals
- Latency relationships
- Infrastructure degradation
- Incident relationships
- Potential cascading failures

This helps reduce the time required to move from an alert to a meaningful investigation.

---

### 🧠 AI Provider Abstraction

NexusOps uses an AI provider abstraction layer that allows intelligence providers to be changed without redesigning the application architecture.

Supported architecture includes:

- Local deterministic provider
- Google Gemini
- OpenAI
- Anthropic Claude

The local deterministic provider allows the application to operate without requiring an external AI API key.

---

### 🛡️ Safe Decision Support

NexusOps AI follows a human-in-the-loop operational model.

The platform can provide:

- Investigation recommendations
- Operational assessments
- Remediation suggestions
- Evidence-based reasoning

However:

**NexusOps does not automatically execute infrastructure changes.**

Infrastructure actions remain under engineer control.

---

## 🧠 Intelligence Architecture

```text
                         NEXUSOPS AI
                              |
                   Streamlit Command Center
                              |
             +----------------+----------------+
             |                                 |
      Incident Intelligence              AI Copilot
             |                                 |
             +----------------+----------------+
                              |
                    Operational Context
                              |
             +----------------+----------------+
             |                |               |
         Telemetry        Incidents      Correlations
             |                |               |
             +----------------+----------------+
                              |
                     AI Provider Layer
                              |
             +----------------+----------------+
             |                |               |
           Local           Gemini          OpenAI
        Deterministic                      Claude
