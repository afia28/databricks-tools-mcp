# Databricks Tools MCP Server

## Quick Commands

```bash
# Setup
uv sync                              # Install dependencies
cp .env.example .env                 # Create environment file
# Edit .env with your Databricks credentials

# Run Server
uv run databricks-tools              # Analyst mode (default workspace only)
uv run databricks-tools --developer  # Developer mode (all workspaces)

# Development
uv run ruff check .                  # Lint code
uv run ruff format .                 # Format code
pre-commit run --all-files           # Run all pre-commit hooks

# Testing
uv run python src/databricks_tools/server.py  # Test directly
uv run pytest tests/                           # Run all tests
uv run pytest tests/ --cov=src/databricks_tools  # Run tests with coverage
```

## Project Structure

- `src/databricks_tools/server.py` - Main MCP server with all 13 tools
- `src/databricks_tools/config/models.py` - Pydantic configuration models (US-1.1)
- `src/databricks_tools/config/workspace.py` - Workspace configuration manager (US-1.2)
- `src/databricks_tools/core/token_counter.py` - Token counting utility with caching (US-2.1)
- `src/databricks_tools/core/connection.py` - Database connection manager (US-2.2)
- `src/databricks_tools/core/query_executor.py` - SQL query executor service (US-2.3)
- `src/databricks_tools/core/container.py` - Application container for dependency injection (US-5.1)
- `src/databricks_tools/security/role_manager.py` - Role-based access control manager (US-1.3)
- `src/databricks_tools/services/catalog_service.py` - Catalog operations service (US-3.1)
- `src/databricks_tools/services/table_service.py` - Table operations service (US-3.2)
- `src/databricks_tools/services/function_service.py` - UDF operations service (US-3.3)
- `src/databricks_tools/services/chunking_service.py` - Response chunking service (US-4.1)
- `src/databricks_tools/services/response_manager.py` - Response formatting manager (US-4.2)
- `tests/test_config/test_models.py` - Configuration model tests (32 tests, 100% coverage)
- `tests/test_config/test_workspace.py` - Workspace manager tests (14 tests, 94% coverage)
- `tests/test_core/test_token_counter.py` - Token counter tests (28 tests, 100% coverage)
- `tests/test_core/test_connection.py` - Connection manager tests (16 tests, 100% coverage)
- `tests/test_core/test_query_executor.py` - Query executor tests (22 tests, 100% coverage)
- `tests/test_core/test_container.py` - Application container tests (23 tests, 100% coverage)
- `tests/test_security/test_role_manager.py` - Role manager tests (21 tests, 92% coverage)
- `tests/test_services/test_catalog_service.py` - Catalog service tests (30 tests, 100% coverage)
- `tests/test_services/test_table_service.py` - Table service tests (41 tests, 100% coverage)
- `tests/test_services/test_function_service.py` - Function service tests (36 tests, 100% coverage)
- `tests/test_services/test_chunking_service.py` - Chunking service tests (30 tests, 100% coverage)
- `tests/test_services/test_response_manager.py` - Response manager tests (39 tests, 100% coverage)
- `pyproject.toml` - Project configuration and dependencies
- `.env` - Databricks workspace credentials (not in git)

## Key Features

1. **Multi-Workspace Support**: Configure multiple Databricks workspaces via environment variables
2. **Role-Based Access**: Analyst (default workspace only) vs Developer (all workspaces)
3. **Automatic Chunking**: Responses exceeding 9000 tokens are automatically chunked
4. **13 MCP Tools**: Comprehensive Databricks Unity Catalog exploration

## Adding to Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "databricks-tools": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/ahmed/PycharmProjects/PythonProject/databricks-tools-clean",
        "databricks-tools"
      ]
    }
  }
}
```

## Environment Variables

See `.env.example` for all configuration options.

**Analyst Mode (Default):**
- Uses `DATABRICKS_*` variables only
- Single workspace access

**Developer Mode:**
- Uses prefixed variables (e.g., `PRODUCTION_DATABRICKS_*`)
- Multiple workspace access

## Available MCP Tools

1. `list_workspaces` - List configured workspaces
2. `get_table_row_count` - Count rows in a table
3. `get_table_details` - Fetch table schema and data
4. `run_query` - Execute SQL queries
5. `list_catalogs` - List all catalogs
6. `list_schemas` - List schemas in catalogs
7. `list_tables` - List tables in schemas
8. `list_columns` - List columns with metadata
9. `list_user_functions` - List UDFs in catalog.schema
10. `describe_function` - Describe a specific UDF
11. `list_and_describe_all_functions` - List and describe all UDFs
12. `get_chunk` - Retrieve chunked response data
13. `get_chunking_session_info` - Get chunk session info

## Making Changes

For incremental improvements:
1. Make small, focused changes
2. Test immediately with `uv run databricks-tools`
3. Run linting: `uv run ruff check . && uv run ruff format .`
4. Commit frequently

## Troubleshooting

- **Import errors**: Run `uv sync` to install dependencies
- **Connection errors**: Check `.env` file has correct credentials
- **Token errors**: Verify Databricks tokens haven't expired
- **MCP errors**: Test with `uv run databricks-tools` directly

## User Story Status

### Completed User Stories

**US-1.1: Pydantic Configuration Models** - Completed
- Created WorkspaceConfig and ServerConfig Pydantic models
- Comprehensive validation and type safety
- 32 tests, 100% coverage

**US-1.2: Extract Workspace Configuration Manager** - Completed
- WorkspaceConfigManager with Factory pattern
- Role-based access control (analyst/developer modes)
- Workspace discovery from environment variables
- Backward compatible integration with server.py
- 14 tests, 94% coverage

**US-1.3: Create Role-Based Access Control Manager** - Completed
- Implemented Strategy pattern for role-based access control
- Role enum (ANALYST, DEVELOPER) for type-safe role definitions
- RoleStrategy ABC with AnalystStrategy and DeveloperStrategy implementations
- RoleManager delegates workspace access decisions to appropriate strategy
- Integrated with WorkspaceConfigManager (backward compatible)
- Updated server.py to use RoleManager instead of string-based roles
- 21 tests, 92% coverage

**US-2.1: Token Counter Utility** - Completed
- Created TokenCounter class in core package for token counting with caching
- Implemented count_tokens method for text strings
- Implemented estimate_tokens method for JSON/dict objects
- Implemented estimate_response_tokens method with formatting options
- Used @lru_cache decorator for encoding caching (maxsize=4)
- Supports multiple models (gpt-4, gpt-3.5-turbo, cl100k_base, etc.)
- Graceful fallback to cl100k_base for unknown models
- Wrapper functions in server.py maintain backward compatibility
- 28 tests, 100% coverage

**US-2.2: Database Connection Manager** - Completed
- Created ConnectionManager class with context manager protocol
- Implements __enter__ and __exit__ for automatic resource management
- Accepts WorkspaceConfig for connection parameters
- Automatically closes connections on context exit
- Supports connection pooling through connection reuse
- Handles connection errors gracefully with proper exception propagation
- Full integration with databricks.sql.connect
- SecretStr handling for secure access token management
- 16 tests, 100% coverage

**US-2.3: Query Executor Service** - Completed
- Created QueryExecutor class using Repository pattern
- Implements execute_query method returning pandas DataFrame
- Implements execute_query_with_catalog for catalog context queries
- Integrates with ConnectionManager for safe resource management
- Uses WorkspaceConfigManager for workspace resolution
- Legacy wrapper functions in server.py maintain backward compatibility
- Handles query errors gracefully with proper exception propagation
- Full type hints and Google-style docstrings
- 22 tests, 100% coverage
- Phase 2 - Core Services: COMPLETE

**US-3.1: Create Catalog Service** - Completed
- Created CatalogService class in services package
- Implements list_catalogs and list_schemas methods
- Delegates to QueryExecutor for database operations
- Full dependency injection pattern with TokenCounter and QueryExecutor
- 30 tests, 100% coverage

**US-3.2: Create Table Service** - Completed
- Created TableService class in services package
- Implements list_tables, list_columns, get_table_row_count, get_table_details methods
- Filters internal Databricks columns (_rescued_data)
- Full dependency injection pattern
- 41 tests, 100% coverage

**US-3.3: Create Function Service** - Completed
- Created FunctionService class in services package
- Implements list_user_functions, describe_function, list_and_describe_all_functions methods
- Parses and filters UDF descriptions for cleaner output
- Full dependency injection pattern
- 36 tests, 100% coverage
- Total tests: 267 tests, all passing
- Phase 3 - Service Layer: COMPLETE

**US-4.1: Create Chunking Service** - Completed
- Created ChunkingService class in services package
- Implements create_chunked_response, get_chunk, get_session_info methods
- Session-based state management with UUID session IDs
- Automatic session cleanup/expiry mechanism (60-minute TTL)
- Replaced global CHUNK_SESSIONS dict with service instance
- Integrated with get_chunk and get_chunking_session_info MCP tools
- 30 tests, 100% coverage

**US-4.2: Create Response Manager** - Completed
- Created ResponseManager class in services package for centralized response formatting
- Implements format_response() with automatic token checking and chunking
- Implements format_error() for consistent error response formatting
- Integrated with all 13 MCP tools in server.py
- Eliminated ~200 lines of duplicated JSON serialization code
- Reduced server.py by 62 net lines through code reuse
- Automatic chunking for responses exceeding 9000 token limit
- Support for auto_chunk=False parameter for special cases
- 39 tests, 100% coverage
- Total tests: 306 tests, all passing
- Phase 4 - Chunking & Response Management: COMPLETE

**US-5.1: Create Application Container** - Completed
- Created ApplicationContainer class in core package for dependency injection
- Wires all 9 services with proper dependencies (role_manager, workspace_manager, token_counter, query_executor, catalog_service, table_service, function_service, chunking_service, response_manager)
- Eliminates global state through instance-based design
- Supports role-based configuration (ANALYST/DEVELOPER modes)
- Configurable max_tokens parameter propagated to all services
- Easy test container creation for unit testing
- Multiple independent containers can coexist
- 23 tests, 100% coverage
- Total tests: 329 tests, all passing
- Applied code formatting to 20 files (net -240 lines)
- Phase 5 - Integration: IN PROGRESS
