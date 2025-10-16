"""Comprehensive test suite for WorkspaceConfigManager.

This module tests the workspace configuration manager with role-based access control,
environment variable discovery, error handling, and integration with server.py.

Test Coverage:
- Role-based access control (analyst vs developer)
- Workspace discovery and listing
- Error handling for missing/invalid configurations
- Private methods for complete coverage
- Legacy wrapper functions in server.py
"""

import logging
import os

import pytest

from databricks_tools.config.workspace import WorkspaceConfigManager


class TestWorkspaceConfigManager:
    """Tests for WorkspaceConfigManager class.

    This test class covers all aspects of the WorkspaceConfigManager including
    role-based access control, workspace discovery, error handling, and integration
    with the configuration system.
    """

    # ==================== Role-Based Access Control Tests ====================

    def test_workspace_manager_analyst_mode_default_only(
        self, multi_workspace_env: pytest.MonkeyPatch
    ):
        """Test analyst mode always returns default workspace, ignoring requested workspace.

        Analyst role should be restricted to the default workspace only. When requesting
        a specific workspace like 'production', the manager should return the default
        workspace configuration instead.

        Args:
            multi_workspace_env: Fixture providing multiple workspace configurations.
        """
        manager = WorkspaceConfigManager(role="analyst")

        # Request production, but should get default due to analyst role
        config = manager.get_workspace_config("production")

        assert config.workspace_name == "default"
        assert config.server_hostname == "https://default.databricks.com"
        assert config.http_path == "/sql/1.0/warehouses/default123"

    def test_workspace_manager_analyst_mode_available_workspaces(
        self, multi_workspace_env: pytest.MonkeyPatch
    ):
        """Test analyst mode only sees default workspace even with multiple configured.

        Even when multiple workspaces are configured in the environment, analyst
        users should only see the default workspace in their available list.

        Args:
            multi_workspace_env: Fixture providing multiple workspace configurations.
        """
        manager = WorkspaceConfigManager(role="analyst")

        workspaces = manager.get_available_workspaces()

        assert workspaces == ["default"]
        assert len(workspaces) == 1

    def test_workspace_manager_developer_mode_specific_workspace(
        self, multi_workspace_env: pytest.MonkeyPatch
    ):
        """Test developer mode can access specific workspace configurations.

        Developer role should have full access to all configured workspaces. Requesting
        a specific workspace like 'production' should return that workspace's config.

        Args:
            multi_workspace_env: Fixture providing multiple workspace configurations.
        """
        manager = WorkspaceConfigManager(role="developer")

        # Request production workspace
        config = manager.get_workspace_config("production")

        assert config.workspace_name == "production"
        assert config.server_hostname == "https://prod.databricks.com"
        assert config.http_path == "/sql/1.0/warehouses/prod123"

    def test_workspace_manager_developer_mode_fallback_to_default(
        self, multi_workspace_env: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ):
        """Test developer mode falls back to default for non-existent workspace.

        When a developer requests a workspace that doesn't exist, the manager should
        log a warning and fall back to the default workspace configuration.

        Args:
            multi_workspace_env: Fixture providing multiple workspace configurations.
            caplog: Pytest fixture for capturing log messages.
        """
        manager = WorkspaceConfigManager(role="developer")

        # Capture warning logs
        with caplog.at_level(logging.WARNING):
            config = manager.get_workspace_config("nonexistent")

        # Should fall back to default
        assert config.workspace_name == "default"
        assert config.server_hostname == "https://default.databricks.com"

        # Should have logged a warning
        assert "Workspace 'nonexistent' not found" in caplog.text
        assert "using default workspace" in caplog.text

    def test_workspace_manager_developer_mode_all_workspaces(
        self, multi_workspace_env: pytest.MonkeyPatch
    ):
        """Test developer mode can see all configured workspaces.

        Developer role should have visibility to all configured workspaces in the
        environment. The list should be sorted alphabetically.

        Args:
            multi_workspace_env: Fixture providing multiple workspace configurations.
        """
        manager = WorkspaceConfigManager(role="developer")

        workspaces = manager.get_available_workspaces()

        # Should include all three workspaces, sorted
        assert workspaces == ["default", "dev", "production"]
        assert len(workspaces) == 3

    # ==================== Error Handling Tests ====================

    def test_workspace_manager_no_default_configured(self, clean_env: pytest.MonkeyPatch):
        """Test ValueError raised when no default workspace is configured.

        When trying to access configuration without a default workspace set up,
        the manager should raise a clear ValueError explaining the issue. In analyst
        mode, production workspace exists but analyst can't see it, so error says
        no workspaces are configured.

        Args:
            clean_env: Fixture providing clean environment without Databricks configs.
        """
        # Set up only production workspace, no default
        clean_env.setenv("PRODUCTION_DATABRICKS_SERVER_HOSTNAME", "https://prod.databricks.com")
        clean_env.setenv("PRODUCTION_DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/prod123")
        clean_env.setenv("PRODUCTION_DATABRICKS_TOKEN", "dapi_prod_token_1234567890ab")

        manager = WorkspaceConfigManager(role="analyst")

        with pytest.raises(ValueError) as exc_info:
            manager.get_workspace_config()

        # Should mention default workspace and indicate no workspaces configured
        error_msg = str(exc_info.value)
        assert "default" in error_msg.lower()
        assert "not found" in error_msg.lower()
        # In analyst mode with no default, available_workspaces is empty
        assert "no workspaces" in error_msg.lower()

    def test_workspace_manager_empty_environment(self, clean_env: pytest.MonkeyPatch):
        """Test ValueError when no Databricks configuration exists at all.

        When the environment has no Databricks workspace configurations,
        attempting to get a workspace config should raise a clear error.

        Args:
            clean_env: Fixture providing clean environment without Databricks configs.
        """
        manager = WorkspaceConfigManager(role="developer")

        with pytest.raises(ValueError) as exc_info:
            manager.get_workspace_config()

        # Should indicate no workspaces are configured
        error_msg = str(exc_info.value)
        assert "not found" in error_msg.lower() or "no workspaces" in error_msg.lower()

    def test_workspace_manager_partial_configuration(
        self, partial_config_env: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ):
        """Test incomplete workspace configuration is not available.

        When a workspace has incomplete configuration (missing required environment
        variables), it should not appear in the available workspaces list. In developer
        mode, trying to access it falls back to default workspace with a warning.

        Args:
            partial_config_env: Fixture providing incomplete workspace configuration.
            caplog: Pytest fixture for capturing log messages.
        """
        manager = WorkspaceConfigManager(role="developer")

        # Incomplete workspace should not be in available list
        workspaces = manager.get_available_workspaces()
        assert "incomplete" not in workspaces
        assert "default" in workspaces  # Default should still be available

        # Trying to access incomplete workspace falls back to default (developer mode behavior)
        with caplog.at_level(logging.WARNING):
            config = manager.get_workspace_config("incomplete")

        # Should fall back to default
        assert config.workspace_name == "default"
        # Should have logged a warning about fallback
        assert "Workspace 'incomplete' not found" in caplog.text
        assert "using default workspace" in caplog.text

    def test_workspace_manager_developer_no_default_but_other_workspaces_exist(
        self, clean_env: pytest.MonkeyPatch
    ):
        """Test developer mode error when workspace not found and no default exists.

        This edge case tests when:
        - Developer requests a workspace that doesn't exist
        - Default workspace doesn't exist (no fallback)
        - But OTHER workspaces DO exist and should be listed in error

        Args:
            clean_env: Fixture providing clean environment without Databricks configs.
        """
        # Set up production workspace only, no default
        clean_env.setenv("PRODUCTION_DATABRICKS_SERVER_HOSTNAME", "https://prod.databricks.com")
        clean_env.setenv("PRODUCTION_DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/prod123")
        clean_env.setenv("PRODUCTION_DATABRICKS_TOKEN", "dapi_prod_token_1234567890ab")

        manager = WorkspaceConfigManager(role="developer")

        # Request non-existent staging workspace
        with pytest.raises(ValueError) as exc_info:
            manager.get_workspace_config("staging")

        # Should list available workspaces in error message
        error_msg = str(exc_info.value)
        assert "staging" in error_msg.lower()
        assert "Available workspaces:" in error_msg
        assert "production" in error_msg

    # ==================== Discovery Tests ====================

    def test_workspace_manager_discover_prefixes(self, multi_workspace_env: pytest.MonkeyPatch):
        """Test workspace prefix discovery from environment variables.

        The manager should be able to discover all workspace prefixes by scanning
        environment variables for patterns like {PREFIX}_DATABRICKS_SERVER_HOSTNAME.

        Args:
            multi_workspace_env: Fixture providing multiple workspace configurations.
        """
        manager = WorkspaceConfigManager(role="developer")

        # Call private method to test discovery
        prefixes = manager._discover_workspace_prefixes()

        # Should discover PRODUCTION and DEV prefixes (not default)
        assert "PRODUCTION" in prefixes
        assert "DEV" in prefixes
        assert len(prefixes) == 2
        # Default workspace has no prefix, so it shouldn't be in the set
        assert "" not in prefixes

    def test_workspace_manager_default_workspace_always_exists(
        self, default_workspace_env: pytest.MonkeyPatch
    ):
        """Test default workspace is always available when configured.

        The default workspace should always appear in the available workspaces
        list for both analyst and developer roles when it's properly configured.

        Args:
            default_workspace_env: Fixture providing default workspace configuration.
        """
        # Test with analyst role
        analyst_manager = WorkspaceConfigManager(role="analyst")
        analyst_workspaces = analyst_manager.get_available_workspaces()
        assert "default" in analyst_workspaces

        # Test with developer role
        dev_manager = WorkspaceConfigManager(role="developer")
        dev_workspaces = dev_manager.get_available_workspaces()
        assert "default" in dev_workspaces

    # ==================== Initialization Tests ====================

    def test_workspace_manager_invalid_role(self):
        """Test ValueError raised for invalid role during initialization.

        Only 'analyst' and 'developer' are valid roles. Any other value should
        raise a ValueError with a clear error message.
        """
        with pytest.raises(ValueError) as exc_info:
            WorkspaceConfigManager(role="admin")

        error_msg = str(exc_info.value)
        assert "Invalid role" in error_msg
        assert "admin" in error_msg
        assert "analyst" in error_msg
        assert "developer" in error_msg

    def test_workspace_manager_role_validation(self, default_workspace_env: pytest.MonkeyPatch):
        """Test both valid roles initialize successfully.

        Both 'analyst' and 'developer' roles should initialize without errors
        and be able to access workspace configurations.

        Args:
            default_workspace_env: Fixture providing default workspace configuration.
        """
        # Test analyst role
        analyst_manager = WorkspaceConfigManager(role="analyst")
        assert analyst_manager.role == "analyst"
        config = analyst_manager.get_workspace_config()
        assert config.workspace_name == "default"

        # Test developer role
        developer_manager = WorkspaceConfigManager(role="developer")
        assert developer_manager.role == "developer"
        config = developer_manager.get_workspace_config()
        assert config.workspace_name == "default"


# ==================== Fixtures ====================


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Clean environment before each test.

    Removes all Databricks-related environment variables to ensure tests
    start with a clean slate and don't interfere with each other.

    Args:
        monkeypatch: Pytest fixture for modifying environment.

    Returns:
        The monkeypatch fixture for further environment modifications.
    """
    # Remove all Databricks env vars
    databricks_keys = [k for k in os.environ if "DATABRICKS" in k]
    for key in databricks_keys:
        monkeypatch.delenv(key, raising=False)
    return monkeypatch


@pytest.fixture
def default_workspace_env(clean_env: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Set up default workspace environment.

    Creates a minimal valid default workspace configuration for testing.

    Args:
        clean_env: Clean environment fixture.

    Returns:
        Monkeypatch fixture with default workspace configured.
    """
    clean_env.setenv("DATABRICKS_SERVER_HOSTNAME", "https://default.databricks.com")
    clean_env.setenv("DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/default123")
    clean_env.setenv("DATABRICKS_TOKEN", "dapi_default_token_1234567890ab")
    return clean_env


@pytest.fixture
def multi_workspace_env(
    default_workspace_env: pytest.MonkeyPatch,
) -> pytest.MonkeyPatch:
    """Set up multiple workspaces in environment.

    Creates default, production, and dev workspace configurations for testing
    multi-workspace scenarios and role-based access control.

    Args:
        default_workspace_env: Default workspace environment fixture.

    Returns:
        Monkeypatch fixture with multiple workspaces configured.
    """
    # Add production workspace
    default_workspace_env.setenv(
        "PRODUCTION_DATABRICKS_SERVER_HOSTNAME", "https://prod.databricks.com"
    )
    default_workspace_env.setenv("PRODUCTION_DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/prod123")
    default_workspace_env.setenv("PRODUCTION_DATABRICKS_TOKEN", "dapi_prod_token_1234567890ab")

    # Add dev workspace
    default_workspace_env.setenv("DEV_DATABRICKS_SERVER_HOSTNAME", "https://dev.databricks.com")
    default_workspace_env.setenv("DEV_DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/dev123")
    default_workspace_env.setenv("DEV_DATABRICKS_TOKEN", "dapi_dev_token_1234567890ab")

    return default_workspace_env


@pytest.fixture
def partial_config_env(default_workspace_env: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Set up environment with incomplete workspace configuration.

    Creates a scenario where one workspace is properly configured (default)
    but another workspace has incomplete configuration (missing required variables).

    Args:
        default_workspace_env: Default workspace environment fixture.

    Returns:
        Monkeypatch fixture with partial configuration.
    """
    # Add incomplete workspace (missing TOKEN)
    default_workspace_env.setenv(
        "INCOMPLETE_DATABRICKS_SERVER_HOSTNAME", "https://incomplete.databricks.com"
    )
    default_workspace_env.setenv(
        "INCOMPLETE_DATABRICKS_HTTP_PATH", "/sql/1.0/warehouses/incomplete123"
    )
    # Intentionally NOT setting INCOMPLETE_DATABRICKS_TOKEN

    return default_workspace_env
