"""Application container for dependency injection.

This module provides an ApplicationContainer class for centralized dependency
injection of all services in the Databricks Tools MCP server.
"""

from databricks_tools.config.workspace import WorkspaceConfigManager
from databricks_tools.core.query_executor import QueryExecutor
from databricks_tools.core.token_counter import TokenCounter
from databricks_tools.security.role_manager import Role, RoleManager
from databricks_tools.services.catalog_service import CatalogService
from databricks_tools.services.chunking_service import ChunkingService
from databricks_tools.services.function_service import FunctionService
from databricks_tools.services.response_manager import ResponseManager
from databricks_tools.services.table_service import TableService


class ApplicationContainer:
    """Dependency injection container for all application services.

    This class wires all services with their dependencies, eliminating global state
    and making the application easily testable.

    Attributes:
        role_manager: RoleManager instance for role-based access control.
        workspace_manager: WorkspaceConfigManager instance for workspace management.
        token_counter: TokenCounter instance for token counting.
        query_executor: QueryExecutor instance for SQL query execution.
        catalog_service: CatalogService instance for catalog operations.
        table_service: TableService instance for table operations.
        function_service: FunctionService instance for UDF operations.
        chunking_service: ChunkingService instance for response chunking.
        response_manager: ResponseManager instance for response formatting.

    Example:
        >>> # Production use
        >>> container = ApplicationContainer(role=Role.DEVELOPER)
        >>> catalogs = container.catalog_service.list_catalogs()
        >>>
        >>> # Testing use
        >>> test_container = ApplicationContainer(role=Role.ANALYST, max_tokens=5000)
        >>> assert test_container.response_manager.max_tokens == 5000
    """

    def __init__(self, role: Role = Role.ANALYST, max_tokens: int = 9000) -> None:
        """Initialize ApplicationContainer with all dependencies.

        Creates and wires all services with proper dependency injection.

        Args:
            role: User role (ANALYST or DEVELOPER). Defaults to ANALYST.
            max_tokens: Maximum tokens per response. Defaults to 9000.

        Example:
            >>> # Analyst mode (default)
            >>> container = ApplicationContainer()
            >>>
            >>> # Developer mode
            >>> container = ApplicationContainer(role=Role.DEVELOPER)
            >>>
            >>> # Custom token limit
            >>> container = ApplicationContainer(max_tokens=5000)
        """
        # Core infrastructure
        self.role_manager = RoleManager(role=role)
        self.workspace_manager = WorkspaceConfigManager(role_manager=self.role_manager)
        self.token_counter = TokenCounter(model="gpt-4")
        self.query_executor = QueryExecutor(workspace_manager=self.workspace_manager)

        # Business services
        self.catalog_service = CatalogService(
            query_executor=self.query_executor,
            token_counter=self.token_counter,
            max_tokens=max_tokens,
        )

        self.table_service = TableService(
            query_executor=self.query_executor,
            token_counter=self.token_counter,
            max_tokens=max_tokens,
        )

        self.function_service = FunctionService(
            query_executor=self.query_executor,
            token_counter=self.token_counter,
            max_tokens=max_tokens,
        )

        # Response management
        self.chunking_service = ChunkingService(
            token_counter=self.token_counter, max_tokens=max_tokens
        )

        self.response_manager = ResponseManager(
            token_counter=self.token_counter,
            chunking_service=self.chunking_service,
            max_tokens=max_tokens,
        )
