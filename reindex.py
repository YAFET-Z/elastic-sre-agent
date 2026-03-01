import os
import requests
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()

# 1. Connect to Elastic
CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")
API_KEY = os.getenv("ELASTIC_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not CLOUD_ID or not API_KEY:
    print("❌ Error: Missing .env variables for Elastic!")
    exit()

client = Elasticsearch(cloud_id=CLOUD_ID, api_key=API_KEY)
INDEX_NAME = "codebase-index"

# 2. Delete the old index
print(f"🗑️  Deleting old index '{INDEX_NAME}'...")
client.indices.delete(index=INDEX_NAME, ignore=[400, 404])

# 3. Create the new index (768 dimensions for text-embedding-004)
print("🆕 Creating new index...")
client.indices.create(index=INDEX_NAME, mappings={
    "properties": {
        "file_path": {"type": "keyword"},
        "content": {"type": "text"},
        "text_vector": {"type": "dense_vector", "dims": 768} 
    }
})

# 4. Helper to get Google Embeddings
def get_google_embedding(text):
    # Use text-embedding-004
    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GEMINI_KEY}"
    
    data = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": text[:9000]}]},
        "taskType": "RETRIEVAL_DOCUMENT"  # <--- CRITICAL FIX: Tells Google this is data to be stored
    } 
    
    try:
        res = requests.post(url, json=data)
        if res.status_code == 200:
            return res.json()['embedding']['values']
        else:
            # If 004 fails, try the older 'embedding-001' as a last resort fallback
            print(f"⚠️ 004 Error: {res.text}. Trying fallback...")
            return None
    except Exception as e:
        print(f"⚠️ Connection Error: {e}")
        return None

# 5. Re-Ingest the Code
print("🚀 Starting Re-indexing...")
repo_path = "./temp_repo" 

count = 0
for root, _, files in os.walk(repo_path):
    for file in files:
        if file.endswith(".py") or file.endswith(".html"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                print(f"   Processing: {file}...")
                vector = get_google_embedding(content)
                
                if vector:
                    doc = {
                        "file_path": path,
                        "content": content,
                        "text_vector": vector
                    }
                    client.index(index=INDEX_NAME, document=doc)
                    count += 1
            except Exception as e:
                print(f"   Skipping {file}: {e}")

print(f"\n✅ Success! Re-indexed {count} files.")