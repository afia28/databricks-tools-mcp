"""
Testing Examples for Databricks Tools MCP Server

This module demonstrates testing patterns and best practices for:
- Unit testing services in isolation
- Mocking dependencies
- Integration testing
- Test fixtures and setup
- Achieving high test coverage
"""

from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from databricks_tools.config.models import WorkspaceConfig
from databricks_tools.core.container import ApplicationContainer
from databricks_tools.core.query_executor import QueryExecutor
from databricks_tools.core.token_counter import TokenCounter
from databricks_tools.security.role_manager import Role
from databricks_tools.services.catalog_service import CatalogService

# ============================================================================
# UNIT TESTING - Testing Services in Isolation
# ============================================================================


def test_catalog_service_list_catalogs():
    """
    Example: Unit test for CatalogService.list_catalogs()

    This demonstrates:
    - Mocking dependencies (TokenCounter, QueryExecutor)
    - Testing service logic in isolation
    - Verifying return values
    """
    # Arrange: Create mocks
    mock_token_counter = Mock(spec=TokenCounter)
    mock_query_executor = Mock(spec=QueryExecutor)

    # Setup mock return value - simulate database response
    mock_df = pd.DataFrame({"catalog_name": ["main", "analytics", "testing"]})
    mock_query_executor.execute_query.return_value = mock_df

    # Create service with mocked dependencies
    catalog_service = CatalogService(mock_token_counter, mock_query_executor)

    # Act: Call the method
    result = catalog_service.list_catalogs()

    # Assert: Verify results
    assert "catalogs" in result
    assert len(result["catalogs"]) == 3
    assert "main" in result["catalogs"]
    assert "analytics" in result["catalogs"]
    assert "testing" in result["catalogs"]

    # Verify the query executor was called with correct SQL
    mock_query_executor.execute_query.assert_called_once()
    call_args = mock_query_executor.execute_query.call_args
    assert "SHOW CATALOGS" in call_args[0][0]


def test_catalog_service_list_schemas():
    """
    Example: Unit test for CatalogService.list_schemas()
    """
    # Arrange
    mock_token_counter = Mock(spec=TokenCounter)
    mock_query_executor = Mock(spec=QueryExecutor)

    mock_df = pd.DataFrame({"namespace": ["default", "production", "staging"]})
    mock_query_executor.execute_query_with_catalog.return_value = mock_df

    catalog_service = CatalogService(mock_token_counter, mock_query_executor)

    # Act
    result = catalog_service.list_schemas("main")

    # Assert
    assert "schemas" in result
    assert len(result["schemas"]) == 3
    assert "default" in result["schemas"]

    # Verify correct catalog was used
    mock_query_executor.execute_query_with_catalog.assert_called_once()
    call_args = mock_query_executor.execute_query_with_catalog.call_args
    assert call_args[1]["catalog"] == "main"


def test_catalog_service_error_handling():
    """
    Example: Test error handling in services
    """
    # Arrange
    mock_token_counter = Mock(spec=TokenCounter)
    mock_query_executor = Mock(spec=QueryExecutor)

    # Simulate database error
    mock_query_executor.execute_query.side_effect = Exception("Database connection failed")

    catalog_service = CatalogService(mock_token_counter, mock_query_executor)

    # Act & Assert: Verify exception is raised
    with pytest.raises(Exception) as exc_info:
        catalog_service.list_catalogs()

    assert "Database connection failed" in str(exc_info.value)


# ============================================================================
# FIXTURE EXAMPLES - Reusable Test Setup
# ============================================================================


@pytest.fixture
def mock_token_counter():
    """Fixture: Create a mocked TokenCounter."""
    mock = Mock(spec=TokenCounter)
    mock.count_tokens.return_value = 100
    mock.estimate_tokens.return_value = 500
    return mock


@pytest.fixture
def mock_query_executor():
    """Fixture: Create a mocked QueryExecutor with default behavior."""
    mock = Mock(spec=QueryExecutor)

    # Default return value - can be overridden in tests
    mock.execute_query.return_value = pd.DataFrame({"result": [1, 2, 3]})

    return mock


@pytest.fixture
def catalog_service(mock_token_counter, mock_query_executor):
    """Fixture: Create CatalogService with mocked dependencies."""
    return CatalogService(mock_token_counter, mock_query_executor)


def test_using_fixtures(catalog_service, mock_query_executor):
    """
    Example: Using pytest fixtures for cleaner tests.
    """
    # Arrange: Override mock behavior for this test
    mock_df = pd.DataFrame({"catalog_name": ["test_catalog"]})
    mock_query_executor.execute_query.return_value = mock_df

    # Act
    result = catalog_service.list_catalogs()

    # Assert
    assert len(result["catalogs"]) == 1
    assert "test_catalog" in result["catalogs"]


# ============================================================================
# INTEGRATION TESTING - Testing Component Interactions
# ============================================================================


@patch("databricks_tools.core.connection.ConnectionManager")
def test_query_executor_integration(mock_connection_class):
    """
    Example: Integration test with partial mocking.

    This tests QueryExecutor with a mocked database connection
    but real WorkspaceConfigManager.
    """
    # Arrange: Setup mock connection
    mock_connection = MagicMock()
    mock_cursor = MagicMock()

    # Create mock Arrow table for fetchall_arrow()
    mock_arrow_table = MagicMock()
    mock_df = pd.DataFrame({"result": [1, 2, 3]})
    mock_arrow_table.to_pandas.return_value = mock_df

    mock_cursor.fetchall_arrow.return_value = mock_arrow_table
    mock_connection.__enter__.return_value.cursor.return_value = mock_cursor
    mock_connection_class.return_value = mock_connection

    # Create real WorkspaceConfigManager with mocked workspace config
    from databricks_tools.config.workspace import WorkspaceConfigManager
    from databricks_tools.security.role_manager import RoleManager

    with patch.object(WorkspaceConfigManager, "get_workspace_config") as mock_get_config:
        mock_config = WorkspaceConfig(
            server_hostname="https://test.databricks.com",
            http_path="/sql/1.0/warehouses/test",
            access_token="test_token",
        )
        mock_get_config.return_value = mock_config

        role_manager = RoleManager(Role.ANALYST)
        workspace_manager = WorkspaceConfigManager(role_manager)
        query_executor = QueryExecutor(workspace_manager)

        # Act
        result_df = query_executor.execute_query("SELECT 1")

        # Assert
        assert len(result_df) == 3
        assert "result" in result_df.columns
        mock_cursor.execute.assert_called_once_with("SELECT 1")


# ============================================================================
# CONTAINER TESTING - Testing with ApplicationContainer
# ============================================================================


def test_application_container_initialization():
    """
    Example: Test ApplicationContainer initialization.
    """
    # Act
    container = ApplicationContainer(role=Role.ANALYST, max_tokens=5000)

    # Assert: Verify all services are initialized
    assert container.role_manager is not None
    assert container.workspace_manager is not None
    assert container.token_counter is not None
    assert container.query_executor is not None
    assert container.catalog_service is not None
    assert container.table_service is not None
    assert container.function_service is not None
    assert container.chunking_service is not None
    assert container.response_manager is not None

    # Verify role configuration
    assert container.role_manager.role == Role.ANALYST


def test_container_with_mocked_services():
    """
    Example: Create a test container with mocked services.
    """
    # Create container
    container = ApplicationContainer(role=Role.ANALYST)

    # Replace service with mock
    mock_catalog_service = Mock()
    mock_catalog_service.list_catalogs.return_value = {"catalogs": ["test_catalog"]}
    container.catalog_service = mock_catalog_service

    # Use the container with mocked service
    result = container.catalog_service.list_catalogs()

    assert result["catalogs"] == ["test_catalog"]


# ============================================================================
# PARAMETERIZED TESTING - Testing Multiple Scenarios
# ============================================================================


@pytest.mark.parametrize(
    "role,expected_workspace_count",
    [
        (Role.ANALYST, 1),  # Analyst has access to 1 workspace only
        (Role.DEVELOPER, 1),  # Developer can have multiple (depends on env)
    ],
)
def test_role_based_workspace_access(role, expected_workspace_count):
    """
    Example: Parameterized test for role-based access.

    This tests different roles with expected behaviors.
    """
    container = ApplicationContainer(role=role)

    workspaces = container.workspace_manager.get_available_workspaces()

    # In test environment with single workspace, both roles see 1 workspace
    # In production with multiple workspaces, developer would see more
    assert len(workspaces) >= expected_workspace_count


@pytest.mark.parametrize(
    "sql,expected_columns",
    [
        ("SELECT 1 as col1", ["col1"]),
        ("SELECT 1 as a, 2 as b", ["a", "b"]),
        ("SELECT 1 as x, 2 as y, 3 as z", ["x", "y", "z"]),
    ],
)
def test_query_columns(sql, expected_columns, mock_query_executor):
    """
    Example: Parameterized test for query execution.
    """
    # Create mock DataFrame with expected columns
    data = {col: [1] for col in expected_columns}
    mock_df = pd.DataFrame(data)
    mock_query_executor.execute_query.return_value = mock_df

    # Execute query
    result_df = mock_query_executor.execute_query(sql)

    # Verify columns
    assert list(result_df.columns) == expected_columns


# ============================================================================
# COVERAGE BEST PRACTICES
# ============================================================================


def test_edge_case_empty_dataframe(mock_token_counter, mock_query_executor):
    """
    Example: Test edge case with empty results.
    """
    # Arrange: Return empty DataFrame
    mock_query_executor.execute_query.return_value = pd.DataFrame()

    catalog_service = CatalogService(mock_token_counter, mock_query_executor)

    # Act
    result = catalog_service.list_catalogs()

    # Assert: Service handles empty results gracefully
    assert "catalogs" in result
    assert len(result["catalogs"]) == 0


def test_edge_case_null_values(mock_token_counter, mock_query_executor):
    """
    Example: Test handling of NULL values.
    """
    # Arrange: Return DataFrame with NULL values
    mock_df = pd.DataFrame({"catalog_name": ["catalog1", None, "catalog2"]})
    mock_query_executor.execute_query.return_value = mock_df

    catalog_service = CatalogService(mock_token_counter, mock_query_executor)

    # Act
    result = catalog_service.list_catalogs()

    # Assert: NULL values are handled properly
    assert "catalogs" in result
    # Check how service handles NaN - might filter or convert to string
    assert len(result["catalogs"]) >= 2


# ============================================================================
# ASYNC/MOCK BEST PRACTICES
# ============================================================================


def test_mock_call_verification():
    """
    Example: Verify mock calls and arguments.
    """
    mock_executor = Mock(spec=QueryExecutor)
    mock_executor.execute_query.return_value = pd.DataFrame({"result": [1]})

    # Call with specific arguments
    mock_executor.execute_query("SELECT 1", workspace="prod")

    # Verify call count
    assert mock_executor.execute_query.call_count == 1

    # Verify call arguments
    mock_executor.execute_query.assert_called_with("SELECT 1", workspace="prod")

    # Verify using call_args
    args, kwargs = mock_executor.execute_query.call_args
    assert args[0] == "SELECT 1"
    assert kwargs["workspace"] == "prod"


def test_mock_side_effects():
    """
    Example: Using side_effect for dynamic mock behavior.
    """
    mock_executor = Mock(spec=QueryExecutor)

    # Setup side effect - different results for different calls
    mock_executor.execute_query.side_effect = [
        pd.DataFrame({"result": [1]}),
        pd.DataFrame({"result": [2]}),
        pd.DataFrame({"result": [3]}),
    ]

    # First call returns first result
    result1 = mock_executor.execute_query("SELECT 1")
    assert result1["result"].iloc[0] == 1

    # Second call returns second result
    result2 = mock_executor.execute_query("SELECT 2")
    assert result2["result"].iloc[0] == 2

    # Third call returns third result
    result3 = mock_executor.execute_query("SELECT 3")
    assert result3["result"].iloc[0] == 3


# ============================================================================
# RUNNING TESTS
# ============================================================================


if __name__ == "__main__":
    """
    Run tests using pytest.

    Commands:
        # Run all tests in this file
        pytest examples/testing_example.py

        # Run with verbose output
        pytest examples/testing_example.py -v

        # Run with coverage
        pytest examples/testing_example.py --cov=databricks_tools

        # Run specific test
        pytest examples/testing_example.py::test_catalog_service_list_catalogs

        # Run tests matching pattern
        pytest examples/testing_example.py -k "catalog"
    """
    import sys

    print("\n" + "=" * 80)
    print("DATABRICKS TOOLS MCP SERVER - TESTING EXAMPLES")
    print("=" * 80 + "\n")

    print("This file contains testing examples and patterns.")
    print("Run with pytest to execute the tests:")
    print()
    print("  pytest examples/testing_example.py -v")
    print()
    print("=" * 80 + "\n")

    # Exit with code to indicate these are examples, not runnable script
    sys.exit(0)
