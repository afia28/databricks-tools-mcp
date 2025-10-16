"""Table service for Unity Catalog table operations.

This module provides a TableService class for centralized table-related
operations with consistent error handling and query execution.
"""

from databricks_tools.core.query_executor import QueryExecutor
from databricks_tools.core.token_counter import TokenCounter


class TableService:
    """Service for Unity Catalog table operations.

    This class provides centralized methods for listing tables, columns,
    and fetching table details from Databricks Unity Catalog with consistent
    query execution patterns.

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
        >>> service = TableService(query_executor, token_counter)
        >>> tables = service.list_tables("my_catalog", ["schema1", "schema2"])
        >>> columns = service.list_columns("my_catalog", "schema1", ["table1"])
    """

    def __init__(
        self,
        query_executor: QueryExecutor,
        token_counter: TokenCounter,
        max_tokens: int = 9000,
    ) -> None:
        """Initialize TableService with dependencies.

        Args:
            query_executor: QueryExecutor instance for executing SQL queries.
            token_counter: TokenCounter instance for token estimation.
            max_tokens: Maximum tokens allowed in responses. Defaults to 9000.

        Example:
            >>> service = TableService(query_executor, token_counter)
            >>> service = TableService(query_executor, token_counter, max_tokens=5000)
        """
        self.query_executor = query_executor
        self.token_counter = token_counter
        self.max_tokens = max_tokens

    def list_tables(
        self, catalog: str, schemas: list[str], workspace: str | None = None
    ) -> dict[str, list[str]]:
        """List tables for given catalog and schemas.

        Executes SHOW TABLES query for each schema and returns a mapping
        of schema names to their table lists.

        Args:
            catalog: The catalog name.
            schemas: List of schema names under the given catalog.
            workspace: Optional workspace name. If None, uses default workspace.

        Returns:
            Dictionary mapping schema names to lists of table names.

        Raises:
            ValueError: If workspace is not found or catalog/schema doesn't exist.
            databricks.sql.exc.Error: If database query execution fails.

        Example:
            >>> service = TableService(query_executor, token_counter)
            >>> tables = service.list_tables("main", ["default", "staging"])
            >>> print(tables)
            {
                'default': ['customers', 'orders', 'products'],
                'staging': ['temp_data']
            }
            >>>
            >>> # List tables in specific workspace
            >>> tables = service.list_tables("analytics", ["reports"], workspace="production")
        """
        result = {}
        for schema in schemas:
            query = f"SHOW TABLES IN {catalog}.{schema}"
            df = self.query_executor.execute_query(query, workspace)
            result[schema] = df["tableName"].tolist()
        return result

    def list_columns(
        self,
        catalog: str,
        schema: str,
        tables: list[str],
        workspace: str | None = None,
    ) -> dict[str, list[dict]]:
        """List columns with metadata for given tables.

        For each table, executes DESCRIBE TABLE EXTENDED query and extracts
        column metadata (name, type, description).

        Args:
            catalog: The catalog name.
            schema: The schema name.
            tables: List of table names to inspect.
            workspace: Optional workspace name. If None, uses default workspace.

        Returns:
            Dictionary mapping table names to lists of column metadata dictionaries.
            Each column dict contains: name, type, description.

        Raises:
            ValueError: If workspace is not found or table doesn't exist.
            databricks.sql.exc.Error: If database query execution fails.

        Example:
            >>> service = TableService(query_executor, token_counter)
            >>> columns = service.list_columns("main", "default", ["customers"])
            >>> print(columns)
            {
                'customers': [
                    {'name': 'id', 'type': 'bigint', 'description': 'Customer ID'},
                    {'name': 'name', 'type': 'string', 'description': 'Customer name'},
                    {'name': 'email', 'type': 'string', 'description': ''}
                ]
            }
            >>>
            >>> # List columns for multiple tables
            >>> columns = service.list_columns(
            ...     "analytics", "reports", ["daily", "monthly"],
            ...     workspace="production"
            ... )
        """
        result = {}
        for table in tables:
            query = f"DESCRIBE TABLE EXTENDED {catalog}.{schema}.{table}"
            df = self.query_executor.execute_query(query, workspace)
            # Filter to only the schema description section
            metadata = []
            for _, row in df.iterrows():
                if row["col_name"] and not row["col_name"].startswith("#"):
                    metadata.append(
                        {
                            "name": row["col_name"],
                            "type": row["data_type"],
                            "description": row.get("comment", ""),
                        }
                    )
            result[table] = metadata
        return result

    def get_table_row_count(
        self,
        catalog: str,
        schema: str,
        table_name: str,
        workspace: str | None = None,
    ) -> dict:
        """Get row count and pagination estimates for a table.

        Executes COUNT(*) query and calculates estimated pages for common page sizes.

        Args:
            catalog: The catalog name where the table is stored.
            schema: The schema name where the table is stored.
            table_name: The name of the table to count rows from.
            workspace: Optional workspace name. If None, uses default workspace.

        Returns:
            Dictionary with table_name, total_rows, and estimated_pages.
            estimated_pages contains page counts for sizes: 50, 100, 250, 500, 1000.

        Raises:
            ValueError: If workspace is not found or table doesn't exist.
            databricks.sql.exc.Error: If database query execution fails.

        Example:
            >>> service = TableService(query_executor, token_counter)
            >>> count_info = service.get_table_row_count("main", "default", "customers")
            >>> print(count_info)
            {
                'table_name': 'main.default.customers',
                'total_rows': 15000,
                'estimated_pages': {
                    'pages_with_50_rows': 300,
                    'pages_with_100_rows': 150,
                    'pages_with_250_rows': 60,
                    'pages_with_500_rows': 30,
                    'pages_with_1000_rows': 15
                }
            }
            >>>
            >>> # Get count for table in specific workspace
            >>> count_info = service.get_table_row_count(
            ...     "analytics", "reports", "daily_summary",
            ...     workspace="production"
            ... )
        """
        query = f"SELECT COUNT(*) as row_count FROM {catalog}.{schema}.{table_name}"
        df = self.query_executor.execute_query(query, workspace)

        row_count = int(df.iloc[0]["row_count"])

        # Calculate estimated pages for common page sizes
        page_sizes = [50, 100, 250, 500, 1000]
        pages_info = {}
        for size in page_sizes:
            pages_info[f"pages_with_{size}_rows"] = (row_count + size - 1) // size

        result = {
            "table_name": f"{catalog}.{schema}.{table_name}",
            "total_rows": row_count,
            "estimated_pages": pages_info,
        }

        return result

    def get_table_details(
        self,
        catalog: str,
        schema: str,
        table_name: str,
        limit: int | None = 1000,
        workspace: str | None = None,
    ) -> dict:
        """Get table schema and sample data.

        Executes SELECT query to fetch table schema and sample data.

        Args:
            catalog: The catalog name where the table is stored.
            schema: The schema name where the table is stored.
            table_name: The name of the table to retrieve details from.
            limit: Total number of rows to fetch. If None, fetches all rows (use with caution).
            workspace: Optional workspace name. If None, uses default workspace.

        Returns:
            Dictionary with table_name, schema, and data.
            - data: List of row dictionaries
            - schema: Table schema information
            - table_name: Fully qualified table name

        Raises:
            ValueError: If workspace is not found or table doesn't exist.
            databricks.sql.exc.Error: If database query execution fails.

        Example:
            >>> service = TableService(query_executor, token_counter)
            >>> details = service.get_table_details("main", "default", "customers", limit=5)
            >>> print(details)
            {
                'table_name': 'main.default.customers',
                'schema': {'fields': [...], 'primaryKey': [], 'pandas_version': '1.4.0'},
                'data': [
                    {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
                    {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'},
                    ...
                ]
            }
            >>>
            >>> # Get all data (no limit)
            >>> details = service.get_table_details("main", "default", "small_table", limit=None)
            >>>
            >>> # Get data from specific workspace
            >>> details = service.get_table_details(
            ...     "analytics", "reports", "summary",
            ...     limit=100, workspace="production"
            ... )
        """
        # Build query with optional limit
        if limit is not None:
            query = f"SELECT * FROM {catalog}.{schema}.{table_name} LIMIT {limit}"
        else:
            query = f"SELECT * FROM {catalog}.{schema}.{table_name}"

        df = self.query_executor.execute_query(query, workspace)

        # Convert DataFrame to JSON-serializable format
        data_records = df.to_dict(orient="records")

        # Extract schema from DataFrame columns
        schema_fields = [{"name": str(col), "type": str(dtype)} for col, dtype in df.dtypes.items()]

        result = {
            "table_name": f"{catalog}.{schema}.{table_name}",
            "schema": schema_fields,
            "data": data_records,
        }

        return result
