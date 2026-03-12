import ssl as ssl_module

import pytest


@pytest.fixture
def _production_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host:5432/db")
    monkeypatch.delenv("DB_CA_CERT_PATH", raising=False)


@pytest.fixture
def _development_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host:5432/db")


def _reload_database_module():
    """Re-import database module to pick up new env vars."""
    import importlib

    import app.config
    importlib.reload(app.config)

    import app.database
    importlib.reload(app.database)
    return app.database


def _reload_config_module():
    """Re-import config module to pick up new env vars."""
    import importlib

    import app.config
    importlib.reload(app.config)
    return app.config


@pytest.mark.usefixtures("_production_env")
class TestProductionSSL:
    def test_ssl_context_is_set(self):
        db = _reload_database_module()
        ssl_ctx = db.connect_args.get("ssl")
        assert ssl_ctx is not None
        assert isinstance(ssl_ctx, ssl_module.SSLContext)

    def test_ssl_verifies_certificates(self):
        db = _reload_database_module()
        ssl_ctx = db.connect_args["ssl"]
        assert ssl_ctx.verify_mode == ssl_module.CERT_REQUIRED
        assert ssl_ctx.check_hostname is True

    def test_custom_ca_cert_loaded(self, tmp_path, monkeypatch):
        import subprocess

        cert_path = tmp_path / "ca-certificate.crt"
        subprocess.run(
            [
                "openssl", "req", "-x509", "-newkey", "rsa:2048",
                "-keyout", str(tmp_path / "key.pem"),
                "-out", str(cert_path),
                "-days", "1", "-nodes",
                "-subj", "/CN=test",
            ],
            check=True,
            capture_output=True,
        )

        loaded_paths = []
        original = ssl_module.SSLContext.load_verify_locations

        def recording_load(self, *args, **kwargs):
            loaded_paths.append(args[0] if args else kwargs.get("cafile"))
            return original(self, *args, **kwargs)

        monkeypatch.setattr(ssl_module.SSLContext, "load_verify_locations", recording_load)
        monkeypatch.setenv("DB_CA_CERT_PATH", str(cert_path))
        db = _reload_database_module()
        ssl_ctx = db.connect_args["ssl"]
        assert ssl_ctx.verify_mode == ssl_module.CERT_REQUIRED
        assert str(cert_path) in loaded_paths

    def test_empty_string_ca_cert_path_does_not_load(self, monkeypatch):
        """Empty string for DB_CA_CERT_PATH should not attempt to load certificates."""
        monkeypatch.setenv("DB_CA_CERT_PATH", "")
        db = _reload_database_module()
        ssl_ctx = db.connect_args["ssl"]
        # Should still have a valid SSL context with default verification
        assert ssl_ctx.verify_mode == ssl_module.CERT_REQUIRED
        assert ssl_ctx.check_hostname is True

    def test_invalid_cert_path_raises_error(self, monkeypatch):
        """Non-existent certificate path should raise a RuntimeError."""
        monkeypatch.setenv("DB_CA_CERT_PATH", "/nonexistent/path/to/cert.pem")
        with pytest.raises(RuntimeError, match="CA certificate not found"):
            _reload_database_module()

    def test_invalid_cert_content_raises_error(self, tmp_path, monkeypatch):
        """File with invalid certificate content should raise a RuntimeError."""
        invalid_cert = tmp_path / "invalid.crt"
        invalid_cert.write_text("This is not a valid certificate")
        monkeypatch.setenv("DB_CA_CERT_PATH", str(invalid_cert))
        with pytest.raises(RuntimeError, match="Invalid database CA certificate"):
            _reload_database_module()

    def test_ssl_protocol_is_secure(self):
        """Verify that a secure TLS protocol version is used."""
        db = _reload_database_module()
        ssl_ctx = db.connect_args["ssl"]
        # create_default_context uses secure protocol by default (TLS 1.2+)
        # Verify it's not SSLv2, SSLv3, or TLSv1.0
        assert ssl_ctx.protocol in (
            ssl_module.PROTOCOL_TLS,
            ssl_module.PROTOCOL_TLS_CLIENT,
        )

    def test_ssl_context_has_no_insecure_options(self):
        """Verify SSL context does not have insecure options enabled."""
        db = _reload_database_module()
        ssl_ctx = db.connect_args["ssl"]
        # create_default_context should have secure defaults
        # Check that it disables old SSL versions
        options = ssl_ctx.options
        # SSLv2 is not available in modern OpenSSL (OP_NO_SSLv2 = 0)
        # SSLv3 should be disabled
        assert options & ssl_module.OP_NO_SSLv3
        # Also verify minimum TLS version is set (if available)
        if hasattr(ssl_ctx, "minimum_version"):
            # Should be at least TLS 1.2
            assert ssl_ctx.minimum_version >= ssl_module.TLSVersion.TLSv1_2


@pytest.mark.usefixtures("_development_env")
class TestDevelopmentSSL:
    def test_no_ssl_in_development(self):
        db = _reload_database_module()
        assert "ssl" not in db.connect_args


class TestConfigDefaults:
    def test_db_ca_cert_path_defaults_to_empty_string(self, monkeypatch):
        """Verify db_ca_cert_path has a secure default (empty string)."""
        # Clear any existing env var
        monkeypatch.delenv("DB_CA_CERT_PATH", raising=False)
        config = _reload_config_module()
        assert config.settings.db_ca_cert_path == ""

    def test_db_ca_cert_path_from_env(self, monkeypatch):
        """Verify db_ca_cert_path can be set from environment variable."""
        test_path = "/path/to/cert.pem"
        monkeypatch.setenv("DB_CA_CERT_PATH", test_path)
        config = _reload_config_module()
        assert config.settings.db_ca_cert_path == test_path

    def test_app_env_defaults_to_development(self, monkeypatch):
        """Verify app_env has a safe default."""
        monkeypatch.delenv("APP_ENV", raising=False)
        config = _reload_config_module()
        assert config.settings.app_env == "development"


class TestNonProductionEnvironments:
    def test_staging_environment_no_ssl(self, monkeypatch):
        """Staging environment should not enable SSL (only production)."""
        monkeypatch.setenv("APP_ENV", "staging")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host:5432/db")
        db = _reload_database_module()
        assert "ssl" not in db.connect_args

    def test_testing_environment_no_ssl(self, monkeypatch):
        """Testing environment should not enable SSL (only production)."""
        monkeypatch.setenv("APP_ENV", "testing")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host:5432/db")
        db = _reload_database_module()
        assert "ssl" not in db.connect_args

    def test_arbitrary_environment_no_ssl(self, monkeypatch):
        """Any non-production environment should not enable SSL."""
        monkeypatch.setenv("APP_ENV", "local-docker")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host:5432/db")
        db = _reload_database_module()
        assert "ssl" not in db.connect_args


class TestSSLContextReuse:
    @pytest.mark.usefixtures("_production_env")
    def test_multiple_reloads_create_new_contexts(self, monkeypatch):
        """Each reload should create a new SSL context instance."""
        db1 = _reload_database_module()
        ssl_ctx1 = db1.connect_args["ssl"]

        db2 = _reload_database_module()
        ssl_ctx2 = db2.connect_args["ssl"]

        # They should be different instances but with same config
        assert ssl_ctx1 is not ssl_ctx2
        assert ssl_ctx1.verify_mode == ssl_ctx2.verify_mode
        assert ssl_ctx1.check_hostname == ssl_ctx2.check_hostname


