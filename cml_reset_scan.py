"""CML Job — clear demo data and run fresh AI scan. Subprocess wrapper for PBJ."""
import subprocess
import sys
import os

try:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
except NameError:
    PROJECT_ROOT = os.getcwd()

os.chdir(PROJECT_ROOT)

try:
    import anthropic
except ImportError:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--quiet",
         "--no-warn-script-location", "-r", "requirements.txt"],
        stdout=sys.stdout, stderr=sys.stderr
    )

print("[Sentinel] Resetting DB and running real AI scan...", flush=True)
subprocess.run(
    [sys.executable, "scripts/reset_and_scan.py"],
    cwd=PROJECT_ROOT, stdout=sys.stdout, stderr=sys.stderr
)
