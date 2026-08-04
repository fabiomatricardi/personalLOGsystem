"""
Personal Log Manager - FastAPI Application Entry Point
"""
import sys
import os
import logging
import threading
import time
import socket

# Determine base directory for the app
if getattr(sys, 'frozen', False):
    APP_BASE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = sys._MEIPASS
else:
    APP_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BUNDLE_DIR = APP_BASE_DIR

# Ensure data directory exists next to the executable (or project root)
DATA_DIR = os.path.join(APP_BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Set up logging to a file next to the executable
LOG_FILE = os.path.join(APP_BASE_DIR, "personallog.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ]
)
logger = logging.getLogger("personallog")

logger.info(f"Starting Personal Log Manager")
logger.info(f"APP_BASE_DIR: {APP_BASE_DIR}")
logger.info(f"BUNDLE_DIR: {BUNDLE_DIR}")
logger.info(f"DATA_DIR: {DATA_DIR}")
logger.info(f"Frozen: {getattr(sys, 'frozen', False)}")

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from backend.database import init_db
from backend.routers import entries, tags, analysis, import_export, settings

server_shutdown = False

PORT_FALLBACKS = [8001, 8002, 8003, 5000, 3000, 18080, 28080]


def find_available_port(preferred: int) -> int:
    """Try preferred port, then fallback to alternatives."""
    for port in [preferred] + PORT_FALLBACKS:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return preferred


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized")

    # Find frontend dist - check bundle dir first, then project root
    frontend_dist = os.path.join(BUNDLE_DIR, "frontend", "dist")
    if not os.path.isdir(frontend_dist):
        frontend_dist = os.path.join(APP_BASE_DIR, "frontend", "dist")
    if not os.path.isdir(frontend_dist):
        frontend_dist = os.path.join(APP_BASE_DIR, "frontend", "dist")

    logger.info(f"Frontend dist: {frontend_dist} (exists: {os.path.isdir(frontend_dist)})")

    if os.path.isdir(frontend_dist):
        import webbrowser
        port = getattr(app.state, 'port', 8000)
        logger.info("Opening browser...")
        webbrowser.open(f"http://localhost:{port}")
    else:
        logger.warning("Frontend dist not found!")

    yield


app = FastAPI(
    title="Personal Log Manager",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(entries.router)
app.include_router(tags.router)
app.include_router(analysis.router)
app.include_router(import_export.router)
app.include_router(settings.router)


@app.post("/api/shutdown")
async def shutdown():
    global server_shutdown
    server_shutdown = True
    threading.Thread(target=lambda: (time.sleep(1) or os._exit(0)), daemon=True).start()
    return {"status": "shutting down"}


# Find frontend dist for SPA serving
frontend_dist = os.path.join(BUNDLE_DIR, "frontend", "dist")
if not os.path.isdir(frontend_dist):
    frontend_dist = os.path.join(APP_BASE_DIR, "frontend", "dist")

logger.info(f"SPA frontend_dist: {frontend_dist}")

if os.path.isdir(frontend_dist):
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return HTMLResponse(content="<h1>Personal Log Manager</h1><p>Frontend not built. Run: npm run build</p>")
else:
    @app.get("/")
    async def root():
        return HTMLResponse(content="<h1>Personal Log Manager</h1><p>Frontend not found. Path: " + frontend_dist + "</p>")


if __name__ == "__main__":
    import uvicorn

    # When frozen with --noconsole, stdout/stderr are None.
    # Uvicorn's logging tries sys.stdout.isatty() which crashes.
    # Fix: redirect stdout/stderr to the log file before uvicorn starts.
    if getattr(sys, 'frozen', False) and sys.stdout is None:
        log_stream = open(LOG_FILE, "a", encoding="utf-8")
        sys.stdout = log_stream
        sys.stderr = log_stream

    from backend.services.config import load_config
    config = load_config()
    preferred_port = config.get("app", {}).get("port", 8000)
    port = find_available_port(preferred_port)

    if port != preferred_port:
        logger.warning(f"Port {preferred_port} unavailable, using port {port}")

    app.state.port = port
    logger.info(f"Starting uvicorn server on port {port}...")
    uvicorn.run(app, host="127.0.0.1", port=port)
