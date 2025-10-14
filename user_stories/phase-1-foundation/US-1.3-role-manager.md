# US-1.3: Create Role-Based Access Control Manager

## Metadata
- **Story ID**: US-1.3
- **Title**: Create Role-Based Access Control Manager
- **Phase**: Phase 1 - Foundation
- **Estimated LOC**: ~60 lines
- **Dependencies**: US-1.2 (Workspace Configuration Manager)
- **Status**: ⬜ Not Started

## Overview
Extract role-based access control logic into a dedicated RoleManager class using the Strategy pattern. This centralizes role logic and makes it reusable across the application.

## User Story
**As a** developer
**I want** a centralized role management system
**So that** role-based access control is consistent and testable throughout the application

## Acceptance Criteria
1. ✅ RoleManager class created with Strategy pattern
2. ✅ Supports "analyst" and "developer" roles
3. ✅ Can validate role values
4. ✅ Provides role-specific workspace filtering
5. ✅ Integrates with WorkspaceConfigManager
6. ✅ Global ROLE variable in server.py uses RoleManager
7. ✅ All tests pass with 100% coverage
8. ✅ No breaking changes to existing functionality

## Technical Requirements

### Class to Create: RoleManager

#### Role Strategies
```python
from enum import Enum
from abc import ABC, abstractmethod

class Role(str, Enum):
    """Available user roles."""
    ANALYST = "analyst"
    DEVELOPER = "developer"

class RoleStrategy(ABC):
    """Abstract base class for role strategies."""

    @abstractmethod
    def can_access_workspace(self, workspace_name: str) -> bool:
        """Check if role can access specified workspace."""
        pass

    @abstractmethod
    def filter_workspaces(self, all_workspaces: list[str]) -> list[str]:
        """Filter workspaces based on role permissions."""
        pass

class AnalystStrategy(RoleStrategy):
    """Analyst role: access only to default workspace."""

    def can_access_workspace(self, workspace_name: str) -> bool:
        return workspace_name == "default"

    def filter_workspaces(self, all_workspaces: list[str]) -> list[str]:
        return ["default"] if "default" in all_workspaces else []

class DeveloperStrategy(RoleStrategy):
    """Developer role: access to all workspaces."""

    def can_access_workspace(self, workspace_name: str) -> bool:
        return True

    def filter_workspaces(self, all_workspaces: list[str]) -> list[str]:
        return all_workspaces
```

#### RoleManager Class
```python
class RoleManager:
    """Manages role-based access control."""

    def __init__(self, role: Role | str = Role.ANALYST):
        self.role = Role(role) if isinstance(role, str) else role
        self._strategy = self._create_strategy()

    def _create_strategy(self) -> RoleStrategy:
        """Factory method to create role strategy."""
        if self.role == Role.ANALYST:
            return AnalystStrategy()
        elif self.role == Role.DEVELOPER:
            return DeveloperStrategy()
        else:
            raise ValueError(f"Unknown role: {self.role}")

    def can_access_workspace(self, workspace_name: str) -> bool:
        """Check if current role can access workspace."""
        return self._strategy.can_access_workspace(workspace_name)

    def filter_workspaces(self, workspaces: list[str]) -> list[str]:
        """Filter workspaces based on role permissions."""
        return self._strategy.filter_workspaces(workspaces)

    def normalize_workspace_request(self, requested: str | None) -> str | None:
        """Normalize workspace request based on role.

        Analyst mode: Always returns None (force default)
        Developer mode: Returns requested workspace as-is
        """
        if self.role == Role.ANALYST:
            return None
        return requested
```

## Design Patterns Used
- **Strategy Pattern**: Different strategies for analyst vs developer roles
- **Factory Pattern**: RoleManager creates appropriate strategy
- **Enum Pattern**: Type-safe role definitions

## Key Implementation Notes

### Integration with WorkspaceConfigManager
```python
# In workspace.py - Update to use RoleManager
class WorkspaceConfigManager:
    def __init__(self, role_manager: RoleManager):
        self.role_manager = role_manager

    def get_workspace_config(self, workspace: str | None = None) -> WorkspaceConfig:
        # Normalize workspace request based on role
        workspace = self.role_manager.normalize_workspace_request(workspace)
        # ... rest of implementation

    def get_available_workspaces(self) -> list[str]:
        # Discover all workspaces
        all_workspaces = self._discover_all_workspaces()
        # Filter based on role
        return self.role_manager.filter_workspaces(all_workspaces)
```

### Integration with server.py
```python
# In server.py
from databricks_tools.security.role_manager import RoleManager, Role

# Parse role from command line
args = parser.parse_args()
role = Role.DEVELOPER if args.developer else Role.ANALYST

# Create role manager
role_manager = RoleManager(role=role)

# Pass to workspace manager
workspace_manager = WorkspaceConfigManager(role_manager=role_manager)
```

## Files to Create/Modify

### Create
- `src/databricks_tools/security/__init__.py`
- `src/databricks_tools/security/role_manager.py`

### Modify
- `src/databricks_tools/config/workspace.py` (integrate RoleManager)
- `src/databricks_tools/server.py` (use RoleManager instead of global ROLE)

## Test Cases

### File: `tests/test_security/test_role_manager.py`

1. **test_role_enum_values**
   - Verify Role.ANALYST and Role.DEVELOPER exist
   - Assertions: Enum values are correct strings

2. **test_role_manager_analyst_initialization**
   - Input: Role.ANALYST
   - Expected: Creates AnalystStrategy
   - Assertions: Strategy type is correct

3. **test_role_manager_developer_initialization**
   - Input: Role.DEVELOPER
   - Expected: Creates DeveloperStrategy
   - Assertions: Strategy type is correct

4. **test_analyst_strategy_default_workspace_only**
   - Input: AnalystStrategy, various workspace names
   - Expected: Only "default" allowed
   - Assertions: can_access_workspace("default") == True, others False

5. **test_analyst_strategy_filter_workspaces**
   - Input: List with multiple workspaces
   - Expected: Only ["default"] returned
   - Assertions: Filtered list correct

6. **test_developer_strategy_all_workspaces**
   - Input: DeveloperStrategy, various workspace names
   - Expected: All allowed
   - Assertions: can_access_workspace() always True

7. **test_developer_strategy_filter_workspaces**
   - Input: List with multiple workspaces
   - Expected: All workspaces returned
   - Assertions: No filtering occurred

8. **test_role_manager_normalize_analyst**
   - Input: Analyst role, request "production"
   - Expected: Returns None
   - Assertions: Normalized to None

9. **test_role_manager_normalize_developer**
   - Input: Developer role, request "production"
   - Expected: Returns "production"
   - Assertions: No change to request

10. **test_role_manager_invalid_role**
    - Input: Invalid role string
    - Expected: ValueError raised
    - Assertions: Error message indicates invalid role

11. **test_role_manager_from_string**
    - Input: "analyst" string
    - Expected: Correctly converts to Role.ANALYST
    - Assertions: Role enum set correctly

## Definition of Done

- [ ] Role enum created with ANALYST and DEVELOPER values
- [ ] RoleStrategy ABC created with required methods
- [ ] AnalystStrategy and DeveloperStrategy implemented
- [ ] RoleManager class implemented
- [ ] Integration with WorkspaceConfigManager complete
- [ ] Integration with server.py complete
- [ ] All 11 test cases pass
- [ ] Test coverage is 100% for security/role_manager.py
- [ ] Type hints present on all functions/methods
- [ ] Docstrings added to all classes and methods
- [ ] Code passes `ruff check` and `ruff format`
- [ ] No breaking changes to existing functionality
- [ ] Code reviewed and approved

## Expected Outcome

After completing this story:

1. **Centralized Role Logic**: All role logic in one place
2. **Strategy Pattern**: Easy to add new roles in future
3. **Type Safety**: Role enum prevents invalid role values
4. **Testability**: Each strategy independently testable
5. **Foundation Complete**: Phase 1 complete, ready for Phase 2

### Example Usage
```python
from databricks_tools.security.role_manager import RoleManager, Role

# Create role manager
role_manager = RoleManager(role=Role.ANALYST)

# Check access
can_access = role_manager.can_access_workspace("production")  # False

# Filter workspaces
filtered = role_manager.filter_workspaces(["default", "prod", "dev"])  # ["default"]

# Normalize request
normalized = role_manager.normalize_workspace_request("prod")  # None
```

## Related User Stories
- **Depends on**: US-1.2 (Workspace Configuration Manager)
- **Blocks**: US-2.1, US-2.2, US-2.3
- **Completes**: Phase 1 - Foundation

## Notes
- This completes the foundation phase
- All Phase 2+ stories can now use role-based access
- Consider adding more roles in future (e.g., "admin", "read-only")
