from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

# --- CONFIGURATION ---
load_dotenv()

CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")
API_KEY = os.getenv("ELASTIC_API_KEY")

client = Elasticsearch(cloud_id=CLOUD_ID, api_key=API_KEY)

# We are faking a crash in the Flask app
log_entry = {
    "@timestamp": datetime.now(timezone.utc).isoformat(),
    "service.name": "flask-backend",
    "log.level": "ERROR",
    "message": "TemplateNotFound: index.html",
    "error.stack_trace": """
Traceback (most recent call last):
  File "/src/flask/templating.py", line 85, in _get_source_fast
    raise TemplateNotFound(template)
jinja2.exceptions.TemplateNotFound: index.html
    """
}

# Ingest the log into a data stream or index
client.index(index="logs-app-default", document=log_entry)
print("ERROR INJECTED: The system is now 'broken'. Agent has a target.")