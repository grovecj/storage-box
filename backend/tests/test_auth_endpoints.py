"""Tests for auth endpoints and auth enforcement.

Uses mocked dependencies to avoid database connection pool issues.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from fastapi import HTTPException
from app.dependencies import get_current_user, get_current_user_optional
from app.models.user import User
from app.services import auth_service
from app.config import settings


# ---------------------------------------------------------------------------
# Helper: create a mock User
# ---------------------------------------------------------------------------

def _make_user(id=1, google_id="google-123", email="test@example.com", name="Test User"):
    user = MagicMock(spec=User)
    user.id = id
    user.google_id = google_id
    user.email = email
    user.name = name
    user.picture_url = None
    user.created_at = datetime(2024, 1, 1)
    user.updated_at = datetime(2024, 1, 1)
    return user


# ---------------------------------------------------------------------------
# Dependencies tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestGetCurrentUserDependency:
    async def test_raises_401_when_no_credentials(self):
        """Should raise 401 when no Bearer token is provided."""
        mock_db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=None, db=mock_db)
        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail

    async def test_raises_401_when_token_invalid(self):
        """Should raise 401 when token is invalid."""
        mock_db = AsyncMock()
        mock_creds = MagicMock()
        mock_creds.credentials = "invalid-token"

        with patch.object(auth_service, "get_current_user", return_value=None) as mock_auth:
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=mock_creds, db=mock_db)
            assert exc_info.value.status_code == 401
            mock_auth.assert_called_once_with(mock_db, "invalid-token")

    async def test_returns_user_when_token_valid(self):
        """Should return user when token is valid."""
        mock_db = AsyncMock()
        mock_creds = MagicMock()
        mock_creds.credentials = "valid-token"
        user = _make_user()

        with patch.object(auth_service, "get_current_user", return_value=user):
            result = await get_current_user(credentials=mock_creds, db=mock_db)
            assert result == user


@pytest.mark.asyncio
class TestGetCurrentUserOptionalDependency:
    async def test_returns_none_when_no_credentials(self):
        """Should return None when no Bearer token is provided."""
        mock_db = AsyncMock()
        result = await get_current_user_optional(credentials=None, db=mock_db)
        assert result is None

    async def test_returns_none_when_token_invalid(self):
        """Should return None (not raise) when token is invalid."""
        mock_db = AsyncMock()
        mock_creds = MagicMock()
        mock_creds.credentials = "bad-token"

        with patch.object(auth_service, "get_current_user", return_value=None):
            result = await get_current_user_optional(credentials=mock_creds, db=mock_db)
            assert result is None

    async def test_returns_user_when_token_valid(self):
        """Should return user when token is valid."""
        mock_db = AsyncMock()
        mock_creds = MagicMock()
        mock_creds.credentials = "valid-token"
        user = _make_user()

        with patch.object(auth_service, "get_current_user", return_value=user):
            result = await get_current_user_optional(credentials=mock_creds, db=mock_db)
            assert result == user


# ---------------------------------------------------------------------------
# Auth service: get_or_create_user
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestGetOrCreateUser:
    async def test_creates_new_user(self):
        """Should create a new user if none exists with that google_id."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        google_info = {
            "sub": "google-new-123",
            "email": "new@example.com",
            "name": "New User",
            "picture": "https://example.com/pic.jpg",
        }

        # Patch the User constructor to return a mock
        user = await auth_service.get_or_create_user(mock_db, google_info)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_updates_existing_user(self):
        """Should update an existing user's info."""
        existing_user = _make_user()
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_db.execute.return_value = mock_result

        google_info = {
            "sub": "google-123",
            "email": "updated@example.com",
            "name": "Updated Name",
            "picture": "https://example.com/new-pic.jpg",
        }

        await auth_service.get_or_create_user(mock_db, google_info)
        assert existing_user.email == "updated@example.com"
        assert existing_user.name == "Updated Name"
        mock_db.commit.assert_called_once()

    async def test_uses_id_field_as_fallback(self):
        """Should fall back to 'id' field if 'sub' is missing."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        google_info = {
            "id": "alt-google-id",
            "email": "alt@example.com",
            "name": "Alt User",
        }

        await auth_service.get_or_create_user(mock_db, google_info)
        mock_db.add.assert_called_once()


# ---------------------------------------------------------------------------
# Auth service: create_dev_user
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestCreateDevUser:
    async def test_creates_dev_user_if_not_exists(self):
        """Should create a dev user with google_id='dev-user'."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        await auth_service.create_dev_user(mock_db)
        mock_db.add.assert_called_once()
        added_user = mock_db.add.call_args[0][0]
        assert added_user.google_id == "dev-user"
        assert added_user.email == "dev@localhost"

    async def test_returns_existing_dev_user(self):
        """Should return the existing dev user without creating a new one."""
        existing_user = _make_user(google_id="dev-user", email="dev@localhost")
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_db.execute.return_value = mock_result

        result = await auth_service.create_dev_user(mock_db)
        assert result == existing_user
        mock_db.add.assert_not_called()


# ---------------------------------------------------------------------------
# Auth service: get_current_user (token decode + db lookup)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestGetCurrentUserFromToken:
    async def test_valid_token_looks_up_user(self):
        """Should decode token and query the database for the user."""
        user = _make_user(id=42)
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db.execute.return_value = mock_result

        token = auth_service.create_access_token(42)
        result = await auth_service.get_current_user(mock_db, token)
        assert result == user
        # Verify the DB was queried
        mock_db.execute.assert_called_once()

    async def test_valid_token_nonexistent_user_returns_none(self):
        """Should return None if user_id from token doesn't exist in DB."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        token = auth_service.create_access_token(99999)
        result = await auth_service.get_current_user(mock_db, token)
        assert result is None


# ---------------------------------------------------------------------------
# Auth router: google endpoint behavior
# ---------------------------------------------------------------------------

class TestGoogleLoginEndpoint:
    def test_raises_503_without_oauth_config(self):
        """The /auth/google endpoint raises 503 when OAuth is not configured."""
        from app.routers.auth import google_login
        import asyncio

        async def _run():
            # settings.google_client_id is "" in dev
            with pytest.raises(HTTPException) as exc_info:
                await google_login()
            assert exc_info.value.status_code == 503

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_run())
        finally:
            loop.close()


class TestDevTokenEndpointLogic:
    def test_raises_403_when_oauth_configured(self, monkeypatch):
        """The /auth/dev-token should return 403 when OAuth IS configured."""
        from app.routers import auth as auth_module
        import asyncio

        # Patch the settings object used by the auth module directly
        monkeypatch.setattr(auth_module.settings, "google_client_id", "real-id")
        monkeypatch.setattr(auth_module.settings, "google_client_secret", "real-secret")

        async def _run():
            mock_db = AsyncMock()
            with pytest.raises(HTTPException) as exc_info:
                await auth_module.get_dev_token(db=mock_db)
            assert exc_info.value.status_code == 403

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_run())
        finally:
            loop.close()
