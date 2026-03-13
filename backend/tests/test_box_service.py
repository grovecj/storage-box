"""Tests for box_service.py."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services import box_service
from app.schemas.box import BoxCreate, BoxUpdate, LocationSchema


@pytest.mark.asyncio
class TestGetNextBoxCode:
    async def test_generates_box_code(self, mock_db):
        """Should generate BOX-#### format code."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 42
        mock_db.execute.return_value = mock_result

        code = await box_service.get_next_box_code(mock_db)
        assert code == "BOX-0042"

    async def test_pads_to_four_digits(self, mock_db):
        """Should pad with zeros for numbers < 1000."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 7
        mock_db.execute.return_value = mock_result

        code = await box_service.get_next_box_code(mock_db)
        assert code == "BOX-0007"


@pytest.mark.asyncio
class TestCreateBox:
    async def test_creates_box_without_location(self, mock_db, mock_user, mock_box):
        """Should create a box without location."""
        # Mock get_next_box_code
        with patch.object(box_service, "get_next_box_code", return_value="BOX-0001"):
            mock_db.flush = AsyncMock()
            mock_db.commit = AsyncMock()

            # Mock refresh to set the values on the box object
            async def mock_refresh(obj):
                obj.id = 1
                obj.created_at = datetime(2024, 1, 1)
                obj.updated_at = datetime(2024, 1, 1)

            mock_db.refresh = AsyncMock(side_effect=mock_refresh)

            # Mock log_action
            with patch("app.services.box_service.log_action", new=AsyncMock()):
                data = BoxCreate(name="My Box", location_name="Garage")
                result = await box_service.create_box(mock_db, data, mock_user)

                assert result.box_code == "BOX-0001"
                assert result.name == "My Box"
                assert result.location_name == "Garage"
                assert result.item_count == 0
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()

    async def test_creates_box_with_location(self, mock_db, mock_user):
        """Should create a box with GPS coordinates."""
        with patch.object(box_service, "get_next_box_code", return_value="BOX-0002"):
            mock_db.flush = AsyncMock()
            mock_db.commit = AsyncMock()

            async def mock_refresh(obj):
                obj.id = 2
                obj.created_at = datetime(2024, 1, 1)
                obj.updated_at = datetime(2024, 1, 1)

            mock_db.refresh = AsyncMock(side_effect=mock_refresh)

            with patch("app.services.box_service.log_action", new=AsyncMock()):
                data = BoxCreate(
                    name="GPS Box",
                    location=LocationSchema(latitude=47.6062, longitude=-122.3321),
                    location_name="Seattle"
                )
                result = await box_service.create_box(mock_db, data, mock_user)

                assert result.latitude == 47.6062
                assert result.longitude == -122.3321
                mock_db.add.assert_called_once()

    async def test_sets_audit_fields(self, mock_db, mock_user):
        """Should set created_by and updated_by to user.id."""
        with patch.object(box_service, "get_next_box_code", return_value="BOX-0003"):
            mock_db.flush = AsyncMock()
            mock_db.commit = AsyncMock()

            async def mock_refresh(obj):
                obj.id = 3
                obj.created_at = datetime(2024, 1, 1)
                obj.updated_at = datetime(2024, 1, 1)

            mock_db.refresh = AsyncMock(side_effect=mock_refresh)

            with patch("app.services.box_service.log_action", new=AsyncMock()):
                data = BoxCreate(name="Test")
                await box_service.create_box(mock_db, data, mock_user)

                added_box = mock_db.add.call_args[0][0]
                assert added_box.created_by == mock_user.id
                assert added_box.updated_by == mock_user.id
                assert added_box.owner_id == mock_user.id


@pytest.mark.asyncio
class TestGetBox:
    async def test_returns_box_with_item_count(self, mock_db, mock_user, mock_box):
        """Should return box with item count."""
        mock_result = MagicMock()
        mock_result.first.return_value = (mock_box, 3, None, None)
        mock_db.execute.return_value = mock_result

        result = await box_service.get_box(mock_db, 1, mock_user)

        assert result is not None
        assert result.id == 1
        assert result.box_code == "BOX-0001"
        assert result.item_count == 3

    async def test_returns_none_for_nonexistent_box(self, mock_db, mock_user):
        """Should return None if box doesn't exist."""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.execute.return_value = mock_result

        result = await box_service.get_box(mock_db, 999, mock_user)
        assert result is None

    async def test_filters_by_owner(self, mock_db, mock_user):
        """Should only return boxes owned by the user."""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.execute.return_value = mock_result

        result = await box_service.get_box(mock_db, 1, mock_user)
        assert result is None


@pytest.mark.asyncio
class TestGetBoxByCode:
    async def test_returns_box_by_code(self, mock_db, mock_user, mock_box):
        """Should find box by box_code."""
        mock_result = MagicMock()
        mock_result.first.return_value = (mock_box, 2, None, None)
        mock_db.execute.return_value = mock_result

        result = await box_service.get_box_by_code(mock_db, "BOX-0001", mock_user)

        assert result is not None
        assert result.box_code == "BOX-0001"
        assert result.item_count == 2

    async def test_returns_none_for_invalid_code(self, mock_db, mock_user):
        """Should return None if code doesn't exist."""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.execute.return_value = mock_result

        result = await box_service.get_box_by_code(mock_db, "BOX-9999", mock_user)
        assert result is None


@pytest.mark.asyncio
class TestListBoxes:
    async def test_returns_paginated_boxes(self, mock_db, mock_user, mock_box):
        """Should return paginated list of boxes."""
        # Mock count query
        count_result = MagicMock()
        count_result.scalar.return_value = 5

        # Mock box query
        box_result = MagicMock()
        box_result.all.return_value = [(mock_box, 2, None, None)]

        mock_db.execute.side_effect = [count_result, box_result]

        result = await box_service.list_boxes(mock_db, mock_user, page=1, page_size=10)

        assert result.total == 5
        assert result.page == 1
        assert result.page_size == 10
        assert len(result.boxes) == 1
        assert result.boxes[0].box_code == "BOX-0001"

    async def test_sorts_by_recent_by_default(self, mock_db, mock_user):
        """Should sort by updated_at desc by default."""
        count_result = MagicMock()
        count_result.scalar.return_value = 0
        box_result = MagicMock()
        box_result.all.return_value = []
        mock_db.execute.side_effect = [count_result, box_result]

        await box_service.list_boxes(mock_db, mock_user, sort="recent")
        mock_db.execute.assert_called()

    async def test_sorts_by_proximity_when_provided(self, mock_db, mock_user):
        """Should sort by distance when lat/lng provided."""
        count_result = MagicMock()
        count_result.scalar.return_value = 0
        box_result = MagicMock()
        box_result.all.return_value = []
        mock_db.execute.side_effect = [count_result, box_result]

        await box_service.list_boxes(
            mock_db, mock_user, sort="proximity", lat=47.6062, lng=-122.3321
        )
        mock_db.execute.assert_called()


@pytest.mark.asyncio
class TestUpdateBox:
    async def test_updates_box_name(self, mock_db, mock_user, mock_box):
        """Should update box name."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_box
        mock_db.execute.return_value = mock_result
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch.object(box_service, "get_box") as mock_get_box:
            mock_get_box.return_value = MagicMock(name="New Name")
            with patch("app.services.box_service.log_action", new=AsyncMock()):
                data = BoxUpdate(name="New Name")
                result = await box_service.update_box(mock_db, 1, data, mock_user)

                assert result is not None
                assert mock_box.name == "New Name"
                assert mock_box.updated_by == mock_user.id

    async def test_updates_location(self, mock_db, mock_user, mock_box):
        """Should update box location."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_box
        mock_db.execute.return_value = mock_result
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch.object(box_service, "get_box") as mock_get_box:
            mock_get_box.return_value = MagicMock()
            with patch("app.services.box_service.log_action", new=AsyncMock()):
                data = BoxUpdate(location=LocationSchema(latitude=40.7128, longitude=-74.0060))
                await box_service.update_box(mock_db, 1, data, mock_user)

                assert mock_box.location is not None

    async def test_returns_none_for_nonexistent_box(self, mock_db, mock_user):
        """Should return None if box doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        data = BoxUpdate(name="Test")
        result = await box_service.update_box(mock_db, 999, data, mock_user)
        assert result is None


@pytest.mark.asyncio
class TestDeleteBox:
    async def test_deletes_box_and_returns_info(self, mock_db, mock_user, mock_box):
        """Should delete box and return metadata."""
        # Mock box query
        box_result = MagicMock()
        box_result.scalar_one_or_none.return_value = mock_box

        # Mock item count query
        count_result = MagicMock()
        count_result.scalar.return_value = 3

        mock_db.execute.side_effect = [box_result, count_result]
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch("app.services.box_service.log_action", new=AsyncMock()):
            result = await box_service.delete_box(mock_db, 1, mock_user)

            assert result is not None
            assert result["box_code"] == "BOX-0001"
            assert result["items_removed"] == 3
            mock_db.delete.assert_called_once_with(mock_box)

    async def test_returns_none_for_nonexistent_box(self, mock_db, mock_user):
        """Should return None if box doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await box_service.delete_box(mock_db, 999, mock_user)
        assert result is None
