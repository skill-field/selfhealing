"""CML Job — Pull latest code from git and install dependencies."""
import subprocess
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)

print("[Sentinel] Pulling latest code from git...", flush=True)
subprocess.run(["git", "pull", "origin", "main"], cwd=PROJECT_ROOT,
               stdout=sys.stdout, stderr=sys.stderr)

print("[Sentinel] Installing dependencies...", flush=True)
subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "--quiet",
     "--no-warn-script-location", "-r", "requirements.txt"],
    stdout=sys.stdout, stderr=sys.stderr
)
print("[Sentinel] Done.", flush=True)
