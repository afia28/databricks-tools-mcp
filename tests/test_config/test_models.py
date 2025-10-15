"""Comprehensive test suite for Pydantic configuration models.

This module tests the WorkspaceConfig and ServerConfig models, covering:
- Valid object creation
- Field validation (hostname, http_path, token, max_response_tokens)
- Default values
- Environment variable loading
- Immutability (frozen models)
- Security (token not in repr)
- JSON serialization

Test coverage goal: 100% for src/databricks_tools/config/models.py
"""

import json
import os
from typing import Any

import pytest
from pydantic import ValidationError

from databricks_tools.config.models import ServerConfig, WorkspaceConfig

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def valid_workspace_data() -> dict[str, Any]:
    """Provide valid data for creating a WorkspaceConfig."""
    return {
        "server_hostname": "https://my-workspace.cloud.databricks.com",
        "http_path": "/sql/1.0/warehouses/abc123def456",
        "access_token": "dapi1234567890abcdef1234567890ab",
        "workspace_name": "production",
    }


@pytest.fixture
def valid_long_token() -> str:
    """Provide a valid token that's 32+ characters but doesn't start with dapi."""
    return "a" * 32


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch):
    """Clean up environment variables before and after tests."""
    # Remove any Databricks-related env vars
    databricks_keys = [k for k in os.environ if "DATABRICKS" in k]
    for key in databricks_keys:
        monkeypatch.delenv(key, raising=False)

    yield monkeypatch

    # Restore original env (monkeypatch does this automatically, but being explicit)


# =============================================================================
# WorkspaceConfig Tests
# =============================================================================


class TestWorkspaceConfig:
    """Tests for WorkspaceConfig Pydantic model."""

    def test_workspace_config_valid_creation(self, valid_workspace_data: dict[str, Any]):
        """Test creating a valid WorkspaceConfig with all required fields.

        This test validates that a WorkspaceConfig can be created with valid
        inputs and that all fields are correctly assigned.
        """
        config = WorkspaceConfig(**valid_workspace_data)

        assert config.server_hostname == valid_workspace_data["server_hostname"]
        assert config.http_path == valid_workspace_data["http_path"]
        assert config.access_token.get_secret_value() == valid_workspace_data["access_token"]
        assert config.workspace_name == valid_workspace_data["workspace_name"]

    def test_workspace_config_invalid_hostname(self):
        """Test validation fails for hostname without https://.

        The server_hostname must start with 'https://' to ensure secure connections.
        """
        with pytest.raises(ValidationError) as exc_info:
            WorkspaceConfig(
                server_hostname="http://insecure.databricks.com",
                http_path="/sql/1.0/warehouses/abc123",
                access_token="dapi1234567890abcdef1234567890ab",
            )

        # Check that the error message mentions https://
        error_msg = str(exc_info.value)
        assert "https://" in error_msg.lower()

    def test_workspace_config_invalid_http_path(self):
        """Test validation fails for http_path not starting with /sql/.

        The http_path must start with '/sql/' to conform to Databricks SQL warehouse format.
        """
        with pytest.raises(ValidationError) as exc_info:
            WorkspaceConfig(
                server_hostname="https://my-workspace.cloud.databricks.com",
                http_path="/api/2.0/warehouses/abc123",
                access_token="dapi1234567890abcdef1234567890ab",
            )

        # Check that the error message mentions /sql/
        error_msg = str(exc_info.value)
        assert "/sql/" in error_msg

    def test_workspace_config_invalid_token_too_short(self):
        """Test validation fails for token that's too short and doesn't start with dapi.

        Access tokens must either start with 'dapi' or be at least 32 characters long.
        """
        with pytest.raises(ValidationError) as exc_info:
            WorkspaceConfig(
                server_hostname="https://my-workspace.cloud.databricks.com",
                http_path="/sql/1.0/warehouses/abc123",
                access_token="short_token",
            )

        # Check that the error message mentions token requirements
        error_msg = str(exc_info.value)
        assert "dapi" in error_msg.lower() or "32" in error_msg

    def test_workspace_config_valid_token_dapi_short(self):
        """Test that a short token starting with 'dapi' is valid.

        Tokens starting with 'dapi' are considered valid even if shorter than 32 chars.
        """
        config = WorkspaceConfig(
            server_hostname="https://my-workspace.cloud.databricks.com",
            http_path="/sql/1.0/warehouses/abc123",
            access_token="dapi123",
        )

        assert config.access_token.get_secret_value() == "dapi123"

    def test_workspace_config_valid_token_long(self, valid_long_token: str):
        """Test that a 32+ character token is valid even without 'dapi' prefix.

        Tokens of 32+ characters are considered valid regardless of prefix.
        """
        config = WorkspaceConfig(
            server_hostname="https://my-workspace.cloud.databricks.com",
            http_path="/sql/1.0/warehouses/abc123",
            access_token=valid_long_token,
        )

        assert config.access_token.get_secret_value() == valid_long_token

    def test_workspace_config_empty_required_fields(self):
        """Test validation fails for empty required fields.

        All required fields (hostname, http_path, access_token) must be non-empty.
        """
        # Test empty hostname
        with pytest.raises(ValidationError):
            WorkspaceConfig(
                server_hostname="",
                http_path="/sql/1.0/warehouses/abc123",
                access_token="dapi1234567890abcdef1234567890ab",
            )

        # Test empty http_path
        with pytest.raises(ValidationError):
            WorkspaceConfig(
                server_hostname="https://my-workspace.cloud.databricks.com",
                http_path="",
                access_token="dapi1234567890abcdef1234567890ab",
            )

        # Test empty access_token
        with pytest.raises(ValidationError):
            WorkspaceConfig(
                server_hostname="https://my-workspace.cloud.databricks.com",
                http_path="/sql/1.0/warehouses/abc123",
                access_token="",
            )

    def test_workspace_config_default_workspace_name(self):
        """Test that workspace_name defaults to 'default' when not provided.

        The workspace_name field should default to 'default' for the primary workspace.
        """
        config = WorkspaceConfig(
            server_hostname="https://my-workspace.cloud.databricks.com",
            http_path="/sql/1.0/warehouses/abc123",
            access_token="dapi1234567890abcdef1234567890ab",
        )

        assert config.workspace_name == "default"

    def test_workspace_config_from_env(self, clean_env: pytest.MonkeyPatch):
        """Test creating WorkspaceConfig from environment variables (no prefix).

        The from_env() method should read DATABRICKS_* variables for the default workspace.
        """
        # Set environment variables
        clean_env.setenv("DATABRICKS_SERVER_HOSTNAME", "https://env-workspace.databricks.com")
        clean_env.setenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/env123")
        clean_env.setenv("DATABRICKS_TOKEN", "dapi_env_token_1234567890abcdef")

        # Create config from environment
        config = WorkspaceConfig.from_env()

        assert config.server_hostname == "https://env-workspace.databricks.com"
        assert config.http_path == "/sql/1.0/warehouses/env123"
        assert config.access_token.get_secret_value() == "dapi_env_token_1234567890abcdef"
        assert config.workspace_name == "default"

    def test_workspace_config_from_env_with_prefix(self, clean_env: pytest.MonkeyPatch):
        """Test creating WorkspaceConfig from prefixed environment variables.

        The from_env(prefix="PRODUCTION") method should read PRODUCTION_DATABRICKS_*
        variables and set workspace_name to 'production'.
        """
        # Set environment variables with PRODUCTION_ prefix
        clean_env.setenv(
            "PRODUCTION_DATABRICKS_SERVER_HOSTNAME",
            "https://production.databricks.com",
        )
        clean_env.setenv("PRODUCTION_DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/prod123")
        clean_env.setenv("PRODUCTION_DATABRICKS_TOKEN", "dapi_prod_token_1234567890abcdef")

        # Create config from environment with prefix
        config = WorkspaceConfig.from_env(prefix="PRODUCTION")

        assert config.server_hostname == "https://production.databricks.com"
        assert config.http_path == "/sql/1.0/warehouses/prod123"
        assert config.access_token.get_secret_value() == "dapi_prod_token_1234567890abcdef"
        assert config.workspace_name == "production"

    def test_workspace_config_from_env_with_trailing_underscore(
        self, clean_env: pytest.MonkeyPatch
    ):
        """Test that from_env() handles prefix with trailing underscore correctly.

        The method should handle both 'STAGING' and 'STAGING_' prefix formats.
        """
        # Set environment variables with STAGING_ prefix
        clean_env.setenv(
            "STAGING_DATABRICKS_SERVER_HOSTNAME",
            "https://staging.databricks.com",
        )
        clean_env.setenv("STAGING_DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/staging123")
        clean_env.setenv("STAGING_DATABRICKS_TOKEN", "dapi_staging_token_1234567890ab")

        # Create config with trailing underscore in prefix
        config = WorkspaceConfig.from_env(prefix="STAGING_")

        assert config.server_hostname == "https://staging.databricks.com"
        assert config.workspace_name == "staging"

    def test_workspace_config_from_env_missing_variables(self, clean_env: pytest.MonkeyPatch):
        """Test that from_env() raises ValueError when required env vars are missing.

        Missing environment variables should result in a clear error message.
        """
        # Don't set any environment variables
        with pytest.raises(ValueError) as exc_info:
            WorkspaceConfig.from_env()

        # Check that the error message mentions missing variables
        error_msg = str(exc_info.value)
        assert "missing" in error_msg.lower()
        assert "DATABRICKS_SERVER_HOSTNAME" in error_msg
        assert "DATABRICKS_HTTP_PATH" in error_msg
        assert "DATABRICKS_TOKEN" in error_msg

    def test_workspace_config_from_env_partial_variables(self, clean_env: pytest.MonkeyPatch):
        """Test that from_env() raises ValueError when only some env vars are set.

        All three required variables must be present.
        """
        # Set only one variable
        clean_env.setenv("DATABRICKS_SERVER_HOSTNAME", "https://partial.databricks.com")

        with pytest.raises(ValueError) as exc_info:
            WorkspaceConfig.from_env()

        error_msg = str(exc_info.value)
        assert "DATABRICKS_HTTP_PATH" in error_msg
        assert "DATABRICKS_TOKEN" in error_msg

    def test_workspace_config_immutable(self, valid_workspace_data: dict[str, Any]):
        """Test that WorkspaceConfig is immutable (frozen=True).

        Attempting to modify any field after creation should raise an error.
        """
        config = WorkspaceConfig(**valid_workspace_data)

        # Attempt to modify a field
        with pytest.raises(ValidationError) as exc_info:
            config.server_hostname = "https://new-hostname.databricks.com"  # type: ignore

        # Check that error indicates the model is frozen
        error_msg = str(exc_info.value)
        assert "frozen" in error_msg.lower() or "immutable" in error_msg.lower()

    def test_workspace_config_token_not_in_repr(self, valid_workspace_data: dict[str, Any]):
        """Test that access_token value is not exposed in repr() or str().

        For security, the token value should be hidden when printing the config object.
        SecretStr should show '**********' instead of the actual value.
        """
        config = WorkspaceConfig(**valid_workspace_data)

        # Get string representations
        config_str = str(config)
        config_repr = repr(config)

        # Actual token value should NOT appear in either representation
        actual_token = valid_workspace_data["access_token"]
        assert actual_token not in config_str
        assert actual_token not in config_repr

        # SecretStr should show something like '**********' or 'SecretStr'
        assert "SecretStr" in config_repr or "*" in config_str

    def test_workspace_config_whitespace_stripping(self):
        """Test that whitespace is automatically stripped from string fields.

        The model config includes str_strip_whitespace=True.
        """
        config = WorkspaceConfig(
            server_hostname="  https://whitespace.databricks.com  ",
            http_path="  /sql/1.0/warehouses/abc123  ",
            access_token="  dapi1234567890abcdef1234567890ab  ",
            workspace_name="  production  ",
        )

        # Whitespace should be stripped
        assert config.server_hostname == "https://whitespace.databricks.com"
        assert config.http_path == "/sql/1.0/warehouses/abc123"
        assert config.access_token.get_secret_value() == "dapi1234567890abcdef1234567890ab"
        assert config.workspace_name == "production"

    def test_workspace_config_whitespace_only_hostname(self):
        """Test that whitespace-only hostname becomes empty and fails validation.

        After stripping, the custom validator should catch this edge case.
        """
        with pytest.raises(ValidationError):
            WorkspaceConfig(
                server_hostname="   ",  # Becomes "" after stripping
                http_path="/sql/1.0/warehouses/abc123",
                access_token="dapi1234567890abcdef1234567890ab",
            )

    def test_workspace_config_whitespace_only_http_path(self):
        """Test that whitespace-only http_path becomes empty and fails validation.

        After stripping, the custom validator should catch this edge case.
        """
        with pytest.raises(ValidationError):
            WorkspaceConfig(
                server_hostname="https://workspace.databricks.com",
                http_path="   ",  # Becomes "" after stripping
                access_token="dapi1234567890abcdef1234567890ab",
            )

    def test_workspace_config_validator_empty_hostname(self):
        """Test the custom validator directly for empty hostname.

        This tests the validator method directly to ensure defensive code works.
        """
        with pytest.raises(ValueError, match="server_hostname cannot be empty"):
            WorkspaceConfig.validate_server_hostname("")

    def test_workspace_config_validator_empty_http_path(self):
        """Test the custom validator directly for empty http_path.

        This tests the validator method directly to ensure defensive code works.
        """
        with pytest.raises(ValueError, match="http_path cannot be empty"):
            WorkspaceConfig.validate_http_path("")


# =============================================================================
# ServerConfig Tests
# =============================================================================


class TestServerConfig:
    """Tests for ServerConfig Pydantic model."""

    def test_server_config_default_values(self):
        """Test that ServerConfig has correct default values.

        Default max_response_tokens should be 9000, and catalog/schema should be None.
        """
        config = ServerConfig()

        assert config.max_response_tokens == 9000
        assert config.default_catalog is None
        assert config.default_schema is None

    def test_server_config_custom_values(self):
        """Test creating ServerConfig with custom values.

        All fields should accept custom values and store them correctly.
        """
        config = ServerConfig(
            max_response_tokens=15000,
            default_catalog="analytics",
            default_schema="core",
        )

        assert config.max_response_tokens == 15000
        assert config.default_catalog == "analytics"
        assert config.default_schema == "core"

    def test_server_config_invalid_max_tokens_too_low(self):
        """Test validation fails when max_response_tokens is below 1000.

        The minimum allowed value is 1000 tokens.
        """
        with pytest.raises(ValidationError) as exc_info:
            ServerConfig(max_response_tokens=500)

        # Check that error message mentions the minimum value
        error_msg = str(exc_info.value)
        assert "1000" in error_msg

    def test_server_config_invalid_max_tokens_too_high(self):
        """Test validation fails when max_response_tokens exceeds 25000.

        The maximum allowed value is 25000 tokens (MCP limit).
        """
        with pytest.raises(ValidationError) as exc_info:
            ServerConfig(max_response_tokens=30000)

        # Check that error message mentions the maximum value
        error_msg = str(exc_info.value)
        assert "25000" in error_msg

    def test_server_config_valid_token_boundaries(self):
        """Test that boundary values for max_response_tokens are valid.

        Both 1000 (minimum) and 25000 (maximum) should be accepted.
        """
        # Test minimum boundary
        config_min = ServerConfig(max_response_tokens=1000)
        assert config_min.max_response_tokens == 1000

        # Test maximum boundary
        config_max = ServerConfig(max_response_tokens=25000)
        assert config_max.max_response_tokens == 25000

    def test_server_config_optional_catalog_schema(self):
        """Test that catalog and schema can be provided independently.

        Either field can be set without the other being required.
        """
        # Only catalog
        config1 = ServerConfig(default_catalog="analytics")
        assert config1.default_catalog == "analytics"
        assert config1.default_schema is None

        # Only schema
        config2 = ServerConfig(default_schema="core")
        assert config2.default_catalog is None
        assert config2.default_schema == "core"

        # Both
        config3 = ServerConfig(default_catalog="analytics", default_schema="core")
        assert config3.default_catalog == "analytics"
        assert config3.default_schema == "core"

    def test_server_config_json_serialization(self):
        """Test that ServerConfig can be serialized to/from JSON.

        The model should support round-trip JSON serialization while preserving values.
        """
        # Create config with custom values
        original_config = ServerConfig(
            max_response_tokens=12000,
            default_catalog="production",
            default_schema="tables",
        )

        # Serialize to JSON
        json_str = original_config.model_dump_json()
        json_dict = json.loads(json_str)

        # Verify JSON structure
        assert json_dict["max_response_tokens"] == 12000
        assert json_dict["default_catalog"] == "production"
        assert json_dict["default_schema"] == "tables"

        # Deserialize back to config
        restored_config = ServerConfig.model_validate_json(json_str)

        # Verify values match
        assert restored_config.max_response_tokens == original_config.max_response_tokens
        assert restored_config.default_catalog == original_config.default_catalog
        assert restored_config.default_schema == original_config.default_schema

    def test_server_config_immutable(self):
        """Test that ServerConfig is immutable (frozen=True).

        Attempting to modify any field after creation should raise an error.
        """
        config = ServerConfig(max_response_tokens=15000)

        # Attempt to modify a field
        with pytest.raises(ValidationError) as exc_info:
            config.max_response_tokens = 20000  # type: ignore

        # Check that error indicates the model is frozen
        error_msg = str(exc_info.value)
        assert "frozen" in error_msg.lower() or "immutable" in error_msg.lower()

    def test_server_config_whitespace_stripping(self):
        """Test that whitespace is automatically stripped from string fields.

        The model config includes str_strip_whitespace=True.
        """
        config = ServerConfig(
            default_catalog="  analytics  ",
            default_schema="  core  ",
        )

        # Whitespace should be stripped
        assert config.default_catalog == "analytics"
        assert config.default_schema == "core"

    def test_server_config_none_values_explicit(self):
        """Test that None can be explicitly set for optional fields.

        Optional fields should accept None as a valid value.
        """
        config = ServerConfig(
            max_response_tokens=10000,
            default_catalog=None,
            default_schema=None,
        )

        assert config.default_catalog is None
        assert config.default_schema is None

    def test_server_config_validator_too_low(self):
        """Test the custom validator directly for value below minimum.

        This tests the validator method directly to ensure defensive code works.
        """
        with pytest.raises(ValueError, match="max_response_tokens must be at least 1000"):
            ServerConfig.validate_max_response_tokens(500)

    def test_server_config_validator_too_high(self):
        """Test the custom validator directly for value above maximum.

        This tests the validator method directly to ensure defensive code works.
        """
        with pytest.raises(ValueError, match="max_response_tokens cannot exceed 25000"):
            ServerConfig.validate_max_response_tokens(30000)
