import streamlit as st
import datetime
import pandas as pd
import random

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
# We count any log that is HOLD or REROUTE and has channel 'WhatsApp'
avoided_incidents = sum(
    1 for log in st.session_state.logs
    if ("HOLD" in log["AI Action Status"] or "REROUTE" in log["AI Action Status"]) and log["Channel"] == "WhatsApp"
)
costs_saved = avoided_incidents * 0.08

# Unsubscribes Prevented (predictive model: say 1 unsubscribe prevented for every 2 avoided incidents, or scaled appropriately)
unsubscribes_prevented = int(avoided_incidents * 0.5 + held_count * 0.25)

# System Throttle Rate: (Held + Rerouted) / Total Audited
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

# Add a divider
st.markdown("---")

# Layout split for Live Logs (left) and Judge Sandbox (right)
left_panel, right_panel = st.columns([7, 3])

with left_panel:
    st.subheader("📡 Global Traffic Control Console")
    st.write("Live intercept logs showing active workflow traffic and automated LLM-enforced verdicts.")
    
    # Convert list of logs to a DataFrame to display
    df_logs = pd.DataFrame(st.session_state.logs)
    
    # Style and format the dataframe
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
        
        run_audit = st.form_submit_button("Run Traffic Audit")
        
    if run_audit:
        # Simple input verification
        if not sandbox_email:
            st.warning("Please specify a target contact email.")
        else:
            with st.spinner("Analyzing HubSpot interaction history and auditing payload with Gemini..."):
                # --- MOCK SIMULATION LOGIC ---
                # Under active development. To be wired with live APIs in subsequent phases.
                
                # Mock a judgment decision based on keywords
                lower_msg = sandbox_message.lower()
                is_aggressive = any(kw in lower_msg for kw in ["urgent", "deposit now", "100%", "immediate", "hurry"])
                
                if sandbox_channel == "WhatsApp" and is_aggressive:
                    action = "HOLD 🛑"
                    reason = "AGGRESSIVE FATIGUE RISK: Highly urgent commercial WhatsApp request sent too soon after the last customer touchpoint. Paused for 24 hours to prevent churn."
                elif sandbox_channel == "WhatsApp":
                    action = "REROUTE 🔀"
                    reason = "HIGH IMPACT MITIGATION: WhatsApp channel request downgraded to low-impact email to protect customer's Meta subscription health."
                else:
                    action = "APPROVED ✅"
                    reason = "SAFE SENTIMENT: Campaign message meets compliance thresholds. Contact engagement history is within safe limits for Email dispatch."
                
                # Append to st.session_state
                new_log = {
                    "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Workflow Source": f"Sandbox: {sandbox_workflow}",
                    "Contact ID/Country": f"{sandbox_email} (Sandbox)",
                    "Channel": sandbox_channel,
                    "AI Action Status": action,
                    "Reasoning Breakdown": reason
                }
                
                # Insert at the beginning of logs list for instant display at the top of the table/df
                st.session_state.logs.insert(0, new_log)
                
                # Success notification and raw outputs
                st.success(f"Audit completed: {action}")
                
                st.markdown("### Raw LLM Logic Output")
                st.code(f"""
[Gemini Input Prompt]
Evaluate the following outbound marketing campaign:
Channel: {sandbox_channel}
Workflow: {sandbox_workflow}
Proposed Text: "{sandbox_message}"

[Contact Timeline Context (Mocked Sandbox Profile)]
- Last contacted: 18 hours ago via Email
- Active Opt-in: Yes
- Fatigue Score: High

[Verdict Decision Block]
ACTION: {action.split()[0]}
REASONING: {reason}
                """, language="json")
                
                # Trigger a rerun so the main table updates immediately
                st.rerun()
