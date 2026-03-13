"""Unit tests for OAuth configuration fields in config.py."""
import pytest


def _reload_config_module():
    """Re-import config module to pick up new env vars."""
    import importlib
    import app.config
    importlib.reload(app.config)
    return app.config


@pytest.fixture
def _oauth_env(monkeypatch):
    """Set OAuth environment variables."""
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")


@pytest.fixture
def _custom_jwt_env(monkeypatch):
    """Set custom JWT configuration."""
    monkeypatch.setenv("JWT_ALGORITHM", "HS512")
    monkeypatch.setenv("JWT_EXPIRATION_MINUTES", "1440")  # 1 day


class TestOAuthConfig:
    """Test OAuth configuration defaults and environment loading."""

    def test_google_client_id_defaults_to_empty(self, monkeypatch):
        """Should default to empty string when not configured."""
        monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
        config = _reload_config_module()
        assert config.settings.google_client_id == ""

    def test_google_client_secret_defaults_to_empty(self, monkeypatch):
        """Should default to empty string when not configured."""
        monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
        config = _reload_config_module()
        assert config.settings.google_client_secret == ""

    @pytest.mark.usefixtures("_oauth_env")
    def test_loads_oauth_from_environment(self):
        """Should load OAuth credentials from environment variables."""
        config = _reload_config_module()
        assert config.settings.google_client_id == "test-client-id"
        assert config.settings.google_client_secret == "test-client-secret"


class TestJWTConfig:
    """Test JWT configuration defaults and environment loading."""

    def test_jwt_algorithm_defaults_to_hs256(self, monkeypatch):
        """Should default to HS256 algorithm."""
        monkeypatch.delenv("JWT_ALGORITHM", raising=False)
        config = _reload_config_module()
        assert config.settings.jwt_algorithm == "HS256"

    def test_jwt_expiration_defaults_to_7_days(self, monkeypatch):
        """Should default to 7 days (10080 minutes)."""
        monkeypatch.delenv("JWT_EXPIRATION_MINUTES", raising=False)
        config = _reload_config_module()
        assert config.settings.jwt_expiration_minutes == 60 * 24 * 7

    @pytest.mark.usefixtures("_custom_jwt_env")
    def test_loads_jwt_config_from_environment(self):
        """Should load JWT configuration from environment variables."""
        config = _reload_config_module()
        assert config.settings.jwt_algorithm == "HS512"
        assert config.settings.jwt_expiration_minutes == 1440


class TestSecretKeyConfig:
    """Test secret key configuration."""

    def test_secret_key_defaults_to_dev_value(self, monkeypatch):
        """Should have a default development secret key."""
        monkeypatch.delenv("SECRET_KEY", raising=False)
        config = _reload_config_module()
        assert config.settings.secret_key == "dev-secret-key"

    def test_loads_secret_key_from_environment(self, monkeypatch):
        """Should load secret key from environment variable."""
        monkeypatch.setenv("SECRET_KEY", "production-secret-key-xyz")
        config = _reload_config_module()
        assert config.settings.secret_key == "production-secret-key-xyz"


class TestAppBaseUrlConfig:
    """Test app base URL configuration."""

    def test_app_base_url_defaults_to_localhost(self, monkeypatch):
        """Should default to localhost for development."""
        monkeypatch.delenv("APP_BASE_URL", raising=False)
        config = _reload_config_module()
        assert config.settings.app_base_url == "http://localhost"

    def test_loads_app_base_url_from_environment(self, monkeypatch):
        """Should load app base URL from environment variable."""
        monkeypatch.setenv("APP_BASE_URL", "https://boxes.example.com")
        config = _reload_config_module()
        assert config.settings.app_base_url == "https://boxes.example.com"
