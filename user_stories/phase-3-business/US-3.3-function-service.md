# US-3.3: Create Function Service

## Metadata
- **Story ID**: US-3.3
- **Title**: Create Function Service
- **Phase**: Phase 3 - Business Services
- **Estimated LOC**: ~140 lines
- **Dependencies**: US-2.1 (TokenCounter), US-2.3 (QueryExecutor)
- **Status**: ⬜ Not Started

## Overview
Extract UDF operations into FunctionService. Handles list_user_functions, describe_function, list_and_describe_all_functions.

## User Story
**As a** developer
**I want** UDF operations centralized in a service
**So that** function logic is reusable and consistently enforces token limits

## Acceptance Criteria
1. ✅ FunctionService class created
2. ✅ list_user_functions() method implemented
3. ✅ describe_function() method implemented
4. ✅ list_and_describe_all_functions() method implemented
5. ✅ Function description parsing centralized
6. ✅ MCP tools use service
7. ✅ All tests pass with 90%+ coverage

## Technical Requirements

### Class: FunctionService

```python
class FunctionService:
    """Service for user-defined function operations."""

    def __init__(self, query_executor: QueryExecutor, token_counter: TokenCounter, max_tokens: int = 9000):
        self.query_executor = query_executor
        self.token_counter = token_counter
        self.max_tokens = max_tokens

    def list_user_functions(self, catalog: str, schema: str, workspace: str | None = None) -> dict:
        """List all UDFs in catalog.schema."""
        pass

    def describe_function(self, function_name: str, catalog: str, schema: str, workspace: str | None = None) -> dict:
        """Get detailed function information."""
        pass

    def list_and_describe_all_functions(self, catalog: str, schema: str, workspace: str | None = None) -> dict:
        """List and describe all functions."""
        pass

    def _parse_function_description(self, df: pd.DataFrame) -> list[str]:
        """Parse DESCRIBE FUNCTION EXTENDED output."""
        pass
```

## Test Cases (11 tests)
1. test_function_service_list_functions
2. test_function_service_describe_function
3. test_function_service_list_and_describe_all
4. test_function_service_parse_description
5. test_function_service_no_functions
6. test_function_service_invalid_function
7. test_function_service_catalog_schema_defaults
8. test_function_service_token_limit
9. test_function_service_workspace_parameter
10. test_function_service_error_handling
11. test_integration_with_mcp_tools

## Files
- **Create**: `src/databricks_tools/services/function_service.py`
- **Modify**: `src/databricks_tools/server.py`
- **Test**: `tests/test_services/test_function_service.py`

## Expected Outcome
All business services complete, ready for chunking (Phase 4).

## Related Stories
- **Depends on**: US-2.1, US-2.3
- **Completes**: Phase 3 - Business Services
