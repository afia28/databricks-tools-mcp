"""Query execution service for Databricks SQL operations.

This module provides a QueryExecutor class that implements the Repository pattern
for centralized and testable database query execution.
"""

import pandas as pd

from databricks_tools.config.workspace import WorkspaceConfigManager
from databricks_tools.core.connection import ConnectionManager


class QueryExecutor:
    """Repository for executing Databricks SQL queries.

    This class implements the Repository pattern to abstract data access logic
    and provide a centralized, testable interface for executing SQL queries
    against Databricks.

    Attributes:
        workspace_manager: WorkspaceConfigManager for accessing workspace configurations.

    Example:
        >>> from databricks_tools.config.workspace import WorkspaceConfigManager
        >>> from databricks_tools.security.role_manager import RoleManager, Role
        >>>
        >>> # Create workspace manager
        >>> role_manager = RoleManager(role=Role.DEVELOPER)
        >>> workspace_manager = WorkspaceConfigManager(role_manager=role_manager)
        >>>
        >>> # Create query executor
        >>> executor = QueryExecutor(workspace_manager)
        >>>
        >>> # Execute simple query
        >>> df = executor.execute_query("SELECT 1 as value")
        >>>
        >>> # Execute query with catalog context
        >>> df = executor.execute_query_with_catalog(
        ...     catalog="my_catalog",
        ...     query="SELECT * FROM my_schema.my_table LIMIT 10"
        ... )
    """

    def __init__(self, workspace_manager: WorkspaceConfigManager) -> None:
        """Initialize QueryExecutor with workspace manager.

        Args:
            workspace_manager: WorkspaceConfigManager instance for accessing
                             workspace configurations.

        Example:
            >>> workspace_manager = WorkspaceConfigManager()
            >>> executor = QueryExecutor(workspace_manager)
        """
        self.workspace_manager = workspace_manager

    def execute_query(
        self,
        query: str,
        workspace: str | None = None,
        parse_dates: list[str] | None = None,
    ) -> pd.DataFrame:
        """Execute SQL query and return results as pandas DataFrame.

        Executes the provided SQL query using the specified workspace connection
        and returns the results as a pandas DataFrame.

        Args:
            query: SQL query string to execute.
            workspace: Optional workspace name. If None, uses default workspace.
            parse_dates: Optional list of column names to parse as dates.

        Returns:
            pandas DataFrame containing query results.

        Raises:
            ValueError: If workspace is not found or query is invalid.
            databricks.sql.exc.Error: If database query execution fails.

        Example:
            >>> executor = QueryExecutor(workspace_manager)
            >>>
            >>> # Simple query
            >>> df = executor.execute_query("SELECT 1 as value")
            >>>
            >>> # Query with date parsing
            >>> df = executor.execute_query(
            ...     "SELECT * FROM my_table",
            ...     parse_dates=["created_at", "updated_at"]
            ... )
            >>>
            >>> # Query on specific workspace
            >>> df = executor.execute_query(
            ...     "SELECT COUNT(*) as count FROM my_table",
            ...     workspace="production"
            ... )
        """
        # Get workspace configuration
        config = self.workspace_manager.get_workspace_config(workspace)

        # Execute query using connection manager
        with ConnectionManager(config) as connection:
            df = pd.read_sql(query, connection, parse_dates=parse_dates)

        return df

    def execute_query_with_catalog(
        self,
        catalog: str,
        query: str,
        workspace: str | None = None,
    ) -> pd.DataFrame:
        """Execute query with catalog context set.

        Sets the catalog context before executing the query. This allows queries
        to reference tables without fully qualified names (catalog.schema.table).

        Args:
            catalog: Catalog name to set as context.
            query: SQL query string to execute.
            workspace: Optional workspace name. If None, uses default workspace.

        Returns:
            pandas DataFrame containing query results.

        Raises:
            ValueError: If workspace or catalog is not found.
            databricks.sql.exc.Error: If database query execution fails.

        Example:
            >>> executor = QueryExecutor(workspace_manager)
            >>>
            >>> # Query with catalog context
            >>> df = executor.execute_query_with_catalog(
            ...     catalog="production",
            ...     query="SELECT * FROM sales.orders LIMIT 10"
            ... )
            >>>
            >>> # Query on specific workspace with catalog
            >>> df = executor.execute_query_with_catalog(
            ...     catalog="analytics",
            ...     query="SELECT COUNT(*) FROM reports.daily_summary",
            ...     workspace="production"
            ... )
        """
        # Get workspace configuration
        config = self.workspace_manager.get_workspace_config(workspace)

        # Execute query with catalog context
        with ConnectionManager(config) as connection:
            cursor = connection.cursor()

            try:
                # Set catalog context
                cursor.execute(f"USE CATALOG {catalog}")

                # Execute main query
                cursor.execute(query)

                # Fetch results
                result = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                df = pd.DataFrame(result, columns=columns)

            finally:
                cursor.close()

        return df
