"""SSE events route — real-time event streaming."""

import asyncio
import json
from datetime import datetime, timezone
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

router = APIRouter(tags=["Events"])

# List of asyncio.Queue instances, one per connected SSE client
_client_queues: list[asyncio.Queue] = []


async def broadcast_event(event_type: str, data: dict) -> None:
    """Push an event to all connected SSE clients.

    Args:
        event_type: Event name (e.g., 'error_detected', 'classification_done').
        data: Event payload dict.
    """
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
        if q in _client_queues:
            _client_queues.remove(q)


async def _event_generator(queue: asyncio.Queue):
    """Generate SSE events from a client-specific queue, with heartbeats."""
    try:
        while True:
            try:
                # Wait for an event with a timeout (for heartbeat)
                event = await asyncio.wait_for(queue.get(), timeout=15.0)
                event_type = event.get("type", "message")
                yield {
                    "event": event_type,
                    "data": json.dumps(event),
                }
            except asyncio.TimeoutError:
                # Send heartbeat
                heartbeat = {
                    "type": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                yield {
                    "event": "heartbeat",
                    "data": json.dumps(heartbeat),
                }
    finally:
        # Remove queue when client disconnects
        if queue in _client_queues:
            _client_queues.remove(queue)


@router.get("/events/stream")
async def event_stream():
    """SSE endpoint for real-time event streaming."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _client_queues.append(queue)
    return EventSourceResponse(_event_generator(queue))
