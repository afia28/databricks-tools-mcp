"""Pydantic configuration models for Databricks Tools MCP Server.

This module provides validated configuration models for Databricks workspace
connections and server settings, ensuring type safety and data validation
throughout the application.
"""

import os
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class WorkspaceConfig(BaseModel):
    """Configuration for a Databricks workspace connection.

    This model validates and stores the necessary credentials and connection
    information for a Databricks workspace. All fields are validated to ensure
    they meet the required format and security standards.

    Attributes:
        server_hostname: The Databricks workspace URL (must start with https://).
        http_path: The SQL warehouse HTTP path (must start with /sql/).
        access_token: The API access token (stored securely, not shown in repr).
        workspace_name: Optional identifier for the workspace (default: "default").

    Examples:
        Create a workspace configuration manually:
        >>> config = WorkspaceConfig(
        ...     server_hostname="https://my-workspace.cloud.databricks.com",
        ...     http_path="/sql/1.0/warehouses/abc123",
        ...     access_token="dapi_my_secret_token_here",
        ...     workspace_name="production"
        ... )

        Create from environment variables (default workspace):
        >>> import os
        >>> os.environ["DATABRICKS_SERVER_HOSTNAME"] = "https://workspace.com"
        >>> os.environ["DATABRICKS_HTTP_PATH"] = "/sql/1.0/warehouses/123"
        >>> os.environ["DATABRICKS_TOKEN"] = "dapi_token_here"
        >>> config = WorkspaceConfig.from_env()

        Create from environment variables (prefixed workspace):
        >>> os.environ["PRODUCTION_DATABRICKS_SERVER_HOSTNAME"] = "https://prod.com"
        >>> os.environ["PRODUCTION_DATABRICKS_HTTP_PATH"] = "/sql/1.0/warehouses/456"
        >>> os.environ["PRODUCTION_DATABRICKS_TOKEN"] = "dapi_prod_token"
        >>> config = WorkspaceConfig.from_env(prefix="PRODUCTION_")
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    server_hostname: str = Field(
        ...,
        description="Databricks workspace URL (must start with https://)",
        min_length=1,
    )
    http_path: str = Field(
        ...,
        description="SQL warehouse HTTP path (must start with /sql/)",
        min_length=1,
    )
    access_token: SecretStr = Field(
        ...,
        description="Databricks API access token (secured, not shown in repr)",
    )
    workspace_name: str = Field(
        default="default",
        description="Workspace identifier for multi-workspace environments",
        min_length=1,
    )

    @field_validator("server_hostname")
    @classmethod
    def validate_server_hostname(cls, v: str) -> str:
        """Validate that server_hostname starts with https://.

        Args:
            v: The server hostname to validate.

        Returns:
            The validated server hostname.

        Raises:
            ValueError: If the hostname doesn't start with https://.
        """
        if not v:
            raise ValueError("server_hostname cannot be empty")
        if not v.startswith("https://"):
            raise ValueError("server_hostname must start with 'https://'")
        return v

    @field_validator("http_path")
    @classmethod
    def validate_http_path(cls, v: str) -> str:
        """Validate that http_path starts with /sql/.

        Args:
            v: The HTTP path to validate.

        Returns:
            The validated HTTP path.

        Raises:
            ValueError: If the path doesn't start with /sql/.
        """
        if not v:
            raise ValueError("http_path cannot be empty")
        if not v.startswith("/sql/"):
            raise ValueError("http_path must start with '/sql/'")
        return v

    @field_validator("access_token")
    @classmethod
    def validate_access_token(cls, v: SecretStr) -> SecretStr:
        """Validate that access_token is either dapi* or at least 32 characters.

        Args:
            v: The access token to validate (as SecretStr).

        Returns:
            The validated access token.

        Raises:
            ValueError: If the token is invalid or too short.
        """
        token_value = v.get_secret_value()
        if not token_value:
            raise ValueError("access_token cannot be empty")
        if not (token_value.startswith("dapi") or len(token_value) >= 32):
            raise ValueError(
                "access_token must start with 'dapi' or be at least 32 characters long"
            )
        return v

    @classmethod
    def from_env(cls, prefix: str = "") -> "WorkspaceConfig":
        """Create a WorkspaceConfig from environment variables.

        This factory method reads configuration from environment variables following
        the Databricks naming convention. It supports prefixed variables for
        multi-workspace environments.

        Args:
            prefix: Optional prefix for environment variable names. If provided,
                variables will be read as {prefix}DATABRICKS_*. If empty, reads
                from DATABRICKS_* directly. Do not include the underscore separator.

        Returns:
            A validated WorkspaceConfig instance.

        Raises:
            ValueError: If required environment variables are missing or invalid.

        Examples:
            Load default workspace configuration:
            >>> config = WorkspaceConfig.from_env()

            Load production workspace configuration:
            >>> config = WorkspaceConfig.from_env(prefix="PRODUCTION")

        Environment Variables:
            - {prefix}DATABRICKS_SERVER_HOSTNAME: Workspace URL
            - {prefix}DATABRICKS_HTTP_PATH: SQL warehouse path
            - {prefix}DATABRICKS_TOKEN: API access token
        """
        # Construct environment variable names with prefix
        env_prefix = f"{prefix}_" if prefix and not prefix.endswith("_") else prefix
        hostname_key = f"{env_prefix}DATABRICKS_SERVER_HOSTNAME"
        path_key = f"{env_prefix}DATABRICKS_HTTP_PATH"
        token_key = f"{env_prefix}DATABRICKS_TOKEN"

        # Read from environment
        server_hostname = os.getenv(hostname_key)
        http_path = os.getenv(path_key)
        access_token = os.getenv(token_key)

        # Check for missing variables
        missing_vars = []
        if not server_hostname:
            missing_vars.append(hostname_key)
        if not http_path:
            missing_vars.append(path_key)
        if not access_token:
            missing_vars.append(token_key)

        if missing_vars:
            workspace_label = prefix.rstrip("_").lower() if prefix else "default"
            raise ValueError(
                f"Missing required environment variables for '{workspace_label}' workspace: "
                f"{', '.join(missing_vars)}"
            )

        # Determine workspace name from prefix
        workspace_name = prefix.rstrip("_").lower() if prefix else "default"

        # Create and validate the config
        # Type ignore comments needed because mypy doesn't understand that None values were already checked above
        return cls(
            server_hostname=server_hostname,  # type: ignore[arg-type]
            http_path=http_path,  # type: ignore[arg-type]
            access_token=access_token,  # type: ignore[arg-type]
            workspace_name=workspace_name,
        )


class ServerConfig(BaseModel):
    """Configuration for the MCP server runtime behavior.

    This model defines server-level settings that control response handling,
    token limits, and default catalog/schema for operations.

    Attributes:
        max_response_tokens: Maximum tokens allowed per response (1000-25000).
        default_catalog: Default catalog name for UDF operations (optional).
        default_schema: Default schema name for UDF operations (optional).

    Examples:
        Create server config with defaults:
        >>> config = ServerConfig()
        >>> config.max_response_tokens
        9000

        Create custom server config:
        >>> config = ServerConfig(
        ...     max_response_tokens=15000,
        ...     default_catalog="analytics",
        ...     default_schema="core"
        ... )

        Use with optional defaults:
        >>> config = ServerConfig(default_catalog="staging")
        >>> config.default_schema is None
        True
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    max_response_tokens: int = Field(
        default=9000,
        description="Maximum tokens per response (MCP limit is 25000, keeping buffer)",
        ge=1000,
        le=25000,
    )
    default_catalog: str | None = Field(
        default=None,
        description="Default catalog for UDF operations",
    )
    default_schema: str | None = Field(
        default=None,
        description="Default schema for UDF operations",
    )

    @field_validator("max_response_tokens")
    @classmethod
    def validate_max_response_tokens(cls, v: int) -> int:
        """Validate that max_response_tokens is within acceptable range.

        Args:
            v: The token limit to validate.

        Returns:
            The validated token limit.

        Raises:
            ValueError: If the token limit is outside the range [1000, 25000].
        """
        if v < 1000:
            raise ValueError("max_response_tokens must be at least 1000")
        if v > 25000:
            raise ValueError("max_response_tokens cannot exceed 25000")
        return v
