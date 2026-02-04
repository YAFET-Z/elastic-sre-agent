import os
import json
import requests
import time
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

# Load Environment Variables
load_dotenv()

class GeminiBrain:
    """
    A robust wrapper for the Gemini API using direct HTTP requests.
    This bypasses library version issues and supports 'Auto-Discovery'.
    """
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model_url = self._discover_model()

    def _discover_model(self):
        print("🧠 [Brain] Initializing... Detecting available models...")
        try:
            response = requests.get(f"{self.base_url}/models?key={self.api_key}")
            if response.status_code != 200: raise Exception(f"API Error: {response.text}")
            
            # Smart Selection Logic
            models = response.json().get('models', [])
            for m in models:
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    if 'flash' in m['name'] and '2.5' in m['name']: return self._build_url(m['name']) # Priority 1: Flash 2.5
            for m in models:
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    if 'flash' in m['name']: return self._build_url(m['name']) # Priority 2: Flash 1.5
            
            # Fallback
            return self._build_url("models/gemini-1.5-flash")
        except Exception as e:
            print(f"⚠️ [Brain] Auto-detect failed ({e}). Defaulting to Flash.")
            return self._build_url("models/gemini-1.5-flash")

    def _build_url(self, model_name):
        print(f"✅ [Brain] Connected to: {model_name}")
        return f"{self.base_url}/{model_name}:generateContent?key={self.api_key}"

    def think(self, prompt):
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            response = requests.post(self.model_url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                return f"ERROR: {response.text}"
        except Exception as e:
            return f"CONNECTION ERROR: {e}"

class ElasticTools:
    """
    The 'Hands' of the Agent. Handles all interactions with the database.
    """
    def __init__(self, cloud_id, api_key):
        print("🛠️ [Tools] Connecting to Elastic Cloud...")
        self.client = Elasticsearch(cloud_id=cloud_id, api_key=api_key)
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

    def fetch_latest_error(self):
        """Tool 1: Reads the logs"""
        response = self.client.search(
            index="logs-app-default",
            sort=[{"@timestamp": "desc"}],
            size=1,
            query={ "match": { "log.level": "ERROR" } }
        )
        if len(response['hits']['hits']) == 0: return None
        log = response['hits']['hits'][0]['_source']
        return f"{log['message']}\n{log.get('error.stack_trace', '')}"

    def search_codebase(self, query):
        """Tool 2: Searches the code"""
        vector = self.embedder.encode(query).tolist()
        response = self.client.search(
            index="codebase-index",
            size=1,
            knn={
                "field": "text_vector",
                "query_vector": vector,
                "k": 5,
                "num_candidates": 100
            }
        )
        if len(response['hits']['hits']) > 0:
            return response['hits']['hits'][0]['_source']
        return None

class IncidentResponseAgent:
    """
    The Orchestrator. Manages the workflow between Brain and Tools.
    """
    def __init__(self):
        self.brain = GeminiBrain(os.getenv("GEMINI_API_KEY"))
        self.tools = ElasticTools(os.getenv("ELASTIC_CLOUD_ID"), os.getenv("ELASTIC_API_KEY"))

    def run(self):
        print("\n🚀 AGENT STARTED: Monitoring System Health...\n" + "="*50)
        
        # Step 1: Check Logs
        error = self.tools.fetch_latest_error()
        if not error:
            print("✅ System Healthy. No active incidents.")
            return

        print(f"🚨 ALERT DETECTED: {error.splitlines()[0]}")
        
        # Step 2: Retrieve Context
        print("🔍 retrieving relevant code from Elastic...")
        code_context = self.tools.search_codebase(error)
        
        if not code_context:
            print("❌ Could not find relevant source code.")
            return

        print(f"📂 Context Found: {code_context['file_path']}")

        # Step 3: Reason & Fix
        print("🤔 Analyzing root cause and generating patch...")
        prompt = f"""
        You are a Site Reliability Engineer (SRE) Agent.
        
        INCIDENT REPORT:
        - Error Message: {error}
        - Suspected File: {code_context['file_path']}
        
        SOURCE CODE:
        {code_context['content']}
        
        YOUR MISSION:
        1. Explain why this error occurred (Root Cause).
        2. Rewrite the code to fix the bug.
        3. Explain your fix.
        """
        
        solution = self.brain.think(prompt)
        
        print("\n" + "="*50)
        print("🤖 AGENT REPORT")
        print("="*50)
        print(solution)

if __name__ == "__main__":
    agent = IncidentResponseAgent()
    agent.run()