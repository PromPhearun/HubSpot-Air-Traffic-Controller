# HubSpot Air Traffic Controller

## 📌 Project Overview & Context
You are assisting me, a member of the Deriv MarTech building a prototype for the Deriv AI Hackathon.

The HubSpot Air Traffic Controller is a centralized, automated system-wide communication gatekeeper designed to manage marketing volume, protect customer experience, and reduce costs. In a massive global footprint like Deriv's, various departments and regional teams run independent HubSpot workflows simultaneously. Without a centralized gatekeeper, a customer can easily be bombarded with multiple automated emails and premium WhatsApp messages within a short window. This leads to user fatigue, unsubscribe spikes, and costly WhatsApp spam block rates from Meta.

This application serves as a Global Traffic Control Room. It intercepts outgoing communication requests, utilizes an LLM to evaluate the contact's recent live interaction history from HubSpot, and dynamically enforces an ALLOW, HOLD, or REROUTE verdict.

## 🛠️ Tech Stack & Dependencies
Language: Python 3.10+

UI Framework: Streamlit

Integrations: HubSpot CRM API (via Python requests), Gemini API key.

Environment Management: python-dotenv

## 🔑 Environment Configuration (.env)
The app must support an isolated HubSpot Standard Sandbox environment for risk-free development, while preserving a transparent placeholder path to production. Create and reference a .env file with this exact structure:

```bash
# Gemini API Credentials
GEMINI_API_KEY="your_gemini_api_key_here"

# HubSpot Sandbox Integration (Active Development)
HUBSPOT_API_TOKEN="your_hubspot_sandbox_private_app_token_here"

# HubSpot Production Placeholder (Future Deployment)
# HUBSPOT_API_TOKEN="your_hubspot_production_private_app_token_here"
```

## 📐 Application Architecture & Data Flow
```
[HubSpot Workflow Outbound Trigger] 
                │
                ▼
  [Centralized Webhook Listener]
                │
                ▼
    [HubSpot API Data Fetcher] ───► Retrieves real Contact Profile & Timeline
                │
                ▼
       [Gemini LLM Engine]     ───► Analyzes timeline context & evaluates fatigue risk
                │
                ▼
    [Streamlit Control Center] ───► Logs transaction live & visualizes macro ecosystem metrics
```

## 📊 Streamlit UI Design Specs
The dashboard must be a single-page, professional web app configured in layout="wide" with a dark-mode friendly theme.

### 1. Executive Analytics Header
Four prominent metric columns (st.metric) providing immediate financial and administrative ROI tracking:

- **Est. WhatsApp Costs Saved**: Calculated dynamically assuming $0.08 per avoided message fatigue incident.
- **Unsubscribes Prevented**: A predictive metric representing saved customer churn.
- **Total Traffic Audited**: A running counter of all evaluations processed by the controller.
- **System Throttle Rate**: The percentage of overall traffic currently paused or rerouted ((Held + Rerouted) / Total Audited).

### 2. Main Live Control Console (Left Core Section)
A real-time data table or interactive stream showing system decisions. Each row must capture an intercept transaction:

`Timestamp | Workflow Source | Contact ID/Country | Channel | AI Action Status | Reasoning Breakdown`

*Note on Actions:* Statuses should be color-coded or emoji-tagged:
- **APPROVED ✅** (Safe to send)
- **HOLD 🛑** (Fatigue risk detected; paused for 24 hours)
- **REROUTE 🔀** (Downgraded from WhatsApp to low-impact Email)

### 3. Judge’s Interactive Sandbox (Right Sidebar / Secondary Tab)
An interactive simulation hub where hackathon judges can test the engine live:
- An input field to specify a real target contact email residing within the HubSpot Sandbox.
- A selection dropdown for the intended channel (WhatsApp, Email).
- A text entry field to draft a proposed marketing campaign message.
- A "Run Traffic Audit" submission button that triggers the live backend API chain and outputs the raw LLM logic transparently.

## 🚀 Step-by-Step Implementation Roadmap

### Phase 1: Environment & App Scaffold
- [ ] Verify .env file parsing pipeline.
- [ ] Initialize the Streamlit app setup layout with wide view and placeholder metric components.
- [ ] Create dummy/mock data structures for the main telemetry table so the UI can be reviewed immediately.

### Phase 2: HubSpot CRM API Client
- [ ] Build a robust API helper to fetch contact data by email (`/crm/v3/objects/contacts/{email}`).
- [ ] Build an extraction layer to grab recent timeline events, communication logs, or notes associated with that contact token.
- [ ] Handle API edge cases gracefully (e.g., Contact Not Found, Missing Scopes, Rate Limits).

### Phase 3: Gemini Judgment Engine
- [ ] Construct a highly specialized system prompt for Gemini acting as the "Air Traffic Controller".
- [ ] Program the prompt to parse incoming timeline arrays, inspect the proposed message for marketing aggressiveness/urgency, and output a strict structured response (Action + Rationale).

### Phase 4: Full System Wiring & Simulation Mode
- [ ] Tie the UI Sandbox to the active HubSpot and Gemini pipelines.
- [ ] Add a "Simulation Streamer" utility function that continuously populates the live stream with realistic global traffic pings (e.g., automatically generating mock background requests from regions like LATAM, EU/CIS, AFRICA, and ASIA) so the dashboard looks functional and highly alive during the presentation demo.
