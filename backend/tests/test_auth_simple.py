"""Simplified auth tests that focus on testable units without complex DB fixtures."""
import pytest
from datetime import datetime, timedelta
from jose import jwt
from app.services import auth_service
from app.config import settings
from unittest.mock import AsyncMock, MagicMock
from app.models.user import User


class TestJWTTokens:
    """Test JWT token creation and validation without database."""

    def test_creates_valid_jwt_token(self):
        """Should create a JWT token with correct structure."""
        user_id = 123
        token = auth_service.create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == str(user_id)
        assert "exp" in payload
        assert "iat" in payload

    def test_token_expiration_is_set(self):
        """Should set expiration time according to config."""
        user_id = 456
        before_creation = datetime.utcnow()
        token = auth_service.create_access_token(user_id)
        after_creation = datetime.utcnow()

        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])

        expected_exp = iat_time + timedelta(minutes=settings.jwt_expiration_minutes)
        assert abs((exp_time - expected_exp).total_seconds()) < 10

        assert before_creation - timedelta(seconds=2) <= iat_time <= after_creation + timedelta(seconds=2)

    def test_different_users_get_different_tokens(self):
        """Should create unique tokens for different users."""
        token1 = auth_service.create_access_token(1)
        token2 = auth_service.create_access_token(2)

        assert token1 != token2

        payload1 = jwt.decode(token1, settings.secret_key, algorithms=[settings.jwt_algorithm])
        payload2 = jwt.decode(token2, settings.secret_key, algorithms=[settings.jwt_algorithm])

        assert payload1["sub"] == "1"
        assert payload2["sub"] == "2"


@pytest.mark.asyncio
class TestTokenValidation:
    """Test JWT token validation."""

    async def test_expired_token_returns_none(self):
        """Should return None for expired token."""
        # Create mock database session
        mock_db = AsyncMock()

        # Create token that expired 1 hour ago
        expired_payload = {
            "sub": "123",
            "exp": datetime.utcnow() - timedelta(hours=1),
            "iat": datetime.utcnow() - timedelta(hours=2),
        }
        expired_token = jwt.encode(
            expired_payload,
            settings.secret_key,
            algorithm=settings.jwt_algorithm
        )

        user = await auth_service.get_current_user(mock_db, expired_token)
        assert user is None

    async def test_invalid_signature_returns_none(self):
        """Should return None for token with invalid signature."""
        mock_db = AsyncMock()

        payload = {
            "sub": "123",
            "exp": datetime.utcnow() + timedelta(hours=1),
        }
        bad_token = jwt.encode(payload, "wrong-secret", algorithm=settings.jwt_algorithm)

        user = await auth_service.get_current_user(mock_db, bad_token)
        assert user is None

    async def test_malformed_token_returns_none(self):
        """Should return None for malformed token."""
        mock_db = AsyncMock()
        user = await auth_service.get_current_user(mock_db, "not-a-jwt-token")
        assert user is None

    async def test_token_with_missing_sub_returns_none(self):
        """Should return None if token missing 'sub' claim."""
        mock_db = AsyncMock()

        payload = {
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

        user = await auth_service.get_current_user(mock_db, token)
        assert user is None

    async def test_token_with_invalid_user_id_returns_none(self):
        """Should return None if token has non-integer user_id."""
        mock_db = AsyncMock()

        payload = {
            "sub": "not-a-number",
            "exp": datetime.utcnow() + timedelta(hours=1),
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

        user = await auth_service.get_current_user(mock_db, token)
        assert user is None


@pytest.mark.asyncio
class TestUserCreation:
    """Test user creation from Google OAuth data."""

    async def test_missing_required_fields_raises_error(self):
        """Should raise ValueError if required fields are missing."""
        mock_db = AsyncMock()

        # Missing email
        with pytest.raises(ValueError, match="Invalid Google user info"):
            await auth_service.get_or_create_user(mock_db, {
                "sub": "123",
                "name": "Test",
            })

        # Missing name
        with pytest.raises(ValueError, match="Invalid Google user info"):
            await auth_service.get_or_create_user(mock_db, {
                "sub": "123",
                "email": "test@example.com",
            })

        # Missing google_id
        with pytest.raises(ValueError, match="Invalid Google user info"):
            await auth_service.get_or_create_user(mock_db, {
                "email": "test@example.com",
                "name": "Test",
            })
