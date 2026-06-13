# ✈️ HubSpot Air Traffic Controller

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Streamlit-red.svg)](https://streamlit.io/)
[![Hackathon](https://img.shields.io/badge/project-Deriv%20AI%20Hackathon-orange.svg)](https://github.com/PromPhearun/HubSpot-Air-Traffic-Controller)

**HubSpot Air Traffic Controller** is a centralized, automated system-wide communication gatekeeper designed to manage marketing volume, protect customer experience, and reduce costs. 

Developed as a prototype for the **Deriv AI Hackathon** by the **Deriv MarTech** team, this application serves as a Global Traffic Control Room. It intercepts outgoing communication requests, utilizes an LLM to evaluate the contact's recent live interaction history from HubSpot, and dynamically enforces an `ALLOW`, `HOLD`, or `REROUTE` verdict to prevent customer fatigue.

---

## 📌 Problem Statement & Context

In a massive global footprint like **Deriv's**, multiple regional and departmental teams operate independent HubSpot workflows simultaneously. Without a centralized gatekeeper:
1. **User Fatigue:** A customer can easily be bombarded with multiple automated emails and high-impact WhatsApp messages within a very short window.
2. **High Opt-Out Rates:** Over-communication leads directly to spikes in unsubscribes and churn.
3. **Meta Spam Penalties:** Frequent WhatsApp messaging triggers high spam block rates, resulting in increased costs and domain reputation damage.

**The Solution:** This controller acts as a global pre-flight check. Before any automated outbound communication goes out, the request is audited.

---

## 📐 System Architecture & Data Flow

The flow of data from trigger to verdict and dashboard visualization:

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

---

## 🛠️ Key Features

*   **Executive Analytics Header:** Real-time financial and administrative ROI tracking:
    *   **Est. WhatsApp Costs Saved:** Calculated dynamically based on avoided message fatigue incidents ($0.08 per avoided incident).
    *   **Unsubscribes Prevented:** Predictive model representing saved customer churn.
    *   **Total Traffic Audited:** A running counter of all evaluations processed.
    *   **System Throttle Rate:** Percentage of overall traffic currently paused or rerouted.
*   **Global Traffic Control Console:** A live-updating telemetry stream showing real-time decisions:
    *   **APPROVED ✅**: Safe to send.
    *   **HOLD 🛑**: Fatigue risk detected; paused for 24 hours.
    *   **REROUTE 🔀**: Downgraded from premium WhatsApp to low-impact Email.
*   **Judge’s Interactive Sandbox:** An interactive simulation hub where users can run a target HubSpot Sandbox contact through a live traffic audit using custom marketing copy.

---

## ⚙️ Tech Stack & Dependencies

*   **Language:** Python 3.10+
*   **UI Framework:** Streamlit
*   **Integrations:** HubSpot CRM API, Gemini API (via Google GenAI)
*   **Data Manipulation:** Pandas, Numpy
*   **Environment Management:** Python-dotenv

---

## 🔑 Installation & Configuration

### 1. Prerequisites
Ensure you have Python 3.10 or higher installed on your machine.

### 2. Clone the Repository
```bash
git clone https://github.com/PromPhearun/HubSpot-Air-Traffic-Controller.git
cd "HubSpot Air Traffic Controller"
```

### 3. Create a `.env` File
Create a `.env` file in the root directory with the following structure:
```bash
# Gemini API Credentials
GEMINI_API_KEY="your_gemini_api_key_here"

# HubSpot Sandbox Integration (Active Development)
HUBSPOT_API_TOKEN="your_hubspot_sandbox_private_app_token_here"

# HubSpot Production Placeholder (Future Deployment)
# HUBSPOT_API_TOKEN="your_hubspot_production_private_app_token_here"
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Launch the Dashboard
```bash
streamlit run app.py
```

---

## 🛡️ Security & Compliance Guardrails

The project implements rigid security guardrails in accordance with `/security.md` and the Deriv global standards:
*   **Sandbox Isolation:** All active development write operations are strictly bound to the HubSpot Standard Sandbox environment. Production tokens remain safely placeholder-defined.
*   **API Key Safety:** The `.env` configuration file is explicitly ignored in `.gitignore` to prevent credential leaks.
*   **Safe Dependency Management:** Official packages and versions are pinned in `requirements.txt` to guard against upstream supply chain or typosquatting threats.

---

## 🚀 Hackathon Roadmap

- [x] **Phase 1: Environment & App Scaffold**
    - [x] Streamlit wide-layout integration with telemetry metrics.
    - [x] Dynamic mock datastream for UI verification.
- [ ] **Phase 2: HubSpot CRM API Client**
    - [ ] Target contact search via HubSpot CRM SDK/API (`/crm/v3/objects/contacts`).
    - [ ] Interaction timeline & log retrieval logic.
- [ ] **Phase 3: Gemini Judgment Engine**
    - [ ] Air Traffic Controller system prompt configuration.
    - [ ] Strict JSON decision payload extraction.
- [ ] **Phase 4: Full System Wiring & Simulation Mode**
    - [ ] Wire active APIs to sandbox inputs.
    - [ ] Enable background simulated stream to demonstrate live traffic from various regions (LATAM, EU, ASIA, AFRICA).
