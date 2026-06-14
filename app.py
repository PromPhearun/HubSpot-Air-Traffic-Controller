import streamlit as st
import datetime
import pandas as pd
import requests
import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env
load_dotenv()

# Set Streamlit layout configuration to wide
st.set_page_config(
    page_title="HubSpot Air Traffic Controller",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling for Dark Mode/Hackathon Vibe ---
st.markdown("""
<style>
    .metric-card {
        background-color: #1e293b;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #3b82f6;
        margin-bottom: 10px;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.8rem;
        color: #f8fafc;
        font-weight: 700;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- Title Header ---
st.title("🎛️ HubSpot Air Traffic Controller")
st.caption("Deriv AI Hackathon Prototype — Global Outgoing Communication Interceptor & Guardrail")

# --- Environment Configuration Check ---
hubspot_token = os.getenv("HUBSPOT_API_TOKEN")
gemini_key = os.getenv("GEMINI_API_KEY")

env_error = False
if not hubspot_token or "your_hubspot" in hubspot_token:
    st.sidebar.error("❌ HUBSPOT_API_TOKEN is missing or not configured in .env")
    env_error = True

if not gemini_key or "your_gemini" in gemini_key:
    st.sidebar.error("❌ GEMINI_API_KEY is missing or not configured in .env")
    env_error = True

# --- Helper Functions ---

def validate_email(email: str) -> bool:
    """Validate email format to prevent injection and bad inputs."""
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(email_regex, email))

def fetch_hubspot_contact_timeline(email: str):
    """
    Fetches the HubSpot contact's core properties and associated notes.
    """
    if not hubspot_token:
        raise ValueError("HUBSPOT_API_TOKEN is not configured.")
        
    headers = {
        "Authorization": f"Bearer {hubspot_token}",
        "Content-Type": "application/json"
    }
    
    # Clean the input email parameter
    email = email.strip()
    
    # 1. Fetch contact by email with properties and associations
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{email}?idProperty=email&properties=firstname,country&associations=notes"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 404:
        return None
        
    response.raise_for_status()
    contact_data = response.json()
    
    properties = contact_data.get("properties", {})
    firstname = properties.get("firstname", "Unknown")
    country = properties.get("country", "Unknown")
    contact_id = contact_data.get("id")
    
    # 2. Extract and fetch associated notes if any
    timeline_events = []
    associations = contact_data.get("associations", {})
    notes_associations = associations.get("notes", {}).get("results", [])
    
    if notes_associations:
        for assoc in notes_associations[:5]:  # Fetch up to 5 recent notes
            note_id = assoc.get("id")
            note_url = f"https://api.hubapi.com/crm/v3/objects/notes/{note_id}?properties=hs_note_body,hs_timestamp"
            note_resp = requests.get(note_url, headers=headers)
            if note_resp.status_code == 200:
                note_data = note_resp.json()
                note_props = note_data.get("properties", {})
                body = note_props.get("hs_note_body", "")
                timestamp = note_props.get("hs_timestamp", "")
                
                # HTML strip/clean for note body to keep it readable
                clean_body = re.sub(r'<[^>]+>', '', body)
                timeline_events.append({
                    "type": "Communication/Note",
                    "timestamp": timestamp,
                    "content": clean_body
                })
                
    return {
        "firstname": firstname,
        "country": country,
        "id": contact_id,
        "timeline": timeline_events
    }

def evaluate_communication_fatigue(timeline, proposed_message: str, channel: str):
    """
    Evaluates communication timeline against proposed message and channel for spamming/fatigue risks.
    Supports either OpenAI API key (starts with sk-) or Google Gemini API key.
    """
    if not gemini_key:
        raise ValueError("API Key (GEMINI_API_KEY) is not configured in .env.")
        
    timeline_desc = ""
    if timeline and len(timeline) > 0:
        for idx, event in enumerate(timeline):
            timeline_desc += f"{idx+1}. [{event['timestamp']}] {event['type']}: {event['content']}\n"
    else:
        timeline_desc = "No recent communication history recorded."
        
    system_instruction = (
        "You are the HubSpot Air Traffic Controller, a centralized, automated system-wide communication gatekeeper "
        "designed to manage marketing volume, protect customer experience, and reduce costs.\n"
        "Your task is to evaluate an outgoing communication request against a contact's recent history to prevent "
        "user fatigue and high unsubscribe rates.\n\n"
        "You MUST output your final decision in a strict format containing:\n"
        "STATUS: <APPROVED, HOLD, or REROUTE>\n"
        "RATIONALE: <Your concise reasoning explaining why this action was taken, max 2 sentences. "
        "Include references to channel limits, fatigue, or communication frequency.>\n\n"
        "Rules:\n"
        "- APPROVED: If there is no communication in the last 24 hours, or the contact is highly engaged and communications are balanced.\n"
        "- HOLD: Pause the communication for 24 hours if the contact has received too many premium messages (like WhatsApp) "
        "recently (e.g., more than 1 in 24h, or 2 in 48h) or if the message is extremely aggressive/redundant.\n"
        "- REROUTE: Downgrade from a high-impact/expensive channel (like WhatsApp) to a low-impact channel (like Email) "
        "if they received a WhatsApp message recently but can still receive Email, or if we want to save costs while still delivering the message."
    )
    
    prompt = f"""
Evaluate the following outbound marketing campaign request:
Proposed Channel: {channel}
Proposed Message: "{proposed_message}"

Contact's Recent Communication Timeline:
{timeline_desc}

Based on the rules, provide your verdict.
"""
    
    # Check if the API key belongs to OpenAI (starts with 'sk-')
    if gemini_key.strip().startswith("sk-"):
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {gemini_key.strip()}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        res_data = response.json()
        text = res_data["choices"][0]["message"]["content"]
    else:
        # Standard Google Gemini SDK call
        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2
            )
        )
        text = response.text
    
    # Parse STATUS and RATIONALE from response
    status = "APPROVED ✅"
    rationale = text
    
    if "STATUS:" in text:
        try:
            parts = text.split("STATUS:", 1)[1].split("\n", 1)
            raw_status = parts[0].strip().upper()
            if "HOLD" in raw_status:
                status = "HOLD 🛑"
            elif "REROUTE" in raw_status:
                status = "REROUTE 🔀"
            else:
                status = "APPROVED ✅"
            
            if "RATIONALE:" in parts[1]:
                rationale = parts[1].split("RATIONALE:", 1)[1].strip()
            else:
                rationale = parts[1].strip()
        except Exception:
            pass
            
    return status, rationale

# --- Initialize Session State for Telemetry ---
if "logs" not in st.session_state:
    st.session_state.logs = [
        {
            "Timestamp": "2026-06-13 10:05:12",
            "Workflow Source": "LATAM Welcome Series",
            "Contact ID/Country": "jose.gomez@example.cl (Chile)",
            "Channel": "WhatsApp",
            "AI Action Status": "HOLD 🛑",
            "Reasoning Breakdown": "Sent 2 WhatsApp campaigns in last 48 hours. Postponed to prevent user fatigue and high opt-out risk."
        },
        {
            "Timestamp": "2026-06-13 10:06:01",
            "Workflow Source": "EU/CIS Flash Sale",
            "Contact ID/Country": "v.schmidt@example.de (Germany)",
            "Channel": "Email",
            "AI Action Status": "APPROVED ✅",
            "Reasoning Breakdown": "No marketing communication sent in last 7 days. Low fatigue risk."
        },
        {
            "Timestamp": "2026-06-13 10:06:45",
            "Workflow Source": "ASIA Promo Pulse",
            "Contact ID/Country": "tanaka@example.jp (Japan)",
            "Channel": "WhatsApp",
            "AI Action Status": "REROUTE 🔀",
            "Reasoning Breakdown": "Frequent touchpoints detected on premium channel. Downgraded to low-impact Email to preserve customer goodwill."
        },
        {
            "Timestamp": "2026-06-13 10:07:11",
            "Workflow Source": "AFRICA Retention Push",
            "Contact ID/Country": "b.kamau@example.ke (Kenya)",
            "Channel": "Email",
            "AI Action Status": "APPROVED ✅",
            "Reasoning Breakdown": "Contact has high engagement rates and last received an email 5 days ago."
        }
    ]

# --- Dynamic Calculation of Metrics ---
total_audited = len(st.session_state.logs)
held_count = sum(1 for log in st.session_state.logs if "HOLD" in log["AI Action Status"])
reroute_count = sum(1 for log in st.session_state.logs if "REROUTE" in log["AI Action Status"])

# Est. WhatsApp Costs Saved: $0.08 per avoided fatigue incident (HOLD or REROUTE from WhatsApp)
avoided_incidents = sum(
    1 for log in st.session_state.logs
    if ("HOLD" in log["AI Action Status"] or "REROUTE" in log["AI Action Status"]) and log["Channel"] == "WhatsApp"
)
costs_saved = avoided_incidents * 0.08

# Unsubscribes Prevented
unsubscribes_prevented = int(avoided_incidents * 0.5 + held_count * 0.25)

# System Throttle Rate
throttle_rate = ((held_count + reroute_count) / total_audited * 100) if total_audited > 0 else 0.0

# --- Executive Analytics Header (4 metric cards) ---
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #22c55e;">
         <div class="metric-label">Est. WhatsApp Costs Saved</div>
         <div class="metric-value">${costs_saved:.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with m_col2:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #3b82f6;">
         <div class="metric-label">Unsubscribes Prevented</div>
         <div class="metric-value">{unsubscribes_prevented}</div>
    </div>
    """, unsafe_allow_html=True)

with m_col3:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #eab308;">
         <div class="metric-label">Total Traffic Audited</div>
         <div class="metric-value">{total_audited}</div>
    </div>
    """, unsafe_allow_html=True)

with m_col4:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #ef4444;">
         <div class="metric-label">System Throttle Rate</div>
         <div class="metric-value">{throttle_rate:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Layout split for Live Logs (left) and Judge Sandbox (right)
left_panel, right_panel = st.columns([7, 3])

with left_panel:
    st.subheader("📡 Global Traffic Control Console")
    st.write("Live intercept logs showing active workflow traffic and automated LLM-enforced verdicts.")
    
    # Convert list of logs to a DataFrame to display
    df_logs = pd.DataFrame(st.session_state.logs)
    
    st.dataframe(
        df_logs,
        column_config={
            "Timestamp": st.column_config.TextColumn("Timestamp", width="medium"),
            "Workflow Source": st.column_config.TextColumn("Workflow Source", width="medium"),
            "Contact ID/Country": st.column_config.TextColumn("Contact ID/Country", width="large"),
            "Channel": st.column_config.TextColumn("Channel", width="small"),
            "AI Action Status": st.column_config.TextColumn("AI Action Status", width="small"),
            "Reasoning Breakdown": st.column_config.TextColumn("Reasoning Breakdown", width="max"),
        },
        use_container_width=True,
        hide_index=True
    )

with right_panel:
    st.subheader("⚖️ Judge's Interactive Sandbox")
    st.write("Simulate a marketing workflow trigger on a sandbox contact to test the judgment engine.")
    
    with st.form("sandbox_form", clear_on_submit=False):
        sandbox_email = st.text_input("Target Contact Email (Sandbox)", value="example_user@deriv.com")
        sandbox_channel = st.selectbox("Intended Channel", ["WhatsApp", "Email"])
        sandbox_workflow = st.selectbox(
            "Select Originating Workflow",
            ["LATAM Welcome Series", "EU/CIS Flash Sale", "ASIA Promo Pulse", "AFRICA Retention Push", "AdHoc Broadcast Campaign"]
        )
        sandbox_message = st.text_area(
            "Proposed Marketing Message",
            value="Urgent! Only 24 hours left to secure your 100% deposit bonus. Deposit now!",
            placeholder="Type your message content here..."
        )
        
        run_audit = st.form_submit_button("Run Traffic Audit", disabled=env_error)
        
    if run_audit:
        # Validate input parameters and state
        if env_error:
            st.error("Please configure the missing keys in your .env file before running an audit.")
        elif not sandbox_email:
            st.warning("Please specify a target contact email.")
        elif not validate_email(sandbox_email):
            st.error("Please enter a valid target email address (e.g., user@example.com) to prevent bad request parameters.")
        elif not sandbox_message.strip():
            st.warning("Please provide a marketing message to audit.")
        else:
            with st.spinner("Analyzing HubSpot interaction history and auditing payload with Gemini..."):
                try:
                    # 1. Fetch live contact from HubSpot Sandbox
                    contact_info = fetch_hubspot_contact_timeline(sandbox_email)
                    
                    if contact_info is None:
                        st.error(f"Contact '{sandbox_email}' not found in HubSpot Sandbox. "
                                 f"Please create the contact in your Sandbox or verify the email.")
                    else:
                        firstname = contact_info["firstname"]
                        country = contact_info["country"]
                        timeline = contact_info["timeline"]
                        
                        # 2. Evaluate using Gemini Judgment Engine
                        action, reason = evaluate_communication_fatigue(timeline, sandbox_message, sandbox_channel)
                        
                        # 3. Append results to session state log
                        new_log = {
                            "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Workflow Source": f"Sandbox: {sandbox_workflow}",
                            "Contact ID/Country": f"{sandbox_email} ({country})",
                            "Channel": sandbox_channel,
                            "AI Action Status": action,
                            "Reasoning Breakdown": f"👤 {firstname} — {reason}"
                        }
                        
                        st.session_state.logs.insert(0, new_log)
                        
                        # Success notifications
                        st.success(f"Audit completed: {action}")
                        
                        st.markdown("### Raw AI Controller & CRM Diagnostics")
                        st.code(f"""
[HubSpot CRM Fetch Output]
Contact Name: {firstname}
Country: {country}
ID: {contact_info['id']}
Timeline Events: {len(timeline)} notes retrieved.

[Gemini Input Prompt]
Evaluate the following outbound marketing campaign:
Channel: {sandbox_channel}
Workflow: {sandbox_workflow}
Proposed Text: "{sandbox_message}"

[Contact Timeline Context (HubSpot Sandbox Profile)]
{timeline if timeline else "No recent communications recorded."}

[Verdict Decision Block]
ACTION: {action}
REASONING: {reason}
                        """, language="json")
                        
                        # Rerun to update telemetry metrics instantly
                        st.rerun()
                except Exception as e:
                    st.error(f"System Error: {str(e)}")
