import os
import requests
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

# Load Environment Variables
load_dotenv()

class GeminiBrain:
    """
    Direct HTTP wrapper for Gemini (Generation).
    """
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model_url = f"{self.base_url}/models/gemini-2.5-flash:generateContent?key={self.api_key}"

    def think(self, prompt):
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            response = requests.post(self.model_url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                # Fallback to older model if 2.5 fails
                fallback_url = f"{self.base_url}/models/gemini-1.5-flash:generateContent?key={self.api_key}"
                response = requests.post(fallback_url, headers=headers, json=data)
                if response.status_code == 200:
                     return response.json()['candidates'][0]['content']['parts'][0]['text']
                return f"ERROR: {response.text}"
        except Exception as e:
            return f"CONNECTION ERROR: {e}"

class ElasticTools:
    """
    The 'Hands' of the Agent. Now uses Google API for Embeddings (Lightweight).
    """
    def __init__(self, cloud_id, api_key, gemini_key):
        print("🛠️ [Tools] Connecting to Elastic Cloud...")
        self.client = Elasticsearch(cloud_id=cloud_id, api_key=api_key)
        self.gemini_key = gemini_key
        self.embed_url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={self.gemini_key}"

    def _get_embedding(self, text):
        """Generates vector using Google API instead of local RAM"""
        headers = {'Content-Type': 'application/json'}
        data = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]}
        }
        try:
            response = requests.post(self.embed_url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()['embedding']['values']
            else:
                print(f"❌ Embedding Error: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            return None

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
        """Tool 2: Searches the code using Cloud Vectors"""
        vector = self._get_embedding(query)
        if not vector: return None
        
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
    def __init__(self):
        self.brain = GeminiBrain(os.getenv("GEMINI_API_KEY"))
        # Pass Gemini Key to tools for embedding
        self.tools = ElasticTools(
            os.getenv("ELASTIC_CLOUD_ID"), 
            os.getenv("ELASTIC_API_KEY"),
            os.getenv("GEMINI_API_KEY")
        )

    def run(self):
        # ... (Keep existing run logic if running locally, but Streamlit uses individual methods)
        pass