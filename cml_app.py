"""CML Application entry point — installs deps and launches Sentinel."""

import subprocess
import sys
import os

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Install dependencies
print("[Sentinel] Installing Python dependencies...", flush=True)
subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "--quiet", "--no-warn-script-location", "-r", "requirements.txt"],
    stdout=sys.stdout, stderr=sys.stderr
)
print("[Sentinel] Dependencies installed.", flush=True)

# Seed demo data if DB doesn't exist
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sentinel.db")
if not os.path.exists(db_path):
    print("[Sentinel] Seeding demo data...", flush=True)
    subprocess.run([sys.executable, "scripts/seed_demo_data.py"], check=False)

# Start the app
port = int(os.environ.get("CDSW_APP_PORT", "8081"))
print(f"[Sentinel] Starting on 127.0.0.1:{port}...", flush=True)

# Import and run after deps are installed
import uvicorn

# CML PBJ runtimes require binding to 127.0.0.1 (not 0.0.0.0)
# PBJ's nginx proxy handles external traffic and forwards to localhost
uvicorn.run("app:app", host="127.0.0.1", port=port, log_level="info")
