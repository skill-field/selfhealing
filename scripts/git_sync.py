"""Pull latest code from git and reset stale database."""
import subprocess
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)

print("[Git Sync] Pulling latest code...", flush=True)
subprocess.run(["git", "fetch", "origin", "main"], check=True)
subprocess.run(["git", "reset", "--hard", "origin/main"], check=True)
print("[Git Sync] Code synced.", flush=True)

# Delete stale DB so it re-seeds with correct model preferences
db_path = os.path.join(PROJECT_ROOT, "data", "sentinel.db")
for f in [db_path, db_path + "-shm", db_path + "-wal"]:
    if os.path.exists(f):
        os.remove(f)
        print(f"[Git Sync] Deleted {f}", flush=True)

print("[Git Sync] Done. Restart the app to apply changes.", flush=True)
