"""CML Application entry point — robust startup with error handling."""
import subprocess
import sys
import os
import time
import traceback

# Resolve project root (handles both app mode and workbench/Jupyter)
try:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
except NameError:
    PROJECT_ROOT = os.getcwd()

os.chdir(PROJECT_ROOT)
os.makedirs("data", exist_ok=True)

port = int(os.environ.get("CDSW_APP_PORT", "8081"))
print(f"[Sentinel] Starting (port={port}, root={PROJECT_ROOT})", flush=True)

try:
    # Fast dep check — only install if missing
    try:
        import fastapi
        import uvicorn
        print("[Sentinel] Dependencies already installed.", flush=True)
    except ImportError:
        print("[Sentinel] Installing dependencies...", flush=True)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet",
             "--no-warn-script-location", "-r", "requirements.txt"],
            stdout=sys.stdout, stderr=sys.stderr
        )
        import uvicorn
        print("[Sentinel] Dependencies installed.", flush=True)

    # Seed demo data if needed
    db_path = os.path.join(PROJECT_ROOT, "data", "sentinel.db")
    if not os.path.exists(db_path):
        print("[Sentinel] Seeding demo data...", flush=True)
        subprocess.run([sys.executable, "scripts/seed_demo_data.py"], check=False)

    # Start the app — bind to 127.0.0.1 per Cloudera AMP convention
    print(f"[Sentinel] Launching uvicorn on 127.0.0.1:{port}", flush=True)
    uvicorn.run("app:app", host="127.0.0.1", port=port, log_level="info")

except Exception as e:
    print(f"[Sentinel] FATAL: {e}", flush=True)
    print(traceback.format_exc(), flush=True)
    # Keep process alive so CML logs are visible
    time.sleep(30)
