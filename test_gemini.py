import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={key}"

data = {
    "model": "models/text-embedding-004",
    "content": {"parts": [{"text": "Hello world"}]}
}

print(f"Testing Key: {key[:5]}... (Hidden)")
response = requests.post(url, json=data)

if response.status_code == 200:
    print("✅ SUCCESS! API Key is working.")
else:
    print(f"❌ ERROR: {response.status_code}")
    print(response.text)