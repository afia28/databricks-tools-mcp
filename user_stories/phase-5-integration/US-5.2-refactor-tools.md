# US-5.2: Refactor MCP Tools to Use Services

## Metadata
- **Story ID**: US-5.2
- **Title**: Refactor All MCP Tools to Use Services
- **Phase**: Phase 5 - MCP Tool Integration
- **Estimated LOC**: ~200 lines changed
- **Dependencies**: US-5.1 (ApplicationContainer)
- **Status**: ⬜ Not Started

## Overview
Update all 13 MCP tools to use injected services from ApplicationContainer. Keep tool signatures identical for backward compatibility.

## User Story
**As a** developer
**I want** MCP tools to use injected services
**So that** tools are thin wrappers around business logic

## Acceptance Criteria
1. ✅ All 13 MCP tools updated
2. ✅ Tools use container services
3. ✅ Tool signatures unchanged
4. ✅ All tools tested and working
5. ✅ No breaking changes
6. ✅ Integration tests pass

## Tools to Refactor (13 total)

### 1. list_workspaces
```python
@mcp.tool()
async def list_workspaces() -> str:
    workspaces = container.workspace_manager.get_available_workspaces()
    return container.response_manager.format_response(workspaces)
```

### 2-3. Chunking Tools
- get_chunk
- get_chunking_session_info

### 4-5. Table Tools
- get_table_row_count
- get_table_details

### 6. Query Tool
- run_query

### 7-8. Catalog Tools
- list_catalogs
- list_schemas

### 9-10. Table Metadata
- list_tables
- list_columns

### 11-13. Function Tools
- list_user_functions
- describe_function
- list_and_describe_all_functions

## Test Strategy
- Update each tool incrementally
- Test after each change
- Keep integration tests passing
- Verify backward compatibility

## Files
- **Modify**: `src/databricks_tools/server.py` (all tools)
- **Test**: `tests/test_integration/` (verify all tools work)

## Related Stories
- **Depends on**: US-5.1
- **Blocks**: US-5.3
