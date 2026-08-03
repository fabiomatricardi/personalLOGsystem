"""
Personal Log Manager - FastAPI Application Entry Point
"""
import sys
import os

if getattr(sys, 'frozen', False):
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from backend.database import init_db
from backend.routers import entries, tags, analysis, import_export, settings

server_shutdown = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
    if os.path.isdir(frontend_dist):
        import webbrowser
        webbrowser.open("http://localhost:8000")
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
    import os
    os._exit(0)
    return {"status": "shutting down"}


frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
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
        return HTMLResponse(content="<h1>Personal Log Manager</h1><p>Frontend not built. Run: npm run build in frontend/</p>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
