# US-2.3: Create Query Executor Service

## Metadata
- **Story ID**: US-2.3
- **Title**: Create Query Executor Service
- **Phase**: Phase 2 - Core Services
- **Estimated LOC**: ~100 lines
- **Dependencies**: US-1.2 (Workspace Manager), US-2.2 (Connection Manager)
- **Status**: ⬜ Not Started

## Overview
Create QueryExecutor service using Repository pattern to execute SQL queries against Databricks. Centralizes all database query logic.

## User Story
**As a** developer
**I want** a centralized query execution service
**So that** database operations are consistent, testable, and reusable

## Acceptance Criteria
1. ✅ QueryExecutor class using Repository pattern
2. ✅ execute_query() returns pandas DataFrame
3. ✅ execute_query_with_catalog() sets catalog context
4. ✅ Uses ConnectionManager for connections
5. ✅ Handles query errors gracefully
6. ✅ Legacy wrapper functions in server.py work
7. ✅ All tests pass with 95%+ coverage

## Technical Requirements

### Class: QueryExecutor

```python
import pandas as pd
from databricks_tools.config.workspace import WorkspaceConfigManager
from databricks_tools.core.connection import ConnectionManager

class QueryExecutor:
    """Repository for executing Databricks SQL queries."""

    def __init__(self, workspace_manager: WorkspaceConfigManager):
        self.workspace_manager = workspace_manager

    def execute_query(
        self,
        query: str,
        workspace: str | None = None,
        parse_dates: list[str] | None = None
    ) -> pd.DataFrame:
        """Execute SQL query and return DataFrame."""
        config = self.workspace_manager.get_workspace_config(workspace)

        with ConnectionManager(config) as connection:
            df = pd.read_sql(query, connection, parse_dates=parse_dates)

        return df

    def execute_query_with_catalog(
        self,
        catalog: str,
        query: str,
        workspace: str | None = None
    ) -> pd.DataFrame:
        """Execute query with catalog context set."""
        config = self.workspace_manager.get_workspace_config(workspace)

        with ConnectionManager(config) as connection:
            cursor = connection.cursor()

            # Set catalog context
            cursor.execute(f"USE CATALOG {catalog}")

            # Execute main query
            cursor.execute(query)

            # Fetch results
            result = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            df = pd.DataFrame(result, columns=columns)

            cursor.close()

        return df
```

## Design Patterns Used
- **Repository Pattern**: Abstracts data access
- **Dependency Injection**: Receives WorkspaceConfigManager
- **Context Manager**: Uses ConnectionManager

## Key Implementation Notes

### Integration with server.py
```python
# In server.py
_query_executor = QueryExecutor(workspace_manager)

def databricks_sql_query(query: str, parse_dates: list = None, workspace: str | None = None) -> pd.DataFrame:
    """Legacy wrapper."""
    return _query_executor.execute_query(query, workspace, parse_dates)

def databricks_sql_query_with_catalog(catalog: str, query: str, workspace: str | None = None) -> pd.DataFrame:
    """Legacy wrapper."""
    return _query_executor.execute_query_with_catalog(catalog, query, workspace)
```

## Test Cases (13 tests)

1. **test_query_executor_simple_query**
2. **test_query_executor_with_workspace**
3. **test_query_executor_parse_dates**
4. **test_query_executor_empty_result**
5. **test_query_executor_large_result**
6. **test_query_executor_query_error**
7. **test_query_executor_connection_error**
8. **test_query_executor_with_catalog**
9. **test_query_executor_catalog_not_exists**
10. **test_query_executor_multiple_queries**
11. **test_query_executor_workspace_fallback**
12. **test_query_executor_invalid_workspace**
13. **test_legacy_wrapper_functions**

## Files
- **Create**: `src/databricks_tools/core/query_executor.py`
- **Modify**: `src/databricks_tools/server.py` (add wrappers)
- **Test**: `tests/test_core/test_query_executor.py`

## Expected Outcome
Repository pattern implemented, ready for all business services (Phase 3).

## Related Stories
- **Depends on**: US-1.2, US-2.2
- **Blocks**: US-3.1, US-3.2, US-3.3
- **Completes**: Phase 2 - Core Services
