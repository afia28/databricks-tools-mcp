# US-2.2: Create Database Connection Manager

## Metadata
- **Story ID**: US-2.2
- **Title**: Create Database Connection Manager
- **Phase**: Phase 2 - Core Services
- **Estimated LOC**: ~90 lines
- **Dependencies**: US-1.1 (Pydantic Models), US-1.2 (Workspace Manager)
- **Status**: ⬜ Not Started

## Overview
Create a ConnectionManager class to handle Databricks SQL connections with context manager support for safe resource handling.

## User Story
**As a** developer
**I want** centralized database connection management
**So that** connections are safely handled and reusable across services

## Acceptance Criteria
1. ✅ ConnectionManager class with context manager protocol
2. ✅ Accepts WorkspaceConfig for connection parameters
3. ✅ Automatically closes connections
4. ✅ Supports connection pooling (future-ready)
5. ✅ Handles connection errors gracefully
6. ✅ All tests pass with 95%+ coverage

## Technical Requirements

### Class: ConnectionManager

```python
from databricks import sql
from databricks_tools.config.models import WorkspaceConfig
from typing import Optional

class ConnectionManager:
    """Manages Databricks SQL connections with context manager support."""

    def __init__(self, config: WorkspaceConfig):
        self.config = config
        self._connection: Optional[sql.Connection] = None

    def __enter__(self) -> sql.Connection:
        """Context manager entry - create connection."""
        self._connection = sql.connect(
            server_hostname=self.config.server_hostname,
            http_path=self.config.http_path,
            access_token=self.config.access_token
        )
        return self._connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def get_connection(self) -> sql.Connection:
        """Get connection (for non-context manager usage)."""
        if not self._connection:
            self._connection = sql.connect(
                server_hostname=self.config.server_hostname,
                http_path=self.config.http_path,
                access_token=self.config.access_token
            )
        return self._connection

    def close(self):
        """Explicitly close connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
```

## Design Patterns Used
- **Context Manager**: Safe resource management with `__enter__`/`__exit__`
- **Factory**: Creates connections from configuration
- **Resource Management**: Ensures connections are closed

## Test Cases (12 tests)

1. **test_connection_manager_context_manager**
2. **test_connection_manager_auto_close**
3. **test_connection_manager_get_connection**
4. **test_connection_manager_explicit_close**
5. **test_connection_manager_invalid_credentials**
6. **test_connection_manager_connection_error**
7. **test_connection_manager_reuse_connection**
8. **test_connection_manager_multiple_contexts**
9. **test_connection_manager_exception_handling**
10. **test_connection_manager_from_workspace_config**
11. **test_connection_manager_connection_properties**
12. **test_connection_manager_is_closed**

## Files
- **Create**: `src/databricks_tools/core/connection.py`
- **Test**: `tests/test_core/test_connection.py`

## Expected Outcome
Safe, reusable connection management ready for QueryExecutor (US-2.3).

## Related Stories
- **Depends on**: US-1.1, US-1.2
- **Blocks**: US-2.3
