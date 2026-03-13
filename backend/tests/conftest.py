import os
import pytest
import pytest_asyncio
from sqlalchemy import text, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.database import get_db, async_session as app_async_session
from app.models.user import User
from app.models.box import StorageBox
from app.models.item import BoxItem, Item
from app.models.audit import AuditLog
from app.config import settings
from app.main import app


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    """
    Create a new database session for each test.
    Uses the app's existing database session maker.
    Cleans up test data after each test.
    """
    async with app_async_session() as session:
        # Override the app's get_db dependency to use our test session
        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        yield session

        # Clean up test data - delete in reverse dependency order
        await session.execute(delete(AuditLog))
        await session.execute(delete(BoxItem))
        await session.execute(delete(StorageBox))
        await session.execute(delete(Item))
        await session.execute(delete(User).where(User.email.like('%@example.com')))
        await session.execute(delete(User).where(User.google_id.like('test-%')))
        await session.execute(delete(User).where(User.email == 'dev@localhost'))
        await session.commit()

        # Clean up
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        google_id="test-google-id-1",
        email="test1@example.com",
        name="Test User 1",
        picture_url="https://example.com/pic1.jpg",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user_2(db_session: AsyncSession) -> User:
    """Create a second test user for isolation tests."""
    user = User(
        google_id="test-google-id-2",
        email="test2@example.com",
        name="Test User 2",
        picture_url="https://example.com/pic2.jpg",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_box(db_session: AsyncSession, test_user: User) -> StorageBox:
    """Create a test storage box."""
    box = StorageBox(
        box_code="BOX-0001",
        name="Test Box",
        location_name="Test Location",
        owner_id=test_user.id,
        created_by=test_user.id,
        updated_by=test_user.id,
    )
    db_session.add(box)
    await db_session.commit()
    await db_session.refresh(box)
    return box


@pytest_asyncio.fixture
async def test_box_user_2(db_session: AsyncSession, test_user_2: User) -> StorageBox:
    """Create a test storage box for user 2."""
    box = StorageBox(
        box_code="BOX-0002",
        name="Test Box User 2",
        location_name="Test Location 2",
        owner_id=test_user_2.id,
        created_by=test_user_2.id,
        updated_by=test_user_2.id,
    )
    db_session.add(box)
    await db_session.commit()
    await db_session.refresh(box)
    return box
