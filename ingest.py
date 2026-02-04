import os
import git
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer

# --- CONFIGURATION ---
load_dotenv()  # This loads ELASTIC_CLOUD_ID and ELASTIC_API_KEY from your .env file

CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")
API_KEY = os.getenv("ELASTIC_API_KEY")

# We use Flask as a test subject.
REPO_URL = "https://github.com/pallets/flask.git"
INDEX_NAME = "codebase-index"

# --- SETUP ---
print("Connecting to Elastic...")
client = Elasticsearch(
    cloud_id=CLOUD_ID,
    api_key=API_KEY
)

print("Loading AI Model (this takes a second)...")
# We use a small, fast model for this hackathon
model = SentenceTransformer('all-MiniLM-L6-v2')

# --- LOGIC ---
def clone_repo():
    if os.path.exists("./temp_repo"):
        print("Repo already exists locally. Skipping clone.")
        return
    print(f"Cloning {REPO_URL}...")
    git.Repo.clone_from(REPO_URL, "./temp_repo")

def generate_docs():
    valid_extensions = {'.py', '.js', '.ts', '.java', '.go'}
    
    for root, _, files in os.walk("./temp_repo"):
        if '.git' in root: continue
        
        for file in files:
            if os.path.splitext(file)[1] in valid_extensions:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Split huge files into 1000-char chunks so the AI doesn't choke
                    chunks = [content[i:i+1000] for i in range(0, len(content), 1000)]
                    
                    for i, chunk in enumerate(chunks):
                        vector = model.encode(chunk).tolist() # The Magic: Text -> Numbers
                        yield {
                            "_index": INDEX_NAME,
                            "_source": {
                                "file_path": file_path,
                                "content": chunk,
                                "chunk_index": i,
                                "repo_name": REPO_URL.split("/")[-1],
                                "text_vector": vector 
                            }
                        }
                except Exception as e:
                    pass

# --- EXECUTION ---
# 1. Create Index with Vector Mapping
if not client.indices.exists(index=INDEX_NAME):
    mapping = {
        "mappings": {
            "properties": {
                "content": {"type": "text"},
                "file_path": {"type": "keyword"},
                "text_vector": {
                    "type": "dense_vector",
                    "dims": 384, 
                    "index": True,
                    "similarity": "cosine" 
                }
            }
        }
    }
    client.indices.create(index=INDEX_NAME, body=mapping)
    print("Index created.")
else:
    print("Index already exists. Appending data...")

# 2. Run
clone_repo()
print("Ingesting code... (This might take a minute)")
helpers.bulk(client, generate_docs())
print("SUCCESS: Codebase is inside Elasticsearch.")