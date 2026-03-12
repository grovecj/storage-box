from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine, Base
from app.routers import boxes, items, transfers, search, tags, reports, audit, config


@asynccontextmanager
async def lifespan(app: FastAPI):
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

app.include_router(boxes.router, prefix="/api/v1")
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
