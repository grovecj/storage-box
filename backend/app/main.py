import logging
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import settings
from app.database import Base, async_session, engine
from app.routers import audit, auth, boxes, config, groups, items, reports, search, tags, transfers

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Log connection target (not password) for debugging
    parsed = urlparse(settings.database_url)
    logger.info(
        f"DB connect: host={parsed.hostname} port={parsed.port}"
        f" db={parsed.path} user={parsed.username} env={settings.app_env}"
    )

    # Create extensions and tables on startup
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.run_sync(Base.metadata.create_all)

        # Seed default tags
        await conn.execute(text("""
            INSERT INTO tags (name) VALUES ('PCB'), ('VACATION'), ('LONG_TERM')
            ON CONFLICT (name) DO NOTHING
        """))

        # Create and sync box_code_seq so new codes never reuse old ones
        await conn.execute(text("CREATE SEQUENCE IF NOT EXISTS box_code_seq START 1"))
        await conn.execute(text("""
            SELECT setval('box_code_seq',
                GREATEST(
                    (SELECT COALESCE(MAX(CAST(SUBSTR(box_code, 5) AS INTEGER)), 0)
                     FROM storage_boxes),
                    (SELECT last_value FROM box_code_seq)
                )
            )
        """))

    # Seed sample data in development only
    if settings.app_env == "development":
        from app.seed import seed_if_empty
        async with async_session() as db:
            await seed_if_empty(db)

    yield

    await engine.dispose()


app = FastAPI(
    title="Storage Box API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [settings.app_base_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(boxes.router, prefix="/api/v1")
app.include_router(groups.router, prefix="/api/v1")
app.include_router(items.router, prefix="/api/v1")
app.include_router(transfers.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(tags.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(config.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}


# Serve frontend static files in production
static_dir = Path(__file__).parent.parent / "static"
if static_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="static-assets")

    @app.get("/{path:path}")
    async def serve_spa(request: Request, path: str):
        # Serve actual files if they exist, otherwise fall back to index.html (SPA routing)
        file_path = static_dir / path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(static_dir / "index.html"))
