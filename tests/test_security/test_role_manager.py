"""Comprehensive tests for Role-Based Access Control Manager.

This test suite provides 100% coverage for the role_manager module,
testing all aspects of the Strategy pattern implementation for RBAC.

Test Coverage:
- Role enum values and string conversion
- RoleStrategy implementations (AnalystStrategy, DeveloperStrategy)
- RoleManager initialization and strategy selection
- Workspace access validation
- Workspace filtering
- Request normalization
- Error handling for invalid roles
"""

import pytest

from databricks_tools.security.role_manager import (
    AnalystStrategy,
    DeveloperStrategy,
    Role,
    RoleManager,
    RoleStrategy,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def analyst_manager() -> RoleManager:
    """Create analyst role manager.

    Returns:
        RoleManager configured with analyst role.
    """
    return RoleManager(role=Role.ANALYST)


@pytest.fixture
def developer_manager() -> RoleManager:
    """Create developer role manager.

    Returns:
        RoleManager configured with developer role.
    """
    return RoleManager(role=Role.DEVELOPER)


@pytest.fixture
def analyst_strategy() -> AnalystStrategy:
    """Create analyst strategy directly.

    Returns:
        AnalystStrategy instance for direct testing.
    """
    return AnalystStrategy()


@pytest.fixture
def developer_strategy() -> DeveloperStrategy:
    """Create developer strategy directly.

    Returns:
        DeveloperStrategy instance for direct testing.
    """
    return DeveloperStrategy()


# ============================================================================
# Test Classes
# ============================================================================


class TestRoleEnum:
    """Tests for Role enum.

    Verifies that the Role enum has correct values and supports
    string conversion for flexible initialization.
    """

    def test_role_enum_values(self) -> None:
        """Test that Role enum has correct values.

        Verifies:
        - ANALYST enum value is "analyst"
        - DEVELOPER enum value is "developer"
        - Can create Role from string values
        """
        # Test enum values
        assert Role.ANALYST.value == "analyst"
        assert Role.DEVELOPER.value == "developer"

        # Test string conversion
        assert Role("analyst") == Role.ANALYST
        assert Role("developer") == Role.DEVELOPER

    def test_role_enum_invalid_string(self) -> None:
        """Test that invalid role string raises ValueError.

        Verifies that attempting to create a Role from an invalid
        string raises a ValueError exception.
        """
        with pytest.raises(ValueError):
            Role("admin")

        with pytest.raises(ValueError):
            Role("invalid_role")


class TestAnalystStrategy:
    """Tests for AnalystStrategy.

    Verifies that analyst users have restricted access limited to
    the default workspace only.
    """

    def test_analyst_strategy_default_workspace_only(
        self, analyst_strategy: AnalystStrategy
    ) -> None:
        """Test analyst can only access default workspace.

        Verifies:
        - Can access "default" workspace (returns True)
        - Cannot access "production" workspace (returns False)
        - Cannot access "dev" workspace (returns False)
        - Cannot access any other workspace (returns False)
        """
        assert analyst_strategy.can_access_workspace("default") is True
        assert analyst_strategy.can_access_workspace("production") is False
        assert analyst_strategy.can_access_workspace("dev") is False
        assert analyst_strategy.can_access_workspace("staging") is False
        assert analyst_strategy.can_access_workspace("test") is False

    def test_analyst_strategy_case_sensitive(self, analyst_strategy: AnalystStrategy) -> None:
        """Test analyst workspace access is case-sensitive.

        Verifies that only exact "default" matches return True,
        and case variations like "DEFAULT" or "Default" return False.
        """
        assert analyst_strategy.can_access_workspace("default") is True
        assert analyst_strategy.can_access_workspace("DEFAULT") is False
        assert analyst_strategy.can_access_workspace("Default") is False

    def test_analyst_strategy_filter_workspaces(self, analyst_strategy: AnalystStrategy) -> None:
        """Test analyst workspace filtering.

        Verifies:
        - Filters list to only include "default" when present
        - Returns empty list when "default" not present
        - Handles empty input list
        """
        # Test with default present
        workspaces = ["default", "production", "dev"]
        filtered = analyst_strategy.filter_workspaces(workspaces)
        assert filtered == ["default"]

        # Test without default present
        workspaces_no_default = ["production", "dev"]
        filtered_empty = analyst_strategy.filter_workspaces(workspaces_no_default)
        assert filtered_empty == []

        # Test with empty list
        assert analyst_strategy.filter_workspaces([]) == []

        # Test with only default
        assert analyst_strategy.filter_workspaces(["default"]) == ["default"]


class TestDeveloperStrategy:
    """Tests for DeveloperStrategy.

    Verifies that developer users have unrestricted access to all
    configured workspaces.
    """

    def test_developer_strategy_all_workspaces(self, developer_strategy: DeveloperStrategy) -> None:
        """Test developer can access all workspaces.

        Verifies:
        - Can access "default" workspace
        - Can access "production" workspace
        - Can access any arbitrary workspace name
        - Always returns True for any workspace
        """
        assert developer_strategy.can_access_workspace("default") is True
        assert developer_strategy.can_access_workspace("production") is True
        assert developer_strategy.can_access_workspace("dev") is True
        assert developer_strategy.can_access_workspace("staging") is True
        assert developer_strategy.can_access_workspace("anything") is True
        assert developer_strategy.can_access_workspace("random_workspace") is True

    def test_developer_strategy_filter_workspaces(
        self, developer_strategy: DeveloperStrategy
    ) -> None:
        """Test developer workspace filtering.

        Verifies:
        - Returns all workspaces unchanged
        - Preserves order of workspaces
        - Handles empty list
        """
        # Test with multiple workspaces
        workspaces = ["default", "production", "dev"]
        filtered = developer_strategy.filter_workspaces(workspaces)
        assert filtered == workspaces
        assert filtered == ["default", "production", "dev"]

        # Test order preservation
        workspaces_ordered = ["production", "staging", "dev", "default"]
        filtered_ordered = developer_strategy.filter_workspaces(workspaces_ordered)
        assert filtered_ordered == workspaces_ordered

        # Test with empty list
        assert developer_strategy.filter_workspaces([]) == []

        # Test with single workspace
        assert developer_strategy.filter_workspaces(["production"]) == ["production"]


class TestRoleManager:
    """Tests for RoleManager.

    Verifies the RoleManager correctly implements the Strategy pattern,
    delegating workspace access control to the appropriate strategy
    based on the user's role.
    """

    def test_role_manager_analyst_initialization(self, analyst_manager: RoleManager) -> None:
        """Test RoleManager creates AnalystStrategy for analyst role.

        Verifies:
        - Manager stores correct role enum
        - Manager creates AnalystStrategy instance
        - Strategy is accessible via _strategy attribute
        """
        assert analyst_manager.role == Role.ANALYST
        assert isinstance(analyst_manager._strategy, AnalystStrategy)

    def test_role_manager_developer_initialization(self, developer_manager: RoleManager) -> None:
        """Test RoleManager creates DeveloperStrategy for developer role.

        Verifies:
        - Manager stores correct role enum
        - Manager creates DeveloperStrategy instance
        - Strategy is accessible via _strategy attribute
        """
        assert developer_manager.role == Role.DEVELOPER
        assert isinstance(developer_manager._strategy, DeveloperStrategy)

    def test_role_manager_from_string(self) -> None:
        """Test RoleManager initialization from string.

        Verifies:
        - Can create manager with "analyst" string
        - Can create manager with "developer" string
        - String is correctly converted to Role enum
        """
        # Test analyst string
        analyst_from_string = RoleManager(role="analyst")
        assert analyst_from_string.role == Role.ANALYST
        assert isinstance(analyst_from_string._strategy, AnalystStrategy)

        # Test developer string
        developer_from_string = RoleManager(role="developer")
        assert developer_from_string.role == Role.DEVELOPER
        assert isinstance(developer_from_string._strategy, DeveloperStrategy)

    def test_role_manager_from_enum_directly(self) -> None:
        """Test RoleManager initialization with Role enum directly.

        Verifies:
        - Can create manager with Role.ANALYST enum
        - Can create manager with Role.DEVELOPER enum
        - Enum is stored directly without conversion
        - Covers the else branch in __init__ (line 305)
        """
        # Test with Role.ANALYST enum
        analyst_from_enum = RoleManager(role=Role.ANALYST)
        assert analyst_from_enum.role == Role.ANALYST
        assert isinstance(analyst_from_enum._strategy, AnalystStrategy)

        # Test with Role.DEVELOPER enum
        developer_from_enum = RoleManager(role=Role.DEVELOPER)
        assert developer_from_enum.role == Role.DEVELOPER
        assert isinstance(developer_from_enum._strategy, DeveloperStrategy)

    def test_role_manager_default_role(self) -> None:
        """Test RoleManager defaults to analyst role.

        Verifies:
        - Default role is ANALYST (principle of least privilege)
        - Default strategy is AnalystStrategy
        """
        default_manager = RoleManager()
        assert default_manager.role == Role.ANALYST
        assert isinstance(default_manager._strategy, AnalystStrategy)

    def test_role_manager_invalid_role(self) -> None:
        """Test RoleManager raises ValueError for invalid role.

        Verifies:
        - Invalid role string raises ValueError
        - Error message indicates invalid role
        - Error message suggests valid options
        """
        with pytest.raises(ValueError) as exc_info:
            RoleManager(role="admin")

        error_message = str(exc_info.value)
        assert "Invalid role" in error_message
        assert "admin" in error_message
        assert "analyst" in error_message or "developer" in error_message

    def test_role_manager_can_access_workspace_analyst(self, analyst_manager: RoleManager) -> None:
        """Test analyst manager workspace access through delegation.

        Verifies:
        - Manager delegates to AnalystStrategy
        - Can access default workspace
        - Cannot access other workspaces
        """
        assert analyst_manager.can_access_workspace("default") is True
        assert analyst_manager.can_access_workspace("production") is False
        assert analyst_manager.can_access_workspace("dev") is False

    def test_role_manager_can_access_workspace_developer(
        self, developer_manager: RoleManager
    ) -> None:
        """Test developer manager workspace access through delegation.

        Verifies:
        - Manager delegates to DeveloperStrategy
        - Can access all workspaces
        - Returns True for any workspace name
        """
        assert developer_manager.can_access_workspace("default") is True
        assert developer_manager.can_access_workspace("production") is True
        assert developer_manager.can_access_workspace("dev") is True
        assert developer_manager.can_access_workspace("anything") is True

    def test_role_manager_filter_workspaces_analyst(self, analyst_manager: RoleManager) -> None:
        """Test analyst manager workspace filtering through delegation.

        Verifies:
        - Manager delegates to AnalystStrategy
        - Filters to only default workspace
        - Returns empty list when default not present
        """
        workspaces = ["default", "production", "dev"]
        assert analyst_manager.filter_workspaces(workspaces) == ["default"]

        workspaces_no_default = ["production", "dev"]
        assert analyst_manager.filter_workspaces(workspaces_no_default) == []

    def test_role_manager_filter_workspaces_developer(self, developer_manager: RoleManager) -> None:
        """Test developer manager workspace filtering through delegation.

        Verifies:
        - Manager delegates to DeveloperStrategy
        - Returns all workspaces unchanged
        - Preserves workspace order
        """
        workspaces = ["default", "production", "dev"]
        assert developer_manager.filter_workspaces(workspaces) == workspaces

    def test_role_manager_normalize_analyst(self, analyst_manager: RoleManager) -> None:
        """Test analyst manager normalizes all requests to None.

        Verifies:
        - normalize_workspace_request("production") returns None
        - normalize_workspace_request("dev") returns None
        - normalize_workspace_request(None) returns None
        - Analysts always get default workspace regardless of request
        """
        assert analyst_manager.normalize_workspace_request("production") is None
        assert analyst_manager.normalize_workspace_request("dev") is None
        assert analyst_manager.normalize_workspace_request("staging") is None
        assert analyst_manager.normalize_workspace_request(None) is None
        assert analyst_manager.normalize_workspace_request("default") is None

    def test_role_manager_normalize_developer(self, developer_manager: RoleManager) -> None:
        """Test developer manager preserves workspace requests.

        Verifies:
        - normalize_workspace_request("production") returns "production"
        - normalize_workspace_request("dev") returns "dev"
        - normalize_workspace_request(None) returns None
        - Developers get exactly what they request
        """
        assert developer_manager.normalize_workspace_request("production") == "production"
        assert developer_manager.normalize_workspace_request("dev") == "dev"
        assert developer_manager.normalize_workspace_request("staging") == "staging"
        assert developer_manager.normalize_workspace_request(None) is None
        assert developer_manager.normalize_workspace_request("default") == "default"


class TestRoleStrategyAbstract:
    """Tests for RoleStrategy abstract base class.

    Verifies that RoleStrategy enforces implementation of abstract methods
    and cannot be instantiated directly.
    """

    def test_role_strategy_cannot_instantiate(self) -> None:
        """Test that RoleStrategy ABC cannot be instantiated directly.

        Verifies that attempting to create a RoleStrategy instance
        raises TypeError because it's an abstract base class.
        """
        with pytest.raises(TypeError):
            RoleStrategy()  # type: ignore

    def test_role_strategy_subclass_must_implement_methods(self) -> None:
        """Test that RoleStrategy subclass must implement abstract methods.

        Verifies that a subclass without implementing abstract methods
        cannot be instantiated.
        """

        # Create incomplete subclass
        class IncompleteStrategy(RoleStrategy):
            pass

        with pytest.raises(TypeError):
            IncompleteStrategy()  # type: ignore
