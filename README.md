# NexusOps AI

NexusOps AI is an AI-assisted cloud operations platform for monitoring infrastructure health, investigating incidents, analyzing operational telemetry, and providing decision-support recommendations.

## Current Version

**v0.4 — AI Copilot**

Built on top of:
- **v0.2** Interactive Command Center
- **v0.3** Incident Intelligence

## Features

- Command Center dashboard with KPI metrics and operations charts
- Incident Intelligence with timeline, telemetry evidence, and root-cause hypotheses
- AI Copilot with structured operational assessments
- Simulated deterministic telemetry (not live production infrastructure)

## Architecture

```
NexusOps UI (Streamlit)
  ↓
AI Copilot / Incident Intelligence
  ↓
Operational Context Engine
  ↓
Telemetry + Incidents + Correlations + Analytics
  ↓
AI Provider Abstraction
  ↓
Structured CopilotResponse
```

### Key modules

| Module | Purpose |
|--------|---------|
| `telemetry.py` | Deterministic demo telemetry engine |
| `core/operational_context.py` | Compact operational context for Copilot |
| `core/copilot_model.py` | Structured Copilot models |
| `services/copilot_service.py` | Copilot orchestration |
| `ai/providers.py` | Provider abstraction + fallback |
| `ai/engine.py` | Copilot and investigation engines |
| `app/copilot_ui.py` | Copilot UI rendering |

## Local Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Testing

```bash
python -m pytest -q
```

## AI Provider Configuration

By default, NexusOps uses a **local deterministic fallback** provider. No API key is required.

Optional environment variables:

| Variable | Description |
|----------|-------------|
| `NEXUSOPS_AI_PROVIDER` | `local`, `claude`, `gemini`, or `openai` |
| `ANTHROPIC_API_KEY` | Claude API key |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | Gemini API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `NEXUSOPS_CLAUDE_MODEL` | Optional Claude model override |
| `NEXUSOPS_GEMINI_MODEL` | Optional Gemini model override |
| `NEXUSOPS_OPENAI_MODEL` | Optional OpenAI model override |

External provider SDKs are optional. If credentials or SDKs are missing, NexusOps falls back to the local deterministic provider.

## Safety Boundary

NexusOps v0.4 is **decision-support only**. The Copilot may recommend investigation and remediation steps, but it does **not** execute infrastructure changes automatically.

## Simulated Telemetry Disclaimer

All telemetry in the current build is **simulated demo data** for development and portfolio demonstration. It does not represent live AWS, GCP, or Azure production infrastructure unless explicitly integrated in a future version.

## Limitations

- No live cloud telemetry integration yet
- No automated remediation actions
- External AI providers require optional SDK installation and API credentials
- Chat history is session-scoped only (no database persistence)
