import os

# Define the folder
base_folder = "temp_repo"
os.makedirs(base_folder, exist_ok=True)

# 1. Create the broken file (routes.py)
# This matches the "TemplateNotFound" error in our logs
routes_code = """
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    # ERROR: This template does not exist!
    return render_template("index.html")

@app.route('/health')
def health():
    return "OK"
"""

# 2. Create a main entry point (app.py)
app_code = """
from routes import app

if __name__ == "__main__":
    app.run(debug=True)
"""

# Write files to disk
with open(f"{base_folder}/routes.py", "w") as f:
    f.write(routes_code)
    
with open(f"{base_folder}/app.py", "w") as f:
    f.write(app_code)

print(f"✅ Created broken app files in '{base_folder}/'.")
print("👉 Now run 'python ingest.py' to load them into the database.")