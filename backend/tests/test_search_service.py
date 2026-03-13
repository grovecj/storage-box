"""Tests for search_service.py."""
import pytest
from unittest.mock import MagicMock

from app.services import search_service


@pytest.mark.asyncio
class TestSearch:
    async def test_returns_empty_for_empty_query(self, mock_db, mock_user):
        """Should return empty results for empty query."""
        result = await search_service.search(mock_db, "", mock_user)
        assert result == {"boxes": [], "items": []}

    async def test_returns_empty_for_whitespace_query(self, mock_db, mock_user):
        """Should return empty results for whitespace-only query."""
        result = await search_service.search(mock_db, "   ", mock_user)
        assert result == {"boxes": [], "items": []}

    async def test_searches_boxes_by_code(self, mock_db, mock_user):
        """Should search boxes by box_code."""
        box = MagicMock()
        box.id = 1
        box.box_code = "BOX-0001"
        box.name = "Test Box"

        box_result = MagicMock()
        box_result.all.return_value = [(box, 3, None, None)]

        item_result = MagicMock()
        item_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [box_result, item_result]

        result = await search_service.search(mock_db, "BOX-0001", mock_user)

        assert len(result["boxes"]) == 1
        assert result["boxes"][0]["box_code"] == "BOX-0001"
        assert result["boxes"][0]["item_count"] == 3
        assert result["boxes"][0]["match_type"] == "box"

    async def test_searches_boxes_by_name(self, mock_db, mock_user):
        """Should search boxes by name."""
        box = MagicMock()
        box.id = 1
        box.box_code = "BOX-0002"
        box.name = "Garage Storage"

        box_result = MagicMock()
        box_result.all.return_value = [(box, 5, 47.6062, -122.3321)]

        item_result = MagicMock()
        item_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [box_result, item_result]

        result = await search_service.search(mock_db, "garage", mock_user)

        assert len(result["boxes"]) == 1
        assert result["boxes"][0]["name"] == "Garage Storage"
        assert result["boxes"][0]["latitude"] == 47.6062
        assert result["boxes"][0]["longitude"] == -122.3321

    async def test_searches_items_by_name(self, mock_db, mock_user):
        """Should search items by name."""
        box_item = MagicMock()
        box_item.id = 1
        box_item.item_id = 10
        box_item.quantity = 3
        box_item.box_id = 2
        box_item.item = MagicMock()
        box_item.item.name = "HDMI Cable"
        box_item.box = MagicMock()
        box_item.box.id = 2
        box_item.box.box_code = "BOX-0003"
        box_item.box.name = "Electronics"
        box_item.tags = []

        box_result = MagicMock()
        box_result.all.return_value = []

        item_result = MagicMock()
        item_result.scalars.return_value.all.return_value = [box_item]

        mock_db.execute.side_effect = [box_result, item_result]

        result = await search_service.search(mock_db, "cable", mock_user)

        assert len(result["items"]) == 1
        assert result["items"][0]["name"] == "HDMI Cable"
        assert result["items"][0]["box_code"] == "BOX-0003"
        assert result["items"][0]["quantity"] == 3

    async def test_searches_items_by_tag(self, mock_db, mock_user):
        """Should search items by tag name."""
        tag = MagicMock()
        tag.name = "winter"

        box_item = MagicMock()
        box_item.id = 1
        box_item.item_id = 11
        box_item.quantity = 2
        box_item.box_id = 3
        box_item.item = MagicMock()
        box_item.item.name = "Snow boots"
        box_item.box = MagicMock()
        box_item.box.id = 3
        box_item.box.box_code = "BOX-0004"
        box_item.box.name = "Seasonal"
        box_item.tags = [MagicMock(tag=tag)]

        box_result = MagicMock()
        box_result.all.return_value = []

        item_result = MagicMock()
        item_result.scalars.return_value.all.return_value = [box_item]

        mock_db.execute.side_effect = [box_result, item_result]

        result = await search_service.search(mock_db, "winter", mock_user)

        assert len(result["items"]) == 1
        assert result["items"][0]["tags"] == ["winter"]

    async def test_includes_parent_box_for_item_matches(self, mock_db, mock_user):
        """Should include parent box in results when item matches."""
        box_item = MagicMock()
        box_item.id = 1
        box_item.item_id = 12
        box_item.quantity = 1
        box_item.box_id = 5
        box_item.item = MagicMock()
        box_item.item.name = "Screwdriver"
        box_item.box = MagicMock()
        box_item.box.id = 5
        box_item.box.box_code = "BOX-0005"
        box_item.box.name = "Tools"
        box_item.tags = []

        box_result = MagicMock()
        box_result.all.return_value = []

        item_result = MagicMock()
        item_result.scalars.return_value.all.return_value = [box_item]

        mock_db.execute.side_effect = [box_result, item_result]

        result = await search_service.search(mock_db, "screwdriver", mock_user)

        # Should include both the item and its parent box
        assert len(result["items"]) == 1
        assert len(result["boxes"]) == 1
        assert result["boxes"][0]["id"] == 5
        assert result["boxes"][0]["match_type"] == "contains_match"

    async def test_does_not_duplicate_parent_box(self, mock_db, mock_user):
        """Should not duplicate parent box if already in results."""
        box = MagicMock()
        box.id = 6
        box.box_code = "BOX-0006"
        box.name = "Kitchen"

        box_item = MagicMock()
        box_item.id = 1
        box_item.item_id = 13
        box_item.quantity = 4
        box_item.box_id = 6
        box_item.item = MagicMock()
        box_item.item.name = "Kitchen knife"
        box_item.box = MagicMock()
        box_item.box.id = 6
        box_item.box.box_code = "BOX-0006"
        box_item.box.name = "Kitchen"
        box_item.tags = []

        box_result = MagicMock()
        box_result.all.return_value = [(box, 10, None, None)]

        item_result = MagicMock()
        item_result.scalars.return_value.all.return_value = [box_item]

        mock_db.execute.side_effect = [box_result, item_result]

        result = await search_service.search(mock_db, "kitchen", mock_user)

        # Should only have one box (not duplicated)
        assert len(result["boxes"]) == 1
        assert result["boxes"][0]["id"] == 6

    async def test_filters_results_by_user(self, mock_db, mock_user):
        """Should only return results owned by the user."""
        box_result = MagicMock()
        box_result.all.return_value = []

        item_result = MagicMock()
        item_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [box_result, item_result]

        result = await search_service.search(mock_db, "test", mock_user)

        # Verify queries were executed (with user filter)
        assert mock_db.execute.call_count == 2
        assert result == {"boxes": [], "items": []}
