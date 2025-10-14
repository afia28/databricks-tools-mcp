# US-3.2: Create Table Service

## Metadata
- **Story ID**: US-3.2
- **Title**: Create Table Service
- **Phase**: Phase 3 - Business Services
- **Estimated LOC**: ~150 lines
- **Dependencies**: US-2.1 (TokenCounter), US-2.3 (QueryExecutor)
- **Status**: ⬜ Not Started

## Overview
Extract table operations into TableService. Handles list_tables, list_columns, get_table_row_count, get_table_details.

## User Story
**As a** developer
**I want** table operations centralized in a service
**So that** table logic is reusable and consistently enforces token limits

## Acceptance Criteria
1. ✅ TableService class created
2. ✅ list_tables() method implemented
3. ✅ list_columns() method implemented
4. ✅ get_table_row_count() method implemented
5. ✅ get_table_details() method implemented
6. ✅ Token checking centralized
7. ✅ MCP tools use service
8. ✅ All tests pass with 90%+ coverage

## Technical Requirements

### Class: TableService

```python
class TableService:
    """Service for table operations."""

    def __init__(self, query_executor: QueryExecutor, token_counter: TokenCounter, max_tokens: int = 9000):
        self.query_executor = query_executor
        self.token_counter = token_counter
        self.max_tokens = max_tokens

    def list_tables(self, catalog: str, schemas: list[str], workspace: str | None = None) -> dict[str, list[str]]:
        """List tables for given catalog and schemas."""
        pass

    def list_columns(self, catalog: str, schema: str, tables: list[str], workspace: str | None = None) -> dict[str, list[dict]]:
        """List columns with metadata for given tables."""
        pass

    def get_table_row_count(self, catalog: str, schema: str, table_name: str, workspace: str | None = None) -> dict:
        """Get row count and pagination estimates."""
        pass

    def get_table_details(self, catalog: str, schema: str, table_name: str, limit: int | None = 1000, workspace: str | None = None) -> dict:
        """Get table schema and sample data."""
        pass
```

## Test Cases (12 tests)
1. test_table_service_list_tables
2. test_table_service_list_columns
3. test_table_service_get_row_count
4. test_table_service_get_details
5. test_table_service_get_details_no_limit
6. test_table_service_large_table
7. test_table_service_empty_table
8. test_table_service_invalid_table
9. test_table_service_token_limit
10. test_table_service_workspace_parameter
11. test_table_service_pagination_estimates
12. test_integration_with_mcp_tools

## Files
- **Create**: `src/databricks_tools/services/table_service.py`
- **Modify**: `src/databricks_tools/server.py`
- **Test**: `tests/test_services/test_table_service.py`

## Related Stories
- **Depends on**: US-2.1, US-2.3
- **Blocks**: US-3.3
