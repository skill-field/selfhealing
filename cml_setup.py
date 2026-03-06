"""CML setup job — install deps and seed data. Run BEFORE starting the application."""
import subprocess
import sys
import os

# Resolve project root (handles both app mode and Jupyter workbench)
try:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
except NameError:
    PROJECT_ROOT = os.getcwd()

os.chdir(PROJECT_ROOT)
os.makedirs("data", exist_ok=True)

print(f"[Sentinel] Setup starting in {PROJECT_ROOT}", flush=True)
print(f"[Sentinel] Python: {sys.version}", flush=True)

# Show current cml_app.py to verify git sync
print("[Sentinel] === cml_app.py content ===", flush=True)
try:
    with open("cml_app.py") as f:
        print(f.read(), flush=True)
except Exception as e:
    print(f"Cannot read cml_app.py: {e}", flush=True)
print("[Sentinel] === end cml_app.py ===", flush=True)

print("[Sentinel] Installing Python dependencies...", flush=True)
subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "--quiet",
     "--no-warn-script-location", "-r", "requirements.txt"],
    stdout=sys.stdout, stderr=sys.stderr
)
print("[Sentinel] Dependencies installed.", flush=True)

db_path = os.path.join(PROJECT_ROOT, "data", "sentinel.db")
if not os.path.exists(db_path):
    print("[Sentinel] Seeding demo data...", flush=True)
    subprocess.run([sys.executable, "scripts/seed_demo_data.py"], check=False)
    print("[Sentinel] Seed done.", flush=True)
else:
    print(f"[Sentinel] DB already exists at {db_path}", flush=True)

print("[Sentinel] Setup complete.", flush=True)
