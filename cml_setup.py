"""CML setup job — install deps and seed data. Run BEFORE starting the application."""
import logging
import subprocess
import sys
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("sentinel.setup")

# Resolve project root (handles both app mode and Jupyter workbench)
try:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
except NameError:
    PROJECT_ROOT = os.getcwd()

os.chdir(PROJECT_ROOT)
os.makedirs("data", exist_ok=True)

logger.info(f"[Sentinel] Setup starting in {PROJECT_ROOT}")
logger.info(f"[Sentinel] Python: {sys.version}")

# Show current cml_app.py to verify git sync
logger.info("[Sentinel] === cml_app.py content ===")
try:
    with open("cml_app.py") as f:
        logger.info(f.read())
except Exception as e:
    logger.info(f"Cannot read cml_app.py: {e}")
logger.info("[Sentinel] === end cml_app.py ===")

logger.info("[Sentinel] Installing Python dependencies...")
subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "--quiet",
     "--no-warn-script-location", "-r", "requirements.txt"],
    stdout=sys.stdout, stderr=sys.stderr
)
logger.info("[Sentinel] Dependencies installed.")

db_path = os.path.join(PROJECT_ROOT, "data", "sentinel.db")
if not os.path.exists(db_path):
    logger.info("[Sentinel] Seeding demo data...")
    subprocess.run([sys.executable, "scripts/seed_demo_data.py"], check=False)
    logger.info("[Sentinel] Seed done.")
else:
    logger.info(f"[Sentinel] DB already exists at {db_path}")

logger.info("[Sentinel] Setup complete.")
