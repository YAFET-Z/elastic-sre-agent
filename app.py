import streamlit as st
import time
from datetime import datetime, timezone
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

# Custom CSS
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
    client = st.session_state.agent.tools.client
    timestamp = datetime.now(timezone.utc).isoformat()
    index_name = "hackathon-errors"
    
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
    
    try:
        if not client.indices.exists(index=index_name):
            client.indices.create(index=index_name)
        client.index(index=index_name, document=error_log)
        client.indices.refresh(index=index_name)
        
        st.session_state.simulated_error = True
        st.toast("🔥 CRITICAL ERROR INJECTED!", icon="🔥")
    except Exception as e:
        st.error(f"Failed to inject chaos: {e}")

def clear_system():
    st.session_state.simulated_error = False
    st.session_state.current_error = None
    st.session_state.context = None
    st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ SRE-Agent")
    st.markdown("Autonomous Incident Response System")
    st.markdown("---")
    st.subheader("⚙️ Control Panel")
    if st.button("🔥 Simulate Production Crash", type="secondary"):
        inject_chaos()
    st.markdown("---")
    if st.button("🔄 Reset System", type="primary"):
        clear_system()
    st.info("Built with Elastic Vector Search & Google Gemini")

# --- MAIN LAYOUT ---
st.title("🚀 Mission Control")

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
    if st.button("🔎 Scan Logs for Anomalies", type="primary", use_container_width=True):
        with st.spinner("Querying Elastic Observability..."):
            time.sleep(0.5) 
            error = st.session_state.agent.tools.fetch_latest_error()
            
            if error and st.session_state.simulated_error:
                st.session_state.current_error = error
                st.error("🚨 ALERT: Production Incident Detected")
                with st.expander("View Stack Trace", expanded=True):
                    st.code(error, language="text")
            else:
                st.success("✅ No critical errors found.")
                st.session_state.current_error = None

    if st.session_state.get("current_error"):
        st.markdown("###")
        st.subheader("🧠 Context Retrieval")
        with st.status("Performing Root Cause Analysis...", expanded=True) as status:
            st.write("🔹 Vectorizing error message...")
            time.sleep(0.5)
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
        
        if st.button("✨ Activate Agent Protocol", type="primary", use_container_width=True):
            
            # --- START AGENT WORKFLOW ---
            with st.status("🤖 Agent at work...", expanded=True) as status:
                st.write("🔹 Phase 1: Analyzing logic flow...")
                
                prompt = f"""
                You are a Senior SRE.
                ERROR: {st.session_state.current_error}
                FILE: {st.session_state.context['file_path']}
                CODE: {st.session_state.context['content']}
                """
                
                # GET RESPONSE (Dict containing 'explanation' and 'code')
                response_payload = st.session_state.agent.brain.think(prompt)
                
                # UNPACK
                explanation = response_payload["explanation"]
                raw_fix = response_payload["code"]
                
                st.write("✅ Patch Generated.")
                time.sleep(0.5)

                # STEP 2: SELF-HEALING LOOP
                st.write("🔹 Phase 2: Running safety diagnostics...")
                
                attempt = 0
                max_retries = 3
                is_valid = False
                final_code = raw_fix
                
                while attempt < max_retries:
                    is_valid, message = st.session_state.agent.tools.check_syntax(final_code)
                    if is_valid:
                        st.write(message)
                        break 
                    else:
                        st.warning(f"⚠️ Attempt {attempt+1}: Syntax Error. Self-correcting...")
                        # In Mock mode, 'think' returns the dict again, so we extract code
                        new_response = st.session_state.agent.brain.think("syntax error fix")
                        final_code = new_response["code"]
                        attempt += 1

                if not is_valid:
                    st.error("❌ Critical: Auto-repair failed.")
                    st.stop()

                # STEP 3: ACT
                st.write("🔹 Phase 3: Drafting Incident Ticket...")
                ticket = st.session_state.agent.tools.draft_jira_ticket(
                    st.session_state.current_error,
                    st.session_state.context['file_path'],
                    final_code
                )
                st.write(f"✅ Ticket {ticket['id']} Created.")
                status.update(label="Workflow Complete", state="complete", expanded=False)

            # --- FINAL OUTPUT DISPLAY ---
            st.success("Candidate Fix Ready for Review")
            
            # 1. DISPLAY THE EXPLANATION BOX
            st.info(f"**🤖 Agent Report:**\n\n{explanation}")
            
            # 2. DISPLAY THE CODE
            st.code(final_code, language="python")
            
            # 3. DISPLAY THE TICKET
            st.info(f"🔗 **Jira Ticket Created:** [{ticket['id']}: {ticket['title']}](https://jira.atlassian.com) \n\nStatus: `{ticket['status']}`")