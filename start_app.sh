#!/bin/bash
# CML Application startup script
# Installs dependencies and starts the FastAPI app

set -e

echo "[Sentinel] Installing Python dependencies..."
pip install -q -r requirements.txt

echo "[Sentinel] Building frontend if needed..."
if [ ! -f "static/index.html" ]; then
    cd frontend
    npm install
    npm run build
    cd ..
fi

echo "[Sentinel] Seeding demo data..."
python scripts/seed_demo_data.py 2>/dev/null || true

echo "[Sentinel] Starting Skillfield Sentinel on port ${CDSW_APP_PORT:-8081}..."
python app.py
