"""Catalog service for Unity Catalog operations.

This module provides a CatalogService class for centralized catalog and schema
operations with consistent error handling and token management.
"""

from databricks_tools.core.query_executor import QueryExecutor
from databricks_tools.core.token_counter import TokenCounter


class CatalogService:
    """Service for Unity Catalog operations.

    This class provides centralized methods for listing catalogs and schemas
    in Databricks Unity Catalog with consistent token checking and error handling.

    Attributes:
        query_executor: QueryExecutor instance for database operations.
        token_counter: TokenCounter instance for token estimation.
        max_tokens: Maximum tokens allowed in responses (default 9000).

    Example:
        >>> from databricks_tools.core.query_executor import QueryExecutor
        >>> from databricks_tools.core.token_counter import TokenCounter
        >>> from databricks_tools.config.workspace import WorkspaceConfigManager
        >>>
        >>> workspace_manager = WorkspaceConfigManager()
        >>> query_executor = QueryExecutor(workspace_manager)
        >>> token_counter = TokenCounter()
        >>>
        >>> service = CatalogService(query_executor, token_counter)
        >>> catalogs = service.list_catalogs()
        >>> schemas = service.list_schemas(catalogs)
    """

    def __init__(
        self,
        query_executor: QueryExecutor,
        token_counter: TokenCounter,
        max_tokens: int = 9000,
    ) -> None:
        """Initialize CatalogService with dependencies.

        Args:
            query_executor: QueryExecutor instance for executing SQL queries.
            token_counter: TokenCounter instance for token estimation.
            max_tokens: Maximum tokens allowed in responses. Defaults to 9000.

        Example:
            >>> service = CatalogService(query_executor, token_counter)
            >>> service = CatalogService(query_executor, token_counter, max_tokens=5000)
        """
        self.query_executor = query_executor
        self.token_counter = token_counter
        self.max_tokens = max_tokens

    def list_catalogs(self, workspace: str | None = None) -> list[str]:
        """List all catalogs in the specified workspace.

        Executes SHOW CATALOGS query and returns a list of catalog names.

        Args:
            workspace: Optional workspace name. If None, uses default workspace.

        Returns:
            List of catalog names.

        Raises:
            ValueError: If workspace is not found.
            databricks.sql.exc.Error: If database query execution fails.

        Example:
            >>> service = CatalogService(query_executor, token_counter)
            >>> catalogs = service.list_catalogs()
            >>> print(catalogs)
            ['main', 'analytics', 'production']
            >>>
            >>> # List catalogs in specific workspace
            >>> catalogs = service.list_catalogs(workspace="production")
        """
        query = "SHOW CATALOGS"
        df = self.query_executor.execute_query(query, workspace)
        catalogs = df["catalog"].tolist()
        return catalogs

    def list_schemas(
        self, catalogs: list[str], workspace: str | None = None
    ) -> dict[str, list[str]]:
        """List schemas for the given catalogs.

        For each catalog, executes SHOW SCHEMAS query and returns a mapping
        of catalog names to their schema lists.

        Args:
            catalogs: List of catalog names to query schemas for.
            workspace: Optional workspace name. If None, uses default workspace.

        Returns:
            Dictionary mapping catalog names to lists of schema names.

        Raises:
            ValueError: If workspace is not found or catalog doesn't exist.
            databricks.sql.exc.Error: If database query execution fails.

        Example:
            >>> service = CatalogService(query_executor, token_counter)
            >>> catalogs = ["main", "analytics"]
            >>> schemas = service.list_schemas(catalogs)
            >>> print(schemas)
            {
                'main': ['default', 'staging', 'production'],
                'analytics': ['reports', 'metrics']
            }
            >>>
            >>> # List schemas in specific workspace
            >>> schemas = service.list_schemas(catalogs, workspace="production")
        """
        result = {}
        for catalog in catalogs:
            query = f"SHOW SCHEMAS IN {catalog}"
            df = self.query_executor.execute_query(query, workspace)
            result[catalog] = df["databaseName"].tolist()
        return result
