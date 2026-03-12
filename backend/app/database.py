import ssl as ssl_module

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

connect_args = {}
if settings.app_env == "production":
    # DigitalOcean managed DB requires SSL with certificate verification.
    # If db_ca_cert_path is empty, the system default CA bundle is used.
    ssl_ctx = ssl_module.create_default_context()
    if settings.db_ca_cert_path:
        try:
            ssl_ctx.load_verify_locations(settings.db_ca_cert_path)
        except FileNotFoundError:
            raise RuntimeError(
                f"Database CA certificate not found at {settings.db_ca_cert_path}. "
                "Verify DB_CA_CERT_PATH is set correctly."
            )
        except ssl_module.SSLError as e:
            raise RuntimeError(
                f"Invalid database CA certificate at {settings.db_ca_cert_path}: {e}"
            )
    connect_args["ssl"] = ssl_ctx

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    pool_size=2,
    max_overflow=1,  # Total max connections: 3
    pool_pre_ping=True,
    connect_args=connect_args,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
