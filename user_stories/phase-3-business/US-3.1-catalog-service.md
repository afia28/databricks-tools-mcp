# US-3.1: Create Catalog Service

## Metadata
- **Story ID**: US-3.1
- **Title**: Create Catalog Service
- **Phase**: Phase 3 - Business Services
- **Estimated LOC**: ~120 lines
- **Dependencies**: US-2.1 (TokenCounter), US-2.3 (QueryExecutor)
- **Status**: ⬜ Not Started

## Overview
Extract catalog/schema listing logic into CatalogService. Consolidates duplicated token checking and error handling.

## User Story
**As a** developer
**I want** catalog operations centralized in a service
**So that** catalog logic is reusable and consistently enforces token limits

## Acceptance Criteria
1. ✅ CatalogService class created
2. ✅ list_catalogs() method implemented
3. ✅ list_schemas() method implemented
4. ✅ Token checking centralized (no duplication)
5. ✅ Error handling consistent across methods
6. ✅ MCP tools use service (backward compatible)
7. ✅ All tests pass with 90%+ coverage

## Technical Requirements

### Class: CatalogService

```python
from databricks_tools.core.query_executor import QueryExecutor
from databricks_tools.core.token_counter import TokenCounter

class CatalogService:
    """Service for Unity Catalog operations."""

    def __init__(self, query_executor: QueryExecutor, token_counter: TokenCounter, max_tokens: int = 9000):
        self.query_executor = query_executor
        self.token_counter = token_counter
        self.max_tokens = max_tokens

    def list_catalogs(self, workspace: str | None = None) -> list[str]:
        """List all catalogs in workspace."""
        query = "SHOW CATALOGS"
        df = self.query_executor.execute_query(query, workspace)
        catalogs = df["catalog"].tolist()
        return catalogs

    def list_schemas(self, catalogs: list[str], workspace: str | None = None) -> dict[str, list[str]]:
        """List schemas for given catalogs."""
        result = {}
        for catalog in catalogs:
            query = f"SHOW SCHEMAS IN {catalog}"
            df = self.query_executor.execute_query(query, workspace)
            result[catalog] = df["databaseName"].tolist()
        return result
```

## Test Cases (10 tests)
1. test_catalog_service_list_catalogs
2. test_catalog_service_list_schemas_single
3. test_catalog_service_list_schemas_multiple
4. test_catalog_service_empty_catalogs
5. test_catalog_service_invalid_catalog
6. test_catalog_service_workspace_parameter
7. test_catalog_service_token_limit_check
8. test_catalog_service_error_handling
9. test_integration_with_mcp_tool_list_catalogs
10. test_integration_with_mcp_tool_list_schemas

## Files
- **Create**: `src/databricks_tools/services/__init__.py`, `src/databricks_tools/services/catalog_service.py`
- **Modify**: `src/databricks_tools/server.py` (MCP tools use service)
- **Test**: `tests/test_services/test_catalog_service.py`

## Expected Outcome
Catalog operations centralized, ready for Table Service (US-3.2).

## Related Stories
- **Depends on**: US-2.1, US-2.3
- **Blocks**: US-3.2
