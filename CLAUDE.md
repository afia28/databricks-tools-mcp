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
- `src/databricks_tools/security/role_manager.py` - Role-based access control manager (US-1.3)
- `tests/test_config/test_models.py` - Configuration model tests (32 tests, 100% coverage)
- `tests/test_config/test_workspace.py` - Workspace manager tests (14 tests, 94% coverage)
- `tests/test_security/test_role_manager.py` - Role manager tests (21 tests, 92% coverage)
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
- Total tests: 67 tests, all passing
