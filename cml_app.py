"""CML Application entry point — runs uvicorn as subprocess to avoid PBJ event loop conflict."""
import logging
import subprocess
import sys
import os
import time
import signal

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("sentinel.cml_app")

# Resolve project root (handles both app mode and workbench/Jupyter)
try:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
except NameError:
    PROJECT_ROOT = os.getcwd()

os.chdir(PROJECT_ROOT)
os.makedirs("data", exist_ok=True)

port = int(os.environ.get("CDSW_APP_PORT", "8081"))
logger.info(f"[Sentinel] Starting (port={port}, root={PROJECT_ROOT})")

# Always pull latest code from git
try:
    logger.info("[Sentinel] Pulling latest code from git...")
    subprocess.check_call(
        ["git", "pull", "origin", "main", "--ff-only"],
        cwd=PROJECT_ROOT, stdout=sys.stdout, stderr=sys.stderr
    )
    logger.info("[Sentinel] Code updated.")
except Exception as e:
    logger.info(f"[Sentinel] Git pull skipped: {e}")

# Clear __pycache__ to prevent stale bytecode
import shutil
for dirpath, dirs, _files in os.walk(PROJECT_ROOT):
    for d in dirs:
        if d == "__pycache__":
            p = os.path.join(dirpath, d)
            shutil.rmtree(p, ignore_errors=True)
            logger.info(f"[Sentinel] Cleared {p}")

try:
    # Always install deps (requirements.txt may have changed after git pull)
    logger.info("[Sentinel] Installing dependencies...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--quiet",
         "--no-warn-script-location", "-r", "requirements.txt"],
        stdout=sys.stdout, stderr=sys.stderr
    )
    logger.info("[Sentinel] Dependencies installed.")

    # Seed demo data if needed
    db_path = os.path.join(PROJECT_ROOT, "data", "sentinel.db")
    if not os.path.exists(db_path):
        logger.info("[Sentinel] Seeding demo data...")
        subprocess.run([sys.executable, "scripts/seed_demo_data.py"], check=False)

    # Run uvicorn as a subprocess to avoid asyncio.run() conflict with PBJ's event loop
    logger.info(f"[Sentinel] Launching uvicorn on 127.0.0.1:{port}")
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
    logger.info(f"[Sentinel] uvicorn exited with code {proc.returncode}")

except Exception as e:
    logger.error("FATAL: %s", e, exc_info=True)
    time.sleep(30)
