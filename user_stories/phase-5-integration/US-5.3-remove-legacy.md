# US-5.3: Remove Legacy Helper Functions

## Metadata
- **Story ID**: US-5.3
- **Title**: Remove Legacy Helper Functions from server.py
- **Phase**: Phase 5 - MCP Tool Integration
- **Estimated LOC**: ~100 lines removed
- **Dependencies**: US-5.2 (Refactored Tools)
- **Status**: ⬜ Not Started

## Overview
Clean up server.py by removing old helper functions that have been replaced by services. This completes the refactoring.

## User Story
**As a** developer
**I want** server.py to contain only MCP tool definitions
**So that** the codebase is clean and maintainable

## Acceptance Criteria
1. ✅ All old helper functions removed
2. ✅ Only MCP tools and container remain
3. ✅ No duplicate logic
4. ✅ All imports cleaned up
5. ✅ All tests still pass
6. ✅ Full regression suite passes

## Functions to Remove
1. get_workspace_config()
2. get_available_workspaces()
3. count_tokens()
4. estimate_response_tokens()
5. create_chunked_response()
6. databricks_sql_query()
7. databricks_sql_query_with_catalog()

## Global State to Remove
1. ROLE (replaced by container)
2. CHUNK_SESSIONS (replaced by service)
3. MAX_RESPONSE_TOKENS (moved to container)

## Final server.py Structure
```python
# Imports
from databricks_tools.core.container import ApplicationContainer
from mcp.server.fastmcp import FastMCP

# Initialize
load_dotenv()
mcp = FastMCP("databricks_sql")

# Container (initialized in main())
container: ApplicationContainer | None = None

# 13 MCP tool definitions (@mcp.tool())
...

# main() function
def main():
    global container
    args = parser.parse_args()
    role = Role.DEVELOPER if args.developer else Role.ANALYST
    container = ApplicationContainer(role=role)
    mcp.run(transport="stdio")
```

## Test Cases
- Full regression test suite
- Verify all 13 tools work
- Verify role-based access
- Verify chunking works
- Performance benchmarks

## Files
- **Modify**: `src/databricks_tools/server.py` (cleanup)
- **Test**: `tests/test_integration/` (full suite)

## Expected Outcome
Clean, modular server.py with ~300 lines (down from 1231).

## Related Stories
- **Depends on**: US-5.2
- **Completes**: Phase 5 - MCP Tool Integration
