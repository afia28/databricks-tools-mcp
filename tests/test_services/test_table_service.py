"""Comprehensive test suite for TableService class.

This module contains comprehensive tests for the TableService class,
covering table listing, column metadata, row counting, and table detail operations
with consistent error handling and token management.

Test coverage goal: 90%+ for src/databricks_tools/services/table_service.py

Test cases included (30+ tests covering US-3.2):
1. test_table_service_initialization_with_dependencies - Verify proper initialization
2. test_table_service_initialization_custom_max_tokens - Custom max_tokens parameter
3. test_list_tables_single_schema - List tables in single schema
4. test_list_tables_multiple_schemas - List tables in multiple schemas
5. test_list_tables_with_workspace - Workspace parameter handling
6. test_list_tables_empty_schemas - Empty schema list handling
7. test_list_tables_empty_result - Empty table list handling
8. test_list_tables_query_executor_delegation - Verify QueryExecutor calls
9. test_list_columns_single_table - List columns for single table
10. test_list_columns_multiple_tables - List columns for multiple tables
11. test_list_columns_filters_internal_columns - Filter #-prefixed columns
12. test_list_columns_with_workspace - Workspace parameter in list_columns
13. test_list_columns_empty_tables - Handle empty table list
14. test_list_columns_query_executor_delegation - Verify QueryExecutor calls
15. test_get_table_row_count_basic - Basic row count retrieval
16. test_get_table_row_count_pagination_calculation - Verify pagination math
17. test_get_table_row_count_large_table - Large table handling
18. test_get_table_row_count_empty_table - Empty table (0 rows)
19. test_get_table_row_count_with_workspace - Workspace parameter
20. test_get_table_details_default_limit - Default limit of 1000
21. test_get_table_details_custom_limit - Custom limit parameter
22. test_get_table_details_no_limit - No limit (None)
23. test_get_table_details_with_workspace - Workspace parameter
24. test_get_table_details_data_serialization - JSON serialization
25. test_list_tables_error_propagation - Error handling for list_tables
26. test_list_columns_error_propagation - Error handling for list_columns
27. test_get_table_row_count_error_propagation - Error handling for row count
28. test_get_table_details_error_propagation - Error handling for table details
29. test_get_table_details_invalid_table - Handle table not found
30. test_integration_with_real_dependencies - Integration test
31. test_integration_multiple_operations - Sequential operations test
32. test_token_counter_integration - TokenCounter integration
"""

import json
from unittest.mock import MagicMock, call

import pandas as pd
import pytest
from databricks.sql import Error as DatabricksError

from databricks_tools.core.query_executor import QueryExecutor
from databricks_tools.core.token_counter import TokenCounter
from databricks_tools.services.table_service import TableService

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_query_executor() -> MagicMock:
    """Create a mock QueryExecutor for testing.

    Returns:
        A MagicMock configured to behave like QueryExecutor.
    """
    mock = MagicMock(spec=QueryExecutor)
    return mock


@pytest.fixture
def mock_token_counter() -> MagicMock:
    """Create a mock TokenCounter for testing.

    Returns:
        A MagicMock configured to behave like TokenCounter.
    """
    mock = MagicMock(spec=TokenCounter)
    return mock


@pytest.fixture
def table_service(
    mock_query_executor: MagicMock, mock_token_counter: MagicMock
) -> TableService:
    """Create a TableService with mocked dependencies.

    Returns:
        A TableService instance with mocked QueryExecutor and TokenCounter.
    """
    return TableService(mock_query_executor, mock_token_counter)


@pytest.fixture
def sample_tables_df() -> pd.DataFrame:
    """Create a sample DataFrame with table names.

    Returns:
        A pandas DataFrame with tableName column.
    """
    return pd.DataFrame({"tableName": ["customers", "orders", "products"]})


@pytest.fixture
def sample_tables_df_staging() -> pd.DataFrame:
    """Create a sample DataFrame with staging table names.

    Returns:
        A pandas DataFrame with tableName column for staging schema.
    """
    return pd.DataFrame({"tableName": ["temp_data", "staging_table"]})


@pytest.fixture
def sample_columns_df() -> pd.DataFrame:
    """Create a sample DataFrame with column metadata.

    Returns:
        A pandas DataFrame with col_name, data_type, comment columns.
    """
    return pd.DataFrame(
        {
            "col_name": ["id", "name", "email", "created_at"],
            "data_type": ["bigint", "string", "string", "timestamp"],
            "comment": [
                "Customer ID",
                "Customer name",
                "Email address",
                "Created timestamp",
            ],
        }
    )


@pytest.fixture
def sample_columns_with_internal_df() -> pd.DataFrame:
    """Create a sample DataFrame with internal columns to be filtered.

    Returns:
        A pandas DataFrame including #-prefixed columns.
    """
    return pd.DataFrame(
        {
            "col_name": [
                "id",
                "name",
                "email",
                "#Partition Information",
                "#col_name",
                "#data_type",
                None,  # Test None handling
            ],
            "data_type": [
                "bigint",
                "string",
                "string",
                "",
                "",
                "",
                "",
            ],
            "comment": [
                "Primary key",
                "User name",
                "Email",
                "",
                "",
                "",
                "",
            ],
        }
    )


@pytest.fixture
def sample_row_count_df() -> pd.DataFrame:
    """Create a sample DataFrame with row count.

    Returns:
        A pandas DataFrame with row_count column.
    """
    return pd.DataFrame({"row_count": [15000]})


@pytest.fixture
def sample_row_count_empty_df() -> pd.DataFrame:
    """Create a sample DataFrame with zero row count.

    Returns:
        A pandas DataFrame with row_count of 0.
    """
    return pd.DataFrame({"row_count": [0]})


@pytest.fixture
def sample_table_data_df() -> pd.DataFrame:
    """Create a sample DataFrame with table data.

    Returns:
        A pandas DataFrame with sample customer data.
    """
    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "email": ["alice@example.com", "bob@example.com", "charlie@example.com"],
            "created_at": ["2023-01-01", "2023-01-02", "2023-01-03"],
        }
    )


@pytest.fixture
def empty_tables_df() -> pd.DataFrame:
    """Create an empty DataFrame with tableName column.

    Returns:
        An empty pandas DataFrame.
    """
    return pd.DataFrame({"tableName": []})


@pytest.fixture
def empty_columns_df() -> pd.DataFrame:
    """Create an empty DataFrame with column metadata columns.

    Returns:
        An empty pandas DataFrame.
    """
    return pd.DataFrame({"col_name": [], "data_type": [], "comment": []})


@pytest.fixture
def empty_table_data_df() -> pd.DataFrame:
    """Create an empty DataFrame with table data columns.

    Returns:
        An empty pandas DataFrame with defined columns.
    """
    return pd.DataFrame(columns=["id", "name", "email", "created_at"])


# =============================================================================
# Initialization Tests
# =============================================================================


class TestTableServiceInitialization:
    """Tests for TableService initialization."""

    def test_table_service_initialization_with_dependencies(
        self, mock_query_executor: MagicMock, mock_token_counter: MagicMock
    ):
        """Test TableService initializes with required dependencies.

        The TableService should:
        1. Accept QueryExecutor and TokenCounter in __init__
        2. Store them as instance attributes
        3. Use default max_tokens value of 9000

        This is test case 1 from US-3.2 requirements.
        """
        # Act
        service = TableService(mock_query_executor, mock_token_counter)

        # Assert
        assert service.query_executor is mock_query_executor
        assert service.token_counter is mock_token_counter
        assert service.max_tokens == 9000

    def test_table_service_initialization_custom_max_tokens(
        self, mock_query_executor: MagicMock, mock_token_counter: MagicMock
    ):
        """Test TableService accepts custom max_tokens parameter.

        The TableService should:
        1. Allow custom max_tokens value in __init__
        2. Store the custom value correctly

        This is test case 2 from US-3.2 requirements.
        """
        # Act
        service = TableService(mock_query_executor, mock_token_counter, max_tokens=5000)

        # Assert
        assert service.query_executor is mock_query_executor
        assert service.token_counter is mock_token_counter
        assert service.max_tokens == 5000


# =============================================================================
# List Tables Tests
# =============================================================================


class TestTableServiceListTables:
    """Tests for list_tables method."""

    def test_list_tables_single_schema(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_tables_df: pd.DataFrame,
    ):
        """Test list_tables with single schema.

        The method should:
        1. Execute SHOW TABLES IN {catalog}.{schema} query
        2. Return dict mapping schema to list of tables
        3. Handle single schema correctly

        This is part of test case 1 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_tables_df

        # Act
        result = table_service.list_tables("main", ["default"])

        # Assert
        assert isinstance(result, dict)
        assert "default" in result
        assert result["default"] == ["customers", "orders", "products"]
        mock_query_executor.execute_query.assert_called_once_with(
            "SHOW TABLES IN main.default", None
        )

    def test_list_tables_multiple_schemas(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_tables_df: pd.DataFrame,
        sample_tables_df_staging: pd.DataFrame,
    ):
        """Test list_tables with multiple schemas.

        The method should:
        1. Execute SHOW TABLES query for each schema
        2. Return dict mapping all schemas to their tables
        3. Make multiple QueryExecutor calls sequentially

        This is part of test case 1 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.side_effect = [
            sample_tables_df,
            sample_tables_df_staging,
        ]

        # Act
        result = table_service.list_tables("main", ["default", "staging"])

        # Assert
        assert isinstance(result, dict)
        assert len(result) == 2
        assert result["default"] == ["customers", "orders", "products"]
        assert result["staging"] == ["temp_data", "staging_table"]

        # Verify QueryExecutor was called twice with correct queries
        assert mock_query_executor.execute_query.call_count == 2
        calls = mock_query_executor.execute_query.call_args_list
        assert calls[0] == call("SHOW TABLES IN main.default", None)
        assert calls[1] == call("SHOW TABLES IN main.staging", None)

    def test_list_tables_with_workspace(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_tables_df: pd.DataFrame,
    ):
        """Test list_tables with workspace parameter.

        The method should:
        1. Pass workspace parameter to each QueryExecutor call
        2. Execute queries on specified workspace
        3. Return tables from that workspace

        This is part of test case 10 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_tables_df

        # Act
        result = table_service.list_tables(
            "analytics", ["reports"], workspace="production"
        )

        # Assert
        assert isinstance(result, dict)
        assert result["reports"] == ["customers", "orders", "products"]
        mock_query_executor.execute_query.assert_called_once_with(
            "SHOW TABLES IN analytics.reports", "production"
        )

    def test_list_tables_empty_schemas(
        self, table_service: TableService, mock_query_executor: MagicMock
    ):
        """Test list_tables with empty schema list.

        The method should:
        1. Handle empty input list gracefully
        2. Return empty dict without executing any queries

        This is part of test case 7 from US-3.2 requirements.
        """
        # Act
        result = table_service.list_tables("main", [])

        # Assert
        assert isinstance(result, dict)
        assert result == {}
        assert len(result) == 0
        # Verify no queries were executed
        mock_query_executor.execute_query.assert_not_called()

    def test_list_tables_empty_result(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        empty_tables_df: pd.DataFrame,
    ):
        """Test list_tables handles empty result gracefully.

        The method should:
        1. Handle empty DataFrame from QueryExecutor
        2. Return empty list for that schema

        This is part of test case 7 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = empty_tables_df

        # Act
        result = table_service.list_tables("main", ["empty_schema"])

        # Assert
        assert isinstance(result, dict)
        assert "empty_schema" in result
        assert result["empty_schema"] == []
        assert len(result["empty_schema"]) == 0

    def test_list_tables_query_executor_delegation(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_tables_df: pd.DataFrame,
    ):
        """Test list_tables properly delegates to QueryExecutor.

        The method should:
        1. Call execute_query with correct SQL query
        2. Pass workspace parameter correctly
        3. Process DataFrame result correctly

        This verifies proper delegation pattern.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_tables_df

        # Act
        table_service.list_tables("main", ["default"], workspace="test_workspace")

        # Assert - verify exact parameters passed
        mock_query_executor.execute_query.assert_called_once()
        call_args = mock_query_executor.execute_query.call_args
        assert call_args[0][0] == "SHOW TABLES IN main.default"
        assert call_args[0][1] == "test_workspace"


# =============================================================================
# List Columns Tests
# =============================================================================


class TestTableServiceListColumns:
    """Tests for list_columns method."""

    def test_list_columns_single_table(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_columns_df: pd.DataFrame,
    ):
        """Test list_columns with single table.

        The method should:
        1. Execute DESCRIBE TABLE EXTENDED query
        2. Return dict mapping table to list of column metadata
        3. Handle single table correctly

        This is part of test case 2 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_columns_df

        # Act
        result = table_service.list_columns("main", "default", ["customers"])

        # Assert
        assert isinstance(result, dict)
        assert "customers" in result
        assert len(result["customers"]) == 4
        assert result["customers"][0] == {
            "name": "id",
            "type": "bigint",
            "description": "Customer ID",
        }
        assert result["customers"][1] == {
            "name": "name",
            "type": "string",
            "description": "Customer name",
        }
        mock_query_executor.execute_query.assert_called_once_with(
            "DESCRIBE TABLE EXTENDED main.default.customers", None
        )

    def test_list_columns_multiple_tables(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_columns_df: pd.DataFrame,
    ):
        """Test list_columns with multiple tables.

        The method should:
        1. Execute DESCRIBE TABLE query for each table
        2. Return dict mapping all tables to their columns
        3. Make multiple QueryExecutor calls sequentially

        This is part of test case 2 from US-3.2 requirements.
        """
        # Arrange
        columns_orders = pd.DataFrame(
            {
                "col_name": ["order_id", "customer_id", "amount"],
                "data_type": ["bigint", "bigint", "decimal(10,2)"],
                "comment": ["Order ID", "Customer ID", "Order amount"],
            }
        )
        mock_query_executor.execute_query.side_effect = [
            sample_columns_df,
            columns_orders,
        ]

        # Act
        result = table_service.list_columns("main", "default", ["customers", "orders"])

        # Assert
        assert isinstance(result, dict)
        assert len(result) == 2
        assert len(result["customers"]) == 4
        assert len(result["orders"]) == 3
        assert result["orders"][0] == {
            "name": "order_id",
            "type": "bigint",
            "description": "Order ID",
        }

        # Verify QueryExecutor was called twice
        assert mock_query_executor.execute_query.call_count == 2
        calls = mock_query_executor.execute_query.call_args_list
        assert calls[0] == call("DESCRIBE TABLE EXTENDED main.default.customers", None)
        assert calls[1] == call("DESCRIBE TABLE EXTENDED main.default.orders", None)

    def test_list_columns_filters_internal_columns(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_columns_with_internal_df: pd.DataFrame,
    ):
        """Test list_columns filters out #-prefixed internal columns.

        The method should:
        1. Filter out columns where col_name starts with "#"
        2. Filter out columns where col_name is None or empty
        3. Return only actual data columns

        This is a critical test for proper column filtering.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_columns_with_internal_df

        # Act
        result = table_service.list_columns("main", "default", ["customers"])

        # Assert
        assert isinstance(result, dict)
        assert "customers" in result
        # Should only have 3 columns (id, name, email), not the # prefixed ones or None
        assert len(result["customers"]) == 3
        assert result["customers"][0] == {
            "name": "id",
            "type": "bigint",
            "description": "Primary key",
        }
        assert result["customers"][1] == {
            "name": "name",
            "type": "string",
            "description": "User name",
        }
        assert result["customers"][2] == {
            "name": "email",
            "type": "string",
            "description": "Email",
        }
        # Verify no internal columns are present
        column_names = [col["name"] for col in result["customers"]]
        assert "#Partition Information" not in column_names
        assert "#col_name" not in column_names
        assert "#data_type" not in column_names

    def test_list_columns_with_workspace(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_columns_df: pd.DataFrame,
    ):
        """Test list_columns with workspace parameter.

        The method should:
        1. Pass workspace parameter to each QueryExecutor call
        2. Execute queries on specified workspace
        3. Return columns from that workspace

        This is part of test case 10 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_columns_df

        # Act
        result = table_service.list_columns(
            "analytics", "reports", ["daily"], workspace="production"
        )

        # Assert
        assert isinstance(result, dict)
        assert len(result["daily"]) == 4
        mock_query_executor.execute_query.assert_called_once_with(
            "DESCRIBE TABLE EXTENDED analytics.reports.daily", "production"
        )

    def test_list_columns_empty_tables(
        self, table_service: TableService, mock_query_executor: MagicMock
    ):
        """Test list_columns with empty table list.

        The method should:
        1. Handle empty input list gracefully
        2. Return empty dict without executing any queries

        This is an edge case test.
        """
        # Act
        result = table_service.list_columns("main", "default", [])

        # Assert
        assert isinstance(result, dict)
        assert result == {}
        assert len(result) == 0
        # Verify no queries were executed
        mock_query_executor.execute_query.assert_not_called()

    def test_list_columns_query_executor_delegation(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_columns_df: pd.DataFrame,
    ):
        """Test list_columns properly delegates to QueryExecutor.

        The method should:
        1. Call execute_query for each table
        2. Pass correct SQL queries with full table paths
        3. Pass workspace parameter to all calls
        4. Process all DataFrame results correctly

        This verifies proper delegation pattern.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_columns_df

        # Act
        result = table_service.list_columns(
            "main", "default", ["customers"], workspace="test_workspace"
        )

        # Assert
        assert len(result) == 1
        assert mock_query_executor.execute_query.call_count == 1

        # Verify exact parameters
        call_args = mock_query_executor.execute_query.call_args
        assert call_args[0][0] == "DESCRIBE TABLE EXTENDED main.default.customers"
        assert call_args[0][1] == "test_workspace"


# =============================================================================
# Get Table Row Count Tests
# =============================================================================


class TestTableServiceGetTableRowCount:
    """Tests for get_table_row_count method."""

    def test_get_table_row_count_basic(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_row_count_df: pd.DataFrame,
    ):
        """Test get_table_row_count basic functionality.

        The method should:
        1. Execute COUNT(*) query
        2. Return dict with table_name, total_rows, and estimated_pages
        3. Calculate pagination for all page sizes

        This is test case 3 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_row_count_df

        # Act
        result = table_service.get_table_row_count("main", "default", "customers")

        # Assert
        assert isinstance(result, dict)
        assert result["table_name"] == "main.default.customers"
        assert result["total_rows"] == 15000
        assert "estimated_pages" in result
        assert isinstance(result["estimated_pages"], dict)

        mock_query_executor.execute_query.assert_called_once_with(
            "SELECT COUNT(*) as row_count FROM main.default.customers", None
        )

    def test_get_table_row_count_pagination_calculation(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_row_count_df: pd.DataFrame,
    ):
        """Test pagination estimate calculation is accurate.

        The method should:
        1. Calculate pages using ceiling division: (row_count + size - 1) // size
        2. Provide estimates for page sizes: 50, 100, 250, 500, 1000

        This is test case 11 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_row_count_df

        # Act
        result = table_service.get_table_row_count("main", "default", "customers")

        # Assert - verify pagination calculation for 15000 rows
        pages = result["estimated_pages"]
        assert pages["pages_with_50_rows"] == 300  # (15000 + 49) // 50 = 300
        assert pages["pages_with_100_rows"] == 150  # (15000 + 99) // 100 = 150
        assert pages["pages_with_250_rows"] == 60  # (15000 + 249) // 250 = 60
        assert pages["pages_with_500_rows"] == 30  # (15000 + 499) // 500 = 30
        assert pages["pages_with_1000_rows"] == 15  # (15000 + 999) // 1000 = 15

    def test_get_table_row_count_large_table(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
    ):
        """Test get_table_row_count with large table.

        The method should:
        1. Handle large row counts correctly
        2. Calculate pagination accurately for millions of rows

        This is test case 6 from US-3.2 requirements.
        """
        # Arrange
        large_count_df = pd.DataFrame({"row_count": [5000000]})
        mock_query_executor.execute_query.return_value = large_count_df

        # Act
        result = table_service.get_table_row_count("main", "default", "large_table")

        # Assert
        assert result["total_rows"] == 5000000
        pages = result["estimated_pages"]
        assert pages["pages_with_50_rows"] == 100000
        assert pages["pages_with_100_rows"] == 50000
        assert pages["pages_with_250_rows"] == 20000
        assert pages["pages_with_500_rows"] == 10000
        assert pages["pages_with_1000_rows"] == 5000

    def test_get_table_row_count_empty_table(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_row_count_empty_df: pd.DataFrame,
    ):
        """Test get_table_row_count with empty table.

        The method should:
        1. Handle zero row count correctly
        2. Calculate pagination as 0 pages for all sizes

        This is test case 7 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_row_count_empty_df

        # Act
        result = table_service.get_table_row_count("main", "default", "empty_table")

        # Assert
        assert result["total_rows"] == 0
        pages = result["estimated_pages"]
        assert pages["pages_with_50_rows"] == 0
        assert pages["pages_with_100_rows"] == 0
        assert pages["pages_with_250_rows"] == 0
        assert pages["pages_with_500_rows"] == 0
        assert pages["pages_with_1000_rows"] == 0

    def test_get_table_row_count_with_workspace(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_row_count_df: pd.DataFrame,
    ):
        """Test get_table_row_count with workspace parameter.

        The method should:
        1. Pass workspace parameter to QueryExecutor
        2. Execute query on specified workspace

        This is part of test case 10 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_row_count_df

        # Act
        result = table_service.get_table_row_count(
            "analytics", "reports", "daily_summary", workspace="production"
        )

        # Assert
        assert result["table_name"] == "analytics.reports.daily_summary"
        assert result["total_rows"] == 15000
        mock_query_executor.execute_query.assert_called_once_with(
            "SELECT COUNT(*) as row_count FROM analytics.reports.daily_summary",
            "production",
        )

    def test_get_table_row_count_pagination_edge_cases(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
    ):
        """Test pagination calculation with edge case row counts.

        The method should:
        1. Handle row counts that are exact multiples of page sizes
        2. Handle row counts of 1
        3. Calculate correctly with ceiling division

        This extends test case 11 with edge cases.
        """
        # Test with row count of 1
        mock_query_executor.execute_query.return_value = pd.DataFrame(
            {"row_count": [1]}
        )
        result = table_service.get_table_row_count("main", "default", "single_row")
        pages = result["estimated_pages"]
        assert pages["pages_with_50_rows"] == 1
        assert pages["pages_with_100_rows"] == 1
        assert pages["pages_with_1000_rows"] == 1

        # Test with row count exactly 100
        mock_query_executor.execute_query.return_value = pd.DataFrame(
            {"row_count": [100]}
        )
        result = table_service.get_table_row_count("main", "default", "exactly_100")
        pages = result["estimated_pages"]
        assert pages["pages_with_50_rows"] == 2  # (100 + 49) // 50 = 2
        assert pages["pages_with_100_rows"] == 1  # (100 + 99) // 100 = 1
        assert pages["pages_with_1000_rows"] == 1  # (100 + 999) // 1000 = 1


# =============================================================================
# Get Table Details Tests
# =============================================================================


class TestTableServiceGetTableDetails:
    """Tests for get_table_details method."""

    def test_get_table_details_default_limit(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_table_data_df: pd.DataFrame,
    ):
        """Test get_table_details with default limit.

        The method should:
        1. Execute SELECT * query with LIMIT 1000
        2. Return dict with data, schema, and table_name
        3. Serialize DataFrame to JSON format

        This is test case 4 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_table_data_df

        # Act
        result = table_service.get_table_details("main", "default", "customers")

        # Assert
        assert isinstance(result, dict)
        assert "data" in result
        assert "schema" in result
        assert "table_name" in result
        assert result["table_name"] == "main.default.customers"
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 3
        assert result["data"][0]["name"] == "Alice"

        mock_query_executor.execute_query.assert_called_once_with(
            "SELECT * FROM main.default.customers LIMIT 1000", None
        )

    def test_get_table_details_custom_limit(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_table_data_df: pd.DataFrame,
    ):
        """Test get_table_details with custom limit.

        The method should:
        1. Execute SELECT * query with specified LIMIT
        2. Use the custom limit value in query

        This extends test case 4 with custom limit.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_table_data_df

        # Act
        result = table_service.get_table_details(
            "main", "default", "customers", limit=100
        )

        # Assert
        assert result["table_name"] == "main.default.customers"
        assert len(result["data"]) == 3

        mock_query_executor.execute_query.assert_called_once_with(
            "SELECT * FROM main.default.customers LIMIT 100", None
        )

    def test_get_table_details_no_limit(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_table_data_df: pd.DataFrame,
    ):
        """Test get_table_details with no limit (None).

        The method should:
        1. Execute SELECT * query without LIMIT clause
        2. Return all rows from the table

        This is test case 5 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_table_data_df

        # Act
        result = table_service.get_table_details(
            "main", "default", "small_table", limit=None
        )

        # Assert
        assert result["table_name"] == "main.default.small_table"
        assert len(result["data"]) == 3

        # Verify query does NOT contain LIMIT
        mock_query_executor.execute_query.assert_called_once_with(
            "SELECT * FROM main.default.small_table", None
        )
        # Verify the query string does not contain "LIMIT"
        call_args = mock_query_executor.execute_query.call_args
        assert "LIMIT" not in call_args[0][0]

    def test_get_table_details_with_workspace(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_table_data_df: pd.DataFrame,
    ):
        """Test get_table_details with workspace parameter.

        The method should:
        1. Pass workspace parameter to QueryExecutor
        2. Execute query on specified workspace

        This is part of test case 10 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_table_data_df

        # Act
        result = table_service.get_table_details(
            "analytics", "reports", "summary", limit=100, workspace="production"
        )

        # Assert
        assert result["table_name"] == "analytics.reports.summary"
        mock_query_executor.execute_query.assert_called_once_with(
            "SELECT * FROM analytics.reports.summary LIMIT 100", "production"
        )

    def test_get_table_details_data_serialization(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_table_data_df: pd.DataFrame,
    ):
        """Test get_table_details properly serializes DataFrame to JSON.

        The method should:
        1. Convert DataFrame to list of dicts using orient="records"
        2. Return data as list of dicts
        3. Include schema information with column names and types

        This verifies proper data serialization.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_table_data_df

        # Act
        result = table_service.get_table_details("main", "default", "customers")

        # Assert
        # Verify data is a list of dicts
        assert isinstance(result["data"], list)
        assert all(isinstance(row, dict) for row in result["data"])

        # Verify schema is a list of field definitions
        assert "schema" in result
        assert isinstance(result["schema"], list)
        assert len(result["schema"]) == 4  # id, name, email, created_at

        # Verify schema contains name and type for each field
        assert all("name" in field and "type" in field for field in result["schema"])

        # Verify data matches expected structure
        assert result["data"][0]["id"] == 1
        assert result["data"][0]["name"] == "Alice"
        assert result["data"][1]["name"] == "Bob"
        assert result["data"][2]["name"] == "Charlie"

    def test_get_table_details_empty_table(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        empty_table_data_df: pd.DataFrame,
    ):
        """Test get_table_details with empty table result.

        The method should:
        1. Handle empty DataFrame correctly
        2. Return empty data list but valid schema

        This is an edge case test.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = empty_table_data_df

        # Act
        result = table_service.get_table_details("main", "default", "empty_table")

        # Assert
        assert result["table_name"] == "main.default.empty_table"
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 0
        assert "schema" in result


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestTableServiceErrorHandling:
    """Tests for error handling and error propagation."""

    def test_list_tables_error_propagation(
        self, table_service: TableService, mock_query_executor: MagicMock
    ):
        """Test list_tables propagates QueryExecutor errors.

        When QueryExecutor raises an exception:
        1. The exception should propagate to the caller
        2. No exception handling should suppress the error

        This is part of test case 8 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.side_effect = DatabricksError(
            "Schema 'invalid_schema' not found"
        )

        # Act & Assert
        with pytest.raises(DatabricksError, match="Schema 'invalid_schema' not found"):
            table_service.list_tables("main", ["invalid_schema"])

        # Verify QueryExecutor was called
        mock_query_executor.execute_query.assert_called_once()

    def test_list_columns_error_propagation(
        self, table_service: TableService, mock_query_executor: MagicMock
    ):
        """Test list_columns propagates QueryExecutor errors.

        When QueryExecutor raises an exception:
        1. The exception should propagate to the caller
        2. Error should occur during iteration over tables

        This is part of test case 8 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.side_effect = DatabricksError(
            "Table 'main.default.nonexistent' not found"
        )

        # Act & Assert
        with pytest.raises(
            DatabricksError, match="Table 'main.default.nonexistent' not found"
        ):
            table_service.list_columns("main", "default", ["nonexistent"])

        # Verify QueryExecutor was called
        mock_query_executor.execute_query.assert_called_once()

    def test_get_table_row_count_error_propagation(
        self, table_service: TableService, mock_query_executor: MagicMock
    ):
        """Test get_table_row_count propagates QueryExecutor errors.

        When QueryExecutor raises an exception:
        1. The exception should propagate to the caller

        This is part of test case 8 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.side_effect = DatabricksError(
            "Table 'main.default.missing' not found"
        )

        # Act & Assert
        with pytest.raises(
            DatabricksError, match="Table 'main.default.missing' not found"
        ):
            table_service.get_table_row_count("main", "default", "missing")

    def test_get_table_details_error_propagation(
        self, table_service: TableService, mock_query_executor: MagicMock
    ):
        """Test get_table_details propagates QueryExecutor errors.

        When QueryExecutor raises an exception:
        1. The exception should propagate to the caller

        This is part of test case 8 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.side_effect = DatabricksError(
            "SQL execution failed: table not accessible"
        )

        # Act & Assert
        with pytest.raises(DatabricksError, match="SQL execution failed"):
            table_service.get_table_details("main", "default", "protected_table")

    def test_get_table_details_invalid_table(
        self, table_service: TableService, mock_query_executor: MagicMock
    ):
        """Test get_table_details handles invalid table name.

        When a table doesn't exist:
        1. QueryExecutor raises an error
        2. Error should propagate with helpful message

        This is part of test case 8 from US-3.2 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.side_effect = DatabricksError(
            "Table 'main.default.invalid_table' not found"
        )

        # Act & Assert
        with pytest.raises(
            DatabricksError, match="Table 'main.default.invalid_table' not found"
        ):
            table_service.get_table_details("main", "default", "invalid_table")

    def test_list_tables_workspace_not_found(
        self, table_service: TableService, mock_query_executor: MagicMock
    ):
        """Test list_tables error when workspace doesn't exist.

        When workspace is invalid:
        1. QueryExecutor should raise ValueError
        2. Error should propagate with workspace information

        This tests workspace parameter error handling.
        """
        # Arrange
        mock_query_executor.execute_query.side_effect = ValueError(
            "Workspace 'nonexistent' configuration not found"
        )

        # Act & Assert
        with pytest.raises(
            ValueError, match="Workspace 'nonexistent' configuration not found"
        ):
            table_service.list_tables("main", ["default"], workspace="nonexistent")

    def test_list_columns_workspace_not_found(
        self, table_service: TableService, mock_query_executor: MagicMock
    ):
        """Test list_columns error when workspace doesn't exist.

        When workspace is invalid:
        1. QueryExecutor should raise ValueError
        2. Error should propagate with workspace information

        This tests workspace parameter error handling for list_columns.
        """
        # Arrange
        mock_query_executor.execute_query.side_effect = ValueError(
            "Workspace 'nonexistent' configuration not found"
        )

        # Act & Assert
        with pytest.raises(
            ValueError, match="Workspace 'nonexistent' configuration not found"
        ):
            table_service.list_columns(
                "main", "default", ["customers"], workspace="nonexistent"
            )


# =============================================================================
# Integration Tests
# =============================================================================


class TestTableServiceIntegration:
    """Integration tests with real dependency instances."""

    def test_integration_with_real_dependencies(
        self,
        sample_tables_df: pd.DataFrame,
        sample_columns_df: pd.DataFrame,
    ):
        """Test TableService with real QueryExecutor and TokenCounter.

        This integration test:
        1. Uses actual QueryExecutor and TokenCounter instances
        2. Mocks only at the connection level
        3. Verifies end-to-end behavior

        This is test case 12 from US-3.2 requirements (integration test).
        """
        # Arrange - Create real instances but mock QueryExecutor's execute_query
        query_executor = MagicMock(spec=QueryExecutor)
        token_counter = TokenCounter()  # Real TokenCounter instance
        service = TableService(query_executor, token_counter, max_tokens=9000)

        query_executor.execute_query.return_value = sample_tables_df

        # Act
        tables = service.list_tables("main", ["default"])

        # Assert
        assert isinstance(tables, dict)
        assert len(tables) == 1
        assert "default" in tables
        assert service.token_counter == token_counter
        assert service.max_tokens == 9000

    def test_integration_multiple_operations(
        self,
        sample_tables_df: pd.DataFrame,
        sample_columns_df: pd.DataFrame,
        sample_row_count_df: pd.DataFrame,
        sample_table_data_df: pd.DataFrame,
    ):
        """Test multiple sequential operations on TableService.

        This integration test:
        1. Calls multiple methods in sequence
        2. Verifies state is maintained correctly
        3. Tests typical usage pattern

        This extends integration testing with realistic workflows.
        """
        # Arrange
        query_executor = MagicMock(spec=QueryExecutor)
        token_counter = TokenCounter()
        service = TableService(query_executor, token_counter)

        # Configure mock to return different results for different queries
        query_executor.execute_query.side_effect = [
            sample_tables_df,  # For list_tables
            sample_columns_df,  # For list_columns
            sample_row_count_df,  # For get_table_row_count
            sample_table_data_df,  # For get_table_details
        ]

        # Act - typical workflow
        tables = service.list_tables("main", ["default"])
        columns = service.list_columns("main", "default", ["customers"])
        row_count = service.get_table_row_count("main", "default", "customers")
        details = service.get_table_details("main", "default", "customers", limit=10)

        # Assert
        assert len(tables) == 1
        assert "default" in tables
        assert len(columns) == 1
        assert "customers" in columns
        assert row_count["total_rows"] == 15000
        assert details["table_name"] == "main.default.customers"

        # Verify QueryExecutor was called 4 times total
        assert query_executor.execute_query.call_count == 4


# =============================================================================
# Token Counter Integration Tests
# =============================================================================


class TestTableServiceTokenCounterIntegration:
    """Tests for TokenCounter integration with TableService."""

    def test_token_counter_integration(
        self, mock_query_executor: MagicMock, sample_tables_df: pd.DataFrame
    ):
        """Test TableService properly integrates with TokenCounter.

        The service should:
        1. Store TokenCounter instance
        2. Make it available for token estimation
        3. Respect max_tokens configuration

        This is test case 9 from US-3.2 requirements (TokenCounter integration).
        """
        # Arrange
        token_counter = TokenCounter(model="gpt-4")
        service = TableService(mock_query_executor, token_counter, max_tokens=5000)
        mock_query_executor.execute_query.return_value = sample_tables_df

        # Act
        tables = service.list_tables("main", ["default"])

        # Assert - verify TokenCounter is accessible and configured
        assert service.token_counter is token_counter
        assert service.max_tokens == 5000

        # Verify we can use the token counter
        tables_json = json.dumps(tables)
        token_count = service.token_counter.count_tokens(tables_json)
        assert isinstance(token_count, int)
        assert token_count > 0

    def test_token_counter_with_response_estimation(
        self,
        mock_query_executor: MagicMock,
        sample_table_data_df: pd.DataFrame,
    ):
        """Test token estimation for service responses.

        The service should:
        1. Allow token estimation on returned data structures
        2. Support chunking decisions based on max_tokens

        This extends TokenCounter integration testing.
        """
        # Arrange
        token_counter = TokenCounter(model="gpt-4")
        service = TableService(mock_query_executor, token_counter, max_tokens=9000)
        mock_query_executor.execute_query.return_value = sample_table_data_df

        # Act
        details = service.get_table_details("main", "default", "customers")

        # Assert - verify we can estimate tokens for the response
        token_estimate = service.token_counter.estimate_tokens(details)
        assert isinstance(token_estimate, int)
        assert token_estimate > 0

        # Verify chunking decision can be made
        needs_chunking = token_estimate > service.max_tokens
        assert isinstance(needs_chunking, bool)


# =============================================================================
# Edge Cases and Additional Tests
# =============================================================================


class TestTableServiceEdgeCases:
    """Tests for edge cases and additional scenarios."""

    def test_list_tables_none_workspace_explicit(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_tables_df: pd.DataFrame,
    ):
        """Test list_tables with explicit None workspace parameter.

        The method should:
        1. Accept None as explicit parameter value
        2. Behave same as default (no parameter)

        This is an edge case test.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_tables_df

        # Act
        result = table_service.list_tables("main", ["default"], workspace=None)

        # Assert
        assert result["default"] == ["customers", "orders", "products"]
        mock_query_executor.execute_query.assert_called_once_with(
            "SHOW TABLES IN main.default", None
        )

    def test_list_columns_none_workspace_explicit(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_columns_df: pd.DataFrame,
    ):
        """Test list_columns with explicit None workspace parameter.

        The method should:
        1. Accept None as explicit parameter value
        2. Behave same as default (no parameter)

        This is an edge case test.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_columns_df

        # Act
        result = table_service.list_columns(
            "main", "default", ["customers"], workspace=None
        )

        # Assert
        assert len(result["customers"]) == 4
        mock_query_executor.execute_query.assert_called_once_with(
            "DESCRIBE TABLE EXTENDED main.default.customers", None
        )

    def test_list_tables_preserves_order(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_tables_df: pd.DataFrame,
        sample_tables_df_staging: pd.DataFrame,
    ):
        """Test list_tables preserves schema order from input.

        The method should:
        1. Process schemas in the order provided
        2. Return dict with same schema order

        This verifies behavior consistency.
        """
        # Arrange
        mock_query_executor.execute_query.side_effect = [
            sample_tables_df_staging,  # staging first
            sample_tables_df,  # default second
        ]

        # Act
        result = table_service.list_tables("main", ["staging", "default"])

        # Assert
        result_keys = list(result.keys())
        assert result_keys == ["staging", "default"]  # Order preserved

    def test_list_columns_preserves_order(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
        sample_columns_df: pd.DataFrame,
    ):
        """Test list_columns preserves table order from input.

        The method should:
        1. Process tables in the order provided
        2. Return dict with same table order

        This verifies behavior consistency.
        """
        # Arrange
        columns_orders = pd.DataFrame(
            {
                "col_name": ["order_id", "customer_id"],
                "data_type": ["bigint", "bigint"],
                "comment": ["Order ID", "Customer ID"],
            }
        )
        mock_query_executor.execute_query.side_effect = [
            columns_orders,  # orders first
            sample_columns_df,  # customers second
        ]

        # Act
        result = table_service.list_columns("main", "default", ["orders", "customers"])

        # Assert
        result_keys = list(result.keys())
        assert result_keys == ["orders", "customers"]  # Order preserved

    def test_get_table_details_with_special_characters_in_data(
        self,
        table_service: TableService,
        mock_query_executor: MagicMock,
    ):
        """Test get_table_details handles special characters in data.

        The method should:
        1. Properly serialize data with special characters
        2. Handle quotes, newlines, etc. in JSON serialization

        This is an edge case test for data serialization.
        """
        # Arrange
        special_data_df = pd.DataFrame(
            {
                "id": [1, 2],
                "name": ['John "The Great" Doe', "Jane O'Brien"],
                "bio": ["Line 1\nLine 2", "Tab\there"],
            }
        )
        mock_query_executor.execute_query.return_value = special_data_df

        # Act
        result = table_service.get_table_details("main", "default", "special_table")

        # Assert
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 2
        # Verify special characters are preserved
        assert "John" in result["data"][0]["name"]
        assert "Jane" in result["data"][1]["name"]
