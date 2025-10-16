"""Function service for Unity Catalog function operations.

This module provides a FunctionService class for centralized user-defined function
operations with consistent error handling and query execution.
"""

import pandas as pd

from databricks_tools.core.query_executor import QueryExecutor
from databricks_tools.core.token_counter import TokenCounter


class FunctionService:
    """Service for Unity Catalog user-defined function operations.

    This class provides centralized methods for listing and describing user-defined
    functions in Databricks Unity Catalog with consistent query execution patterns.

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
        >>> service = FunctionService(query_executor, token_counter)
        >>> functions = service.list_user_functions("my_catalog", "my_schema")
        >>> details = service.describe_function("my_function", "my_catalog", "my_schema")
    """

    def __init__(
        self,
        query_executor: QueryExecutor,
        token_counter: TokenCounter,
        max_tokens: int = 9000,
    ) -> None:
        """Initialize FunctionService with dependencies.

        Args:
            query_executor: QueryExecutor instance for executing SQL queries.
            token_counter: TokenCounter instance for token estimation.
            max_tokens: Maximum tokens allowed in responses. Defaults to 9000.

        Example:
            >>> service = FunctionService(query_executor, token_counter)
            >>> service = FunctionService(query_executor, token_counter, max_tokens=5000)
        """
        self.query_executor = query_executor
        self.token_counter = token_counter
        self.max_tokens = max_tokens

    def list_user_functions(self, catalog: str, schema: str, workspace: str | None = None) -> dict:
        """List all user-defined functions in catalog.schema.

        Executes SHOW USER FUNCTIONS query and returns a list of function names.

        Args:
            catalog: The catalog name where the functions are stored.
            schema: The schema name where the functions are stored.
            workspace: Optional workspace name. If None, uses default workspace.

        Returns:
            Dictionary with catalog, schema, user_functions list, and function_count.
            Format: {
                "catalog": str,
                "schema": str,
                "user_functions": list[str],
                "function_count": int
            }

        Raises:
            ValueError: If workspace is not found or catalog/schema doesn't exist.
            databricks.sql.exc.Error: If database query execution fails.

        Example:
            >>> service = FunctionService(query_executor, token_counter)
            >>> functions = service.list_user_functions("main", "default")
            >>> print(functions)
            {
                'catalog': 'main',
                'schema': 'default',
                'user_functions': ['my_func', 'another_func'],
                'function_count': 2
            }
            >>>
            >>> # List functions in specific workspace
            >>> functions = service.list_user_functions(
            ...     "analytics", "reports", workspace="production"
            ... )
        """
        query = f"SHOW USER FUNCTIONS IN {catalog}.{schema}"
        df = self.query_executor.execute_query_with_catalog(catalog, query, workspace)

        # Extract function names from the result
        functions = df["function"].tolist() if "function" in df.columns else []

        result = {
            "catalog": catalog,
            "schema": schema,
            "user_functions": functions,
            "function_count": len(functions),
        }

        return result

    def describe_function(
        self,
        function_name: str,
        catalog: str,
        schema: str,
        workspace: str | None = None,
    ) -> dict:
        """Get detailed function information.

        Executes DESCRIBE FUNCTION EXTENDED query and parses the output
        to extract function metadata.

        Args:
            function_name: The name of the function to describe.
            catalog: The catalog name where the function is stored.
            schema: The schema name where the function is stored.
            workspace: Optional workspace name. If None, uses default workspace.

        Returns:
            Dictionary with catalog, schema, function_name, and details list.
            Format: {
                "catalog": str,
                "schema": str,
                "function_name": str,
                "details": list[str]
            }

        Raises:
            ValueError: If workspace is not found or function doesn't exist.
            databricks.sql.exc.Error: If database query execution fails.

        Example:
            >>> service = FunctionService(query_executor, token_counter)
            >>> details = service.describe_function("my_func", "main", "default")
            >>> print(details)
            {
                'catalog': 'main',
                'schema': 'default',
                'function_name': 'my_func',
                'details': [
                    'Function: main.default.my_func',
                    'Type: SCALAR',
                    'Input: (x INT)',
                    'Returns: INT',
                    'Comment: My custom function',
                    'Deterministic: true',
                    'Data Access: NO_SQL'
                ]
            }
            >>>
            >>> # Describe function in specific workspace
            >>> details = service.describe_function(
            ...     "calculate_discount", "sales", "functions",
            ...     workspace="production"
            ... )
        """
        query = f"DESCRIBE FUNCTION EXTENDED {catalog}.{schema}.{function_name}"
        df = self.query_executor.execute_query_with_catalog(catalog, query, workspace)

        # Parse the describe function extended output
        details = self._parse_function_description(df)

        function_info = {
            "catalog": catalog,
            "schema": schema,
            "function_name": function_name,
            "details": details,
        }

        return function_info

    def list_and_describe_all_functions(
        self, catalog: str, schema: str, workspace: str | None = None
    ) -> dict:
        """List and describe all functions in catalog.schema.

        Combines list_user_functions and describe_function to provide
        comprehensive information about all functions in a single call.

        Args:
            catalog: The catalog name where the functions are stored.
            schema: The schema name where the functions are stored.
            workspace: Optional workspace name. If None, uses default workspace.

        Returns:
            Dictionary with catalog, schema, function_count, and functions dict.
            Format: {
                "catalog": str,
                "schema": str,
                "function_count": int,
                "functions": dict[str, list[str]]
            }
            The functions dict maps function names to their details lists.

        Raises:
            ValueError: If workspace is not found or catalog/schema doesn't exist.
            databricks.sql.exc.Error: If database query execution fails.

        Example:
            >>> service = FunctionService(query_executor, token_counter)
            >>> all_funcs = service.list_and_describe_all_functions("main", "default")
            >>> print(all_funcs)
            {
                'catalog': 'main',
                'schema': 'default',
                'function_count': 2,
                'functions': {
                    'my_func': [
                        'Function: main.default.my_func',
                        'Type: SCALAR',
                        'Input: (x INT)',
                        'Returns: INT'
                    ],
                    'another_func': [
                        'Function: main.default.another_func',
                        'Type: TABLE',
                        'Input: ()',
                        'Returns: TABLE(id INT, name STRING)'
                    ]
                }
            }
            >>>
            >>> # List and describe all functions in specific workspace
            >>> all_funcs = service.list_and_describe_all_functions(
            ...     "analytics", "reports", workspace="production"
            ... )
        """
        # First, get list of all functions
        functions_list = self.list_user_functions(catalog, schema, workspace)
        functions = functions_list["user_functions"]

        # Initialize result structure
        result: dict = {
            "catalog": catalog,
            "schema": schema,
            "function_count": len(functions),
            "functions": {},
        }

        # Describe each function
        for func in functions:
            # Extract just the function name (remove catalog.schema prefix if present)
            func_name = func.split(".")[-1]

            try:
                describe_query = f"DESCRIBE FUNCTION EXTENDED {catalog}.{schema}.{func_name}"
                desc_df = self.query_executor.execute_query_with_catalog(
                    catalog, describe_query, workspace
                )

                # Parse the describe extended output with filtering
                function_details = self._parse_function_description(desc_df)
                result["functions"][func_name] = function_details

            except Exception as e:
                # If we can't describe a function, include error info
                result["functions"][func_name] = {
                    "error": "Could not describe function",
                    "message": str(e),
                }

        return result

    def _parse_function_description(self, df: pd.DataFrame) -> list[str]:
        """Parse DESCRIBE FUNCTION EXTENDED output.

        Filters out unwanted lines (Configs, Owner, Create Time) and extracts
        relevant function metadata.

        Args:
            df: DataFrame returned from DESCRIBE FUNCTION EXTENDED query.

        Returns:
            List of cleaned description lines containing function metadata.

        Example:
            >>> # Internal method called by describe_function
            >>> df = query_executor.execute_query("DESCRIBE FUNCTION EXTENDED my_func")
            >>> details = service._parse_function_description(df)
            >>> print(details)
            [
                'Function: main.default.my_func',
                'Type: SCALAR',
                'Input: (x INT)',
                'Returns: INT',
                'Deterministic: true'
            ]
        """
        function_details = []
        skip_configs = False

        for _, row in df.iterrows():
            if pd.notna(row.get("function_desc", "")):
                desc_line = str(row["function_desc"])

                # Check if we should skip this line
                if desc_line.startswith("Configs:"):
                    skip_configs = True
                    continue
                elif desc_line.startswith("Owner:") or desc_line.startswith("Create Time:"):
                    continue
                elif skip_configs and desc_line.startswith("               "):
                    # Skip config lines (they are indented with many spaces)
                    continue
                elif desc_line.startswith("Deterministic:") or desc_line.startswith("Data Access:"):
                    skip_configs = False  # These come after configs, so stop skipping

                # Add lines we want to keep
                if (
                    desc_line.startswith("Function:")
                    or desc_line.startswith("Type:")
                    or desc_line.startswith("Input:")
                    or desc_line.startswith("Returns:")
                    or desc_line.startswith("Comment:")
                    or desc_line.startswith("Deterministic:")
                    or desc_line.startswith("Data Access:")
                    or desc_line.startswith("Body:")
                    or desc_line.startswith("               ")
                ):  # Keep indented Input/Returns lines
                    # For indented lines, only keep if we're not in config section
                    if desc_line.startswith("               ") and not skip_configs:
                        function_details.append(desc_line)
                    elif not desc_line.startswith("               "):
                        function_details.append(desc_line)

        return function_details
