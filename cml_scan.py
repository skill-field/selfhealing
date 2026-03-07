"""CML Job wrapper — runs the AI repo scanner as a subprocess to avoid PBJ event loop conflict."""
import subprocess
import sys
import os

try:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
except NameError:
    PROJECT_ROOT = os.getcwd()

os.chdir(PROJECT_ROOT)

# Install deps if needed
try:
    import anthropic
    import httpx
except ImportError:
    print("[Sentinel] Installing dependencies...", flush=True)
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--quiet",
         "--no-warn-script-location", "-r", "requirements.txt"],
        stdout=sys.stdout, stderr=sys.stderr
    )

# Run scanner as subprocess to avoid asyncio.run() conflict with PBJ's Jupyter event loop
print("[Sentinel] Starting AI repo scanner...", flush=True)
result = subprocess.run(
    [sys.executable, "scripts/scan_repo.py"],
    cwd=PROJECT_ROOT,
    stdout=sys.stdout, stderr=sys.stderr
)
print(f"[Sentinel] Scanner exited with code {result.returncode}", flush=True)
