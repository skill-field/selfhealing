"""CML Job wrapper — Auto-Heal Pipeline (subprocess to avoid PBJ event loop conflict)."""
import subprocess, sys, os
try:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
except NameError:
    PROJECT_ROOT = os.getcwd()
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

try:
    import fastapi
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "--no-warn-script-location", "-r", "requirements.txt"])

subprocess.run([sys.executable, "scripts/auto_heal.py"], check=True)
