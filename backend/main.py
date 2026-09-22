"""
SentinelNet AI - FastAPI Application Server
Entrypoint serving REST APIs, WebSockets, and the SOC Frontend Dashboard.
"""

import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.api.routes import router as api_router
from backend.websocket.manager import ws_manager
from backend.services.monitor_service import monitor_service
from database.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sentinelnet.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Initializing SentinelNet AI Backend...")
    # Initialize Database
    try:
        init_db()
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

    # Set asyncio event loop for background WebSocket dispatch
    loop = asyncio.get_running_loop()
    monitor_service.set_event_loop(loop)

    # Periodic background task to stream stats every 1 second
    async def _periodic_stats_stream():
        while True:
            await asyncio.sleep(1.0)
            if ws_manager.active_connections:
                stats = monitor_service.get_statistics()
                await ws_manager.broadcast_json({
                    "type": "STATS_UPDATE",
                    "data": stats
                })

    stats_task = asyncio.create_task(_periodic_stats_stream())
    logger.info("SentinelNet AI system services initialized successfully.")

    yield

    # Shutdown
    logger.info("Shutting down SentinelNet AI Backend...")
    stats_task.cancel()
    monitor_service.stop_monitoring()


app = FastAPI(
    title="SentinelNet AI",
    description="Real-Time AI Network Intrusion Detection & Monitoring System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)


# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Live WebSocket stream for real-time detection events and telemetry."""
    await ws_manager.connect(websocket)
    try:
        # Send immediate initial state
        await websocket.send_json({
            "type": "INITIAL_STATE",
            "data": {
                "status": monitor_service.get_status(),
                "statistics": monitor_service.get_statistics(),
                "recent_detections": monitor_service.get_recent_detections(limit=25),
            }
        })
        while True:
            # Keep connection alive and receive any client messages/pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket error: {e}")
        await ws_manager.disconnect(websocket)


# Mount Frontend Static Directory
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
