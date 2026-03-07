"""CML Application entry point — runs uvicorn as subprocess to avoid PBJ event loop conflict."""
import subprocess
import sys
import os
import time
import signal

# Resolve project root (handles both app mode and workbench/Jupyter)
try:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
except NameError:
    PROJECT_ROOT = os.getcwd()

os.chdir(PROJECT_ROOT)
os.makedirs("data", exist_ok=True)

port = int(os.environ.get("CDSW_APP_PORT", "8081"))
print(f"[Sentinel] Starting (port={port}, root={PROJECT_ROOT})", flush=True)

# Always pull latest code from git
try:
    print("[Sentinel] Pulling latest code from git...", flush=True)
    subprocess.check_call(
        ["git", "pull", "origin", "main", "--ff-only"],
        cwd=PROJECT_ROOT, stdout=sys.stdout, stderr=sys.stderr
    )
    print("[Sentinel] Code updated.", flush=True)
except Exception as e:
    print(f"[Sentinel] Git pull skipped: {e}", flush=True)

try:
    # Always install deps (requirements.txt may have changed after git pull)
    print("[Sentinel] Installing dependencies...", flush=True)
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--quiet",
         "--no-warn-script-location", "-r", "requirements.txt"],
        stdout=sys.stdout, stderr=sys.stderr
    )
    print("[Sentinel] Dependencies installed.", flush=True)

    # Seed demo data if needed
    db_path = os.path.join(PROJECT_ROOT, "data", "sentinel.db")
    if not os.path.exists(db_path):
        print("[Sentinel] Seeding demo data...", flush=True)
        subprocess.run([sys.executable, "scripts/seed_demo_data.py"], check=False)

    # Run uvicorn as a subprocess to avoid asyncio.run() conflict with PBJ's event loop
    print(f"[Sentinel] Launching uvicorn on 127.0.0.1:{port}", flush=True)
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app",
         "--host", "127.0.0.1", "--port", str(port), "--log-level", "info"],
        cwd=PROJECT_ROOT,
        stdout=sys.stdout, stderr=sys.stderr
    )

    # Forward signals to child process
    def handle_signal(signum, frame):
        proc.send_signal(signum)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    # Wait for uvicorn to exit
    proc.wait()
    print(f"[Sentinel] uvicorn exited with code {proc.returncode}", flush=True)

except Exception as e:
    print(f"[Sentinel] FATAL: {e}", flush=True)
    import traceback
    print(traceback.format_exc(), flush=True)
    time.sleep(30)
