"""Role-based access control for Databricks Tools MCP Server.

This module implements the Strategy pattern for role-based access control (RBAC),
allowing fine-grained control over workspace access permissions. The system currently
supports two roles: analyst (restricted to default workspace) and developer (full access).
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """User roles for workspace access control.

    This enum defines the available user roles in the system. Each role has
    specific permissions enforced by the corresponding RoleStrategy implementation.

    Attributes:
        ANALYST: Restricted access to default workspace only. Suitable for business
            users who only need to query data from the default workspace.
        DEVELOPER: Full access to all configured workspaces. Suitable for engineers
            who need to work across multiple environments (dev, staging, production).

    Examples:
        Create role from string:
        >>> role = Role("analyst")
        >>> print(role)
        Role.ANALYST

        Use role in comparisons:
        >>> if role == Role.ANALYST:
        ...     print("Restricted access")
        Restricted access
    """

    ANALYST = "analyst"
    DEVELOPER = "developer"


class RoleStrategy(ABC):
    """Abstract base class for role-based access control strategies.

    This abstract class defines the interface that all role strategies must implement.
    Each concrete strategy encapsulates the access control logic for a specific role,
    following the Strategy pattern.

    The Strategy pattern is used here to:
    1. Encapsulate role-specific behavior in separate classes
    2. Make it easy to add new roles without modifying existing code
    3. Allow runtime switching between different access control policies

    Implementing classes must provide:
    - Workspace access validation logic
    - Workspace filtering based on permissions
    """

    @abstractmethod
    def can_access_workspace(self, workspace_name: str) -> bool:
        """Check if the role can access the specified workspace.

        Args:
            workspace_name: The name of the workspace to check access for
                (e.g., "default", "production", "staging").

        Returns:
            True if the role has permission to access the workspace, False otherwise.

        Examples:
            >>> strategy = AnalystStrategy()
            >>> strategy.can_access_workspace("default")
            True
            >>> strategy.can_access_workspace("production")
            False
        """
        pass

    @abstractmethod
    def filter_workspaces(self, all_workspaces: list[str]) -> list[str]:
        """Filter workspaces based on role permissions.

        This method takes a list of all available workspaces and returns only
        those that the current role has permission to access.

        Args:
            all_workspaces: Complete list of available workspace names.

        Returns:
            Filtered list containing only workspaces the role can access.
            The order of workspaces is preserved from the input list.

        Examples:
            >>> strategy = AnalystStrategy()
            >>> strategy.filter_workspaces(["default", "production", "dev"])
            ['default']

            >>> dev_strategy = DeveloperStrategy()
            >>> dev_strategy.filter_workspaces(["default", "production", "dev"])
            ['default', 'production', 'dev']
        """
        pass


class AnalystStrategy(RoleStrategy):
    """Access control strategy for analyst users.

    Analysts have restricted access limited to the default workspace only.
    This restriction ensures that business users can only query data from
    the default workspace, preventing accidental access to development or
    production environments.

    Permission rules:
    - Can access: "default" workspace only
    - Cannot access: Any other workspace (production, staging, dev, etc.)

    Examples:
        >>> strategy = AnalystStrategy()
        >>> strategy.can_access_workspace("default")
        True
        >>> strategy.can_access_workspace("production")
        False
    """

    def can_access_workspace(self, workspace_name: str) -> bool:
        """Check if analyst can access the specified workspace.

        Analysts can only access the default workspace. Any request for
        other workspaces will be denied.

        Args:
            workspace_name: The name of the workspace to check access for.

        Returns:
            True only if workspace_name is "default", False otherwise.

        Examples:
            >>> strategy = AnalystStrategy()
            >>> strategy.can_access_workspace("default")
            True
            >>> strategy.can_access_workspace("DEFAULT")
            False
            >>> strategy.can_access_workspace("production")
            False
        """
        return workspace_name == "default"

    def filter_workspaces(self, all_workspaces: list[str]) -> list[str]:
        """Filter workspaces to only include default workspace.

        This method filters the list of workspaces to include only the
        default workspace, if present. If the default workspace is not
        in the list, returns an empty list.

        Args:
            all_workspaces: Complete list of available workspace names.

        Returns:
            List containing ["default"] if default workspace is available,
            otherwise returns empty list [].

        Examples:
            >>> strategy = AnalystStrategy()
            >>> strategy.filter_workspaces(["default", "production", "dev"])
            ['default']
            >>> strategy.filter_workspaces(["production", "dev"])
            []
        """
        if "default" in all_workspaces:
            return ["default"]
        return []


class DeveloperStrategy(RoleStrategy):
    """Access control strategy for developer users.

    Developers have unrestricted access to all configured workspaces.
    This allows engineers to work across multiple environments for
    development, testing, and production operations.

    Permission rules:
    - Can access: All workspaces
    - No restrictions on workspace access

    Examples:
        >>> strategy = DeveloperStrategy()
        >>> strategy.can_access_workspace("production")
        True
        >>> strategy.can_access_workspace("staging")
        True
    """

    def can_access_workspace(self, workspace_name: str) -> bool:
        """Check if developer can access the specified workspace.

        Developers can access any workspace without restrictions.

        Args:
            workspace_name: The name of the workspace to check access for.

        Returns:
            Always returns True, as developers have full access.

        Examples:
            >>> strategy = DeveloperStrategy()
            >>> strategy.can_access_workspace("production")
            True
            >>> strategy.can_access_workspace("anything")
            True
        """
        return True

    def filter_workspaces(self, all_workspaces: list[str]) -> list[str]:
        """Return all workspaces without filtering.

        Developers have access to all workspaces, so no filtering is applied.
        The list is returned unchanged.

        Args:
            all_workspaces: Complete list of available workspace names.

        Returns:
            The same list of workspaces, unmodified.

        Examples:
            >>> strategy = DeveloperStrategy()
            >>> strategy.filter_workspaces(["default", "production", "dev"])
            ['default', 'production', 'dev']
            >>> strategy.filter_workspaces([])
            []
        """
        return all_workspaces


class RoleManager:
    """Manages role-based access control using the Strategy pattern.

    This class provides a unified interface for role-based access control
    by delegating permission checks to the appropriate RoleStrategy implementation.
    It acts as the Context in the Strategy pattern, maintaining a reference to
    a strategy object and delegating work to it.

    The RoleManager handles:
    - Role initialization from enum or string values
    - Strategy selection based on role
    - Workspace access validation
    - Workspace filtering based on permissions
    - Workspace request normalization (analyst vs developer behavior)

    Args:
        role: User role, either as a Role enum value or a string ("analyst", "developer").
            Defaults to Role.ANALYST for security (principle of least privilege).

    Raises:
        ValueError: If the provided role is not a valid Role enum value.

    Examples:
        Create manager with enum:
        >>> manager = RoleManager(role=Role.ANALYST)
        >>> manager.can_access_workspace("default")
        True

        Create manager with string:
        >>> manager = RoleManager(role="developer")
        >>> manager.can_access_workspace("production")
        True

        Use default (analyst) role:
        >>> manager = RoleManager()
        >>> manager.role
        <Role.ANALYST: 'analyst'>
    """

    def __init__(self, role: Role | str = Role.ANALYST) -> None:
        """Initialize role manager with specified role.

        The manager converts string roles to Role enum values and creates
        the appropriate strategy for the given role.

        Args:
            role: User role as Role enum or string. Defaults to Role.ANALYST.

        Raises:
            ValueError: If role string doesn't match a valid Role enum value.

        Examples:
            >>> manager = RoleManager(role=Role.ANALYST)
            >>> manager.role
            <Role.ANALYST: 'analyst'>

            >>> manager = RoleManager(role="developer")
            >>> manager.role
            <Role.DEVELOPER: 'developer'>
        """
        # Convert string to enum if needed
        if isinstance(role, str):
            try:
                self.role = Role(role)
            except ValueError as e:
                raise ValueError(f"Invalid role '{role}'. Must be 'analyst' or 'developer'.") from e
        else:
            self.role = role

        # Create appropriate strategy for this role
        self._strategy = self._create_strategy()

        logger.debug(f"RoleManager initialized with role: {self.role.value}")

    def _create_strategy(self) -> RoleStrategy:
        """Factory method to create the appropriate role strategy.

        This method implements the Factory pattern to instantiate the correct
        RoleStrategy subclass based on the current role.

        Returns:
            A RoleStrategy instance appropriate for the current role.

        Raises:
            ValueError: If the role is not recognized. This should never happen
                if the Role enum is used correctly, but provides defensive programming.

        Examples:
            >>> manager = RoleManager(role=Role.ANALYST)
            >>> isinstance(manager._strategy, AnalystStrategy)
            True
        """
        if self.role == Role.ANALYST:
            return AnalystStrategy()
        elif self.role == Role.DEVELOPER:
            return DeveloperStrategy()
        else:
            # This should never happen with the enum, but defensive programming
            raise ValueError(f"Unknown role: {self.role}")

    def can_access_workspace(self, workspace_name: str) -> bool:
        """Check if current role can access the specified workspace.

        This method delegates the access check to the underlying strategy,
        which implements role-specific permission logic.

        Args:
            workspace_name: The name of the workspace to check access for
                (e.g., "default", "production", "staging").

        Returns:
            True if the current role has permission to access the workspace,
            False otherwise.

        Examples:
            Analyst role (restricted):
            >>> manager = RoleManager(role=Role.ANALYST)
            >>> manager.can_access_workspace("default")
            True
            >>> manager.can_access_workspace("production")
            False

            Developer role (unrestricted):
            >>> manager = RoleManager(role=Role.DEVELOPER)
            >>> manager.can_access_workspace("production")
            True
        """
        return self._strategy.can_access_workspace(workspace_name)

    def filter_workspaces(self, workspaces: list[str]) -> list[str]:
        """Filter workspaces based on role permissions.

        This method delegates workspace filtering to the underlying strategy,
        which applies role-specific access rules to the list of workspaces.

        Args:
            workspaces: List of all available workspace names.

        Returns:
            Filtered list containing only workspaces the current role can access.
            The order of workspaces is preserved from the input list.

        Examples:
            Analyst role (restricted to default):
            >>> manager = RoleManager(role=Role.ANALYST)
            >>> manager.filter_workspaces(["default", "production", "dev"])
            ['default']

            Developer role (access all):
            >>> manager = RoleManager(role=Role.DEVELOPER)
            >>> manager.filter_workspaces(["default", "production", "dev"])
            ['default', 'production', 'dev']
        """
        return self._strategy.filter_workspaces(workspaces)

    def normalize_workspace_request(self, requested: str | None) -> str | None:
        """Normalize workspace request based on role permissions.

        This method enforces role-specific workspace access policies:
        - Analyst mode: Always returns None (forcing default workspace)
        - Developer mode: Returns the requested workspace unchanged

        This normalization ensures that analyst users cannot access non-default
        workspaces even if they explicitly request them, while developer users
        have full control over workspace selection.

        Args:
            requested: The workspace name requested by the user, or None for default.

        Returns:
            For analysts: Always None (forces default workspace)
            For developers: The requested workspace name unchanged (or None)

        Examples:
            Analyst role (force default):
            >>> manager = RoleManager(role=Role.ANALYST)
            >>> manager.normalize_workspace_request("production")
            None
            >>> manager.normalize_workspace_request(None)
            None

            Developer role (respect request):
            >>> manager = RoleManager(role=Role.DEVELOPER)
            >>> manager.normalize_workspace_request("production")
            'production'
            >>> manager.normalize_workspace_request(None)
            None
        """
        if self.role == Role.ANALYST:
            # Analysts always get default workspace, ignore their request
            if requested is not None:
                logger.debug(
                    f"Analyst requested workspace '{requested}', but normalizing to default"
                )
            return None

        # Developer mode: return the requested workspace as-is
        return requested
