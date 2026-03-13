"""Test suite for CI tooling configuration.

Validates that linting and type checking tools are properly configured
and that configuration files have the correct structure.
"""

import tomllib
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent
PYPROJECT = BACKEND_DIR / "pyproject.toml"
REQUIREMENTS = BACKEND_DIR / "requirements.txt"


def _load_pyproject() -> dict:
    return tomllib.loads(PYPROJECT.read_text())


class TestRuffConfiguration:
    """Validate Ruff linting configuration."""

    def test_target_version(self):
        config = _load_pyproject()["tool"]["ruff"]
        assert config["target-version"] == "py312"

    def test_lint_rules_configured(self):
        rules = _load_pyproject()["tool"]["ruff"]["lint"]["select"]
        for required in ("E", "F", "I", "UP", "B", "SIM"):
            assert required in rules, f"Rule set {required!r} not enabled"

    def test_isort_first_party(self):
        isort = _load_pyproject()["tool"]["ruff"]["lint"]["isort"]
        assert "app" in isort["known-first-party"]


class TestMypyConfiguration:
    """Validate mypy type checking configuration."""

    def test_python_version(self):
        config = _load_pyproject()["tool"]["mypy"]
        assert config["python_version"] == "3.12"

    def test_strict_settings(self):
        config = _load_pyproject()["tool"]["mypy"]
        assert config["warn_return_any"] is True
        assert config["strict_equality"] is True
        assert config["warn_unused_ignores"] is True
        assert config["warn_no_return"] is True
        assert config["check_untyped_defs"] is True

    def test_third_party_overrides(self):
        overrides = _load_pyproject()["tool"]["mypy"]["overrides"]
        ignored_modules = []
        for override in overrides:
            if override.get("ignore_missing_imports"):
                ignored_modules.extend(override["module"])
        assert any("geoalchemy2" in m for m in ignored_modules)
        assert any("weasyprint" in m for m in ignored_modules)


class TestRequirements:
    """Validate dev tool dependencies are pinned."""

    def test_ruff_in_requirements(self):
        content = REQUIREMENTS.read_text()
        assert "ruff==" in content

    def test_mypy_in_requirements(self):
        content = REQUIREMENTS.read_text()
        assert "mypy==" in content


class TestPytestConfiguration:
    """Validate pytest configuration."""

    def test_asyncio_mode(self):
        config = _load_pyproject()["tool"]["pytest"]["ini_options"]
        assert config["asyncio_mode"] == "auto"
