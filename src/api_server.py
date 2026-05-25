#!/usr/bin/env python3
"""
FastAPI server — serves the dashboard frontend and streams transaction data
to browser clients over WebSocket.

Usage:
    cd bank-platform/
    python src/api_server.py            # default port 8000
    python src/api_server.py --port 9000
"""

import asyncio
import json
import os
import time
import argparse
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from demo_streamer import stream_to_queue

# ---------------------------------------------------------------------------
# Connection manager
# ---------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self):
        self._clients: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._clients.append(ws)

    def disconnect(self, ws: WebSocket):
        self._clients.discard(ws) if hasattr(self._clients, "discard") else None
        if ws in self._clients:
            self._clients.remove(ws)

    async def broadcast(self, message: str):
        dead = []
        for ws in self._clients:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    @property
    def count(self):
        return len(self._clients)


manager = ConnectionManager()
stream_queue: asyncio.Queue = asyncio.Queue(maxsize=200)
stop_event: asyncio.Event = asyncio.Event()
latest_stats: dict = {}

# ---------------------------------------------------------------------------
# Background broadcast task
# ---------------------------------------------------------------------------

async def broadcast_loop():
    while not stop_event.is_set():
        try:
            payload = await asyncio.wait_for(stream_queue.get(), timeout=1.0)
            latest_stats.update(payload.get("stats", {}))
            if manager.count > 0:
                await manager.broadcast(json.dumps(payload))
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            print(f"[broadcast] error: {e}")

# ---------------------------------------------------------------------------
# App lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    streamer_task = asyncio.create_task(
        stream_to_queue(stream_queue, stop_event),
        name="streamer",
    )
    broadcast_task = asyncio.create_task(broadcast_loop(), name="broadcast")

    print("Stream started. Open http://localhost:8000 in your browser.")
    yield

    stop_event.set()
    streamer_task.cancel()
    broadcast_task.cancel()
    try:
        await streamer_task
        await broadcast_task
    except asyncio.CancelledError:
        pass

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Bank Platform — Live Demo", lifespan=lifespan)

FRONTEND_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "frontend")
)

# Serve static assets (js, css)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/api/stats")
async def stats():
    elapsed = time.time() - latest_stats.get("start_time", time.time())
    return {
        **latest_stats,
        "connected_clients": manager.count,
        "elapsed_seconds": round(elapsed, 1),
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    print(f"[ws] client connected  (total={manager.count})")
    try:
        # Send greeting with current stats so new clients aren't blank
        await ws.send_text(json.dumps({"type": "hello", "stats": latest_stats}))
        while True:
            # Keep the socket alive; data is pushed by broadcast_loop
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
        print(f"[ws] client disconnected (total={manager.count})")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    uvicorn.run("api_server:app", host=args.host, port=args.port, reload=False)
