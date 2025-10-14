# US-1.2: Extract Workspace Configuration Manager

## Metadata
- **Story ID**: US-1.2
- **Title**: Extract Workspace Configuration Manager
- **Phase**: Phase 1 - Foundation
- **Estimated LOC**: ~80 lines
- **Dependencies**: US-1.1 (Pydantic Configuration Models)
- **Status**: ⬜ Not Started

## Overview
Extract workspace configuration logic from server.py into a dedicated WorkspaceConfigManager class. This uses the Factory pattern to create workspace configurations and centralizes all workspace discovery logic.

## User Story
**As a** developer
**I want** a centralized workspace configuration manager
**So that** workspace logic is reusable, testable, and separated from business logic

## Acceptance Criteria
1. ✅ WorkspaceConfigManager class created with Factory pattern
2. ✅ Can load configuration for any workspace by name
3. ✅ Can discover all available workspaces from environment
4. ✅ Respects role-based access (analyst vs developer)
5. ✅ Falls back to default workspace when specified workspace not found (developer mode only)
6. ✅ Provides clear error messages for missing configurations
7. ✅ Original functions in server.py wrapped to use new manager (no breaking changes)
8. ✅ All tests pass with 95%+ coverage
9. ✅ Integration with existing server.py works seamlessly

## Technical Requirements

### Class to Create: WorkspaceConfigManager

#### Responsibilities
- Load workspace configurations from environment variables
- Discover available workspaces
- Apply role-based filtering
- Factory for creating WorkspaceConfig instances

#### Methods

**`__init__(self, role: str = "analyst")`**
- Initialize with role ("analyst" or "developer")
- Store role for filtering logic

**`get_workspace_config(self, workspace: str | None = None) -> WorkspaceConfig`**
- Get configuration for specified workspace
- In analyst mode: always returns default, ignores workspace parameter
- In developer mode: returns requested workspace or falls back to default
- Raises ValueError if no configuration found

**`get_available_workspaces(self) -> list[str]`**
- Returns list of available workspace names
- In analyst mode: only returns ["default"] if configured
- In developer mode: returns all configured workspaces

**`_load_workspace_from_env(self, prefix: str = "") -> WorkspaceConfig | None`**
- Private method to load workspace from environment with given prefix
- Returns None if any required variables are missing
- Uses WorkspaceConfig.from_env() internally

**`_discover_workspace_prefixes(self) -> set[str]`**
- Private method to scan environment for workspace prefixes
- Looks for patterns like {PREFIX}_DATABRICKS_SERVER_HOSTNAME
- Returns set of prefixes found

## Design Patterns Used
- **Factory Pattern**: Creates WorkspaceConfig instances based on workspace name
- **Strategy Pattern**: Different behavior for analyst vs developer roles
- **Singleton Pattern** (optional): Could make this a singleton if needed
- **Facade Pattern**: Simplifies workspace configuration access

## Key Implementation Notes

### Role-Based Filtering Logic
```python
def get_workspace_config(self, workspace: str | None = None) -> WorkspaceConfig:
    """Get workspace configuration with role-based access control."""
    # Analyst mode: always use default, ignore workspace parameter
    if self.role == "analyst":
        workspace = None

    # Determine prefix
    prefix = f"{workspace.upper()}_" if workspace else ""

    # Try to load requested workspace
    config = self._load_workspace_from_env(prefix)

    if config:
        return config

    # Developer mode fallback to default
    if self.role == "developer" and workspace:
        default_config = self._load_workspace_from_env("")
        if default_config:
            logger.warning(f"Workspace '{workspace}' not found, using default")
            return default_config

    # No configuration found
    available = self.get_available_workspaces()
    raise ValueError(
        f"Workspace '{workspace or 'default'}' not configured. "
        f"Available: {', '.join(available)}"
    )
```

### Environment Variable Discovery
```python
def _discover_workspace_prefixes(self) -> set[str]:
    """Discover workspace prefixes from environment variables."""
    import os
    prefixes = set()

    for key in os.environ:
        if key.endswith("_DATABRICKS_SERVER_HOSTNAME"):
            prefix = key.replace("_DATABRICKS_SERVER_HOSTNAME", "")
            if prefix:  # Not the default workspace
                prefixes.add(prefix)

    return prefixes
```

### Integration with Existing Code
```python
# In server.py - Wrapper functions for backward compatibility
_workspace_manager = WorkspaceConfigManager(role=ROLE)

def get_workspace_config(workspace: str | None = None) -> dict[str, str]:
    """Legacy function - wrapper around WorkspaceConfigManager."""
    config = _workspace_manager.get_workspace_config(workspace)
    return {
        "server_hostname": config.server_hostname,
        "http_path": config.http_path,
        "access_token": config.access_token,
    }

def get_available_workspaces() -> list[str]:
    """Legacy function - wrapper around WorkspaceConfigManager."""
    return _workspace_manager.get_available_workspaces()
```

## Files to Create/Modify

### Create
- `src/databricks_tools/config/workspace.py` (main implementation)

### Modify
- `src/databricks_tools/server.py` (add wrapper functions, keep originals working)
- `src/databricks_tools/config/__init__.py` (export WorkspaceConfigManager)

### File Structure
```
src/databricks_tools/
└── config/
    ├── __init__.py (updated)
    ├── models.py (from US-1.1)
    └── workspace.py (new)
```

## Test Cases

### File: `tests/test_config/test_workspace.py`

#### Test Cases for WorkspaceConfigManager

1. **test_workspace_manager_analyst_mode_default_only**
   - Input: Analyst role, request specific workspace
   - Expected: Always returns default workspace config
   - Assertions: Workspace parameter is ignored

2. **test_workspace_manager_analyst_mode_available_workspaces**
   - Input: Analyst role, multiple workspaces configured
   - Expected: get_available_workspaces() returns only ["default"]
   - Assertions: List contains only "default"

3. **test_workspace_manager_developer_mode_specific_workspace**
   - Input: Developer role, request "production" workspace
   - Expected: Returns production workspace config
   - Assertions: Config matches production env vars

4. **test_workspace_manager_developer_mode_fallback_to_default**
   - Input: Developer role, request non-existent workspace
   - Expected: Falls back to default with warning
   - Assertions: Default config returned, warning logged

5. **test_workspace_manager_developer_mode_all_workspaces**
   - Input: Developer role, multiple workspaces configured
   - Expected: get_available_workspaces() returns all workspaces
   - Assertions: All workspace names present

6. **test_workspace_manager_no_default_configured**
   - Input: No default workspace in environment
   - Expected: ValueError raised with clear message
   - Assertions: Error lists available workspaces

7. **test_workspace_manager_discover_prefixes**
   - Input: Environment with PROD_, DEV_, STAGING_ prefixes
   - Expected: All prefixes discovered
   - Assertions: Set contains all three prefixes

8. **test_workspace_manager_default_workspace_always_exists**
   - Input: Default workspace configured
   - Expected: Default always in available list
   - Assertions: "default" in get_available_workspaces()

9. **test_workspace_manager_empty_environment**
   - Input: No Databricks configuration in environment
   - Expected: ValueError on any get_workspace_config() call
   - Assertions: Error message indicates no workspaces

10. **test_workspace_manager_partial_configuration**
    - Input: Environment with SERVER_HOSTNAME but missing TOKEN
    - Expected: Workspace not listed as available
    - Assertions: Incomplete workspace not returned

#### Integration Tests with server.py

11. **test_legacy_get_workspace_config_wrapper**
    - Input: Call legacy get_workspace_config() function
    - Expected: Returns dict with correct keys
    - Assertions: Dict format matches original function

12. **test_legacy_get_available_workspaces_wrapper**
    - Input: Call legacy get_available_workspaces() function
    - Expected: Returns list of workspace names
    - Assertions: List format matches original function

13. **test_workspace_manager_role_change_at_startup**
    - Input: Change ROLE global before manager initialization
    - Expected: Manager respects new role
    - Assertions: Behavior matches expected role

## Definition of Done

- [ ] WorkspaceConfigManager class implemented with all methods
- [ ] Role-based access control working correctly
- [ ] Workspace discovery from environment working
- [ ] Factory pattern correctly creates WorkspaceConfig instances
- [ ] Legacy wrapper functions in server.py maintain backward compatibility
- [ ] All 13 test cases pass
- [ ] Test coverage is 95%+ for config/workspace.py
- [ ] Integration tests with server.py pass
- [ ] No breaking changes to existing MCP tools
- [ ] Type hints present on all functions/methods
- [ ] Docstrings added to all classes and methods
- [ ] Code passes `ruff check` and `ruff format`
- [ ] Logging added for warnings and errors
- [ ] Code reviewed and approved

## Expected Outcome

After completing this story:

1. **Centralized Logic**: All workspace configuration logic in one place
2. **Testability**: Easy to test different role scenarios
3. **Reusability**: WorkspaceConfigManager can be used by other components
4. **Backward Compatible**: Existing server.py code still works
5. **Foundation Ready**: Ready for services to use in Phase 2

### Example Usage
```python
from databricks_tools.config.workspace import WorkspaceConfigManager

# Analyst mode
analyst_manager = WorkspaceConfigManager(role="analyst")
config = analyst_manager.get_workspace_config("production")  # Ignores "production", returns default
workspaces = analyst_manager.get_available_workspaces()  # ["default"]

# Developer mode
dev_manager = WorkspaceConfigManager(role="developer")
prod_config = dev_manager.get_workspace_config("production")
all_workspaces = dev_manager.get_available_workspaces()  # ["default", "production", "dev", ...]

# Legacy usage (in server.py)
config_dict = get_workspace_config("production")  # Still works!
```

## Related User Stories
- **Depends on**: US-1.1 (Pydantic Configuration Models)
- **Blocks**: US-1.3, US-2.2, US-2.3
- **Related to**: All Phase 2+ stories will use this manager

## Notes
- Keep existing server.py functions as thin wrappers
- Add comprehensive logging for debugging
- Consider caching configs if performance becomes an issue
- Document role behavior clearly in docstrings
