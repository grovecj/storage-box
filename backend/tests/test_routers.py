"""Integration tests for API routers."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.dependencies import get_db, get_current_user
from app.schemas.box import BoxResponse, BoxListResponse
from app.schemas.item import BoxItemResponse, BoxItemListResponse
from app.schemas.transfer import TransferResponse


# Helper to create timestamps
NOW = datetime(2024, 1, 1)


@pytest.fixture
def mock_current_user():
    """Mock user for dependency override."""
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    user.name = "Test User"
    return user


@pytest.fixture
def override_dependencies(mock_current_user):
    """Override FastAPI dependencies."""
    async def _get_current_user():
        return mock_current_user

    async def _get_db():
        yield AsyncMock()

    app.dependency_overrides[get_current_user] = _get_current_user
    app.dependency_overrides[get_db] = _get_db

    yield

    app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestBoxesRouter:
    async def test_create_box(self, override_dependencies):
        """Should create a new box."""
        mock_response = BoxResponse(
            id=1,
            box_code="BOX-0001",
            name="My Box",
            location_name="Garage",
            item_count=0,
            created_at=NOW,
            updated_at=NOW,
        )

        with patch("app.routers.boxes.box_service.create_box", return_value=mock_response):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/boxes",
                    json={"name": "My Box", "location_name": "Garage"}
                )

                assert response.status_code == 201
                assert response.json()["box_code"] == "BOX-0001"

    async def test_list_boxes(self, override_dependencies):
        """Should list user's boxes."""
        mock_response = BoxListResponse(
            boxes=[
                BoxResponse(id=1, box_code="BOX-0001", name="Box 1", item_count=5, created_at=NOW, updated_at=NOW),
                BoxResponse(id=2, box_code="BOX-0002", name="Box 2", item_count=3, created_at=NOW, updated_at=NOW),
            ],
            total=2,
            page=1,
            page_size=20,
        )

        with patch("app.routers.boxes.box_service.list_boxes", return_value=mock_response):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/boxes")

                assert response.status_code == 200
                data = response.json()
                assert data["total"] == 2
                assert len(data["boxes"]) == 2

    async def test_get_box_by_id(self, override_dependencies):
        """Should get box by ID."""
        mock_response = BoxResponse(
            id=1,
            box_code="BOX-0001",
            name="Test Box",
            item_count=10,
            created_at=NOW,
            updated_at=NOW,
        )

        with patch("app.routers.boxes.box_service.get_box", return_value=mock_response):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/boxes/1")

                assert response.status_code == 200
                assert response.json()["box_code"] == "BOX-0001"

    async def test_get_box_returns_404_if_not_found(self, override_dependencies):
        """Should return 404 if box doesn't exist."""
        with patch("app.routers.boxes.box_service.get_box", return_value=None):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/boxes/999")

                assert response.status_code == 404

    async def test_get_box_by_code(self, override_dependencies):
        """Should get box by code."""
        mock_response = BoxResponse(
            id=1,
            box_code="BOX-0001",
            name="Test Box",
            item_count=5,
            created_at=NOW,
            updated_at=NOW,
        )

        with patch("app.routers.boxes.box_service.get_box_by_code", return_value=mock_response):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/boxes/code/BOX-0001")

                assert response.status_code == 200
                assert response.json()["id"] == 1

    async def test_update_box(self, override_dependencies):
        """Should update box."""
        mock_response = BoxResponse(
            id=1,
            box_code="BOX-0001",
            name="Updated Name",
            item_count=5,
            created_at=NOW,
            updated_at=NOW,
        )

        with patch("app.routers.boxes.box_service.update_box", return_value=mock_response):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.put(
                    "/api/v1/boxes/1",
                    json={"name": "Updated Name"}
                )

                assert response.status_code == 200
                assert response.json()["name"] == "Updated Name"

    async def test_delete_box(self, override_dependencies):
        """Should delete box."""
        with patch("app.routers.boxes.box_service.delete_box", return_value={"box_code": "BOX-0001", "items_removed": 3}):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete("/api/v1/boxes/1")

                assert response.status_code == 200
                data = response.json()
                assert data["box_code"] == "BOX-0001"
                assert data["items_removed"] == 3


@pytest.mark.asyncio
class TestItemsRouter:
    async def test_list_items(self, override_dependencies):
        """Should list items in a box."""
        mock_response = BoxItemListResponse(
            items=[
                BoxItemResponse(id=1, item_id=1, name="Item 1", quantity=5, tags=[], created_at=NOW, updated_at=NOW),
                BoxItemResponse(id=2, item_id=2, name="Item 2", quantity=3, tags=["test"], created_at=NOW, updated_at=NOW),
            ],
            total=2,
            page=1,
            page_size=10,
        )

        with patch("app.routers.items.item_service.list_items", return_value=mock_response):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/boxes/1/items")

                assert response.status_code == 200
                data = response.json()
                assert len(data["items"]) == 2

    async def test_list_items_returns_404_for_unauthorized_box(self, override_dependencies):
        """Should return 404 if user doesn't own box."""
        with patch("app.routers.items.item_service.list_items", return_value=None):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/boxes/999/items")

                assert response.status_code == 404

    async def test_add_item(self, override_dependencies):
        """Should add item to box."""
        mock_response = BoxItemResponse(
            id=1,
            item_id=1,
            name="New Item",
            quantity=3,
            tags=["test"],
            created_at=NOW,
            updated_at=NOW,
        )

        with patch("app.routers.items.item_service.add_item", return_value=mock_response):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/boxes/1/items",
                    json={"name": "New Item", "quantity": 3, "tags": ["test"]}
                )

                assert response.status_code == 201
                assert response.json()["name"] == "New Item"

    async def test_add_item_returns_400_on_error(self, override_dependencies):
        """Should return 400 on validation error."""
        with patch("app.routers.items.item_service.add_item", side_effect=ValueError("Box at limit")):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/boxes/1/items",
                    json={"name": "Item", "quantity": 1, "tags": []}
                )

                assert response.status_code == 400

    async def test_update_item(self, override_dependencies):
        """Should update item."""
        mock_response = BoxItemResponse(
            id=1,
            item_id=1,
            name="Item",
            quantity=10,
            tags=["updated"],
            created_at=NOW,
            updated_at=NOW,
        )

        with patch("app.routers.items.item_service.update_item", return_value=mock_response):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.put(
                    "/api/v1/boxes/1/items/1",
                    json={"quantity": 10, "tags": ["updated"]}
                )

                assert response.status_code == 200
                assert response.json()["quantity"] == 10

    async def test_delete_item(self, override_dependencies):
        """Should delete item."""
        with patch("app.routers.items.item_service.remove_item", return_value=True):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete("/api/v1/boxes/1/items/1")

                assert response.status_code == 200
                assert response.json()["message"] == "Item removed"


@pytest.mark.asyncio
class TestTransfersRouter:
    async def test_transfer_item(self, override_dependencies):
        """Should transfer item between boxes."""
        mock_response = TransferResponse(
            message="Transferred 3x Cable",
            from_box_code="BOX-0001",
            to_box_code="BOX-0002",
            item_name="Cable",
            quantity=3,
        )

        with patch("app.routers.transfers.transfer_service.transfer_item", return_value=mock_response):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/transfers",
                    json={
                        "from_box_id": 1,
                        "to_box_id": 2,
                        "item_id": 1,
                        "quantity": 3
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["quantity"] == 3
                assert data["from_box_code"] == "BOX-0001"

    async def test_transfer_returns_400_on_error(self, override_dependencies):
        """Should return 400 on validation error."""
        with patch("app.routers.transfers.transfer_service.transfer_item", side_effect=ValueError("Insufficient quantity")):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/transfers",
                    json={
                        "from_box_id": 1,
                        "to_box_id": 2,
                        "item_id": 1,
                        "quantity": 100
                    }
                )

                assert response.status_code == 400


@pytest.mark.asyncio
class TestSearchRouter:
    async def test_search(self, override_dependencies):
        """Should search boxes and items."""
        mock_response = {
            "boxes": [{"id": 1, "box_code": "BOX-0001", "name": "Test"}],
            "items": [{"id": 1, "name": "Cable", "box_code": "BOX-0001"}],
        }

        with patch("app.routers.search.search_service.search", return_value=mock_response):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/search?q=test")

                assert response.status_code == 200
                data = response.json()
                assert len(data["boxes"]) == 1
                assert len(data["items"]) == 1

    async def test_autocomplete(self, override_dependencies):
        """Should autocomplete item names."""
        mock_response = [
            {"id": 1, "name": "Cable"},
            {"id": 2, "name": "Cabbage"},
        ]

        with patch("app.routers.search.item_service.autocomplete_items", return_value=mock_response):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/search/autocomplete/items?q=cab")

                assert response.status_code == 200
                assert len(response.json()) == 2


@pytest.mark.asyncio
class TestReportsRouter:
    async def test_generate_html_report(self, override_dependencies):
        """Should generate HTML report."""
        with patch("app.routers.reports.report_service.generate_html_report", return_value="<html>Report</html>"):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/reports",
                    json={"format": "html"}
                )

                assert response.status_code == 200
                assert response.headers["content-type"] == "text/html; charset=utf-8"
                assert b"<html>Report</html>" in response.content

    async def test_generate_pdf_report(self, override_dependencies):
        """Should generate PDF report."""
        with patch("app.routers.reports.report_service.generate_pdf_report", return_value=b"PDF content"):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/reports",
                    json={"format": "pdf"}
                )

                assert response.status_code == 200
                assert response.headers["content-type"] == "application/pdf"

    async def test_generate_text_report(self, override_dependencies):
        """Should generate text report."""
        with patch("app.routers.reports.report_service.generate_text_report", return_value="Text report"):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/reports",
                    json={"format": "text"}
                )

                assert response.status_code == 200
                assert response.headers["content-type"] == "text/plain; charset=utf-8"

    async def test_generate_csv_report(self, override_dependencies):
        """Should generate CSV report."""
        with patch("app.routers.reports.report_service.generate_csv_report", return_value="box,name\nBOX-0001,Test"):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/reports",
                    json={"format": "csv"}
                )

                assert response.status_code == 200
                assert response.headers["content-type"] == "text/csv; charset=utf-8"


@pytest.mark.asyncio
class TestConfigRouter:
    async def test_get_config(self, override_dependencies):
        """Should return app config."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/config")

            assert response.status_code == 200
            data = response.json()
            assert "base_url" in data
            assert "auth_mode" in data
