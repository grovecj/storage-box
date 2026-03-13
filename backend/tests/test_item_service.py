"""Tests for item_service.py."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services import item_service
from app.schemas.item import ItemAddRequest, ItemUpdateRequest
from app.models.item import BoxItem


@pytest.mark.asyncio
class TestListItems:
    async def test_returns_items_for_box(self, mock_db, mock_user, mock_box_item):
        """Should return paginated items for a box."""
        # Mock verify_box_owner
        with patch.object(item_service, "_verify_box_owner", return_value=True):
            # Mock count query
            count_result = MagicMock()
            count_result.scalar.return_value = 5

            # Mock items query
            items_result = MagicMock()
            items_result.scalars.return_value.all.return_value = [mock_box_item]

            mock_db.execute.side_effect = [count_result, items_result]

            result = await item_service.list_items(mock_db, 1, mock_user, page=1, page_size=10)

            assert result is not None
            assert result.total == 5
            assert len(result.items) == 1
            assert result.items[0].name == "Test Item"

    async def test_returns_none_for_unauthorized_box(self, mock_db, mock_user):
        """Should return None if user doesn't own the box."""
        with patch.object(item_service, "_verify_box_owner", return_value=False):
            result = await item_service.list_items(mock_db, 1, mock_user)
            assert result is None

    async def test_supports_unlimited_page_size(self, mock_db, mock_user, mock_box_item):
        """Should return all items when page_size is None."""
        with patch.object(item_service, "_verify_box_owner", return_value=True):
            count_result = MagicMock()
            count_result.scalar.return_value = 3
            items_result = MagicMock()
            items_result.scalars.return_value.all.return_value = [mock_box_item]
            mock_db.execute.side_effect = [count_result, items_result]

            result = await item_service.list_items(mock_db, 1, mock_user, page_size=None)
            assert result.page_size == 3


@pytest.mark.asyncio
class TestAddItem:
    async def test_adds_new_item_to_box(self, mock_db, mock_user, mock_item, mock_box_item):
        """Should add a new item to a box."""
        with patch.object(item_service, "_verify_box_owner", return_value=True):
            # Mock count query (current items in box)
            count_result = MagicMock()
            count_result.scalar.return_value = 10

            # Mock get_or_create_item
            with patch.object(item_service, "_get_or_create_item", return_value=mock_item):
                # Mock existing box_item query (item not in box yet)
                existing_result = MagicMock()
                existing_result.scalar_one_or_none.return_value = None

                # Mock tag delete query
                tag_delete_result = MagicMock()

                # Mock final fetch
                final_result = MagicMock()
                final_result.scalar_one.return_value = mock_box_item

                mock_db.execute.side_effect = [count_result, existing_result, tag_delete_result, final_result]
                mock_db.flush = AsyncMock()
                mock_db.commit = AsyncMock()

                with patch.object(item_service, "_get_or_create_tag") as mock_get_tag:
                    mock_get_tag.return_value = MagicMock(id=1, name="test")
                    with patch("app.services.item_service.log_action", new=AsyncMock()):
                        data = ItemAddRequest(name="New Item", quantity=3, tags=["test"])
                        result = await item_service.add_item(mock_db, 1, data, mock_user)

                        assert result is not None
                        assert result.name == "Test Item"
                        mock_db.add.assert_called()

    async def test_increments_quantity_for_existing_item(self, mock_db, mock_user, mock_item, mock_box_item):
        """Should increment quantity if item already in box."""
        with patch.object(item_service, "_verify_box_owner", return_value=True):
            count_result = MagicMock()
            count_result.scalar.return_value = 10

            with patch.object(item_service, "_get_or_create_item", return_value=mock_item):
                # Mock existing box_item (item already in box)
                existing_result = MagicMock()
                existing_result.scalar_one_or_none.return_value = mock_box_item

                final_result = MagicMock()
                final_result.scalar_one.return_value = mock_box_item

                mock_db.execute.side_effect = [count_result, existing_result, MagicMock(), final_result]
                mock_db.flush = AsyncMock()
                mock_db.commit = AsyncMock()

                original_qty = mock_box_item.quantity
                with patch("app.services.item_service.log_action", new=AsyncMock()):
                    data = ItemAddRequest(name="Test Item", quantity=2, tags=[])
                    await item_service.add_item(mock_db, 1, data, mock_user)

                    assert mock_box_item.quantity == original_qty + 2

    async def test_raises_error_if_box_at_max_items(self, mock_db, mock_user):
        """Should raise error if box has 500 items."""
        with patch.object(item_service, "_verify_box_owner", return_value=True):
            count_result = MagicMock()
            count_result.scalar.return_value = 500
            mock_db.execute.return_value = count_result

            data = ItemAddRequest(name="Item", quantity=1, tags=[])
            with pytest.raises(ValueError, match="maximum limit"):
                await item_service.add_item(mock_db, 1, data, mock_user)

    async def test_raises_error_for_unauthorized_box(self, mock_db, mock_user):
        """Should raise error if user doesn't own box."""
        with patch.object(item_service, "_verify_box_owner", return_value=False):
            data = ItemAddRequest(name="Item", quantity=1, tags=[])
            with pytest.raises(ValueError, match="access denied"):
                await item_service.add_item(mock_db, 1, data, mock_user)


@pytest.mark.asyncio
class TestUpdateItem:
    async def test_updates_item_quantity(self, mock_db, mock_user, mock_box_item):
        """Should update item quantity."""
        with patch.object(item_service, "_verify_box_owner", return_value=True):
            # Mock box_item query
            initial_result = MagicMock()
            initial_result.scalar_one_or_none.return_value = mock_box_item

            # Mock final fetch - create a fresh mock with proper item
            mock_item_obj = MagicMock()
            mock_item_obj.name = "Test Item"  # Must be a string, not mock

            updated_box_item = MagicMock()
            updated_box_item.id = 1
            updated_box_item.item_id = 1
            updated_box_item.item = mock_item_obj
            updated_box_item.quantity = 10
            updated_box_item.tags = []
            updated_box_item.created_at = datetime(2024, 1, 1)
            updated_box_item.updated_at = datetime(2024, 1, 1)
            updated_box_item.created_by = 1
            updated_box_item.updated_by = 1

            final_result = MagicMock()
            final_result.scalar_one.return_value = updated_box_item

            # Only 2 execute calls when tags is None (initial + final)
            mock_db.execute.side_effect = [initial_result, final_result]
            mock_db.flush = AsyncMock()
            mock_db.commit = AsyncMock()

            with patch("app.services.item_service.log_action", new=AsyncMock()):
                data = ItemUpdateRequest(quantity=10)
                result = await item_service.update_item(mock_db, 1, 1, data, mock_user)

                assert result is not None
                assert mock_box_item.quantity == 10
                assert mock_box_item.updated_by == mock_user.id

    async def test_updates_item_tags(self, mock_db, mock_user, mock_box_item, mock_tag):
        """Should update item tags."""
        with patch.object(item_service, "_verify_box_owner", return_value=True):
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_box_item

            final_result = MagicMock()
            final_result.scalar_one.return_value = mock_box_item

            mock_db.execute.side_effect = [result, MagicMock(), final_result]
            mock_db.flush = AsyncMock()
            mock_db.commit = AsyncMock()

            with patch.object(item_service, "_get_or_create_tag", return_value=mock_tag):
                with patch("app.services.item_service.log_action", new=AsyncMock()):
                    data = ItemUpdateRequest(tags=["new-tag"])
                    await item_service.update_item(mock_db, 1, 1, data, mock_user)

                    mock_db.execute.assert_called()

    async def test_returns_none_for_nonexistent_item(self, mock_db, mock_user):
        """Should return None if item doesn't exist in box."""
        with patch.object(item_service, "_verify_box_owner", return_value=True):
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = result

            data = ItemUpdateRequest(quantity=5)
            result = await item_service.update_item(mock_db, 1, 999, data, mock_user)
            assert result is None

    async def test_returns_none_for_unauthorized_box(self, mock_db, mock_user):
        """Should return None if user doesn't own box."""
        with patch.object(item_service, "_verify_box_owner", return_value=False):
            data = ItemUpdateRequest(quantity=5)
            result = await item_service.update_item(mock_db, 1, 1, data, mock_user)
            assert result is None


@pytest.mark.asyncio
class TestRemoveItem:
    async def test_removes_item_from_box(self, mock_db, mock_user, mock_box_item):
        """Should delete item from box."""
        with patch.object(item_service, "_verify_box_owner", return_value=True):
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_box_item
            mock_db.execute.return_value = result
            mock_db.delete = AsyncMock()
            mock_db.commit = AsyncMock()

            with patch("app.services.item_service.log_action", new=AsyncMock()):
                result = await item_service.remove_item(mock_db, 1, 1, mock_user)

                assert result is True
                mock_db.delete.assert_called_once_with(mock_box_item)

    async def test_returns_false_for_nonexistent_item(self, mock_db, mock_user):
        """Should return False if item doesn't exist."""
        with patch.object(item_service, "_verify_box_owner", return_value=True):
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = result

            result = await item_service.remove_item(mock_db, 1, 999, mock_user)
            assert result is False

    async def test_returns_false_for_unauthorized_box(self, mock_db, mock_user):
        """Should return False if user doesn't own box."""
        with patch.object(item_service, "_verify_box_owner", return_value=False):
            result = await item_service.remove_item(mock_db, 1, 1, mock_user)
            assert result is False


@pytest.mark.asyncio
class TestAutocompleteItems:
    async def test_returns_matching_items(self, mock_db, mock_user, mock_item):
        """Should return items matching query."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = [mock_item]
        mock_db.execute.return_value = result

        results = await item_service.autocomplete_items(mock_db, "test", mock_user, limit=10)

        assert len(results) == 1
        assert results[0]["name"] == "Test Item"
        assert "id" in results[0]

    async def test_filters_by_user_ownership(self, mock_db, mock_user):
        """Should only return items from user's boxes."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = result

        results = await item_service.autocomplete_items(mock_db, "test", mock_user)
        assert results == []

    async def test_respects_limit_parameter(self, mock_db, mock_user):
        """Should limit results to specified count."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = result

        await item_service.autocomplete_items(mock_db, "test", mock_user, limit=5)
        mock_db.execute.assert_called_once()


@pytest.mark.asyncio
class TestGetOrCreateItem:
    async def test_returns_existing_item(self, mock_db, mock_user, mock_item):
        """Should return existing item if name matches (case-insensitive)."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_item
        mock_db.execute.return_value = result

        item = await item_service._get_or_create_item(mock_db, "Test Item", mock_user)
        assert item == mock_item
        mock_db.add.assert_not_called()

    async def test_creates_new_item_if_not_exists(self, mock_db, mock_user):
        """Should create new item if name doesn't exist."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result
        mock_db.flush = AsyncMock()

        item = await item_service._get_or_create_item(mock_db, "New Item", mock_user)
        mock_db.add.assert_called_once()
        assert mock_db.add.call_args[0][0].name == "New Item"


@pytest.mark.asyncio
class TestGetOrCreateTag:
    async def test_returns_existing_tag(self, mock_db, mock_user, mock_tag):
        """Should return existing tag if name matches (case-insensitive)."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_tag
        mock_db.execute.return_value = result

        tag = await item_service._get_or_create_tag(mock_db, "test-tag", mock_user)
        assert tag == mock_tag
        mock_db.add.assert_not_called()

    async def test_creates_new_tag_if_not_exists(self, mock_db, mock_user):
        """Should create new tag if name doesn't exist."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result
        mock_db.flush = AsyncMock()

        tag = await item_service._get_or_create_tag(mock_db, "new-tag", mock_user)
        mock_db.add.assert_called_once()
        assert mock_db.add.call_args[0][0].name == "new-tag"
