import os
from dotenv import load_dotenv

load_dotenv()

cloud_id = os.getenv("ELASTIC_CLOUD_ID")
api_key = os.getenv("ELASTIC_API_KEY")

print(f"--- DEBUGGING .ENV ---")
print(f"Cloud ID found: {cloud_id}")

if cloud_id:
    print(f"Length: {len(cloud_id)}")
    if ":" in cloud_id:
        print("✅ Format looks correct (contains ':')")
    else:
        print("❌ Format INVALID (missing ':'). This causes the ValueError.")
else:
    print("❌ Cloud ID is None. The .env file is not being read.")

print(f"API Key found: {'Yes' if api_key else 'No'}")