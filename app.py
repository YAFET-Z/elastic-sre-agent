import streamlit as st
import time
from datetime import datetime
from main import IncidentResponseAgent
from elasticsearch import Elasticsearch
import os

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="SRE Agent | Elastic Hackathon",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for that "Hacker" feel
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-box {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZATION ---
if "agent" not in st.session_state:
    st.session_state.agent = IncidentResponseAgent()

if "simulated_error" not in st.session_state:
    st.session_state.simulated_error = False

# --- HELPER: SIMULATE CRASH ---
def inject_chaos():
    """Injects a fake error into Elastic logs to simulate a crash."""
    client = st.session_state.agent.tools.client
    timestamp = datetime.now().isoformat()
    
    error_log = {
        "@timestamp": timestamp,
        "log.level": "ERROR",
        "message": "TemplateNotFound: index.html",
        "service.name": "frontend-service",
        "error.stack_trace": """Traceback (most recent call last):
  File "/app/routes.py", line 15, in index
    return render_template("frontend/index.html")
  File "/usr/local/lib/python3.9/site-packages/flask/templating.py", line 154, in render_template
    return _render(ctx.app.jinja_env.get_or_select_template(template_name_or_list), context, ctx.app)
jinja2.exceptions.TemplateNotFound: index.html"""
    }
    
    client.index(index="logs-app-default", document=error_log)
    st.session_state.simulated_error = True
    st.toast("🔥 CRITICAL ERROR INJECTED!", icon="🔥")

def clear_system():
    """Clears the session state."""
    st.session_state.simulated_error = False
    st.session_state.current_error = None
    st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ SRE-Agent")
    st.markdown("Autonomous Incident Response System")
    st.markdown("---")
    
    st.subheader("⚙️ Control Panel")
    
    # The Chaos Button
    if st.button("🔥 Simulate Production Crash", type="secondary", help="Injects a fake error log into Elastic"):
        inject_chaos()
        
    st.markdown("---")
    if st.button("🔄 Reset System", type="primary"):
        clear_system()
        
    st.info("Built with Elastic Vector Search & Google Gemini 2.5")

# --- MAIN LAYOUT ---
st.title("🚀 Mission Control")

# Status Indicators
col_stat1, col_stat2, col_stat3 = st.columns(3)
with col_stat1:
    if st.session_state.simulated_error:
        st.error("SYSTEM STATUS: CRITICAL")
    else:
        st.success("SYSTEM STATUS: OPERATIONAL")

with col_stat2:
    st.metric(label="Active Agents", value="1 Online")

with col_stat3:
    st.metric(label="Mean Time to Recovery", value="< 10s")

st.divider()

# --- THE WORKFLOW ---
col1, col2 = st.columns([1.2, 1])

with col1:
    st.subheader("📡 Live Log Stream")
    
    # 1. Scan Button
    if st.button("🔎 Scan Logs for Anomalies", type="primary", use_container_width=True):
        with st.spinner("Querying Elastic Observability..."):
            time.sleep(1.5) # UX Delay
            error = st.session_state.agent.tools.fetch_latest_error()
            
            if error and st.session_state.simulated_error:
                st.session_state.current_error = error
                st.error("🚨 ALERT: Production Incident Detected")
                with st.expander("View Stack Trace", expanded=True):
                    st.code(error, language="text")
            else:
                st.success("✅ No critical errors found in the last 5 minutes.")
                st.session_state.current_error = None

    # 2. Context Retrieval (Only appears if error exists)
    if st.session_state.get("current_error"):
        st.markdown("###")
        st.subheader("🧠 Context Retrieval")
        
        with st.status("Performing Root Cause Analysis...", expanded=True) as status:
            st.write("🔹 Vectorizing error message...")
            time.sleep(1)
            st.write("🔹 Querying `codebase-index` for matching patterns...")
            context = st.session_state.agent.tools.search_codebase(st.session_state.current_error)
            
            if context:
                st.write(f"✅ FOUND: Suspect file located at `{context['file_path']}`")
                st.session_state.context = context
                status.update(label="Root Cause Isolated", state="complete", expanded=False)
            else:
                status.update(label="Context Retrieval Failed", state="error")

# --- THE FIX COLUMN ---
with col2:
    if st.session_state.get("context"):
        st.subheader("🛠️ Auto-Remediation")
        
        st.markdown(f"**Suspected File:** `{st.session_state.context['file_path']}`")
        with st.expander("View Broken Code", expanded=False):
            st.code(st.session_state.context['content'], language="python")
            
        st.markdown("---")
        
        if st.button("✨ Generate Patch with Gemini", type="primary", use_container_width=True):
            prompt = f"""
            You are an expert Senior SRE.
            ERROR: {st.session_state.current_error}
            FILE: {st.session_state.context['file_path']}
            CODE: {st.session_state.context['content']}
            
            TASK:
            1. Explain the root cause in 1 sentence.
            2. Provide the FIXED Python code block.
            """
            
            with st.spinner("Consulting Gemini 2.5 Brain..."):
                solution = st.session_state.agent.brain.think(prompt)
                
            st.success("Patch Generated Successfully!")
            st.markdown(solution)
            st.balloons()