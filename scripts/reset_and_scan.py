#!/usr/bin/env python3
"""Clear all demo data and run a fresh AI scan with only real results."""
from __future__ import annotations

import asyncio
import os
import sys

try:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    PROJECT_ROOT = os.getcwd()
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

import logging

logger = logging.getLogger("sentinel.reset")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

from database import get_db, init_db


async def reset():
    """Clear all data but keep schema."""
    await init_db()
    db = await get_db()
    try:
        logger.info("[Sentinel] Clearing all demo data...")
        await db.execute("DELETE FROM audit_log")
        await db.execute("DELETE FROM deployments")
        await db.execute("DELETE FROM fixes")
        await db.execute("DELETE FROM errors")
        await db.execute("DELETE FROM feature_requests")
        await db.commit()
        logger.info("[Sentinel] All tables cleared.")
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(reset())
    # Now run the real scanner
    logger.info("[Sentinel] Running AI scanner with real data...")
    import subprocess
    result = subprocess.run(
        [sys.executable, "scripts/scan_repo.py"],
        cwd=PROJECT_ROOT,
        stdout=sys.stdout, stderr=sys.stderr
    )
    logger.info(f"[Sentinel] Done (exit code {result.returncode})")
