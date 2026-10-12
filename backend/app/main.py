import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import api_v1_router
from app.models.entities import Deployment, Document, Chunk, Conversation, Message, UsageLog

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database schema is created
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Ensure storage folder exists
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CiteBot: Enterprise Factual Document Assistant with Deterministic Inline Citations",
    lifespan=lifespan
)

# CORS middleware for widget integration and SPA frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows any origin for embeddable widget
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Router
app.include_router(api_v1_router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }

# Static file & SPA serving
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
backend_static = Path(__file__).resolve().parent.parent / "static"
static_dir = frontend_dist if frontend_dist.exists() else (backend_static if backend_static.exists() else None)

if static_dir and static_dir.exists():
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    widget_file = static_dir / "widget.js"
    if widget_file.exists():
        @app.get("/widget.js")
        async def serve_widget():
            return FileResponse(str(widget_file), media_type="application/javascript")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path == "health":
            return None
        file_path = static_dir / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
