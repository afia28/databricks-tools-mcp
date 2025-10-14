"""Configuration models for Databricks Tools MCP Server.

This package provides Pydantic-based configuration models for managing
Databricks workspace connections and server settings with comprehensive
validation and type safety.
"""

from databricks_tools.config.models import ServerConfig, WorkspaceConfig

__all__ = ["WorkspaceConfig", "ServerConfig"]
