#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/../frontend"
echo "[build] Installing frontend dependencies..."
npm install --silent
echo "[build] Building frontend..."
npm run build
echo "[build] Frontend built to ../static/"
