"""Tests for QueryExecutor service.

This module contains comprehensive tests for the QueryExecutor class,
covering query execution, catalog context, error handling, and integration.

Test coverage goal: 95%+ for src/databricks_tools/core/query_executor.py

Test cases included:
1. test_query_executor_simple_query - Basic query execution
2. test_query_executor_with_workspace - Query on specific workspace
3. test_query_executor_parse_dates - Date parsing functionality
4. test_query_executor_empty_result - Empty DataFrame handling
5. test_query_executor_large_result - Large DataFrame handling
6. test_query_executor_query_error - SQL syntax error handling
7. test_query_executor_connection_error - Connection failure handling
8. test_query_executor_with_catalog - execute_query_with_catalog()
9. test_query_executor_catalog_not_exists - Catalog error handling
10. test_query_executor_multiple_queries - Sequential execution
11. test_query_executor_workspace_fallback - Workspace fallback behavior
12. test_query_executor_invalid_workspace - Invalid workspace handling
13. test_legacy_wrapper_functions - Wrapper function delegation
"""

from unittest.mock import MagicMock, Mock, call, patch

import pandas as pd
import pytest
from databricks.sql import Error as DatabricksError
from pydantic import SecretStr

from databricks_tools.config.models import WorkspaceConfig
from databricks_tools.config.workspace import WorkspaceConfigManager
from databricks_tools.core.query_executor import QueryExecutor

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_workspace_config() -> WorkspaceConfig:
    """Create a mock WorkspaceConfig for testing.

    Returns:
        A WorkspaceConfig instance with valid test credentials.
    """
    return WorkspaceConfig(
        server_hostname="https://test.cloud.databricks.com",
        http_path="/sql/1.0/warehouses/test123",
        access_token=SecretStr("dapi_test_token_12345678901234567890"),
        workspace_name="test",
    )


@pytest.fixture
def mock_workspace_manager(mock_workspace_config: WorkspaceConfig) -> MagicMock:
    """Create a mock WorkspaceConfigManager.

    Returns:
        A MagicMock configured to return a valid WorkspaceConfig.
    """
    manager = MagicMock(spec=WorkspaceConfigManager)
    manager.get_workspace_config.return_value = mock_workspace_config
    return manager


@pytest.fixture
def query_executor(mock_workspace_manager: MagicMock) -> QueryExecutor:
    """Create a QueryExecutor with mock workspace manager.

    Returns:
        A QueryExecutor instance with mocked dependencies.
    """
    return QueryExecutor(mock_workspace_manager)


@pytest.fixture
def mock_dataframe() -> pd.DataFrame:
    """Create a simple mock DataFrame for testing.

    Returns:
        A pandas DataFrame with sample test data.
    """
    return pd.DataFrame(
        {"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "value": [100, 200, 300]}
    )


@pytest.fixture
def empty_dataframe() -> pd.DataFrame:
    """Create an empty DataFrame for testing.

    Returns:
        An empty pandas DataFrame with defined columns.
    """
    return pd.DataFrame(columns=["id", "name", "value"])


@pytest.fixture
def large_dataframe() -> pd.DataFrame:
    """Create a large DataFrame for testing.

    Returns:
        A pandas DataFrame with 1000 rows.
    """
    return pd.DataFrame(
        {
            "id": range(1, 1001),
            "name": [f"User_{i}" for i in range(1, 1001)],
            "value": [i * 100 for i in range(1, 1001)],
        }
    )


@pytest.fixture
def mock_connection() -> MagicMock:
    """Create a mock databricks.sql.Connection.

    Returns:
        A MagicMock configured to behave like a Databricks SQL connection.
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn


# =============================================================================
# Basic Query Execution Tests
# =============================================================================


class TestQueryExecutorBasicQueries:
    """Tests for basic query execution using execute_query()."""

    @patch("databricks_tools.core.query_executor.ConnectionManager")
    @patch("databricks_tools.core.query_executor.pd.read_sql")
    def test_query_executor_simple_query(
        self,
        mock_read_sql: Mock,
        mock_conn_mgr: Mock,
        query_executor: QueryExecutor,
        mock_dataframe: pd.DataFrame,
        mock_connection: MagicMock,
    ):
        """Test basic query execution with execute_query().

        The QueryExecutor should:
        1. Create a connection using ConnectionManager
        2. Execute the query using pd.read_sql
        3. Return a pandas DataFrame

        This is test case 1 from the requirements.
        """
        # Arrange
        mock_conn_mgr.return_value.__enter__.return_value = mock_connection
        mock_read_sql.return_value = mock_dataframe

        # Act
        result = query_executor.execute_query("SELECT * FROM test_table")

        # Assert
        assert isinstance(result, pd.DataFrame)
        pd.testing.assert_frame_equal(result, mock_dataframe)
        mock_read_sql.assert_called_once_with(
            "SELECT * FROM test_table", mock_connection, parse_dates=None
        )
        mock_conn_mgr.assert_called_once()

    @patch("databricks_tools.core.query_executor.ConnectionManager")
    @patch("databricks_tools.core.query_executor.pd.read_sql")
    def test_query_executor_with_workspace(
        self,
        mock_read_sql: Mock,
        mock_conn_mgr: Mock,
        mock_workspace_manager: MagicMock,
        mock_dataframe: pd.DataFrame,
        mock_connection: MagicMock,
    ):
        """Test query execution on a specific workspace.

        The QueryExecutor should:
        1. Call workspace_manager.get_workspace_config with the workspace name
        2. Use the returned config to create a connection
        3. Execute the query and return results

        This is test case 2 from the requirements.
        """
        # Arrange
        mock_conn_mgr.return_value.__enter__.return_value = mock_connection
        mock_read_sql.return_value = mock_dataframe

        prod_config = WorkspaceConfig(
            server_hostname="https://prod.cloud.databricks.com",
            http_path="/sql/1.0/warehouses/prod123",
            access_token=SecretStr("dapi_prod_token_12345678901234567890"),
            workspace_name="production",
        )
        mock_workspace_manager.get_workspace_config.return_value = prod_config

        executor = QueryExecutor(mock_workspace_manager)

        # Act
        result = executor.execute_query("SELECT 1", workspace="production")

        # Assert
        assert isinstance(result, pd.DataFrame)
        mock_workspace_manager.get_workspace_config.assert_called_once_with("production")
        mock_conn_mgr.assert_called_once_with(prod_config)

    @patch("databricks_tools.core.query_executor.ConnectionManager")
    @patch("databricks_tools.core.query_executor.pd.read_sql")
    def test_query_executor_parse_dates(
        self,
        mock_read_sql: Mock,
        mock_conn_mgr: Mock,
        query_executor: QueryExecutor,
        mock_connection: MagicMock,
    ):
        """Test date parsing functionality with parse_dates parameter.

        The QueryExecutor should:
        1. Pass the parse_dates parameter to pd.read_sql
        2. Allow date columns to be parsed automatically

        This is test case 3 from the requirements.
        """
        # Arrange
        mock_conn_mgr.return_value.__enter__.return_value = mock_connection
        df_with_dates = pd.DataFrame(
            {
                "id": [1, 2],
                "created_at": pd.to_datetime(["2023-01-01", "2023-01-02"]),
                "updated_at": pd.to_datetime(["2023-01-15", "2023-01-16"]),
            }
        )
        mock_read_sql.return_value = df_with_dates

        # Act
        result = query_executor.execute_query(
            "SELECT * FROM test_table", parse_dates=["created_at", "updated_at"]
        )

        # Assert
        assert isinstance(result, pd.DataFrame)
        mock_read_sql.assert_called_once_with(
            "SELECT * FROM test_table",
            mock_connection,
            parse_dates=["created_at", "updated_at"],
        )

    @patch("databricks_tools.core.query_executor.ConnectionManager")
    @patch("databricks_tools.core.query_executor.pd.read_sql")
    def test_query_executor_empty_result(
        self,
        mock_read_sql: Mock,
        mock_conn_mgr: Mock,
        query_executor: QueryExecutor,
        empty_dataframe: pd.DataFrame,
        mock_connection: MagicMock,
    ):
        """Test query that returns an empty DataFrame.

        The QueryExecutor should:
        1. Handle empty results gracefully
        2. Return an empty DataFrame with correct structure

        This is test case 4 from the requirements.
        """
        # Arrange
        mock_conn_mgr.return_value.__enter__.return_value = mock_connection
        mock_read_sql.return_value = empty_dataframe

        # Act
        result = query_executor.execute_query("SELECT * FROM empty_table WHERE 1=0")

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert list(result.columns) == ["id", "name", "value"]

    @patch("databricks_tools.core.query_executor.ConnectionManager")
    @patch("databricks_tools.core.query_executor.pd.read_sql")
    def test_query_executor_large_result(
        self,
        mock_read_sql: Mock,
        mock_conn_mgr: Mock,
        query_executor: QueryExecutor,
        large_dataframe: pd.DataFrame,
        mock_connection: MagicMock,
    ):
        """Test query with large result set.

        The QueryExecutor should:
        1. Handle large DataFrames correctly
        2. Not impose artificial limits on result size

        This is test case 5 from the requirements.
        """
        # Arrange
        mock_conn_mgr.return_value.__enter__.return_value = mock_connection
        mock_read_sql.return_value = large_dataframe

        # Act
        result = query_executor.execute_query("SELECT * FROM large_table")

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1000
        assert list(result.columns) == ["id", "name", "value"]


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestQueryExecutorErrorHandling:
    """Tests for error handling and edge cases."""

    @patch("databricks_tools.core.query_executor.ConnectionManager")
    @patch("databricks_tools.core.query_executor.pd.read_sql")
    def test_query_executor_query_error(
        self,
        mock_read_sql: Mock,
        mock_conn_mgr: Mock,
        query_executor: QueryExecutor,
        mock_connection: MagicMock,
    ):
        """Test SQL syntax error handling.

        When pd.read_sql raises an exception:
        1. The exception should propagate to the caller
        2. Connection cleanup should still occur (context manager)

        This is test case 6 from the requirements.
        """
        # Arrange
        mock_conn_mgr.return_value.__enter__.return_value = mock_connection
        mock_read_sql.side_effect = Exception("SQL syntax error: unexpected token")

        # Act & Assert
        with pytest.raises(Exception, match="SQL syntax error"):
            query_executor.execute_query("INVALID SQL QUERY")

        # Verify connection was attempted
        mock_conn_mgr.assert_called_once()

    @patch("databricks_tools.core.query_executor.ConnectionManager")
    def test_query_executor_connection_error(
        self,
        mock_conn_mgr: Mock,
        query_executor: QueryExecutor,
    ):
        """Test database connection failure handling.

        When ConnectionManager raises an exception:
        1. The error should propagate
        2. No query should be executed

        This is test case 7 from the requirements.
        """
        # Arrange
        mock_conn_mgr.return_value.__enter__.side_effect = DatabricksError(
            "Connection failed: network unreachable"
        )

        # Act & Assert
        with pytest.raises(DatabricksError, match="Connection failed"):
            query_executor.execute_query("SELECT 1")

    def test_query_executor_invalid_workspace(self, mock_workspace_manager: MagicMock):
        """Test error when workspace doesn't exist.

        When workspace_manager raises ValueError:
        1. The error should propagate
        2. Include helpful information about available workspaces

        This is test case 12 from the requirements.
        """
        # Arrange
        mock_workspace_manager.get_workspace_config.side_effect = ValueError(
            "Workspace 'nonexistent' configuration not found. Available workspaces: default, production"
        )
        executor = QueryExecutor(mock_workspace_manager)

        # Act & Assert
        with pytest.raises(ValueError, match="Workspace 'nonexistent' configuration not found"):
            executor.execute_query("SELECT 1", workspace="nonexistent")


# =============================================================================
# Catalog Context Tests
# =============================================================================


class TestQueryExecutorWithCatalog:
    """Tests for catalog context queries using execute_query_with_catalog()."""

    @patch("databricks_tools.core.query_executor.ConnectionManager")
    def test_query_executor_with_catalog(
        self,
        mock_conn_mgr: Mock,
        query_executor: QueryExecutor,
        mock_connection: MagicMock,
    ):
        """Test execute_query_with_catalog() sets catalog context.

        The method should:
        1. Execute USE CATALOG command first
        2. Then execute the actual query
        3. Return results as DataFrame

        This is test case 8 from the requirements.
        """
        # Arrange
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_conn_mgr.return_value.__enter__.return_value = mock_connection

        # Mock cursor fetchall and description
        mock_cursor.fetchall.return_value = [(1, "Alice"), (2, "Bob")]
        mock_cursor.description = [("id",), ("name",)]

        # Act
        result = query_executor.execute_query_with_catalog(
            "my_catalog", "SELECT * FROM my_schema.my_table"
        )

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ["id", "name"]

        # Verify USE CATALOG was executed first
        calls = mock_cursor.execute.call_args_list
        assert len(calls) == 2
        assert calls[0] == call("USE CATALOG my_catalog")
        assert calls[1] == call("SELECT * FROM my_schema.my_table")

        # Verify cursor was closed
        mock_cursor.close.assert_called_once()

    @patch("databricks_tools.core.query_executor.ConnectionManager")
    def test_query_executor_catalog_not_exists(
        self,
        mock_conn_mgr: Mock,
        query_executor: QueryExecutor,
        mock_connection: MagicMock,
    ):
        """Test behavior when catalog doesn't exist.

        When USE CATALOG fails:
        1. The exception should propagate
        2. Cursor should still be closed (cleanup)

        This is test case 9 from the requirements.
        """
        # Arrange
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_conn_mgr.return_value.__enter__.return_value = mock_connection

        # Mock cursor.execute to raise error on USE CATALOG
        mock_cursor.execute.side_effect = DatabricksError("Catalog 'invalid' not found")

        # Act & Assert
        with pytest.raises(DatabricksError, match="Catalog 'invalid' not found"):
            query_executor.execute_query_with_catalog("invalid", "SELECT 1")

        # Verify cursor was still closed despite error
        mock_cursor.close.assert_called_once()

    @patch("databricks_tools.core.query_executor.ConnectionManager")
    def test_query_executor_catalog_with_workspace(
        self,
        mock_conn_mgr: Mock,
        mock_workspace_manager: MagicMock,
        mock_connection: MagicMock,
    ):
        """Test execute_query_with_catalog() with specific workspace.

        The method should:
        1. Get the workspace config for the specified workspace
        2. Use that config to create connection
        3. Execute catalog and query

        This extends test case 8 with workspace parameter.
        """
        # Arrange
        prod_config = WorkspaceConfig(
            server_hostname="https://prod.cloud.databricks.com",
            http_path="/sql/1.0/warehouses/prod123",
            access_token=SecretStr("dapi_prod_token_12345678901234567890"),
            workspace_name="production",
        )
        mock_workspace_manager.get_workspace_config.return_value = prod_config

        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_conn_mgr.return_value.__enter__.return_value = mock_connection

        mock_cursor.fetchall.return_value = [(100,)]
        mock_cursor.description = [("count",)]

        executor = QueryExecutor(mock_workspace_manager)

        # Act
        result = executor.execute_query_with_catalog(
            "analytics", "SELECT COUNT(*) as count FROM table", workspace="production"
        )

        # Assert
        assert isinstance(result, pd.DataFrame)
        mock_workspace_manager.get_workspace_config.assert_called_once_with("production")
        mock_conn_mgr.assert_called_once_with(prod_config)

    @patch("databricks_tools.core.query_executor.ConnectionManager")
    def test_query_executor_catalog_empty_result(
        self,
        mock_conn_mgr: Mock,
        query_executor: QueryExecutor,
        mock_connection: MagicMock,
    ):
        """Test execute_query_with_catalog() with empty result.

        The method should:
        1. Handle empty result sets gracefully
        2. Return empty DataFrame with correct columns

        This extends test case 8 with empty results.
        """
        # Arrange
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_conn_mgr.return_value.__enter__.return_value = mock_connection

        # Mock empty result
        mock_cursor.fetchall.return_value = []
        mock_cursor.description = [("id",), ("name",)]

        # Act
        result = query_executor.execute_query_with_catalog(
            "my_catalog", "SELECT * FROM empty_table WHERE 1=0"
        )

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert list(result.columns) == ["id", "name"]

    @patch("databricks_tools.core.query_executor.ConnectionManager")
    def test_query_executor_catalog_cursor_cleanup_on_exception(
        self,
        mock_conn_mgr: Mock,
        query_executor: QueryExecutor,
        mock_connection: MagicMock,
    ):
        """Test cursor is closed even if query execution fails.

        The method should:
        1. Close cursor in finally block
        2. Ensure cleanup happens regardless of exceptions

        This is an edge case for test case 8.
        """
        # Arrange
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_conn_mgr.return_value.__enter__.return_value = mock_connection

        # Mock execute to raise error on second call (the query)
        mock_cursor.execute.side_effect = [
            None,
            DatabricksError("Query execution failed"),
        ]

        # Act & Assert
        with pytest.raises(DatabricksError, match="Query execution failed"):
            query_executor.execute_query_with_catalog("catalog", "SELECT * FROM table")

        # Verify cursor was still closed
        mock_cursor.close.assert_called_once()


# =============================================================================
# Integration Tests
# =============================================================================


class TestQueryExecutorIntegration:
    """Tests for integration with other components."""

    @patch("databricks_tools.core.query_executor.ConnectionManager")
    @patch("databricks_tools.core.query_executor.pd.read_sql")
    def test_query_executor_multiple_queries(
        self,
        mock_read_sql: Mock,
        mock_conn_mgr: Mock,
        query_executor: QueryExecutor,
        mock_connection: MagicMock,
    ):
        """Test sequential query execution.

        The QueryExecutor should:
        1. Create fresh connection for each query (context manager)
        2. Execute queries independently
        3. Clean up connections between queries

        This is test case 10 from the requirements.
        """
        # Arrange
        mock_conn_mgr.return_value.__enter__.return_value = mock_connection

        df1 = pd.DataFrame({"count": [10]})
        df2 = pd.DataFrame({"count": [20]})
        df3 = pd.DataFrame({"count": [30]})
        mock_read_sql.side_effect = [df1, df2, df3]

        # Act
        result1 = query_executor.execute_query("SELECT COUNT(*) FROM table1")
        result2 = query_executor.execute_query("SELECT COUNT(*) FROM table2")
        result3 = query_executor.execute_query("SELECT COUNT(*) FROM table3")

        # Assert
        assert result1["count"][0] == 10
        assert result2["count"][0] == 20
        assert result3["count"][0] == 30

        # Verify ConnectionManager was used 3 times (fresh connection each time)
        assert mock_conn_mgr.call_count == 3

    def test_query_executor_workspace_fallback(self, mock_workspace_manager: MagicMock):
        """Test workspace fallback behavior through WorkspaceConfigManager.

        When a workspace is not found:
        1. WorkspaceConfigManager should handle the fallback
        2. QueryExecutor should use the returned config

        This is test case 11 from the requirements.
        """
        # Arrange
        default_config = WorkspaceConfig(
            server_hostname="https://default.cloud.databricks.com",
            http_path="/sql/1.0/warehouses/default123",
            access_token=SecretStr("dapi_default_token_12345678901234567890"),
            workspace_name="default",
        )

        # Simulate WorkspaceConfigManager fallback behavior
        # When "missing" workspace is requested, it falls back to default
        mock_workspace_manager.get_workspace_config.return_value = default_config

        executor = QueryExecutor(mock_workspace_manager)

        # Act
        with patch("databricks_tools.core.query_executor.ConnectionManager") as mock_conn_mgr:
            with patch("databricks_tools.core.query_executor.pd.read_sql") as mock_read_sql:
                mock_conn = MagicMock()
                mock_conn_mgr.return_value.__enter__.return_value = mock_conn
                mock_read_sql.return_value = pd.DataFrame({"value": [1]})

                result = executor.execute_query("SELECT 1", workspace="missing")

        # Assert
        assert isinstance(result, pd.DataFrame)
        mock_workspace_manager.get_workspace_config.assert_called_once_with("missing")
        # Verify the default config was used (WorkspaceConfigManager handled fallback)
        mock_conn_mgr.assert_called_once_with(default_config)

    def test_query_executor_initialization(self, mock_workspace_manager: MagicMock):
        """Test QueryExecutor initialization.

        The QueryExecutor should:
        1. Accept a WorkspaceConfigManager instance
        2. Store it as an attribute
        3. Be ready to use immediately

        This is a basic integration test.
        """
        # Act
        executor = QueryExecutor(mock_workspace_manager)

        # Assert
        assert executor.workspace_manager is mock_workspace_manager


# =============================================================================
# Legacy Wrapper Function Tests
# =============================================================================


class TestLegacyWrapperFunctions:
    """Tests for server.py wrapper functions."""

    @patch("databricks_tools.server._container")
    def test_databricks_sql_query_wrapper(self, mock_container: MagicMock):
        """Test databricks_sql_query() wrapper function.

        The wrapper should:
        1. Delegate to QueryExecutor.execute_query()
        2. Pass all parameters correctly
        3. Return the DataFrame result

        This is part of test case 13 from the requirements.
        """
        # Import here to avoid circular dependencies
        from databricks_tools.server import databricks_sql_query

        # Arrange
        mock_df = pd.DataFrame({"value": [1, 2, 3]})
        mock_container.query_executor.execute_query.return_value = mock_df

        # Act
        result = databricks_sql_query(
            "SELECT * FROM table", parse_dates=["date_col"], workspace="production"
        )

        # Assert
        pd.testing.assert_frame_equal(result, mock_df)
        mock_container.query_executor.execute_query.assert_called_once_with(
            "SELECT * FROM table", "production", ["date_col"]
        )

    @patch("databricks_tools.server._container")
    def test_databricks_sql_query_with_catalog_wrapper(self, mock_container: MagicMock):
        """Test databricks_sql_query_with_catalog() wrapper function.

        The wrapper should:
        1. Delegate to QueryExecutor.execute_query_with_catalog()
        2. Pass all parameters correctly
        3. Return the DataFrame result

        This is part of test case 13 from the requirements.
        """
        # Import here to avoid circular dependencies
        from databricks_tools.server import databricks_sql_query_with_catalog

        # Arrange
        mock_df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        mock_container.query_executor.execute_query_with_catalog.return_value = mock_df

        # Act
        result = databricks_sql_query_with_catalog(
            "my_catalog", "SELECT * FROM table", workspace="production"
        )

        # Assert
        pd.testing.assert_frame_equal(result, mock_df)
        mock_container.query_executor.execute_query_with_catalog.assert_called_once_with(
            "my_catalog", "SELECT * FROM table", "production"
        )

    @patch("databricks_tools.server._container")
    def test_wrapper_functions_default_parameters(self, mock_container: MagicMock):
        """Test wrapper functions with default parameters.

        The wrappers should:
        1. Use default values for optional parameters
        2. Pass None for workspace and parse_dates when not provided

        This is part of test case 13 from the requirements.
        """
        # Import here to avoid circular dependencies
        from databricks_tools.server import (
            databricks_sql_query,
            databricks_sql_query_with_catalog,
        )

        # Arrange
        mock_df = pd.DataFrame({"value": [42]})
        mock_container.query_executor.execute_query.return_value = mock_df
        mock_container.query_executor.execute_query_with_catalog.return_value = mock_df

        # Act - databricks_sql_query with defaults
        databricks_sql_query("SELECT 1")

        # Act - databricks_sql_query_with_catalog with defaults
        databricks_sql_query_with_catalog("catalog", "SELECT 1")

        # Assert
        mock_container.query_executor.execute_query.assert_called_once_with("SELECT 1", None, None)
        mock_container.query_executor.execute_query_with_catalog.assert_called_once_with(
            "catalog", "SELECT 1", None
        )


# =============================================================================
# Edge Cases and Additional Tests
# =============================================================================


class TestQueryExecutorEdgeCases:
    """Tests for edge cases and additional scenarios."""

    @patch("databricks_tools.core.query_executor.ConnectionManager")
    @patch("databricks_tools.core.query_executor.pd.read_sql")
    def test_query_executor_none_workspace(
        self,
        mock_read_sql: Mock,
        mock_conn_mgr: Mock,
        query_executor: QueryExecutor,
        mock_dataframe: pd.DataFrame,
        mock_connection: MagicMock,
    ):
        """Test execute_query with None workspace (uses default).

        When workspace=None:
        1. Should use default workspace from config manager
        2. Query should execute normally

        This is an edge case test.
        """
        # Arrange
        mock_conn_mgr.return_value.__enter__.return_value = mock_connection
        mock_read_sql.return_value = mock_dataframe

        # Act
        result = query_executor.execute_query("SELECT 1", workspace=None)

        # Assert
        assert isinstance(result, pd.DataFrame)
        pd.testing.assert_frame_equal(result, mock_dataframe)

    @patch("databricks_tools.core.query_executor.ConnectionManager")
    @patch("databricks_tools.core.query_executor.pd.read_sql")
    def test_query_executor_none_parse_dates(
        self,
        mock_read_sql: Mock,
        mock_conn_mgr: Mock,
        query_executor: QueryExecutor,
        mock_dataframe: pd.DataFrame,
        mock_connection: MagicMock,
    ):
        """Test execute_query with None parse_dates (no date parsing).

        When parse_dates=None:
        1. Should pass None to pd.read_sql
        2. No date parsing should occur

        This is an edge case test.
        """
        # Arrange
        mock_conn_mgr.return_value.__enter__.return_value = mock_connection
        mock_read_sql.return_value = mock_dataframe

        # Act
        query_executor.execute_query("SELECT 1", parse_dates=None)

        # Assert
        mock_read_sql.assert_called_once_with("SELECT 1", mock_connection, parse_dates=None)

    @patch("databricks_tools.core.query_executor.ConnectionManager")
    def test_query_executor_catalog_no_description(
        self,
        mock_conn_mgr: Mock,
        query_executor: QueryExecutor,
        mock_connection: MagicMock,
    ):
        """Test execute_query_with_catalog when cursor.description is None.

        When cursor.description is None (e.g., INSERT/UPDATE queries):
        1. Should handle gracefully
        2. Return DataFrame with empty columns

        This is an edge case test.
        """
        # Arrange
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_conn_mgr.return_value.__enter__.return_value = mock_connection

        # Mock cursor with None description
        mock_cursor.fetchall.return_value = []
        mock_cursor.description = None

        # Act
        result = query_executor.execute_query_with_catalog(
            "catalog", "CREATE TABLE test AS SELECT 1"
        )

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result.columns) == 0
        assert len(result) == 0
