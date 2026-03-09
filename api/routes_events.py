"""SSE events route — real-time event streaming."""

import asyncio
import json
import logging
import weakref
from datetime import datetime, timezone
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger("sentinel.sse")

router = APIRouter(tags=["Events"])

# Use a set for O(1) add/remove and prevent unbounded growth
_client_queues: set[asyncio.Queue] = set()


async def broadcast_event(event_type: str, data: dict) -> None:
    """Push an event to all connected SSE clients."""
    payload = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    disconnected = []
    for queue in _client_queues:
        try:
            queue.put_nowait(payload)
        except asyncio.QueueFull:
            disconnected.append(queue)

    # Clean up any full/dead queues
    for q in disconnected:
        _client_queues.discard(q)
        logger.debug("Removed full SSE client queue (total: %d)", len(_client_queues))


async def _event_generator(queue: asyncio.Queue):
    """Generate SSE events from a client-specific queue, with heartbeats."""
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15.0)
                event_type = event.get("type", "message")
                yield {
                    "event": event_type,
                    "data": json.dumps(event),
                }
            except asyncio.TimeoutError:
                heartbeat = {
                    "type": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                yield {
                    "event": "heartbeat",
                    "data": json.dumps(heartbeat),
                }
    except (asyncio.CancelledError, GeneratorExit):
        pass
    finally:
        _client_queues.discard(queue)
        logger.debug("SSE client disconnected (remaining: %d)", len(_client_queues))


@router.get("/events/stream")
async def event_stream():
    """SSE endpoint for real-time event streaming."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _client_queues.add(queue)
    logger.debug("SSE client connected (total: %d)", len(_client_queues))
    return EventSourceResponse(_event_generator(queue))
