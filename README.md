# Databricks Tools MCP Server

A Model Context Protocol (MCP) server for Databricks Unity Catalog exploration with role-based access control.

## Features

- Role-based access control (Analyst/Developer modes)
- Multi-workspace support
- SQL query execution with automatic response chunking
- Unity Catalog exploration (catalogs, schemas, tables, columns)
- Centralized response management with automatic token validation
- Smart response chunking (9000 token limit per response)
- Consistent error formatting across all tools
- User-defined function (UDF) management
- 13 comprehensive MCP tools

## Quick Start

### Installation

**Option 1: Interactive Wizard (Recommended)**

The easiest way to get started:

```bash
# Clone the repository
git clone https://github.com/afia28/databricks-tools.git
cd databricks-tools

# Install dependencies
uv sync

# Run interactive setup wizard
uv run databricks-tools-init

# Follow the prompts to configure your workspace
# Restart Claude Desktop when complete
```

The wizard will:
- Guide you through credential collection
- Validate your Databricks connection
- Update Claude Desktop configuration automatically
- Create a secure `.env` file

**Option 2: Manual Installation**

For advanced users or custom setups:

```bash
# Clone/navigate to the repository
cd databricks-tools

# Install dependencies
uv sync

# Create environment file
cp .env.example .env
# Edit .env with your Databricks credentials
```

See [INSTALLATION.md](INSTALLATION.md) for detailed installation instructions, troubleshooting, and platform-specific guidance.

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

# Type checking
uv run mypy .

# Install pre-commit hooks (includes mypy, pytest, coverage)
uv run pre-commit install

# Run pre-commit checks (includes type checking, tests, 85% coverage threshold)
uv run pre-commit run --all-files

# Run tests manually
uv run pytest tests/

# Run tests with coverage
uv run pytest tests/ --cov=src/databricks_tools --cov-report=term-missing
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
         connection.py    # Database connection manager (US-2.2)
         query_executor.py # SQL query executor service (US-2.3)
      security/
         __init__.py
         role_manager.py  # Role-based access control manager (US-1.3)
      services/
         __init__.py
         catalog_service.py  # Catalog operations service (US-3.1)
         table_service.py    # Table operations service (US-3.2)
         function_service.py # UDF operations service (US-3.3)
         chunking_service.py # Response chunking service (US-4.1)
         response_manager.py # Response formatting manager (US-4.2)
   tests/
      test_config/
         __init__.py
         test_models.py   # Configuration model tests (32 tests, 100% coverage)
         test_workspace.py # Workspace manager tests (14 tests, 94% coverage)
      test_core/
         __init__.py
         test_token_counter.py # Token counter tests (28 tests, 100% coverage)
         test_connection.py    # Connection manager tests (16 tests, 100% coverage)
         test_query_executor.py # Query executor tests (22 tests, 100% coverage)
      test_security/
         __init__.py
         test_role_manager.py # Role manager tests (21 tests, 92% coverage)
      test_services/
         __init__.py
         test_catalog_service.py  # Catalog service tests (30 tests, 100% coverage)
         test_table_service.py    # Table service tests (41 tests, 100% coverage)
         test_function_service.py # Function service tests (36 tests, 100% coverage)
         test_chunking_service.py # Chunking service tests (30 tests, 100% coverage)
         test_response_manager.py # Response manager tests (39 tests, 100% coverage)
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

## Architecture

This project follows clean architecture principles with a modular, type-safe design. See [ARCHITECTURE.md](ARCHITECTURE.md) for comprehensive documentation.

### Design Patterns

The codebase implements several well-established design patterns:

- **Repository Pattern** (`QueryExecutor`) - Abstracts database access and provides clean data operations interface
- **Strategy Pattern** (`RoleManager`) - Implements role-based access control with interchangeable strategies (AnalystStrategy, DeveloperStrategy)
- **Factory Pattern** (`WorkspaceConfig.from_env`) - Encapsulates complex object creation from environment variables
- **Dependency Injection** (`ApplicationContainer`) - Wires all dependencies and eliminates global state
- **Service Layer Pattern** - Business logic organized into focused service classes (CatalogService, TableService, FunctionService, ChunkingService, ResponseManager)
- **Context Manager Protocol** (`ConnectionManager`) - Ensures safe resource management for database connections

### Component Overview

```
MCP Client → Server (13 Tools) → ApplicationContainer → Services → Core → Databricks
```

**Layers:**
- **MCP Server** - 13 tools exposing functionality via Model Context Protocol
- **Application Container** - Dependency injection container wiring all services
- **Service Layer** - Business logic (catalog, table, function, chunking, response services)
- **Core Services** - Token counting, connection management, query execution
- **Security Layer** - Role-based access control with strategy pattern
- **Configuration** - Pydantic models for type-safe configuration

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed diagrams and data flow documentation.

## Usage Examples

The `examples/` directory contains comprehensive usage examples:

- **[basic_usage.py](examples/basic_usage.py)** - Simple operations, error handling, workspace configuration
- **[advanced_queries.py](examples/advanced_queries.py)** - Complex SQL, multi-workspace queries, response chunking
- **[custom_service.py](examples/custom_service.py)** - Creating custom services with dependency injection
- **[testing_example.py](examples/testing_example.py)** - Testing patterns, mocking, fixtures, coverage strategies

### Quick Example: Listing Catalogs

```python
from databricks_tools.core.container import ApplicationContainer
from databricks_tools.security.role_manager import Role

# Create application container
container = ApplicationContainer(role=Role.ANALYST)

# List all catalogs
catalogs = container.catalog_service.list_catalogs()
print(f"Available catalogs: {catalogs['catalogs']}")
```

### Quick Example: Running Queries

```python
from databricks_tools.core.container import ApplicationContainer

# Create container
container = ApplicationContainer()

# Execute SQL query
result_df = container.query_executor.execute_query(
    "SELECT * FROM main.default.my_table LIMIT 10"
)

print(result_df)
```

See [examples/](examples/) for more comprehensive examples.

## Documentation

- [INSTALLATION.md](INSTALLATION.md) - Detailed installation guide with troubleshooting
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture documentation with design patterns and diagrams
- [CLAUDE.md](CLAUDE.md) - Development guide for Claude Code
- [ROLES.md](ROLES.md) - Role-based access control details
- [CHANGELOG.md](CHANGELOG.md) - Version history and release notes
- [examples/](examples/) - Usage examples and patterns
- `.env.example` - Configuration options

## Security

- Store credentials in `.env` (never commit to git)
- Rotate tokens regularly
- Use appropriate Databricks permissions
- Consider service principals for production

## License

MIT
