"""CML Application entry point — installs deps and launches Sentinel."""

import subprocess
import sys
import os

# Install dependencies
print("[Sentinel] Installing Python dependencies...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"])

# Seed demo data if DB doesn't exist
db_path = os.path.join(os.path.dirname(__file__), "data", "sentinel.db")
if not os.path.exists(db_path):
    print("[Sentinel] Seeding demo data...")
    subprocess.run([sys.executable, "scripts/seed_demo_data.py"], check=False)

# Start the app
print(f"[Sentinel] Starting on port {os.environ.get('CDSW_APP_PORT', '8081')}...")

# Import and run after deps are installed
import uvicorn
from app import app
from config import settings

uvicorn.run(app, host="127.0.0.1", port=settings.CDSW_APP_PORT)
