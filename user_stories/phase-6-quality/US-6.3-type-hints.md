# US-6.3: Add Type Hints Throughout

## Metadata
- **Story ID**: US-6.3
- **Title**: Add Comprehensive Type Hints
- **Phase**: Phase 6 - Testing & Quality
- **Estimated LOC**: ~50 lines changed
- **Dependencies**: US-6.2 (Pre-commit with mypy)
- **Status**: ⬜ Not Started

## Overview
Add comprehensive type hints to all functions and methods. Use Python 3.10+ syntax (| instead of Union). Ensure mypy passes with --strict mode.

## User Story
**As a** developer
**I want** comprehensive type hints throughout the codebase
**So that** type errors are caught at development time

## Acceptance Criteria
1. ✅ All functions have type hints
2. ✅ All methods have type hints
3. ✅ Use Python 3.10+ syntax (| for unions)
4. ✅ mypy --strict passes
5. ✅ py.typed marker present
6. ✅ Return types specified
7. ✅ Parameter types specified

## Modern Type Syntax (Python 3.10+)

### Before (old style)
```python
from typing import Optional, Union, List, Dict

def get_config(name: Optional[str] = None) -> Dict[str, str]:
    pass

def process(items: Union[List[str], None]) -> List[Dict[str, int]]:
    pass
```

### After (modern style)
```python
def get_config(name: str | None = None) -> dict[str, str]:
    pass

def process(items: list[str] | None) -> list[dict[str, int]]:
    pass
```

## Areas to Update

### 1. Config Module
- All WorkspaceConfig methods
- WorkspaceConfigManager methods

### 2. Core Module
- TokenCounter methods
- ConnectionManager methods
- QueryExecutor methods
- ApplicationContainer initialization

### 3. Security Module
- RoleManager methods
- Strategy classes

### 4. Services Module
- CatalogService methods
- TableService methods
- FunctionService methods
- ChunkingService methods
- ResponseManager methods

### 5. Server Module
- All MCP tool functions
- main() function

## Test Cases
1. test_mypy_strict_passes
2. test_all_functions_typed
3. test_all_methods_typed
4. test_return_types_specified
5. test_parameter_types_specified

## Commands
```bash
# Run mypy
uv run mypy src/databricks_tools --strict

# Check specific file
uv run mypy src/databricks_tools/server.py --strict
```

## Files
- **Modify**: All Python files in src/databricks_tools/
- **Verify**: `src/databricks_tools/py.typed` exists

## Related Stories
- **Depends on**: US-6.2
- **Blocks**: US-6.4
