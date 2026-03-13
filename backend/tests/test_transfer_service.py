"""Tests for transfer_service.py."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import transfer_service
from app.schemas.transfer import TransferRequest


@pytest.mark.asyncio
class TestTransferItem:
    async def test_transfers_full_quantity(self, mock_db, mock_user, mock_box, mock_box_item):
        """Should transfer entire item quantity between boxes."""
        # Create two different boxes
        from_box = MagicMock()
        from_box.id = 1
        from_box.box_code = "BOX-0001"
        from_box.owner_id = 1

        to_box = MagicMock()
        to_box.id = 2
        to_box.box_code = "BOX-0002"
        to_box.owner_id = 1

        # Source box_item with 5 items
        source_bi = MagicMock()
        source_bi.id = 1
        source_bi.quantity = 5
        source_bi.item_id = 1
        source_bi.item = MagicMock()
        source_bi.item.name = "Cable"
        source_bi.tags = []

        # Mock queries
        from_box_result = MagicMock()
        from_box_result.scalar_one_or_none.return_value = from_box

        to_box_result = MagicMock()
        to_box_result.scalar_one_or_none.return_value = to_box

        source_result = MagicMock()
        source_result.scalar_one_or_none.return_value = source_bi

        dest_result = MagicMock()
        dest_result.scalar_one_or_none.return_value = None  # Item doesn't exist in dest

        mock_db.execute.side_effect = [from_box_result, to_box_result, source_result, dest_result]
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.delete = AsyncMock()

        with patch("app.services.transfer_service.log_action", new=AsyncMock()):
            data = TransferRequest(from_box_id=1, to_box_id=2, item_id=1, quantity=5)
            result = await transfer_service.transfer_item(mock_db, data, mock_user)

            assert result.from_box_code == "BOX-0001"
            assert result.to_box_code == "BOX-0002"
            assert result.item_name == "Cable"
            assert result.quantity == 5
            # Should delete source since full quantity transferred
            mock_db.delete.assert_called_once_with(source_bi)

    async def test_transfers_partial_quantity(self, mock_db, mock_user):
        """Should transfer partial quantity and update source."""
        from_box = MagicMock()
        from_box.id = 1
        from_box.box_code = "BOX-0001"
        from_box.owner_id = 1

        to_box = MagicMock()
        to_box.id = 2
        to_box.box_code = "BOX-0002"
        to_box.owner_id = 1

        source_bi = MagicMock()
        source_bi.quantity = 10
        source_bi.item_id = 1
        source_bi.item = MagicMock()
        source_bi.item.name = "Widget"
        source_bi.tags = []

        from_box_result = MagicMock()
        from_box_result.scalar_one_or_none.return_value = from_box

        to_box_result = MagicMock()
        to_box_result.scalar_one_or_none.return_value = to_box

        source_result = MagicMock()
        source_result.scalar_one_or_none.return_value = source_bi

        dest_result = MagicMock()
        dest_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [from_box_result, to_box_result, source_result, dest_result]
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.delete = AsyncMock()

        with patch("app.services.transfer_service.log_action", new=AsyncMock()):
            data = TransferRequest(from_box_id=1, to_box_id=2, item_id=1, quantity=3)
            await transfer_service.transfer_item(mock_db, data, mock_user)

            # Should reduce source quantity, not delete
            assert source_bi.quantity == 7
            mock_db.delete.assert_not_called()

    async def test_increments_existing_destination_item(self, mock_db, mock_user):
        """Should increment quantity if item exists in destination."""
        from_box = MagicMock()
        from_box.id = 1
        from_box.box_code = "BOX-0001"
        from_box.owner_id = 1

        to_box = MagicMock()
        to_box.id = 2
        to_box.box_code = "BOX-0002"
        to_box.owner_id = 1

        source_bi = MagicMock()
        source_bi.quantity = 5
        source_bi.item_id = 1
        source_bi.item = MagicMock()
        source_bi.item.name = "Gadget"
        source_bi.tags = []

        dest_bi = MagicMock()
        dest_bi.quantity = 3

        from_box_result = MagicMock()
        from_box_result.scalar_one_or_none.return_value = from_box

        to_box_result = MagicMock()
        to_box_result.scalar_one_or_none.return_value = to_box

        source_result = MagicMock()
        source_result.scalar_one_or_none.return_value = source_bi

        dest_result = MagicMock()
        dest_result.scalar_one_or_none.return_value = dest_bi

        mock_db.execute.side_effect = [from_box_result, to_box_result, source_result, dest_result]
        mock_db.commit = AsyncMock()
        mock_db.delete = AsyncMock()

        with patch("app.services.transfer_service.log_action", new=AsyncMock()):
            data = TransferRequest(from_box_id=1, to_box_id=2, item_id=1, quantity=2)
            await transfer_service.transfer_item(mock_db, data, mock_user)

            assert dest_bi.quantity == 5
            assert dest_bi.updated_by == mock_user.id

    async def test_copies_tags_to_new_destination_item(self, mock_db, mock_user):
        """Should copy tags when creating new item in destination."""
        from_box = MagicMock()
        from_box.id = 1
        from_box.box_code = "BOX-0001"
        from_box.owner_id = 1

        to_box = MagicMock()
        to_box.id = 2
        to_box.box_code = "BOX-0002"
        to_box.owner_id = 1

        tag1 = MagicMock()
        tag1.tag_id = 1
        tag2 = MagicMock()
        tag2.tag_id = 2

        source_bi = MagicMock()
        source_bi.quantity = 5
        source_bi.item_id = 1
        source_bi.item = MagicMock()
        source_bi.item.name = "Tagged Item"
        source_bi.tags = [tag1, tag2]

        from_box_result = MagicMock()
        from_box_result.scalar_one_or_none.return_value = from_box

        to_box_result = MagicMock()
        to_box_result.scalar_one_or_none.return_value = to_box

        source_result = MagicMock()
        source_result.scalar_one_or_none.return_value = source_bi

        dest_result = MagicMock()
        dest_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [from_box_result, to_box_result, source_result, dest_result]
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch("app.services.transfer_service.log_action", new=AsyncMock()):
            data = TransferRequest(from_box_id=1, to_box_id=2, item_id=1, quantity=3)
            await transfer_service.transfer_item(mock_db, data, mock_user)

            # Should add 2 tags
            assert mock_db.add.call_count >= 2

    async def test_raises_error_for_nonexistent_source_box(self, mock_db, mock_user):
        """Should raise error if source box doesn't exist."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result

        data = TransferRequest(from_box_id=999, to_box_id=2, item_id=1, quantity=1)
        with pytest.raises(ValueError, match="Source box not found"):
            await transfer_service.transfer_item(mock_db, data, mock_user)

    async def test_raises_error_for_nonexistent_destination_box(self, mock_db, mock_user):
        """Should raise error if destination box doesn't exist."""
        from_box = MagicMock()
        from_box.owner_id = 1

        from_box_result = MagicMock()
        from_box_result.scalar_one_or_none.return_value = from_box

        to_box_result = MagicMock()
        to_box_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [from_box_result, to_box_result]

        data = TransferRequest(from_box_id=1, to_box_id=999, item_id=1, quantity=1)
        with pytest.raises(ValueError, match="Destination box not found"):
            await transfer_service.transfer_item(mock_db, data, mock_user)

    async def test_raises_error_for_nonexistent_item(self, mock_db, mock_user):
        """Should raise error if item doesn't exist in source box."""
        from_box = MagicMock()
        from_box.owner_id = 1

        to_box = MagicMock()
        to_box.owner_id = 1

        from_box_result = MagicMock()
        from_box_result.scalar_one_or_none.return_value = from_box

        to_box_result = MagicMock()
        to_box_result.scalar_one_or_none.return_value = to_box

        source_result = MagicMock()
        source_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [from_box_result, to_box_result, source_result]

        data = TransferRequest(from_box_id=1, to_box_id=2, item_id=999, quantity=1)
        with pytest.raises(ValueError, match="Item not found in source box"):
            await transfer_service.transfer_item(mock_db, data, mock_user)

    async def test_raises_error_for_insufficient_quantity(self, mock_db, mock_user):
        """Should raise error if trying to transfer more than available."""
        from_box = MagicMock()
        from_box.owner_id = 1

        to_box = MagicMock()
        to_box.owner_id = 1

        source_bi = MagicMock()
        source_bi.quantity = 2

        from_box_result = MagicMock()
        from_box_result.scalar_one_or_none.return_value = from_box

        to_box_result = MagicMock()
        to_box_result.scalar_one_or_none.return_value = to_box

        source_result = MagicMock()
        source_result.scalar_one_or_none.return_value = source_bi

        mock_db.execute.side_effect = [from_box_result, to_box_result, source_result]

        data = TransferRequest(from_box_id=1, to_box_id=2, item_id=1, quantity=5)
        with pytest.raises(ValueError, match="Cannot transfer 5, only 2 available"):
            await transfer_service.transfer_item(mock_db, data, mock_user)
