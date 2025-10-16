# Changelog

All notable changes to the databricks-tools-clean project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-01-16

This major release represents a complete architectural refactoring of the databricks-tools MCP server, transforming it from a monolithic structure to a modern, modular, type-safe application following clean architecture principles.

### Added - Phase 1: Configuration & Security

**US-1.1: Pydantic Configuration Models**
- Created `WorkspaceConfig` Pydantic model with comprehensive validation
- Created `ServerConfig` Pydantic model for server settings
- Implemented `SecretStr` for secure token handling
- Factory method `from_env()` for environment-based configuration
- Validation for server hostnames, HTTP paths, and credentials
- 32 comprehensive tests, 100% coverage

**US-1.2: Workspace Configuration Manager**
- Implemented `WorkspaceConfigManager` using Factory pattern
- Environment variable-based workspace discovery
- Support for prefixed workspace configurations (e.g., `PRODUCTION_DATABRICKS_*`)
- Default workspace fallback mechanism
- Role-based workspace filtering integration
- Backward compatible integration with existing server.py
- 14 comprehensive tests, 94% coverage

**US-1.3: Role-Based Access Control Manager**
- Implemented Strategy pattern for role-based access control
- Created `Role` enum (ANALYST, DEVELOPER) for type-safe role definitions
- Developed `RoleStrategy` abstract base class
- Implemented `AnalystStrategy` (default workspace only access)
- Implemented `DeveloperStrategy` (all workspaces access)
- Created `RoleManager` to orchestrate role strategies
- Integrated with `WorkspaceConfigManager` for workspace filtering
- Updated server.py to use `RoleManager` instead of string-based roles
- 21 comprehensive tests, 92% coverage

### Added - Phase 2: Core Services

**US-2.1: Token Counter Utility**
- Created `TokenCounter` class in core package
- Implemented `count_tokens()` method for text strings
- Implemented `estimate_tokens()` method for JSON/dict objects
- Implemented `estimate_response_tokens()` with formatting options
- Used `@lru_cache` decorator for encoding caching (maxsize=4)
- Support for multiple tiktoken models (gpt-4, gpt-3.5-turbo, cl100k_base)
- Graceful fallback to cl100k_base for unknown models
- Maintained backward compatibility with wrapper functions
- 28 comprehensive tests, 100% coverage

**US-2.2: Database Connection Manager**
- Created `ConnectionManager` class implementing context manager protocol
- Implemented `__enter__` and `__exit__` for automatic resource management
- Accepts `WorkspaceConfig` for connection parameters
- Automatic connection closure on context exit
- Support for connection pooling through connection reuse
- Graceful error handling with proper exception propagation
- Full integration with `databricks.sql.connect`
- `SecretStr` handling for secure access token management
- 16 comprehensive tests, 100% coverage

**US-2.3: Query Executor Service**
- Created `QueryExecutor` class using Repository pattern
- Implemented `execute_query()` method returning pandas DataFrame
- Implemented `execute_query_with_catalog()` for catalog context queries
- Integration with `ConnectionManager` for safe resource management
- Integration with `WorkspaceConfigManager` for workspace resolution
- Graceful error handling with proper exception propagation
- Full type hints and Google-style docstrings
- Maintained backward compatibility with legacy wrapper functions
- 22 comprehensive tests, 100% coverage
- **Phase 2 - Core Services: COMPLETE**

### Added - Phase 3: Service Layer

**US-3.1: Catalog Service**
- Created `CatalogService` class in services package
- Implemented `list_catalogs()` method for listing all catalogs
- Implemented `list_schemas()` method for listing schemas in a catalog
- Full dependency injection with `TokenCounter` and `QueryExecutor`
- Delegates database operations to `QueryExecutor`
- Comprehensive error handling
- 30 comprehensive tests, 100% coverage

**US-3.2: Table Service**
- Created `TableService` class in services package
- Implemented `list_tables()` method for listing tables in a schema
- Implemented `list_columns()` method for retrieving column metadata
- Implemented `get_table_row_count()` method for counting table rows
- Implemented `get_table_details()` method for schema and sample data
- Automatic filtering of internal Databricks columns (`_rescued_data`)
- Full dependency injection pattern
- 41 comprehensive tests, 100% coverage

**US-3.3: Function Service**
- Created `FunctionService` class in services package
- Implemented `list_user_functions()` method for listing UDFs in catalog.schema
- Implemented `describe_function()` method for detailed UDF information
- Implemented `list_and_describe_all_functions()` for comprehensive UDF listing
- UDF description parsing and filtering for cleaner output
- Full dependency injection pattern
- 36 comprehensive tests, 100% coverage
- Total tests: 267 tests, all passing
- **Phase 3 - Service Layer: COMPLETE**

### Added - Phase 4: Response Management

**US-4.1: Chunking Service**
- Created `ChunkingService` class in services package
- Implemented `create_chunked_response()` for automatic response chunking
- Implemented `get_chunk()` for retrieving specific chunks by session ID
- Implemented `get_session_info()` for session metadata
- Session-based state management with UUID session IDs
- Automatic session cleanup/expiry mechanism (60-minute TTL)
- Replaced global `CHUNK_SESSIONS` dict with service instance state
- Integrated with `get_chunk` and `get_chunking_session_info` MCP tools
- 30 comprehensive tests, 100% coverage

**US-4.2: Response Manager**
- Created `ResponseManager` class for centralized response formatting
- Implemented `format_response()` with automatic token checking and chunking
- Implemented `format_error()` for consistent error response formatting
- Integrated with all 13 MCP tools in server.py
- Eliminated ~200 lines of duplicated JSON serialization code
- Reduced server.py by 62 net lines through code reuse
- Automatic chunking for responses exceeding 9000 token limit
- Support for `auto_chunk=False` parameter for special cases
- 39 comprehensive tests, 100% coverage
- Total tests: 306 tests, all passing
- **Phase 4 - Chunking & Response Management: COMPLETE**

### Added - Phase 5: Integration

**US-5.1: Application Container**
- Created `ApplicationContainer` class in core package for dependency injection
- Wires all 9 services with proper dependencies:
  - `RoleManager` (security)
  - `WorkspaceConfigManager` (configuration)
  - `TokenCounter` (core utility)
  - `QueryExecutor` (core service)
  - `CatalogService` (business service)
  - `TableService` (business service)
  - `FunctionService` (business service)
  - `ChunkingService` (response service)
  - `ResponseManager` (response service)
- Eliminates global state through instance-based design
- Supports role-based configuration (ANALYST/DEVELOPER modes)
- Configurable `max_tokens` parameter propagated to all services
- Easy test container creation for unit testing
- Multiple independent containers can coexist
- 23 comprehensive tests, 100% coverage
- Total tests: 329 tests, all passing
- Applied code formatting to 20 files (net -240 lines)

**US-5.2: Refactor MCP Tools to Use ApplicationContainer**
- Replaced 9 global service variables with single `ApplicationContainer` instance
- Updated all 13 MCP tools to use `container.{service}` pattern
- Updated 7 legacy wrapper functions to delegate through container
- Simplified `main()` function from 36 to 20 lines (44% reduction)
- Reduced server.py by 47 net lines through refactoring (28% code reduction)
- Added 48 integration tests in `tests/test_server/test_mcp_tools.py`
- Maintained 100% backward compatibility with existing tool signatures
- Achieved 99% test coverage with 377/377 tests passing
- All 6 acceptance criteria met and validated
- Total tests: 377 tests, all passing

**US-5.3: Remove Legacy Helper Functions**
- Removed 7 legacy wrapper functions:
  - `get_workspace_config()`
  - `get_available_workspaces()`
  - `count_tokens()`
  - `estimate_response_tokens()`
  - `create_chunked_response()`
  - `databricks_sql_query()`
  - `databricks_sql_query_with_catalog()`
- Replaced `MAX_RESPONSE_TOKENS` global constant with literal value 9000
- Removed `TokenCounter` import from server.py (no longer needed)
- Updated `run_query()` to use `container.query_executor` directly
- Removed 16 legacy wrapper tests from test files
- Reduced server.py from 773 to 617 lines (-156 lines, -20.2% reduction)
- Total code reduction: 457 lines across all files
- Maintained 100% backward compatibility for all 13 MCP tools
- Achieved 99% test coverage with 361/361 tests passing
- All 6 acceptance criteria met and validated
- Total tests: 361 tests, all passing
- **Phase 5 - Integration: COMPLETE**

### Added - Phase 6: Testing & Quality

**US-6.1: Comprehensive Integration Tests**
- Created 48 integration tests in `tests/test_server/test_mcp_tools.py` (717 lines)
- Comprehensive testing of all 13 MCP tools with mocked Databricks connections
- Role-based access control scenarios (ANALYST vs DEVELOPER modes)
- Chunking scenarios (valid/invalid sessions, chunk retrieval)
- Error handling (invalid workspaces, query failures, connection errors)
- Token limit exceeded scenarios
- Environment variable fallback testing
- Achieved 99% overall code coverage (exceeding 85% target)
- All 361 tests passing
- All 7 acceptance criteria met and validated

**US-6.2: Enhanced Pre-commit Hooks**
- Created `mypy.ini` with pragmatic type checking configuration (50 lines)
- Enhanced `.pre-commit-config.yaml` with mypy, pytest, and coverage hooks
- Added mypy hook (v1.18.2) for type checking all Python files
- Added pytest hook using "uv run pytest" for local test execution
- Added pytest-cov hook with `--cov-fail-under=85` threshold enforcement
- Fixed 9 mypy type errors across 4 files with strategic `type: ignore` comments
- Added `mypy>=1.18.2` to dev dependencies in pyproject.toml
- Updated pre-commit hook versions (pre-commit-hooks v6.0.0, ruff v0.14.0)
- All 12 pre-commit hooks passing:
  - trailing-whitespace
  - end-of-file-fixer
  - check-yaml
  - check-json
  - check-added-large-files
  - check-merge-conflict
  - detect-private-key
  - ruff
  - ruff-format
  - mypy
  - pytest
  - pytest-cov
- Maintained 99% code coverage with 361/361 tests passing
- All 5 acceptance criteria met and validated

**US-6.3: Comprehensive Type Hints**
- Added comprehensive type hints to all 18 source files using modern Python 3.10+ syntax
- Created `py.typed` marker file for PEP 561 compliance
- Enabled mypy strict mode in `mypy.ini` with all strict checks activated:
  - `warn_unused_configs = True`
  - `disallow_any_generics = True`
  - `disallow_subclassing_any = True`
  - `disallow_untyped_calls = True`
  - `disallow_untyped_defs = True`
  - `disallow_incomplete_defs = True`
  - `check_untyped_defs = True`
  - `disallow_untyped_decorators = True`
  - `warn_redundant_casts = True`
  - `warn_unused_ignores = True`
  - `warn_return_any = True`
  - `no_implicit_reexport = True`
  - `strict_equality = True`
  - `strict_concatenate = True`
- Fixed 21 mypy strict mode errors with proper type annotations
- Converted all type hints to modern syntax:
  - `str | None` instead of `Optional[str]`
  - `dict[str, Any]` instead of `Dict[str, Any]`
  - `list[str]` instead of `List[str]`
- Zero old-style typing imports remaining (Optional, Union, List, Dict removed)
- Added `from typing import Any` imports for heterogeneous types
- Updated `__exit__` parameter types to `type[BaseException] | None`
- Scoped strict mypy checking to source files only (`files: ^src/` in pre-commit)
- All 361 tests passing with 99% code coverage maintained
- All 7 acceptance criteria met and validated
- `mypy --strict` passes with 0 errors

**US-6.4: Documentation & Examples**
- Created comprehensive `ARCHITECTURE.md` (500+ lines)
  - Design patterns documentation (Repository, Strategy, Factory, DI, Service Layer)
  - Complete directory structure with explanations
  - Component architecture diagram (ASCII art)
  - Data flow diagrams for key operations
  - Dependency injection graph
  - Testing strategy documentation
  - Extension points and best practices
- Created `examples/` directory with 4 comprehensive examples:
  - `basic_usage.py` - Simple operations and error handling
  - `advanced_queries.py` - Complex SQL, multi-workspace, chunking
  - `custom_service.py` - Creating custom services with DI
  - `testing_example.py` - Testing patterns and best practices
- Created comprehensive `CHANGELOG.md` (this file)
- Updated `README.md` with architecture and design patterns sections
- Updated `CLAUDE.md` with Phase 6 completion summary
- Verified 100% docstring coverage across all public APIs
- All 6 acceptance criteria met and validated
- **Phase 6 - Testing & Quality: COMPLETE**

### Changed

**Architecture Refactoring**
- Refactored monolithic `server.py` into modular architecture
- Improved separation of concerns across 5 packages (config, core, security, services, server)
- Enhanced error handling throughout codebase with specific exception types
- Improved response chunking with automatic session management
- Modernized type hints to Python 3.10+ syntax across entire codebase

**Code Quality Improvements**
- Increased test coverage from unknown to 99%
- Reduced server.py from 773 to 617 lines (-20.2% reduction)
- Eliminated ~200 lines of duplicated code through `ResponseManager`
- Applied consistent code formatting with ruff
- Enabled strict mypy type checking with zero errors

**Performance Enhancements**
- Added token counting cache with `@lru_cache` (maxsize=4)
- Improved connection management with context protocol
- Optimized response formatting with reusable manager

### Removed

**Deprecated Code Cleanup**
- Removed 7 legacy wrapper functions (replaced with container methods)
- Removed global state variables (9 global services replaced with container)
- Removed `MAX_RESPONSE_TOKENS` global constant
- Removed old-style typing imports (Optional, Union, List, Dict)
- Removed 16 legacy wrapper tests (redundant with integration tests)
- Removed unused `TokenCounter` import from server.py

### Fixed

**Type Safety**
- Fixed 9 mypy type errors with strategic `type: ignore` comments (US-6.2)
- Fixed 21 mypy strict mode errors with proper type annotations (US-6.3)
- Fixed all type hint inconsistencies across 18 source files

**Error Handling**
- Improved error handling in all services with specific exceptions
- Enhanced connection error propagation in `ConnectionManager`
- Better query error handling in `QueryExecutor`

### Security

- Implemented `SecretStr` for secure token handling in `WorkspaceConfig`
- Prevented credential logging through Pydantic model configuration
- Enhanced role-based access control with Strategy pattern
- Validated all input through Pydantic models

### Metrics

**Test Coverage**
- Total tests: 361 (100% passing)
- Code coverage: 99%
- Test files: 12
- Test lines of code: ~4,000

**Code Quality**
- Type hint coverage: 100% (strict mypy)
- Pre-commit hooks: 12 (all passing)
- Code reduction: 457 lines through refactoring
- Server.py reduction: 20.2% (773 → 617 lines)

**Package Structure**
- Source files: 18
- Service classes: 9
- Design patterns implemented: 6
- Example files: 4
- Documentation files: 4

## [0.1.0] - 2024-12-15

### Added
- Initial MCP server implementation with 13 tools
- Basic multi-workspace support
- Response chunking for large results
- Role-based access control (analyst/developer modes)
- Unity Catalog exploration capabilities
- Basic test coverage

### Known Issues
- Monolithic server.py structure
- Global state variables
- Limited type safety
- Inconsistent error handling
- Duplicated code patterns

---

## Version History

- **0.2.0** (2025-01-16) - Complete architectural refactoring with clean architecture principles
- **0.1.0** (2024-12-15) - Initial release with basic functionality

## Migration Guide

### Upgrading from 0.1.0 to 0.2.0

The 0.2.0 release maintains 100% backward compatibility for all 13 MCP tools. However, if you were using internal functions or classes directly, please note:

**Breaking Changes for Internal APIs:**
1. Legacy helper functions removed - use `ApplicationContainer` instead
2. Global service variables removed - use container pattern
3. Old-style typing imports removed - use Python 3.10+ syntax

**Recommended Migration Path:**
1. Update to Python 3.10+ (required for modern type hints)
2. Run `uv sync` to update dependencies
3. Update any custom code to use `ApplicationContainer`
4. Run `mypy --strict` to verify type safety
5. Run full test suite: `pytest tests/ --cov=src/databricks_tools`

**No Changes Required For:**
- MCP tool usage (100% compatible)
- Environment configuration
- Claude Desktop integration
- Command-line usage

## Contributors

- Claude Code (AI Assistant)
- Ahmed (Project Lead)

## License

MIT License - See LICENSE file for details
