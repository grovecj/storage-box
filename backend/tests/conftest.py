"""Shared test configuration and fixtures."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.models.user import User
from app.models.box import StorageBox
from app.models.item import Item, BoxItem
from app.models.tag import Tag


@pytest.fixture
def mock_db():
    """Create a mock AsyncSession for database operations."""
    db = AsyncMock()
    # db.add() is synchronous in SQLAlchemy, so use MagicMock to avoid
    # "coroutine never awaited" warnings from AsyncMock.
    db.add = MagicMock()
    return db


@pytest.fixture
def mock_user():
    """Create a mock User instance."""
    user = MagicMock(spec=User)
    user.id = 1
    user.google_id = "google-test-123"
    user.email = "test@example.com"
    user.name = "Test User"
    user.picture_url = None
    user.created_at = datetime(2024, 1, 1)
    user.updated_at = datetime(2024, 1, 1)
    return user


@pytest.fixture
def mock_box():
    """Create a mock StorageBox instance."""
    from app.models.box import StorageBox
    box = StorageBox(
        id=1,
        box_code="BOX-0001",
        name="Test Box",
        location=None,
        location_name="Test Location",
        owner_id=1,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
        created_by=1,
        updated_by=1,
    )
    # Since we're not persisting to DB, manually set the id
    box.id = 1
    return box


@pytest.fixture
def mock_item():
    """Create a mock Item instance."""
    item = MagicMock(spec=Item)
    item.id = 1
    item.name = "Test Item"
    item.created_at = datetime(2024, 1, 1)
    item.updated_at = datetime(2024, 1, 1)
    item.created_by = 1
    item.updated_by = 1
    return item


@pytest.fixture
def mock_box_item(mock_item):
    """Create a mock BoxItem instance."""
    box_item = MagicMock(spec=BoxItem)
    box_item.id = 1
    box_item.box_id = 1
    box_item.item_id = 1
    box_item.quantity = 5
    box_item.item = mock_item
    box_item.tags = []
    box_item.created_at = datetime(2024, 1, 1)
    box_item.updated_at = datetime(2024, 1, 1)
    box_item.created_by = 1
    box_item.updated_by = 1
    return box_item


@pytest.fixture
def mock_tag():
    """Create a mock Tag instance."""
    tag = MagicMock(spec=Tag)
    tag.id = 1
    tag.name = "test-tag"
    tag.created_at = datetime(2024, 1, 1)
    tag.updated_at = datetime(2024, 1, 1)
    tag.created_by = 1
    tag.updated_by = 1
    return tag
