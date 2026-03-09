"""CML Job — Train the error classifier model.

Trains scikit-learn models on historical error data and logs results
to MLflow (CML Experiments). Run as a CML Job on a schedule or manually.
"""
import os
import sys
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)

print("[Sentinel] Installing dependencies...", flush=True)
subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "--quiet",
     "--no-warn-script-location", "-r", "requirements.txt"],
    stdout=sys.stdout, stderr=sys.stderr
)

print("[Sentinel] Training ML classifier...", flush=True)
result = subprocess.run(
    [sys.executable, "-m", "ml.train"],
    cwd=PROJECT_ROOT,
    stdout=sys.stdout,
    stderr=sys.stderr,
)
sys.exit(result.returncode)
