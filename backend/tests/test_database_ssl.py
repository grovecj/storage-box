import ssl as ssl_module

import pytest


@pytest.fixture
def _production_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host:5432/db")


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
        monkeypatch.setenv("DB_CA_CERT_PATH", str(cert_path))
        db = _reload_database_module()
        ssl_ctx = db.connect_args["ssl"]
        assert ssl_ctx.verify_mode == ssl_module.CERT_REQUIRED


@pytest.mark.usefixtures("_development_env")
class TestDevelopmentSSL:
    def test_no_ssl_in_development(self):
        db = _reload_database_module()
        assert "ssl" not in db.connect_args
