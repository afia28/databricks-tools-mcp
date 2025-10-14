# US-5.1: Create Application Container (Dependency Injection)

## Metadata
- **Story ID**: US-5.1
- **Title**: Create Application Container with Dependency Injection
- **Phase**: Phase 5 - MCP Tool Integration
- **Estimated LOC**: ~100 lines
- **Dependencies**: All Phase 1-4 stories
- **Status**: ⬜ Not Started

## Overview
Create ApplicationContainer class to wire all services using Dependency Injection pattern. Eliminates all global state.

## User Story
**As a** developer
**I want** a centralized dependency injection container
**So that** all services are properly wired and testable without globals

## Acceptance Criteria
1. ✅ ApplicationContainer class created
2. ✅ All services instantiated with proper dependencies
3. ✅ Role passed from command-line args
4. ✅ No more global state (except mcp instance)
5. ✅ Easy to create test containers
6. ✅ All tests pass

## Technical Requirements

### Class: ApplicationContainer

```python
from databricks_tools.config.workspace import WorkspaceConfigManager
from databricks_tools.security.role_manager import RoleManager, Role
from databricks_tools.core.token_counter import TokenCounter
from databricks_tools.core.query_executor import QueryExecutor
from databricks_tools.services.catalog_service import CatalogService
from databricks_tools.services.table_service import TableService
from databricks_tools.services.function_service import FunctionService
from databricks_tools.services.chunking_service import ChunkingService
from databricks_tools.services.response_manager import ResponseManager

class ApplicationContainer:
    """Dependency injection container for all services."""

    def __init__(self, role: Role = Role.ANALYST, max_tokens: int = 9000):
        # Core
        self.role_manager = RoleManager(role=role)
        self.workspace_manager = WorkspaceConfigManager(role_manager=self.role_manager)
        self.token_counter = TokenCounter(model="gpt-4")
        self.query_executor = QueryExecutor(workspace_manager=self.workspace_manager)

        # Services
        self.catalog_service = CatalogService(
            query_executor=self.query_executor,
            token_counter=self.token_counter,
            max_tokens=max_tokens
        )

        self.table_service = TableService(
            query_executor=self.query_executor,
            token_counter=self.token_counter,
            max_tokens=max_tokens
        )

        self.function_service = FunctionService(
            query_executor=self.query_executor,
            token_counter=self.token_counter,
            max_tokens=max_tokens
        )

        self.chunking_service = ChunkingService(
            token_counter=self.token_counter,
            max_tokens=max_tokens
        )

        self.response_manager = ResponseManager(
            token_counter=self.token_counter,
            chunking_service=self.chunking_service,
            max_tokens=max_tokens
        )
```

## Test Cases (8 tests)
1. test_container_initialization
2. test_container_all_services_created
3. test_container_analyst_role
4. test_container_developer_role
5. test_container_custom_max_tokens
6. test_container_service_dependencies
7. test_container_for_testing
8. test_container_singleton_like_behavior

## Files
- **Create**: `src/databricks_tools/core/container.py`
- **Modify**: `src/databricks_tools/server.py` (use container)
- **Test**: `tests/test_core/test_container.py`

## Integration with server.py
```python
# In server.py
from databricks_tools.core.container import ApplicationContainer

# Parse args
args = parser.parse_args()
role = Role.DEVELOPER if args.developer else Role.ANALYST

# Create container
container = ApplicationContainer(role=role)

# MCP tools now use container.catalog_service, container.table_service, etc.
```

## Related Stories
- **Depends on**: All Phase 1-4 stories
- **Blocks**: US-5.2
