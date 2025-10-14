"""Workspace configuration manager for Databricks Tools MCP Server.

This module provides centralized workspace configuration management with role-based
access control for Databricks workspaces. It handles loading configurations from
environment variables, discovering available workspaces, and enforcing access policies.
"""

import logging
import os

from databricks_tools.config.models import WorkspaceConfig

logger = logging.getLogger(__name__)


class WorkspaceConfigManager:
    """Manages workspace configurations with role-based access control.

    This class provides a centralized interface for loading and discovering
    Databricks workspace configurations from environment variables. It implements
    role-based access control where analyst users are restricted to the default
    workspace while developer users can access all configured workspaces.

    The manager handles workspace discovery by scanning environment variables for
    patterns like {PREFIX}_DATABRICKS_SERVER_HOSTNAME and provides factory methods
    for creating WorkspaceConfig instances.

    Args:
        role: User role, either "analyst" or "developer". Defaults to "analyst".
            - "analyst": Restricted to default workspace only
            - "developer": Full access to all configured workspaces

    Raises:
        ValueError: If role is not "analyst" or "developer".

    Examples:
        Create manager for analyst (restricted access):
        >>> manager = WorkspaceConfigManager(role="analyst")
        >>> config = manager.get_workspace_config()  # Always returns default
        >>> workspaces = manager.get_available_workspaces()  # ["default"]

        Create manager for developer (full access):
        >>> dev_manager = WorkspaceConfigManager(role="developer")
        >>> prod_config = dev_manager.get_workspace_config("production")
        >>> all_workspaces = dev_manager.get_available_workspaces()
        >>> print(all_workspaces)  # ["default", "production", "staging"]

        Handle missing workspaces with fallback:
        >>> config = dev_manager.get_workspace_config("nonexistent")
        # Falls back to default workspace with warning
    """

    def __init__(self, role: str = "analyst") -> None:
        """Initialize workspace configuration manager with role-based access.

        Args:
            role: User role, either "analyst" or "developer". Defaults to "analyst".

        Raises:
            ValueError: If role is not "analyst" or "developer".
        """
        if role not in ("analyst", "developer"):
            raise ValueError(
                f"Invalid role '{role}'. Role must be either 'analyst' or 'developer'."
            )
        self.role = role

    def get_workspace_config(self, workspace: str | None = None) -> WorkspaceConfig:
        """Get configuration for specified workspace with role-based access control.

        This method loads workspace configuration based on the user's role:
        - Analyst mode: Always returns default workspace, ignores workspace parameter
        - Developer mode: Returns requested workspace or falls back to default

        Args:
            workspace: The workspace name to load (e.g., "production", "staging").
                In analyst mode, this parameter is ignored and default is always used.
                In developer mode, if None or not found, falls back to default workspace.

        Returns:
            A validated WorkspaceConfig instance for the requested or default workspace.

        Raises:
            ValueError: If no workspace configuration is found. Error message includes
                list of available workspaces to help with debugging.

        Examples:
            Analyst mode (always uses default):
            >>> manager = WorkspaceConfigManager(role="analyst")
            >>> config = manager.get_workspace_config("production")
            # Returns default workspace, ignoring "production" parameter

            Developer mode (can access specific workspaces):
            >>> manager = WorkspaceConfigManager(role="developer")
            >>> config = manager.get_workspace_config("production")
            >>> config.workspace_name
            'production'

            Developer mode with fallback:
            >>> config = manager.get_workspace_config("missing")
            # Logs warning and returns default workspace
        """
        # In analyst mode, always use default workspace regardless of input
        if self.role == "analyst":
            workspace = None  # Force default workspace

        # Attempt to load the requested workspace
        if workspace is None:
            # Load default workspace (empty prefix)
            config = self._load_workspace_from_env(prefix="")
            if config is not None:
                return config
        else:
            # Load workspace with specified prefix
            prefix = workspace.upper()
            config = self._load_workspace_from_env(prefix=prefix)
            if config is not None:
                return config

            # In developer mode, try to fall back to default workspace
            if self.role == "developer":
                logger.warning(f"Workspace '{workspace}' not found, using default workspace")
                default_config = self._load_workspace_from_env(prefix="")
                if default_config is not None:
                    return default_config

        # No configuration found - build helpful error message
        available_workspaces = self.get_available_workspaces()
        workspace_label = workspace or "default"

        if available_workspaces:
            raise ValueError(
                f"Workspace '{workspace_label}' configuration not found. "
                f"Available workspaces: {', '.join(available_workspaces)}"
            )
        else:
            raise ValueError(
                f"Workspace '{workspace_label}' configuration not found and no "
                "workspaces are configured. Please check your environment variables."
            )

    def get_available_workspaces(self) -> list[str]:
        """Get list of available workspace names based on role and environment.

        This method returns configured workspaces based on the user's role:
        - Analyst mode: Only returns ["default"] if default workspace is configured
        - Developer mode: Returns all configured workspaces (sorted alphabetically)

        The method scans environment variables to discover workspace configurations
        and validates that each workspace has all required credentials.

        Returns:
            Sorted list of available workspace names. Empty list if no workspaces
            are configured.

        Examples:
            Analyst mode (restricted access):
            >>> manager = WorkspaceConfigManager(role="analyst")
            >>> workspaces = manager.get_available_workspaces()
            >>> print(workspaces)
            ['default']

            Developer mode (full access):
            >>> manager = WorkspaceConfigManager(role="developer")
            >>> workspaces = manager.get_available_workspaces()
            >>> print(workspaces)
            ['default', 'production', 'staging']

            No workspaces configured:
            >>> manager = WorkspaceConfigManager(role="developer")
            >>> workspaces = manager.get_available_workspaces()
            >>> print(workspaces)
            []
        """
        # For analyst role, only return default workspace if it exists
        if self.role == "analyst":
            default_config = self._load_workspace_from_env(prefix="")
            if default_config is not None:
                return ["default"]
            else:
                return []

        # For developer role, return all available workspaces
        workspaces = set()

        # Check for default workspace (empty prefix)
        default_config = self._load_workspace_from_env(prefix="")
        if default_config is not None:
            workspaces.add("default")

        # Discover and check prefixed workspaces
        prefixes = self._discover_workspace_prefixes()
        for prefix in prefixes:
            config = self._load_workspace_from_env(prefix=prefix)
            if config is not None:
                # Convert prefix to workspace name (lowercase)
                workspace_name = prefix.lower()
                workspaces.add(workspace_name)

        return sorted(workspaces)

    def _load_workspace_from_env(self, prefix: str = "") -> WorkspaceConfig | None:
        """Load workspace configuration from environment variables with given prefix.

        This private method attempts to load a WorkspaceConfig using the specified
        prefix. It gracefully handles missing environment variables by returning None
        instead of raising exceptions.

        Args:
            prefix: Environment variable prefix (e.g., "PRODUCTION", "STAGING").
                Empty string means default workspace (unprefixed variables).
                Do not include trailing underscore - it will be added automatically.

        Returns:
            A validated WorkspaceConfig instance if all required variables are present,
            None if any required variables are missing or invalid.

        Examples:
            Load default workspace:
            >>> config = manager._load_workspace_from_env(prefix="")
            >>> config.workspace_name if config else None
            'default'

            Load production workspace:
            >>> config = manager._load_workspace_from_env(prefix="PRODUCTION")
            >>> config.workspace_name if config else None
            'production'

            Handle missing configuration:
            >>> config = manager._load_workspace_from_env(prefix="NONEXISTENT")
            >>> config is None
            True
        """
        try:
            config = WorkspaceConfig.from_env(prefix=prefix)
            return config
        except ValueError as e:
            # Expected behavior - configuration not available
            logger.debug(f"Failed to load workspace with prefix '{prefix}': {e}")
            return None

    def _discover_workspace_prefixes(self) -> set[str]:
        """Discover workspace prefixes by scanning environment variables.

        This private method scans all environment variables to find workspace
        configurations by looking for the pattern {PREFIX}_DATABRICKS_SERVER_HOSTNAME.
        It extracts the prefix part and returns the set of discovered prefixes.

        The default workspace (unprefixed variables) is not included in the returned
        set as it's handled separately.

        Returns:
            Set of workspace prefixes found in environment variables (excluding empty
            prefix for default workspace). Prefixes are in uppercase as they appear
            in environment variable names.

        Examples:
            Environment has PRODUCTION_DATABRICKS_SERVER_HOSTNAME and
            STAGING_DATABRICKS_SERVER_HOSTNAME:
            >>> prefixes = manager._discover_workspace_prefixes()
            >>> sorted(prefixes)
            ['PRODUCTION', 'STAGING']

            Only default workspace configured (no prefixed variables):
            >>> prefixes = manager._discover_workspace_prefixes()
            >>> prefixes
            set()
        """
        prefixes = set()

        # Scan environment variables for workspace patterns
        for key in os.environ:
            if key.endswith("_DATABRICKS_SERVER_HOSTNAME"):
                # Extract the prefix by removing the suffix
                prefix = key.replace("_DATABRICKS_SERVER_HOSTNAME", "")
                # Only add non-empty prefixes (empty means default workspace)
                if prefix:
                    prefixes.add(prefix)

        return prefixes
