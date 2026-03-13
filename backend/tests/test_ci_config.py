"""Test suite for CI tooling configuration.

Validates that linting and type checking tools are properly configured
and that configuration files have the correct structure.

NOTE: This test file only validates backend configuration files that are
accessible from the backend container. Frontend and CI workflow validation
is performed separately via the CI pipeline itself.
"""

import subprocess
from pathlib import Path


class TestBackendToolConfiguration:
    """Validate backend linting and type checking tools."""

    def test_pyproject_toml_exists(self):
        """pyproject.toml must exist in backend directory."""
        config_path = Path(__file__).parent.parent / "pyproject.toml"
        assert config_path.exists(), "pyproject.toml not found"

    def test_ruff_configuration_present(self):
        """pyproject.toml must contain [tool.ruff] section."""
        config_path = Path(__file__).parent.parent / "pyproject.toml"
        content = config_path.read_text()
        assert "[tool.ruff]" in content, "Ruff configuration section missing"
        assert "target-version" in content, "Ruff target-version not set"

    def test_ruff_lint_rules_configured(self):
        """Ruff must have linting rules configured."""
        config_path = Path(__file__).parent.parent / "pyproject.toml"
        content = config_path.read_text()
        assert "[tool.ruff.lint]" in content, "Ruff lint section missing"
        assert "select =" in content, "Ruff lint rules not configured"
        # Verify essential rule sets are enabled
        assert '"E"' in content, "Pycodestyle errors not enabled"
        assert '"F"' in content, "Pyflakes not enabled"

    def test_ruff_isort_configuration(self):
        """Ruff must have isort configuration for import sorting."""
        config_path = Path(__file__).parent.parent / "pyproject.toml"
        content = config_path.read_text()
        assert "[tool.ruff.lint.isort]" in content, "Ruff isort section missing"
        assert '"I"' in content, "Isort rule not enabled in select"

    def test_mypy_configuration_present(self):
        """pyproject.toml must contain [tool.mypy] section."""
        config_path = Path(__file__).parent.parent / "pyproject.toml"
        content = config_path.read_text()
        assert "[tool.mypy]" in content, "Mypy configuration section missing"
        assert 'python_version = "3.12"' in content, "Mypy Python version not set"

    def test_mypy_strict_settings_configured(self):
        """Mypy must have strict type checking settings."""
        config_path = Path(__file__).parent.parent / "pyproject.toml"
        content = config_path.read_text()
        assert "warn_return_any" in content, "Mypy warn_return_any not set"
        assert "strict_equality" in content, "Mypy strict_equality not set"
        assert "warn_unused_ignores" in content, "Mypy warn_unused_ignores not set"
        assert "warn_no_return" in content, "Mypy warn_no_return not set"

    def test_mypy_has_override_for_missing_stubs(self):
        """Mypy must have overrides for third-party libraries without stubs."""
        config_path = Path(__file__).parent.parent / "pyproject.toml"
        content = config_path.read_text()
        assert "[[tool.mypy.overrides]]" in content, "Mypy overrides section missing"
        assert "ignore_missing_imports = true" in content, "Mypy ignore_missing_imports not set"

    def test_requirements_include_ruff(self):
        """requirements.txt must include ruff."""
        reqs_path = Path(__file__).parent.parent / "requirements.txt"
        content = reqs_path.read_text()
        assert "ruff==" in content, "ruff not in requirements.txt"

    def test_requirements_include_mypy(self):
        """requirements.txt must include mypy."""
        reqs_path = Path(__file__).parent.parent / "requirements.txt"
        content = reqs_path.read_text()
        assert "mypy==" in content, "mypy not in requirements.txt"

    def test_pytest_configuration_present(self):
        """pyproject.toml must contain pytest configuration."""
        config_path = Path(__file__).parent.parent / "pyproject.toml"
        content = config_path.read_text()
        assert "[tool.pytest.ini_options]" in content, "Pytest configuration missing"
        assert "asyncio_mode" in content, "Pytest asyncio_mode not configured"


class TestToolsExecutable:
    """Verify that all linting tools can be executed successfully on the codebase."""

    def test_ruff_runs_successfully(self):
        """Ruff must run without errors on current codebase."""
        app_dir = Path(__file__).parent.parent / "app"
        result = subprocess.run(
            ["ruff", "check", str(app_dir)],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Ruff check failed: {result.stdout}\n{result.stderr}"

    def test_mypy_runs_successfully(self):
        """Mypy must run without errors on current codebase."""
        app_dir = Path(__file__).parent.parent / "app"
        result = subprocess.run(
            ["mypy", str(app_dir)],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Mypy check failed: {result.stdout}\n{result.stderr}"

    def test_ruff_version_check(self):
        """Ruff must be installed and executable."""
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "Ruff is not installed or not executable"
        assert "ruff" in result.stdout.lower(), "Unexpected ruff version output"

    def test_mypy_version_check(self):
        """Mypy must be installed and executable."""
        result = subprocess.run(
            ["mypy", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "Mypy is not installed or not executable"
        assert "mypy" in result.stdout.lower(), "Unexpected mypy version output"
