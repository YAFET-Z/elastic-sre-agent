# 🛡️ SRE-Agent: Autonomous Incident Response
**An AI Agent that detects, diagnoses, and patches production crashes using Elasticsearch & Gemini.**



## 🚀 Project Overview
SRE-Agent is a multi-step AI agent built for the **Elasticsearch Agent Builder Hackathon 2026**. It automates "messy internal work" by bridging the gap between observability logs and code remediation.

### The Problem
When a production service crashes, engineers waste critical time manually searching through logs, locating the relevant code, and drafting tickets. This high Mean Time to Recovery (MTTR) impacts business reliability.

### The Solution
SRE-Agent uses a **multi-step workflow** to resolve incidents:
1.  **Observability:** Monitors Elasticsearch for `ERROR` level logs in real-time.
2.  **Context Retrieval:** Uses **Vector Search** on a `codebase-index` to find the exact file and logic responsible for the crash.
3.  **Reasoning:** Leverages **Gemini 2.0 Flash** to analyze the root cause and generate a fix.
4.  **Verification:** Uses a **Syntax Check tool** to verify code integrity before suggesting a patch.
5.  **Action:** Drafts a mock Jira Ticket to integrate into existing workflows.

## 🛠️ Features & Tools
* **Elasticsearch Agent Builder:** Connects the LLM to private codebase data.
* **Vector Search:** Performs semantic search on code chunks stored in Elastic Cloud.
* **Self-Healing Loop:** Automatically retries code generation if a syntax error is detected.
* **Local Embeddings:** Uses `all-MiniLM-L6-v2` locally for high-performance, cost-effective vectorization.

## 📦 Installation & Setup
1. **Clone the Repo:**
   `git clone https://github.com/YAFET-Z/sre-agent.git`
2. **Install Dependencies:**
   `pip install -r requirements.txt`
3. **Environment Variables:**
   Create a `.env` file with `ELASTIC_CLOUD_ID`, `ELASTIC_API_KEY`, and `GEMINI_API_KEY`.
4. **Ingest Codebase:**
   `python ingest.py`
5. **Run the Agent:**
   `streamlit run app.py`

## 🌟 Challenges & Future Work
* **Challenge:** Handling large codebases required efficient chunking and local embedding strategies to stay within API limits.
* **Future:** Implementing **Elastic Workflows** to automate the actual deployment of the patch to a staging environment.
