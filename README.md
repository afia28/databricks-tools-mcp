# Databricks Tools MCP Server

A Model Context Protocol (MCP) server for Databricks Unity Catalog exploration with role-based access control.

## Features

- Role-based access control (Analyst/Developer modes)
- Multi-workspace support
- SQL query execution with automatic response chunking
- Unity Catalog exploration (catalogs, schemas, tables, columns)
- Token-aware response management (9000 token limit per response)
- User-defined function (UDF) management
- 13 comprehensive MCP tools

## Quick Start

### Installation

```bash
# Clone/navigate to the repository
cd databricks-tools-clean

# Install dependencies
uv sync

# Create environment file
cp .env.example .env
# Edit .env with your Databricks credentials
```

### Configuration

Edit `.env` with your Databricks workspace details:

```bash
DATABRICKS_SERVER_HOSTNAME=https://your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_TOKEN=dapi_your_token_here
```

For multiple workspaces (developer mode only), add prefixed variables:
```bash
PRODUCTION_DATABRICKS_SERVER_HOSTNAME=https://prod.cloud.databricks.com
PRODUCTION_DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/prod-id
PRODUCTION_DATABRICKS_TOKEN=dapi_prod_token
```

### Running the Server

```bash
# Analyst mode (default workspace only)
uv run databricks-tools

# Developer mode (all configured workspaces)
uv run databricks-tools --developer
```

### Claude Desktop Integration

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

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

## Available Tools

| Tool | Description |
|------|-------------|
| `list_workspaces` | List all configured workspaces |
| `get_table_row_count` | Get row count for a table |
| `get_table_details` | Fetch table schema and sample data |
| `run_query` | Execute arbitrary SQL queries |
| `list_catalogs` | List all Unity Catalog catalogs |
| `list_schemas` | List schemas in catalogs |
| `list_tables` | List tables in schemas |
| `list_columns` | Get column metadata for tables |
| `list_user_functions` | List UDFs in a catalog.schema |
| `describe_function` | Get detailed UDF information |
| `list_and_describe_all_functions` | List and describe all UDFs |
| `get_chunk` | Retrieve chunked response data |
| `get_chunking_session_info` | Get chunking session information |

## Role-Based Access Control

### Analyst Mode (Default)
- Access limited to default workspace only
- Workspace parameters are **ignored**
- Ideal for business users and analysts
- Run: `uv run databricks-tools`

### Developer Mode
- Access to all configured workspaces
- Can switch between workspaces
- Ideal for technical users
- Run: `uv run databricks-tools --developer`

See [ROLES.md](ROLES.md) for detailed information.

## Development

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Install pre-commit hooks
uv run pre-commit install

# Run pre-commit checks
uv run pre-commit run --all-files
```

## Project Structure

```
databricks-tools-clean/
   src/databricks_tools/
      __init__.py
      server.py           # Main MCP server
      config/
         __init__.py
         models.py        # Pydantic configuration models (US-1.1)
         workspace.py     # Workspace configuration manager (US-1.2)
      core/
         __init__.py
         token_counter.py # Token counting utility with caching (US-2.1)
      security/
         __init__.py
         role_manager.py  # Role-based access control manager (US-1.3)
   tests/
      test_config/
         __init__.py
         test_models.py   # Configuration model tests (32 tests, 100% coverage)
         test_workspace.py # Workspace manager tests (14 tests, 94% coverage)
      test_core/
         __init__.py
         test_token_counter.py # Token counter tests (28 tests, 100% coverage)
      test_security/
         __init__.py
         test_role_manager.py # Role manager tests (21 tests, 92% coverage)
   .github/workflows/
      ci.yml              # CI/CD pipeline
      claude-code.yml     # Claude Code integration
   .claude/
      CLAUDE.md           # Development guide
      settings.local.json # Claude permissions
   pyproject.toml          # Project config
   .env.example            # Environment template
   README.md               # This file
   ROLES.md                # Role documentation
```

## Documentation

- [CLAUDE.md](.claude/CLAUDE.md) - Development guide for Claude Code
- [ROLES.md](ROLES.md) - Role-based access control details
- `.env.example` - Configuration options

## Security

- Store credentials in `.env` (never commit to git)
- Rotate tokens regularly
- Use appropriate Databricks permissions
- Consider service principals for production

## License

MIT
