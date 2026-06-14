import streamlit as st
import datetime
import pandas as pd
import requests
import os
import re
import threading
import json
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
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

# --- Helper to fetch LiteLLM models ---
@st.cache_data(ttl=300)
def fetch_available_models(base_url: str, api_key: str):
    """Fetches available models from the LiteLLM/OpenAI-compatible models endpoint."""
    try:
        url = f"{base_url.rstrip('/')}/models"
        headers = {
            "Authorization": f"Bearer {api_key.strip()}"
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Extract IDs from v1/models format {"data": [{"id": "...", ...}]}
            models = [item["id"] for item in data.get("data", []) if "id" in item]
            return sorted(models)
    except Exception:
        pass
    return []

# --- Environment Configuration Check ---
hubspot_token = os.getenv("HUBSPOT_API_TOKEN")
gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
api_base_url = os.getenv("API_BASE_URL") or os.getenv("OPENAI_API_BASE")
openai_model_name = os.getenv("OPENAI_MODEL_NAME") or "gpt-4o-mini"

env_error = False
if not hubspot_token or "your_hubspot" in hubspot_token:
    st.sidebar.error("❌ HUBSPOT_API_TOKEN is missing or not configured in .env")
    env_error = True

if not gemini_key or "your_gemini" in gemini_key or "your_openai" in gemini_key:
    st.sidebar.error("❌ API key (GEMINI_API_KEY or OPENAI_API_KEY) is missing or not configured in .env")
    env_error = True
else:
    # If using LiteLLM/OpenAI Compatible API
    if api_base_url:
        st.sidebar.success(f"🌐 Connected to LiteLLM/OpenAI compatible Endpoint")
        st.sidebar.info(f"🔗 URL: {api_base_url}")
        
        # Attempt to dynamically fetch model list
        available_models = fetch_available_models(api_base_url, gemini_key)
        if available_models:
            # If default model is in list, pre-select it
            default_idx = 0
            if openai_model_name in available_models:
                default_idx = available_models.index(openai_model_name)
            
            openai_model_name = st.sidebar.selectbox(
                "🤖 Active Model ID",
                options=available_models,
                index=default_idx,
                help="Fetched in real-time from your LiteLLM Model Explorer"
            )
        else:
            st.sidebar.info(f"🤖 Model: {openai_model_name}")
            st.sidebar.warning("⚠️ Could not fetch model list. Using manual model ID.")
            
    elif gemini_key.strip().startswith("sk-"):
        st.sidebar.success("🔑 Using OpenAI API Key")
        st.sidebar.info(f"🤖 Model: {openai_model_name}")
    else:
        st.sidebar.success("🔑 Using Google Gemini API Key")
        st.sidebar.info(f"🤖 Model: gemini-2.5-flash")

# --- Shared Resources and Background Server ---

@st.cache_resource
def get_shared_logs():
    """Persistent thread-safe shared list of webhook logs."""
    return []

@st.cache_resource
def get_shared_logs_lock():
    """Persistent threading lock for shared logs access."""
    return threading.Lock()

def trigger_streamlit_rerun():
    """Triggers a rerun on all active Streamlit sessions to update UI."""
    try:
        from streamlit.runtime import get_instance
        runtime = get_instance()
        if runtime:
            for session_info in runtime._session_info_by_id.values():
                session_info.session.request_rerun()
    except Exception:
        pass

class WebhookHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress logging to console for cleaner stdout/stderr
        pass

    def do_POST(self):
        if self.path not in ['/', '/webhook']:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Path not found"}).encode('utf-8'))
            return

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            payload = json.loads(post_data.decode('utf-8'))
        except Exception:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Malformed JSON payload"}).encode('utf-8'))
            return

        email = payload.get('email', '').strip()
        firstname = payload.get('firstname', '').strip()
        country = payload.get('country', '').strip()
        workflow_source = payload.get('workflow_source', '').strip()
        proposed_message = payload.get('proposed_message', '').strip()
        channel = payload.get('channel', '').strip()

        if not email:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing 'email' in request body"}).encode('utf-8'))
            return

        if not validate_email(email):
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid email format"}).encode('utf-8'))
            return

        try:
            # 1. Fetch live contact from HubSpot Sandbox
            contact_info = fetch_hubspot_contact_timeline(email)
            if contact_info is not None:
                fetched_firstname = contact_info.get("firstname") or firstname or "Unknown"
                fetched_country = contact_info.get("country") or country or "Unknown"
                timeline = contact_info.get("timeline") or []
            else:
                fetched_firstname = firstname or "Unknown"
                fetched_country = country or "Unknown"
                timeline = []

            # 2. Evaluate using Gemini Judgment Engine
            action, reason = evaluate_communication_fatigue(timeline, proposed_message, channel)

            # 3. Create log entry
            new_log = {
                "id": str(uuid.uuid4()),
                "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Workflow Source": f"Webhook: {workflow_source}" if workflow_source else "Webhook Trigger",
                "Contact ID/Country": f"{email} ({fetched_country})",
                "Channel": channel or "Email",
                "AI Action Status": action,
                "Reasoning Breakdown": f"👤 {fetched_firstname} — {reason}"
            }

            # Prepend/append to shared cache
            shared_logs = get_shared_logs()
            lock = get_shared_logs_lock()
            with lock:
                shared_logs.append(new_log)

            # Request Streamlit rerun for immediate UI update
            trigger_streamlit_rerun()

            # Respond with 200 OK
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": action,
                "rationale": reason,
                "contact": {
                    "firstname": fetched_firstname,
                    "country": fetched_country
                }
            }).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Internal judgment server error: {str(e)}"}).encode('utf-8'))

def run_http_server(port):
    server = HTTPServer(('0.0.0.0', port), WebhookHandler)
    server.serve_forever()

@st.cache_resource
def start_background_server(port=8000):
    """Spawns the background HTTP webhook receiver thread exactly once."""
    t = threading.Thread(target=run_http_server, args=(port,), daemon=True)
    t.start()
    return t

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
    Supports either OpenAI API key, custom LiteLLM base URL, or Google Gemini API key.
    """
    if not gemini_key:
        raise ValueError("API Key (GEMINI_API_KEY or OPENAI_API_KEY) is not configured in .env.")
        
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
    
    try:
        # Check if we should use OpenAI / LiteLLM proxy compatibility
        if gemini_key.strip().startswith("sk-") or api_base_url:
            base_url = (api_base_url or "https://api.openai.com/v1").rstrip("/")
            url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {gemini_key.strip()}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": openai_model_name,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 401:
                raise ValueError(
                    f"Unauthorized (401). Please check that your API Key is valid and authorized for the endpoint: {base_url}."
                )
            elif response.status_code == 404:
                raise ValueError(
                    f"Not Found (404). Please verify that the Endpoint Base URL '{base_url}' is correct "
                    f"and that the model '{openai_model_name}' is supported on your provider."
                )
                
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
            
    except requests.exceptions.RequestException as re_err:
        status_code = re_err.response.status_code if re_err.response is not None else "Connection Error"
        resp_text = re_err.response.text if re_err.response is not None else str(re_err)
        
        # Format a beautifully descriptive error
        if status_code == 401:
            raise ValueError(
                f"Unauthorized (401) from LLM Provider. Please ensure your LiteLLM API key is valid "
                f"and that your billing/limits are sufficient."
            )
        elif status_code == 404:
            raise ValueError(
                f"Endpoint/Model Not Found (404) from LLM Provider. Please verify your API_BASE_URL "
                f"({api_base_url}) and check if the model name '{openai_model_name}' is supported."
            )
        else:
            raise RuntimeError(f"HTTP {status_code} Error: {resp_text}")
    except Exception as e:
        raise RuntimeError(f"AI Judgment Engine Error: {str(e)}")
    
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

# --- Synchronize Shared Background Webhook Logs with Streamlit Session State ---
shared_logs = get_shared_logs()
lock = get_shared_logs_lock()
with lock:
    existing_ids = {log.get("id") for log in st.session_state.logs if "id" in log}
    new_items = [log for log in shared_logs if log.get("id") not in existing_ids]
    if new_items:
        for item in new_items:
            st.session_state.logs.insert(0, item)

# --- Start Background API Webhook Server on Port 8000 ---
start_background_server(port=8000)

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
