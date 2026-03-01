import os
import time
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer

# --- CONFIGURATION ---
load_dotenv()

CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")
API_KEY = os.getenv("ELASTIC_API_KEY")

INDEX_NAME = "codebase-index"
# Local model 'all-MiniLM-L6-v2' outputs 384 dimensions
EMBEDDING_DIMS = 384 

print("Connecting to Elastic...")
client = Elasticsearch(
    cloud_id=CLOUD_ID,
    api_key=API_KEY
)

print("⏳ Loading Local AI Model (This runs offline)...")
# This downloads a small 80MB model to your computer
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text):
    # Runs locally on your CPU
    return model.encode(text).tolist()

def generate_docs():
    base_path = "./temp_repo"
    valid_extensions = {'.py', '.js', '.ts', '.java', '.go'}
    
    if not os.path.exists(base_path):
        print(f"❌ Error: {base_path} does not exist. Run setup_demo.py first!")
        return

    for root, _, files in os.walk(base_path):
        if '.git' in root: continue
        
        for file in files:
            if os.path.splitext(file)[1] in valid_extensions:
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Split large files
                chunks = [content[i:i+1000] for i in range(0, len(content), 1000)]
                
                for i, chunk in enumerate(chunks):
                    print(f"🔹 Embedding {file} (chunk {i})...")
                    vector = get_embedding(chunk)
                    yield {
                        "_index": INDEX_NAME,
                        "_source": {
                            "file_path": file_path,
                            "content": chunk,
                            "chunk_index": i,
                            "text_vector": vector 
                        }
                    }

# --- EXECUTION ---
if client.indices.exists(index=INDEX_NAME):
    print("🗑️ Deleting old index...")
    client.indices.delete(index=INDEX_NAME)

mapping = {
    "mappings": {
        "properties": {
            "content": {"type": "text"},
            "file_path": {"type": "keyword"},
            "text_vector": {
                "type": "dense_vector",
                "dims": EMBEDDING_DIMS, 
                "index": True,
                "similarity": "cosine" 
            }
        }
    }
}
client.indices.create(index=INDEX_NAME, body=mapping)
print("✅ Index created (384 dims).")

print("🚀 Ingesting code...")
helpers.bulk(client, generate_docs())
print("✅ SUCCESS: Codebase is inside Elasticsearch.")