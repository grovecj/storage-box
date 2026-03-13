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


@pytest.mark.asyncio
class TestAuditRouter:
    async def test_get_audit_log_returns_paginated_logs(self, override_dependencies, mock_current_user):
        """Should return paginated audit logs for a box."""
        from app.models.audit import AuditLog

        mock_box = MagicMock()
        mock_box.id = 1
        mock_box.owner_id = mock_current_user.id

        mock_log1 = MagicMock(spec=AuditLog)
        mock_log1.id = 1
        mock_log1.action = "box_created"
        mock_log1.details = {"box_code": "BOX-0001"}
        mock_log1.created_at = NOW

        mock_log2 = MagicMock(spec=AuditLog)
        mock_log2.id = 2
        mock_log2.action = "item_added"
        mock_log2.details = {"box_code": "BOX-0001", "item_name": "Cable"}
        mock_log2.created_at = NOW

        async def _get_db():
            db = AsyncMock()

            # First query: check box ownership
            box_result = MagicMock()
            box_result.scalar_one_or_none.return_value = mock_box

            # Second query: count logs
            count_result = MagicMock()
            count_result.scalar.return_value = 2

            # Third query: fetch logs
            logs_result = MagicMock()
            logs_result.scalars.return_value.all.return_value = [mock_log1, mock_log2]

            db.execute.side_effect = [box_result, count_result, logs_result]
            yield db

        app.dependency_overrides[get_db] = _get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/boxes/1/audit-log?page=1&page_size=20")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert data["page"] == 1
            assert data["page_size"] == 20
            assert len(data["logs"]) == 2
            assert data["logs"][0]["action"] == "box_created"
            assert data["logs"][1]["action"] == "item_added"

        app.dependency_overrides.clear()

    async def test_get_audit_log_returns_404_for_nonexistent_box(self, override_dependencies):
        """Should return 404 if box doesn't exist or user doesn't own it."""
        async def _get_db():
            db = AsyncMock()
            # Mock box ownership check returning None
            box_result = MagicMock()
            box_result.scalar_one_or_none.return_value = None
            db.execute.return_value = box_result
            yield db

        app.dependency_overrides[get_db] = _get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/boxes/999/audit-log")

            assert response.status_code == 404
            assert response.json()["detail"] == "Box not found"

        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestTagsRouter:
    async def test_list_tags(self, override_dependencies):
        """Should return list of all tags."""
        from app.models.tag import Tag

        mock_tag1 = MagicMock(spec=Tag)
        mock_tag1.id = 1
        mock_tag1.name = "kitchen"
        mock_tag1.created_at = NOW
        mock_tag1.updated_at = NOW

        mock_tag2 = MagicMock(spec=Tag)
        mock_tag2.id = 2
        mock_tag2.name = "winter"
        mock_tag2.created_at = NOW
        mock_tag2.updated_at = NOW

        async def _get_db():
            db = AsyncMock()
            result = MagicMock()
            result.scalars.return_value.all.return_value = [mock_tag1, mock_tag2]
            db.execute.return_value = result
            yield db

        app.dependency_overrides[get_db] = _get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/tags")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "kitchen"
            assert data[1]["name"] == "winter"

        app.dependency_overrides.clear()

    async def test_create_tag(self, override_dependencies, mock_current_user):
        """Should create a new tag."""
        from app.models.tag import Tag

        async def _get_db():
            db = AsyncMock()

            # First query: check if tag exists
            existing_result = MagicMock()
            existing_result.scalar_one_or_none.return_value = None
            db.execute.return_value = existing_result

            # Mock the new tag that will be returned after refresh
            new_tag = MagicMock(spec=Tag)
            new_tag.id = 1
            new_tag.name = "cables"
            new_tag.created_at = NOW
            new_tag.updated_at = NOW

            async def mock_refresh(tag):
                tag.id = new_tag.id
                tag.name = new_tag.name
                tag.created_at = new_tag.created_at
                tag.updated_at = new_tag.updated_at

            db.refresh = mock_refresh
            yield db

        app.dependency_overrides[get_db] = _get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/tags",
                json={"name": "cables"}
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "cables"

        app.dependency_overrides.clear()

    async def test_create_tag_returns_409_for_duplicate(self, override_dependencies):
        """Should return 409 if tag already exists."""
        from app.models.tag import Tag

        async def _get_db():
            db = AsyncMock()

            # Mock existing tag found
            existing_tag = MagicMock(spec=Tag)
            existing_tag.id = 1
            existing_tag.name = "kitchen"

            existing_result = MagicMock()
            existing_result.scalar_one_or_none.return_value = existing_tag
            db.execute.return_value = existing_result
            yield db

        app.dependency_overrides[get_db] = _get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/tags",
                json={"name": "kitchen"}
            )

            assert response.status_code == 409
            assert response.json()["detail"] == "Tag already exists"

        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_health_check(self, override_dependencies):
        """Should return health status."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
