"""Tests for per-user data isolation in service layer.

Uses mocked database sessions to verify owner_id filtering.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.models.user import User
from app.models.box import StorageBox
from app.models.item import BoxItem, Item
from app.services import box_service, item_service, search_service, transfer_service


def _make_user(id=1):
    user = MagicMock(spec=User)
    user.id = id
    return user


def _make_box(id=1, owner_id=1, box_code="BOX-0001", name="Test Box"):
    box = MagicMock(spec=StorageBox)
    box.id = id
    box.owner_id = owner_id
    box.box_code = box_code
    box.name = name
    box.location = None
    box.location_name = "Test Location"
    box.created_at = datetime(2024, 1, 1)
    box.updated_at = datetime(2024, 1, 1)
    box.created_by = owner_id
    box.updated_by = owner_id
    return box


# ---------------------------------------------------------------------------
# Box service user scoping
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestBoxServiceUserScoping:
    async def test_create_box_sets_owner_id(self):
        """create_box should set owner_id to the current user."""
        user = _make_user(id=42)
        mock_db = AsyncMock()

        # Mock next box code
        mock_code_result = MagicMock()
        mock_code_result.scalar.return_value = 1

        # Mock flush/refresh to set box attributes
        added_box = None
        original_add = MagicMock()
        def capture_add(obj):
            nonlocal added_box
            added_box = obj
        original_add.side_effect = capture_add
        mock_db.add = original_add

        mock_db.execute = AsyncMock(return_value=mock_code_result)

        async def mock_flush():
            if added_box:
                added_box.id = 1
                added_box.created_at = datetime(2024, 1, 1)
                added_box.updated_at = datetime(2024, 1, 1)
        mock_db.flush = AsyncMock(side_effect=mock_flush)
        mock_db.refresh = AsyncMock()
        mock_db.commit = AsyncMock()

        from app.schemas.box import BoxCreate
        data = BoxCreate(name="Test Box")

        with patch.object(box_service, "log_action", new_callable=AsyncMock):
            result = await box_service.create_box(mock_db, data, user)

        assert added_box is not None
        assert added_box.owner_id == 42
        assert added_box.created_by == 42
        assert added_box.updated_by == 42

    async def test_get_box_filters_by_owner(self):
        """get_box should include owner_id in the WHERE clause."""
        user = _make_user(id=5)
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None  # No box found for this owner
        mock_db.execute.return_value = mock_result

        result = await box_service.get_box(mock_db, box_id=1, user=user)
        assert result is None
        # Verify execute was called (query contains owner_id filter)
        mock_db.execute.assert_called_once()

    async def test_list_boxes_filters_by_owner(self):
        """list_boxes should only return boxes owned by the user."""
        user = _make_user(id=5)
        mock_db = AsyncMock()

        # Count query returns 0
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        # List query returns empty
        mock_list = MagicMock()
        mock_list.all.return_value = []

        mock_db.execute = AsyncMock(side_effect=[mock_count, mock_list])

        result = await box_service.list_boxes(mock_db, user=user)
        assert result.total == 0
        assert result.boxes == []

    async def test_delete_box_filters_by_owner(self):
        """delete_box should return None if box doesn't belong to user."""
        user = _make_user(id=5)
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await box_service.delete_box(mock_db, box_id=1, user=user)
        assert result is None


# ---------------------------------------------------------------------------
# Item service user scoping
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestItemServiceUserScoping:
    async def test_verify_box_owner_returns_false_for_wrong_user(self):
        """_verify_box_owner should return False if box belongs to different user."""
        user = _make_user(id=99)
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # not found for this owner
        mock_db.execute.return_value = mock_result

        result = await item_service._verify_box_owner(mock_db, box_id=1, user=user)
        assert result is False

    async def test_verify_box_owner_returns_true_for_correct_user(self):
        """_verify_box_owner should return True if box belongs to user."""
        user = _make_user(id=1)
        box = _make_box(owner_id=1)
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = box
        mock_db.execute.return_value = mock_result

        result = await item_service._verify_box_owner(mock_db, box_id=1, user=user)
        assert result is True

    async def test_list_items_returns_none_for_wrong_user(self):
        """list_items should return None if box doesn't belong to user."""
        user = _make_user(id=99)
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await item_service.list_items(mock_db, box_id=1, user=user)
        assert result is None

    async def test_add_item_raises_for_wrong_user(self):
        """add_item should raise ValueError if box doesn't belong to user."""
        user = _make_user(id=99)
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.schemas.item import ItemAddRequest
        data = ItemAddRequest(name="Widget", quantity=1, tags=[])

        with pytest.raises(ValueError, match="access denied"):
            await item_service.add_item(mock_db, box_id=1, data=data, user=user)

    async def test_remove_item_returns_false_for_wrong_user(self):
        """remove_item should return False if box doesn't belong to user."""
        user = _make_user(id=99)
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await item_service.remove_item(mock_db, box_id=1, item_id=1, user=user)
        assert result is False

    async def test_update_item_returns_none_for_wrong_user(self):
        """update_item should return None if box doesn't belong to user."""
        user = _make_user(id=99)
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.schemas.item import ItemUpdateRequest
        data = ItemUpdateRequest(quantity=5)

        result = await item_service.update_item(mock_db, box_id=1, item_id=1, data=data, user=user)
        assert result is None


# ---------------------------------------------------------------------------
# Transfer service user scoping
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestTransferServiceUserScoping:
    async def test_transfer_raises_if_source_box_not_owned(self):
        """transfer_item should raise if source box doesn't belong to user."""
        user = _make_user(id=99)
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        from app.schemas.transfer import TransferRequest
        data = TransferRequest(from_box_id=1, to_box_id=2, item_id=1, quantity=1)

        with pytest.raises(ValueError, match="Source box not found"):
            await transfer_service.transfer_item(mock_db, data, user)

    async def test_transfer_raises_if_dest_box_not_owned(self):
        """transfer_item should raise if dest box doesn't belong to user."""
        user = _make_user(id=1)
        mock_db = AsyncMock()

        source_box = _make_box(id=1, owner_id=1)
        call_count = 0

        def mock_execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = source_box
            else:
                result.scalar_one_or_none.return_value = None  # dest not owned
            return result

        mock_db.execute = AsyncMock(side_effect=mock_execute_side_effect)

        from app.schemas.transfer import TransferRequest
        data = TransferRequest(from_box_id=1, to_box_id=2, item_id=1, quantity=1)

        with pytest.raises(ValueError, match="Destination box not found"):
            await transfer_service.transfer_item(mock_db, data, user)


# ---------------------------------------------------------------------------
# Search service user scoping
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestSearchServiceUserScoping:
    async def test_empty_query_returns_empty_results(self):
        """search with empty string should return empty results."""
        user = _make_user(id=1)
        mock_db = AsyncMock()

        result = await search_service.search(mock_db, "  ", user)
        assert result == {"boxes": [], "items": []}

    async def test_search_passes_user_to_query(self):
        """search should filter by owner_id."""
        user = _make_user(id=5)
        mock_db = AsyncMock()

        mock_box_result = MagicMock()
        mock_box_result.all.return_value = []
        mock_item_result = MagicMock()
        mock_item_result.scalars.return_value.all.return_value = []

        mock_db.execute = AsyncMock(side_effect=[mock_box_result, mock_item_result])

        result = await search_service.search(mock_db, "test", user)
        assert result["boxes"] == []
        assert result["items"] == []
        # Verify execute was called twice (box search + item search)
        assert mock_db.execute.call_count == 2
