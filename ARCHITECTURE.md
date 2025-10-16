# Databricks Tools MCP Server - Architecture

## Table of Contents
- [Overview](#overview)
- [Design Patterns](#design-patterns)
- [Directory Structure](#directory-structure)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Dependency Injection](#dependency-injection)
- [Testing Strategy](#testing-strategy)

## Overview

The Databricks Tools MCP Server is a modular, type-safe Python application built with clean architecture principles. It provides 13 Model Context Protocol (MCP) tools for exploring and querying Databricks Unity Catalog through a well-structured service layer.

### Key Architectural Goals
- **Modularity**: Clear separation of concerns with dedicated packages for config, core, security, and services
- **Type Safety**: 100% type hint coverage with strict mypy validation
- **Testability**: 99% code coverage with 361 comprehensive tests
- **Maintainability**: Dependency injection eliminates global state and enables easy testing
- **Extensibility**: Service layer pattern allows adding new capabilities without modifying existing code

## Design Patterns

### 1. Repository Pattern
**Location**: `src/databricks_tools/core/query_executor.py`

The QueryExecutor acts as a repository, abstracting database access and providing a clean interface for data operations.

```python
class QueryExecutor:
    def execute_query(self, sql: str, workspace: str = "default") -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame"""

    def execute_query_with_catalog(
        self, sql: str, catalog: str, workspace: str = "default"
    ) -> pd.DataFrame:
        """Execute query with catalog context"""
```

**Benefits**:
- Centralizes all database access logic
- Provides consistent error handling
- Enables easy mocking in tests
- Decouples business logic from data access

### 2. Strategy Pattern
**Location**: `src/databricks_tools/security/role_manager.py`

Role-based access control is implemented using the Strategy pattern with interchangeable role strategies.

```python
class RoleStrategy(ABC):
    @abstractmethod
    def filter_workspaces(
        self, workspaces: dict[str, WorkspaceConfig], default_workspace: str
    ) -> dict[str, WorkspaceConfig]:
        """Filter workspaces based on role permissions"""

class AnalystStrategy(RoleStrategy):
    """Analyst role: access to default workspace only"""

class DeveloperStrategy(RoleStrategy):
    """Developer role: access to all workspaces"""

class RoleManager:
    def __init__(self, role: Role):
        self.role = role
        self._strategy = self._get_strategy()
```

**Benefits**:
- Type-safe role definitions with Role enum
- Easy to add new roles without modifying existing code
- Clear separation of role-specific logic
- Testable role behaviors in isolation

### 3. Factory Pattern
**Location**: `src/databricks_tools/config/models.py`

WorkspaceConfig uses the Factory pattern for creating instances from environment variables.

```python
class WorkspaceConfig(BaseModel):
    @classmethod
    def from_env(cls, prefix: str = "") -> "WorkspaceConfig":
        """Factory method to create workspace config from environment variables"""
        return cls(
            server_hostname=os.getenv(f"{prefix}DATABRICKS_SERVER_HOSTNAME", ""),
            http_path=os.getenv(f"{prefix}DATABRICKS_HTTP_PATH", ""),
            access_token=SecretStr(os.getenv(f"{prefix}DATABRICKS_TOKEN", "")),
        )
```

**Benefits**:
- Encapsulates complex object creation logic
- Provides multiple ways to instantiate objects
- Validates configuration during creation
- Handles environment variable prefixes cleanly

### 4. Dependency Injection Container
**Location**: `src/databricks_tools/core/container.py`

ApplicationContainer wires all dependencies and eliminates global state.

```python
class ApplicationContainer:
    def __init__(
        self,
        role: Role = Role.ANALYST,
        max_tokens: int = 9000,
    ):
        # Core dependencies
        self.role_manager = RoleManager(role)
        self.workspace_manager = WorkspaceConfigManager(self.role_manager)
        self.token_counter = TokenCounter()
        self.query_executor = QueryExecutor(self.workspace_manager)

        # Service layer
        self.catalog_service = CatalogService(self.token_counter, self.query_executor)
        self.table_service = TableService(self.token_counter, self.query_executor)
        self.function_service = FunctionService(self.token_counter, self.query_executor)
        self.chunking_service = ChunkingService()
        self.response_manager = ResponseManager(
            self.token_counter, self.chunking_service, max_tokens
        )
```

**Benefits**:
- Single source of truth for all dependencies
- No global state - multiple containers can coexist
- Easy to create test containers with mocked dependencies
- Clear dependency graph visualization
- Supports different configurations (ANALYST vs DEVELOPER modes)

### 5. Service Layer Pattern
**Location**: `src/databricks_tools/services/`

Business logic is organized into focused service classes, each responsible for a specific domain.

Services:
- **CatalogService**: Catalog and schema operations
- **TableService**: Table listing, details, and row counts
- **FunctionService**: UDF listing and descriptions
- **ChunkingService**: Response chunking and session management
- **ResponseManager**: Response formatting and automatic chunking

**Benefits**:
- Single Responsibility Principle - each service has one purpose
- Reusable business logic across multiple MCP tools
- Testable in isolation with mocked dependencies
- Clear API boundaries

### 6. Context Manager Protocol
**Location**: `src/databricks_tools/core/connection.py`

ConnectionManager implements the context manager protocol for safe resource management.

```python
class ConnectionManager:
    def __enter__(self) -> Connection:
        """Establish database connection"""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Automatically close connection on context exit"""
```

**Benefits**:
- Guaranteed resource cleanup
- Exception-safe connection handling
- Pythonic API using `with` statements
- Prevents connection leaks

## Directory Structure

```
databricks-tools-clean/
├── src/databricks_tools/           # Main application package
│   ├── __init__.py                 # Package initialization
│   ├── py.typed                    # PEP 561 type marker
│   ├── server.py                   # MCP server with 13 tools
│   │
│   ├── config/                     # Configuration & workspace management
│   │   ├── __init__.py
│   │   ├── models.py              # Pydantic models (WorkspaceConfig, ServerConfig)
│   │   └── workspace.py           # WorkspaceConfigManager with factory pattern
│   │
│   ├── core/                       # Core utilities & services
│   │   ├── __init__.py
│   │   ├── container.py           # ApplicationContainer for dependency injection
│   │   ├── token_counter.py       # Token counting with caching
│   │   ├── connection.py          # Database connection manager
│   │   └── query_executor.py      # SQL query executor (repository pattern)
│   │
│   ├── security/                   # Security & access control
│   │   ├── __init__.py
│   │   └── role_manager.py        # Role-based access control (strategy pattern)
│   │
│   └── services/                   # Business logic services
│       ├── __init__.py
│       ├── catalog_service.py     # Catalog operations
│       ├── table_service.py       # Table operations
│       ├── function_service.py    # UDF operations
│       ├── chunking_service.py    # Response chunking
│       └── response_manager.py    # Response formatting
│
├── tests/                          # Comprehensive test suite (361 tests, 99% coverage)
│   ├── test_config/               # Configuration tests (46 tests)
│   │   ├── test_models.py         # Pydantic model tests (32 tests)
│   │   └── test_workspace.py      # Workspace manager tests (14 tests)
│   │
│   ├── test_core/                 # Core service tests (89 tests)
│   │   ├── test_token_counter.py  # Token counter tests (28 tests)
│   │   ├── test_connection.py     # Connection manager tests (16 tests)
│   │   ├── test_query_executor.py # Query executor tests (22 tests)
│   │   └── test_container.py      # Container tests (23 tests)
│   │
│   ├── test_security/             # Security tests (21 tests)
│   │   └── test_role_manager.py   # Role manager tests (21 tests)
│   │
│   ├── test_services/             # Service layer tests (176 tests)
│   │   ├── test_catalog_service.py   # Catalog service tests (30 tests)
│   │   ├── test_table_service.py     # Table service tests (41 tests)
│   │   ├── test_function_service.py  # Function service tests (36 tests)
│   │   ├── test_chunking_service.py  # Chunking service tests (30 tests)
│   │   └── test_response_manager.py  # Response manager tests (39 tests)
│   │
│   └── test_server/               # Integration tests (48 tests)
│       └── test_mcp_tools.py      # MCP tools integration tests
│
├── user_stories/                   # Implementation roadmap
│   ├── phase_1_*.md               # Configuration & Security
│   ├── phase_2_*.md               # Core Services
│   ├── phase_3_*.md               # Service Layer
│   ├── phase_4_*.md               # Response Management
│   ├── phase_5_*.md               # Integration
│   └── phase_6_*.md               # Testing & Quality
│
├── examples/                       # Usage examples
│   ├── basic_usage.py             # Simple query patterns
│   ├── advanced_queries.py        # Complex queries & chunking
│   ├── custom_service.py          # Creating custom services
│   └── testing_example.py         # Testing patterns
│
├── .github/workflows/             # CI/CD pipelines
│   ├── ci.yml                     # Main CI pipeline
│   └── claude-code.yml            # Claude Code integration
│
├── pyproject.toml                 # Project configuration
├── mypy.ini                       # Type checking configuration
├── .pre-commit-config.yaml        # Pre-commit hooks (11 hooks)
├── .env.example                   # Environment template
├── README.md                      # User documentation
├── CLAUDE.md                      # Development guide
├── ARCHITECTURE.md                # This file
├── CHANGELOG.md                   # Version history
└── ROLES.md                       # Role-based access control guide
```

## Component Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         MCP Client                               │
│                    (Claude Desktop, CLI)                         │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 │ MCP Protocol
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                         MCP Server                               │
│                       (server.py)                                │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              13 MCP Tool Functions                       │   │
│  │  • list_workspaces      • list_catalogs                 │   │
│  │  • list_schemas         • list_tables                   │   │
│  │  • list_columns         • get_table_details             │   │
│  │  • get_table_row_count  • run_query                     │   │
│  │  • list_user_functions  • describe_function             │   │
│  │  • list_and_describe_all_functions                      │   │
│  │  • get_chunk            • get_chunking_session_info     │   │
│  └───────────────────────────┬─────────────────────────────┘   │
│                              │                                   │
│                              │ Dependency Injection              │
│                              │                                   │
│  ┌───────────────────────────▼─────────────────────────────┐   │
│  │          ApplicationContainer                            │   │
│  │                                                           │   │
│  │  Wires all dependencies:                                │   │
│  │  • RoleManager (security)                               │   │
│  │  • WorkspaceConfigManager (config)                      │   │
│  │  • TokenCounter (core)                                  │   │
│  │  • QueryExecutor (core)                                 │   │
│  │  • CatalogService (services)                            │   │
│  │  • TableService (services)                              │   │
│  │  • FunctionService (services)                           │   │
│  │  • ChunkingService (services)                           │   │
│  │  • ResponseManager (services)                           │   │
│  └───────────────────────────┬─────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Security Layer │    │   Core Services  │    │ Service Layer   │
│                 │    │                  │    │                 │
│ • RoleManager   │    │ • TokenCounter   │    │ • CatalogSvc    │
│ • Role Enum     │    │ • ConnectionMgr  │    │ • TableSvc      │
│ • Strategies    │    │ • QueryExecutor  │    │ • FunctionSvc   │
│                 │    │                  │    │ • ChunkingSvc   │
│                 │    │                  │    │ • ResponseMgr   │
└─────────────────┘    └────────┬─────────┘    └─────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Databricks SQL      │
                    │   (databricks.sql)    │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Databricks Workspace │
                    │   (Unity Catalog)     │
                    └───────────────────────┘
```

### Layer Responsibilities

#### 1. MCP Server Layer (`server.py`)
- Exposes 13 MCP tools to clients
- Validates input parameters
- Delegates to ApplicationContainer for service access
- Handles MCP protocol communication

#### 2. Security Layer (`security/`)
- **RoleManager**: Orchestrates role-based access control
- **Role Enum**: Type-safe role definitions (ANALYST, DEVELOPER)
- **RoleStrategy**: Abstract strategy for role implementations
- **AnalystStrategy**: Restricts access to default workspace
- **DeveloperStrategy**: Allows access to all workspaces

#### 3. Configuration Layer (`config/`)
- **WorkspaceConfig**: Pydantic model for workspace credentials
- **ServerConfig**: Pydantic model for server settings
- **WorkspaceConfigManager**: Discovers and manages workspace configurations

#### 4. Core Services Layer (`core/`)
- **TokenCounter**: Counts tokens with encoding caching
- **ConnectionManager**: Manages database connections with context protocol
- **QueryExecutor**: Executes SQL queries and returns DataFrames
- **ApplicationContainer**: Wires all dependencies together

#### 5. Business Services Layer (`services/`)
- **CatalogService**: Lists catalogs and schemas
- **TableService**: Manages table operations (list, details, row counts)
- **FunctionService**: Handles UDF operations (list, describe)
- **ChunkingService**: Manages response chunking with sessions
- **ResponseManager**: Formats responses with automatic chunking

## Data Flow

### Request Flow for `run_query` Tool

```
1. MCP Client Request
   │
   ├─► MCP Server receives request
   │   └─► run_query(sql, catalog?, workspace?)
   │
2. Input Validation
   │
   ├─► Validate SQL parameter
   ├─► Validate workspace access (via RoleManager)
   └─► Get WorkspaceConfig (via WorkspaceConfigManager)
   │
3. Query Execution
   │
   ├─► container.query_executor.execute_query()
   │   │
   │   ├─► ConnectionManager creates connection
   │   │   └─► with ConnectionManager(workspace_config):
   │   │
   │   ├─► Execute SQL query
   │   │   └─► cursor.fetchall_arrow().to_pandas()
   │   │
   │   └─► Connection automatically closed (__exit__)
   │
4. Response Formatting
   │
   ├─► container.response_manager.format_response()
   │   │
   │   ├─► Convert DataFrame to dict
   │   │
   │   ├─► TokenCounter estimates response size
   │   │
   │   ├─► If tokens > 9000:
   │   │   └─► ChunkingService.create_chunked_response()
   │   │       ├─► Create session with UUID
   │   │       ├─► Split data into chunks
   │   │       └─► Return first chunk + session info
   │   │
   │   └─► If tokens <= 9000:
   │       └─► Return full response
   │
5. MCP Response
   │
   └─► Return JSON response to client
```

### Workspace Access Flow (Role-Based)

```
1. User runs server with role flag
   │
   ├─► --developer flag → Role.DEVELOPER
   └─► (no flag)       → Role.ANALYST
   │
2. ApplicationContainer initializes
   │
   └─► RoleManager(role)
       │
       ├─► If ANALYST → AnalystStrategy
       │   └─► filter_workspaces() returns {default_workspace}
       │
       └─► If DEVELOPER → DeveloperStrategy
           └─► filter_workspaces() returns all workspaces
   │
3. WorkspaceConfigManager uses filtered workspaces
   │
   └─► get_workspace_config(name)
       │
       ├─► If workspace in allowed_workspaces → return config
       └─► If workspace not allowed → raise ValueError
```

### Response Chunking Flow

```
1. Response exceeds 9000 tokens
   │
2. ChunkingService.create_chunked_response()
   │
   ├─► Generate session_id (UUID4)
   │
   ├─► Calculate chunks_per_response (9000 / row_tokens)
   │
   ├─► Split data into chunks
   │   └─► chunks = [data[i:i+chunks_per_response] for i in range(...)]
   │
   ├─► Store session state
   │   └─► _sessions[session_id] = {
   │           "chunks": chunks,
   │           "total_chunks": len(chunks),
   │           "created_at": datetime.now(),
   │       }
   │
   └─► Return first chunk + metadata
       └─► {
               "chunk_number": 1,
               "total_chunks": N,
               "session_id": "...",
               "data": chunks[0],
               "message": "Use get_chunk tool..."
           }
   │
3. Client calls get_chunk(session_id, chunk_number)
   │
   └─► ChunkingService.get_chunk()
       │
       ├─► Validate session exists
       ├─► Validate chunk_number in range
       └─► Return requested chunk
```

## Dependency Injection

### ApplicationContainer Dependency Graph

```
ApplicationContainer
│
├─► RoleManager
│   └─► Role (enum)
│       ├─► AnalystStrategy
│       └─► DeveloperStrategy
│
├─► WorkspaceConfigManager
│   └─► RoleManager (injected)
│       └─► Filters workspaces based on role
│
├─► TokenCounter
│   └─► No dependencies (standalone utility)
│
├─► QueryExecutor
│   └─► WorkspaceConfigManager (injected)
│       └─► Resolves workspace configurations
│
├─► CatalogService
│   ├─► TokenCounter (injected)
│   └─► QueryExecutor (injected)
│
├─► TableService
│   ├─► TokenCounter (injected)
│   └─► QueryExecutor (injected)
│
├─► FunctionService
│   ├─► TokenCounter (injected)
│   └─► QueryExecutor (injected)
│
├─► ChunkingService
│   └─► No dependencies (manages state internally)
│
└─► ResponseManager
    ├─► TokenCounter (injected)
    ├─► ChunkingService (injected)
    └─► max_tokens (configurable parameter)
```

### Benefits of This Approach

1. **Testability**: Each component can be tested in isolation with mocked dependencies
2. **No Global State**: Multiple containers can coexist with different configurations
3. **Clear Dependencies**: Dependency graph is explicit and easy to understand
4. **Configuration Flexibility**: Role and max_tokens can be configured per container
5. **Lifecycle Management**: Container manages the entire service lifecycle

### Creating Custom Containers for Testing

```python
# Production container (ANALYST mode)
container = ApplicationContainer(role=Role.ANALYST, max_tokens=9000)

# Developer container (all workspaces)
dev_container = ApplicationContainer(role=Role.DEVELOPER, max_tokens=9000)

# Test container with mocked dependencies
test_container = ApplicationContainer(role=Role.ANALYST)
test_container.query_executor = MockQueryExecutor()  # Inject mock
test_container.workspace_manager = MockWorkspaceManager()  # Inject mock
```

## Testing Strategy

### Test Coverage by Layer

| Layer | Tests | Coverage | Key Focus |
|-------|-------|----------|-----------|
| Config | 46 | 96% | Pydantic validation, workspace discovery |
| Core | 89 | 100% | Token counting, connections, queries, DI container |
| Security | 21 | 92% | Role strategies, access control |
| Services | 176 | 100% | Business logic, error handling |
| Integration | 48 | 99% | End-to-end MCP tool flows |
| **Total** | **361** | **99%** | **Comprehensive coverage** |

### Test Categories

#### 1. Unit Tests
- Test individual components in isolation
- Mock all external dependencies
- Focus on business logic correctness
- Example: `test_catalog_service.py`, `test_token_counter.py`

#### 2. Integration Tests
- Test component interactions
- Mock only external services (Databricks)
- Verify data flow through layers
- Example: `test_mcp_tools.py`

#### 3. Validation Tests
- Test Pydantic model validation
- Verify configuration parsing
- Check error handling
- Example: `test_models.py`

#### 4. Strategy Tests
- Test role-based access control
- Verify workspace filtering
- Check permission enforcement
- Example: `test_role_manager.py`

### Quality Gates

All code changes must pass:
1. ✅ **Ruff linting** - Code style and quality
2. ✅ **Ruff formatting** - Consistent code formatting
3. ✅ **Mypy strict mode** - 100% type safety
4. ✅ **Pytest** - All 361 tests passing
5. ✅ **Coverage ≥85%** - Currently at 99%
6. ✅ **Pre-commit hooks** - 11 automated checks

### Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=src/databricks_tools --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_services/test_catalog_service.py

# Run pre-commit checks (includes tests)
uv run pre-commit run --all-files
```

## Extension Points

### Adding New Services

1. Create service class in `services/`
2. Inject required dependencies in `__init__`
3. Add service to `ApplicationContainer`
4. Create comprehensive tests
5. Update this documentation

Example:
```python
# services/metrics_service.py
class MetricsService:
    def __init__(
        self,
        token_counter: TokenCounter,
        query_executor: QueryExecutor,
    ):
        self.token_counter = token_counter
        self.query_executor = query_executor

    def get_table_metrics(self, table: str) -> dict[str, Any]:
        # Implementation
        pass

# core/container.py
class ApplicationContainer:
    def __init__(self, role: Role = Role.ANALYST, max_tokens: int = 9000):
        # ... existing services ...
        self.metrics_service = MetricsService(
            self.token_counter,
            self.query_executor
        )
```

### Adding New Roles

1. Add role to `Role` enum in `security/role_manager.py`
2. Create strategy class implementing `RoleStrategy`
3. Update `RoleManager._get_strategy()` to return new strategy
4. Add tests for new role behavior

### Adding New MCP Tools

1. Add tool function to `server.py`
2. Use `container.{service}` to access dependencies
3. Use `container.response_manager.format_response()` for output
4. Add integration tests in `test_mcp_tools.py`

## Best Practices

1. **Always use type hints** - Enable strict mypy validation
2. **Inject dependencies** - Never use global state or singletons
3. **Write tests first** - Aim for >95% coverage
4. **Use Pydantic for config** - Leverage validation and type safety
5. **Handle errors gracefully** - Provide meaningful error messages
6. **Document with docstrings** - Use Google style for consistency
7. **Keep services focused** - Single Responsibility Principle
8. **Use context managers** - For resource management (connections, files)
9. **Leverage protocols** - For flexible interfaces (ABC, Protocol)
10. **Format with ruff** - Maintain consistent code style

## Performance Considerations

1. **Token counting cache** - `@lru_cache` on encoding (maxsize=4)
2. **Connection reuse** - ConnectionManager supports connection pooling
3. **Chunking sessions** - 60-minute TTL with automatic cleanup
4. **Lazy loading** - Services created once in ApplicationContainer
5. **DataFrame efficiency** - Direct Arrow to Pandas conversion

## Security Considerations

1. **SecretStr for tokens** - Pydantic SecretStr prevents logging credentials
2. **Role-based access** - Strategy pattern enforces workspace boundaries
3. **Input validation** - Pydantic models validate all configuration
4. **Connection cleanup** - Context managers ensure proper resource disposal
5. **Environment variables** - Credentials never hardcoded

## Future Enhancements

Potential areas for extension:
- [ ] Query result caching service
- [ ] Audit logging service
- [ ] Rate limiting for API calls
- [ ] Multiple database backend support
- [ ] Async query execution
- [ ] Workspace health monitoring
- [ ] Query optimization suggestions
- [ ] Custom UDF deployment tools

---

**Last Updated**: January 2025
**Version**: 0.2.0
**Maintainer**: Databricks Tools Team
