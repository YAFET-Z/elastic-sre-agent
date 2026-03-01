import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

print(f"🔎 Checking available models for key: {api_key[:5]}...")

try:
    response = requests.get(url)
    if response.status_code == 200:
        models = response.json().get('models', [])
        print("\n✅ AVAILABLE MODELS:")
        found_embedding = False
        for m in models:
            if "embed" in m['name']:
                print(f"   - {m['name']}")
                found_embedding = True
        
        if not found_embedding:
            print("\n❌ CRITICAL: No embedding models found. Enable 'Generative Language API' in Google Cloud Console.")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Connection Failed: {e}")