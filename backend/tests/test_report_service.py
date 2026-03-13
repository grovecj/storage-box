"""Tests for report_service.py."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import report_service
from app.schemas.report import ReportRequest


@pytest.mark.asyncio
class TestFetchReportData:
    async def test_fetches_all_boxes_by_default(self, mock_db, mock_user):
        """Should fetch all user's boxes when no filters."""
        box = MagicMock()
        box.id = 1
        box.box_code = "BOX-0001"
        box.name = "Test Box"
        box.location = None
        box.location_name = "Test Location"
        box.box_items = []

        result = MagicMock()
        result.scalars.return_value.unique.return_value.all.return_value = [box]
        mock_db.execute.return_value = result

        request = ReportRequest()
        data = await report_service._fetch_report_data(mock_db, request, mock_user)

        assert len(data) == 1
        assert data[0]["box_code"] == "BOX-0001"
        assert data[0]["items"] == []

    async def test_filters_by_box_ids(self, mock_db, mock_user):
        """Should filter by specific box IDs."""
        result = MagicMock()
        result.scalars.return_value.unique.return_value.all.return_value = []
        mock_db.execute.return_value = result

        request = ReportRequest(box_ids=[1, 2, 3])
        await report_service._fetch_report_data(mock_db, request, mock_user)

        mock_db.execute.assert_called_once()

    async def test_filters_by_location(self, mock_db, mock_user):
        """Should filter by location name."""
        result = MagicMock()
        result.scalars.return_value.unique.return_value.all.return_value = []
        mock_db.execute.return_value = result

        request = ReportRequest(location_filter="garage")
        await report_service._fetch_report_data(mock_db, request, mock_user)

        mock_db.execute.assert_called_once()

    async def test_filters_items_by_tags(self, mock_db, mock_user):
        """Should filter items by tags."""
        tag1 = MagicMock()
        tag1.name = "winter"

        box_item1 = MagicMock()
        box_item1.item = MagicMock()
        box_item1.item.name = "Boots"
        box_item1.quantity = 1
        box_item1.tags = [MagicMock(tag=tag1)]

        box_item2 = MagicMock()
        box_item2.item = MagicMock()
        box_item2.item.name = "Shirt"
        box_item2.quantity = 3
        box_item2.tags = []

        box = MagicMock()
        box.id = 1
        box.box_code = "BOX-0001"
        box.name = "Seasonal"
        box.location = None
        box.location_name = None
        box.box_items = [box_item1, box_item2]

        result = MagicMock()
        result.scalars.return_value.unique.return_value.all.return_value = [box]
        mock_db.execute.return_value = result

        request = ReportRequest(tag_filter=["winter"])
        data = await report_service._fetch_report_data(mock_db, request, mock_user)

        # Should only include items with matching tags
        assert len(data) == 1
        assert len(data[0]["items"]) == 1
        assert data[0]["items"][0]["name"] == "Boots"

    async def test_excludes_boxes_with_no_matching_items(self, mock_db, mock_user):
        """Should exclude boxes with no items matching tag filter."""
        box_item = MagicMock()
        box_item.item = MagicMock()
        box_item.item.name = "Item"
        box_item.quantity = 1
        box_item.tags = []

        box = MagicMock()
        box.id = 1
        box.box_code = "BOX-0001"
        box.name = "Box"
        box.location = None
        box.location_name = None
        box.box_items = [box_item]

        result = MagicMock()
        result.scalars.return_value.unique.return_value.all.return_value = [box]
        mock_db.execute.return_value = result

        request = ReportRequest(tag_filter=["winter"])
        data = await report_service._fetch_report_data(mock_db, request, mock_user)

        assert len(data) == 0

    async def test_includes_gps_coordinates(self, mock_db, mock_user):
        """Should extract GPS coordinates from PostGIS location."""
        box = MagicMock()
        box.id = 1
        box.box_code = "BOX-0001"
        box.name = "Box"
        box.location = "SRID=4326;POINT(-122.3321 47.6062)"
        box.location_name = "Seattle"
        box.box_items = []

        box_result = MagicMock()
        box_result.scalars.return_value.unique.return_value.all.return_value = [box]

        coord_result = MagicMock()
        coord_result.first.return_value = (47.6062, -122.3321)

        mock_db.execute.side_effect = [box_result, coord_result]

        request = ReportRequest()
        data = await report_service._fetch_report_data(mock_db, request, mock_user)

        assert data[0]["latitude"] == 47.6062
        assert data[0]["longitude"] == -122.3321


@pytest.mark.asyncio
class TestGenerateHtmlReport:
    async def test_generates_html_with_boxes(self, mock_db, mock_user):
        """Should generate HTML report with box data."""
        with patch.object(report_service, "_fetch_report_data") as mock_fetch:
            mock_fetch.return_value = [{
                "box_code": "BOX-0001",
                "name": "Test Box",
                "latitude": None,
                "longitude": None,
                "location_name": "Garage",
                "items": [{"name": "Item", "quantity": 1, "tags": []}],
            }]

            request = ReportRequest()
            html = await report_service.generate_html_report(mock_db, request, mock_user)

            assert "BOX-0001" in html
            assert "Test Box" in html
            assert "Garage" in html
            assert "Item" in html

    async def test_html_contains_required_structure(self, mock_db, mock_user):
        """Should generate valid HTML structure."""
        with patch.object(report_service, "_fetch_report_data", return_value=[]):
            request = ReportRequest()
            html = await report_service.generate_html_report(mock_db, request, mock_user)

            assert "<!DOCTYPE html>" in html
            assert "<title>Storage Box Inventory Report</title>" in html
            assert "Generated:" in html


@pytest.mark.asyncio
class TestGeneratePdfReport:
    async def test_generates_pdf_from_html(self, mock_db, mock_user):
        """Should generate PDF from HTML."""
        with patch.object(report_service, "generate_html_report") as mock_html:
            mock_html.return_value = "<html><body>Test</body></html>"
            # Patch weasyprint.HTML directly, not from report_service module
            with patch("weasyprint.HTML") as mock_weasy:
                mock_weasy.return_value.write_pdf.return_value = b"PDF content"

                request = ReportRequest()
                pdf = await report_service.generate_pdf_report(mock_db, request, mock_user)

                assert pdf == b"PDF content"
                mock_weasy.assert_called_once()


@pytest.mark.asyncio
class TestGenerateTextReport:
    async def test_generates_text_with_boxes(self, mock_db, mock_user):
        """Should generate text report with box data."""
        with patch.object(report_service, "_fetch_report_data") as mock_fetch:
            mock_fetch.return_value = [{
                "box_code": "BOX-0001",
                "name": "Test Box",
                "latitude": None,
                "longitude": None,
                "location_name": "Garage",
                "items": [{"name": "Hammer", "quantity": 2, "tags": ["tools"]}],
            }]

            request = ReportRequest()
            text = await report_service.generate_text_report(mock_db, request, mock_user)

            assert "BOX-0001" in text
            assert "Test Box" in text
            assert "Garage" in text
            assert "Hammer" in text
            assert "x2" in text
            assert "tools" in text

    async def test_text_contains_summary_stats(self, mock_db, mock_user):
        """Should include summary statistics in text report."""
        with patch.object(report_service, "_fetch_report_data") as mock_fetch:
            mock_fetch.return_value = [
                {
                    "box_code": "BOX-0001",
                    "name": "Box 1",
                    "items": [{"name": "Item1", "quantity": 3, "tags": []}],
                },
                {
                    "box_code": "BOX-0002",
                    "name": "Box 2",
                    "items": [{"name": "Item2", "quantity": 5, "tags": []}],
                },
            ]

            request = ReportRequest()
            text = await report_service.generate_text_report(mock_db, request, mock_user)

            assert "2 boxes" in text
            assert "2 items" in text
            assert "8 qty" in text

    async def test_text_handles_empty_boxes(self, mock_db, mock_user):
        """Should handle boxes with no items."""
        with patch.object(report_service, "_fetch_report_data") as mock_fetch:
            mock_fetch.return_value = [{
                "box_code": "BOX-0001",
                "name": "Empty Box",
                "items": [],
            }]

            request = ReportRequest()
            text = await report_service.generate_text_report(mock_db, request, mock_user)

            assert "(no items)" in text


@pytest.mark.asyncio
class TestGenerateCsvReport:
    async def test_generates_csv_with_boxes(self, mock_db, mock_user):
        """Should generate CSV report with box data."""
        with patch.object(report_service, "_fetch_report_data") as mock_fetch:
            mock_fetch.return_value = [{
                "box_code": "BOX-0001",
                "name": "Test Box",
                "latitude": 47.6062,
                "longitude": -122.3321,
                "location_name": "Seattle",
                "items": [{"name": "Cable", "quantity": 3, "tags": ["tech", "cables"]}],
            }]

            request = ReportRequest()
            csv = await report_service.generate_csv_report(mock_db, request, mock_user)

            assert "Box Code,Box Name,Location,Latitude,Longitude,Item,Quantity,Tags" in csv
            assert "BOX-0001" in csv
            assert "Test Box" in csv
            assert "Cable" in csv
            assert "3" in csv
            assert "tech; cables" in csv

    async def test_csv_handles_empty_boxes(self, mock_db, mock_user):
        """Should include empty boxes in CSV."""
        with patch.object(report_service, "_fetch_report_data") as mock_fetch:
            mock_fetch.return_value = [{
                "box_code": "BOX-0002",
                "name": "Empty",
                "location_name": "Basement",
                "items": [],
            }]

            request = ReportRequest()
            csv = await report_service.generate_csv_report(mock_db, request, mock_user)

            assert "BOX-0002,Empty,Basement" in csv
