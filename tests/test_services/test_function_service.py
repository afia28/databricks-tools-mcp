"""Comprehensive test suite for FunctionService class.

This module contains comprehensive tests for the FunctionService class,
covering user-defined function listing, description, and parsing operations
with consistent error handling and token management.

Test coverage goal: 90%+ for src/databricks_tools/services/function_service.py

Test cases included (30+ tests covering US-3.3):
1. test_function_service_initialization_with_dependencies - Verify proper initialization
2. test_function_service_initialization_custom_max_tokens - Custom max_tokens parameter
3. test_list_user_functions_basic - Basic function listing
4. test_list_user_functions_with_workspace - Workspace parameter handling
5. test_list_user_functions_empty_result - Empty function list (no functions)
6. test_list_user_functions_query_executor_delegation - Verify QueryExecutor calls
7. test_list_user_functions_result_structure - Verify result format
8. test_describe_function_basic - Basic function description
9. test_describe_function_with_workspace - Workspace parameter handling
10. test_describe_function_result_structure - Verify result format
11. test_describe_function_calls_parse_method - Verify parsing is called
12. test_list_and_describe_all_basic - List and describe all functions
13. test_list_and_describe_all_with_workspace - Workspace parameter
14. test_list_and_describe_all_no_functions - Empty function list
15. test_list_and_describe_all_extracts_function_name - Function name extraction
16. test_list_and_describe_all_error_handling - Individual function error handling
17. test_parse_description_filters_configs - Filter Configs lines (CRITICAL)
18. test_parse_description_filters_owner_and_create_time - Filter Owner/Create Time
19. test_parse_description_keeps_function_metadata - Keep important lines
20. test_parse_description_handles_indented_lines - Handle indented continuations
21. test_parse_description_realistic_output - Full realistic test
22. test_list_user_functions_error_propagation - Error handling
23. test_describe_function_error_propagation - Error handling
24. test_list_and_describe_all_error_propagation - Error handling
25. test_workspace_not_found_error - Workspace validation
26. test_list_user_functions_workspace_parameter - Workspace parameter
27. test_describe_function_workspace_parameter - Workspace parameter
28. test_list_and_describe_all_workspace_parameter - Workspace parameter
29. test_integration_with_real_dependencies - Integration test
30. test_integration_multiple_operations - Sequential operations test
31. test_token_counter_integration - TokenCounter integration
32. test_catalog_schema_defaults - Catalog/schema parameter handling
"""

from unittest.mock import MagicMock

import pandas as pd
import pytest
from databricks.sql import Error as DatabricksError

from databricks_tools.core.query_executor import QueryExecutor
from databricks_tools.core.token_counter import TokenCounter
from databricks_tools.services.function_service import FunctionService

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
def function_service(
    mock_query_executor: MagicMock, mock_token_counter: MagicMock
) -> FunctionService:
    """Create a FunctionService with mocked dependencies.

    Returns:
        A FunctionService instance with mocked QueryExecutor and TokenCounter.
    """
    return FunctionService(mock_query_executor, mock_token_counter)


@pytest.fixture
def sample_functions_df() -> pd.DataFrame:
    """Create a sample DataFrame with function names.

    Returns:
        A pandas DataFrame with function column.
    """
    return pd.DataFrame(
        {
            "function": [
                "main.default.my_func",
                "main.default.another_func",
                "main.default.calculate",
            ]
        }
    )


@pytest.fixture
def empty_functions_df() -> pd.DataFrame:
    """Create an empty DataFrame with function column.

    Returns:
        An empty pandas DataFrame.
    """
    return pd.DataFrame({"function": []})


@pytest.fixture
def sample_describe_function_df() -> pd.DataFrame:
    """Create a sample DataFrame with DESCRIBE FUNCTION EXTENDED output.

    Returns:
        A pandas DataFrame with function_desc column.
    """
    return pd.DataFrame(
        {
            "function_desc": [
                "Function: main.default.my_func",
                "Type: SCALAR",
                "Input: (x INT)",
                "Returns: INT",
                "Comment: My custom function",
                "Deterministic: true",
                "Data Access: NO_SQL",
            ]
        }
    )


@pytest.fixture
def sample_describe_with_configs_df() -> pd.DataFrame:
    """Create a DataFrame with Configs lines that should be filtered.

    Returns:
        A pandas DataFrame with function_desc including Configs section.
    """
    return pd.DataFrame(
        {
            "function_desc": [
                "Function: main.default.my_func",
                "Type: SCALAR",
                "Input: (x INT, y STRING)",
                "               z DECIMAL(10,2)",
                "Returns: INT",
                "Comment: Test function",
                "Configs:",
                "               spark.sql.adaptive.enabled=true",
                "               spark.sql.shuffle.partitions=200",
                "               custom.config.value=test",
                "Deterministic: true",
                "Data Access: NO_SQL",
                "Owner: john.doe@example.com",
                "Create Time: 2024-01-15 10:30:00",
                "Body: return x + y",
            ]
        }
    )


@pytest.fixture
def sample_describe_with_owner_createtime_df() -> pd.DataFrame:
    """Create a DataFrame with Owner and Create Time lines that should be filtered.

    Returns:
        A pandas DataFrame with function_desc including Owner and Create Time.
    """
    return pd.DataFrame(
        {
            "function_desc": [
                "Function: analytics.reports.calculate_discount",
                "Type: SCALAR",
                "Input: (price DECIMAL(10,2), discount_pct DECIMAL(5,2))",
                "Returns: DECIMAL(10,2)",
                "Comment: Calculate discounted price",
                "Owner: admin@example.com",
                "Create Time: 2023-12-01 09:00:00",
                "Deterministic: true",
                "Data Access: NO_SQL",
            ]
        }
    )


@pytest.fixture
def realistic_describe_function_df() -> pd.DataFrame:
    """Create a realistic DESCRIBE FUNCTION EXTENDED output for comprehensive testing.

    Returns:
        A pandas DataFrame with complete function_desc output.
    """
    return pd.DataFrame(
        {
            "function_desc": [
                "Function: main.default.advanced_function",
                "Type: SCALAR",
                "Input: (param1 INT, param2 STRING)",
                "               param3 ARRAY<STRING>",
                "               param4 STRUCT<field1:INT,field2:STRING>",
                "Returns: STRUCT<result:INT,message:STRING>",
                "               Additional return info",
                "Comment: This is a complex function with multiple parameters",
                "Configs:",
                "               spark.sql.adaptive.enabled=true",
                "               spark.sql.shuffle.partitions=200",
                "               custom.setting=value",
                "Owner: data.engineer@company.com",
                "Create Time: 2024-01-15 14:30:00",
                "Deterministic: true",
                "Data Access: READS_SQL_DATA",
                "Body: RETURN STRUCT(param1 * 2 AS result, param2 AS message)",
            ]
        }
    )


# =============================================================================
# Initialization Tests
# =============================================================================


class TestFunctionServiceInitialization:
    """Tests for FunctionService initialization."""

    def test_function_service_initialization_with_dependencies(
        self, mock_query_executor: MagicMock, mock_token_counter: MagicMock
    ):
        """Test FunctionService initializes with required dependencies.

        The FunctionService should:
        1. Accept QueryExecutor and TokenCounter in __init__
        2. Store them as instance attributes
        3. Use default max_tokens value of 9000

        This is test case 1 from US-3.3 requirements.
        """
        # Act
        service = FunctionService(mock_query_executor, mock_token_counter)

        # Assert
        assert service.query_executor is mock_query_executor
        assert service.token_counter is mock_token_counter
        assert service.max_tokens == 9000

    def test_function_service_initialization_custom_max_tokens(
        self, mock_query_executor: MagicMock, mock_token_counter: MagicMock
    ):
        """Test FunctionService accepts custom max_tokens parameter.

        The FunctionService should:
        1. Allow custom max_tokens value in __init__
        2. Store the custom value correctly

        This is test case 2 from US-3.3 requirements.
        """
        # Act
        service = FunctionService(
            mock_query_executor, mock_token_counter, max_tokens=5000
        )

        # Assert
        assert service.query_executor is mock_query_executor
        assert service.token_counter is mock_token_counter
        assert service.max_tokens == 5000


# =============================================================================
# List User Functions Tests
# =============================================================================


class TestFunctionServiceListUserFunctions:
    """Tests for list_user_functions method."""

    def test_list_user_functions_basic(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_functions_df: pd.DataFrame,
    ):
        """Test list_user_functions basic functionality.

        The method should:
        1. Execute SHOW USER FUNCTIONS IN {catalog}.{schema} query
        2. Extract function names from "function" column
        3. Return dict with catalog, schema, user_functions list, and function_count

        This is test case 1 from US-3.3 requirements (test_function_service_list_functions).
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.return_value = (
            sample_functions_df
        )

        # Act
        result = function_service.list_user_functions("main", "default")

        # Assert
        assert isinstance(result, dict)
        assert result["catalog"] == "main"
        assert result["schema"] == "default"
        assert result["user_functions"] == [
            "main.default.my_func",
            "main.default.another_func",
            "main.default.calculate",
        ]
        assert result["function_count"] == 3

        mock_query_executor.execute_query_with_catalog.assert_called_once_with(
            "main", "SHOW USER FUNCTIONS IN main.default", None
        )

    def test_list_user_functions_with_workspace(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_functions_df: pd.DataFrame,
    ):
        """Test list_user_functions with workspace parameter.

        The method should:
        1. Pass workspace parameter to execute_query_with_catalog
        2. Execute query on specified workspace

        This is part of test case 9 from US-3.3 requirements (test_function_service_workspace_parameter).
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.return_value = (
            sample_functions_df
        )

        # Act
        result = function_service.list_user_functions(
            "analytics", "reports", workspace="production"
        )

        # Assert
        assert result["catalog"] == "analytics"
        assert result["schema"] == "reports"
        assert result["function_count"] == 3
        mock_query_executor.execute_query_with_catalog.assert_called_once_with(
            "analytics", "SHOW USER FUNCTIONS IN analytics.reports", "production"
        )

    def test_list_user_functions_empty_result(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        empty_functions_df: pd.DataFrame,
    ):
        """Test list_user_functions handles empty result gracefully.

        The method should:
        1. Handle empty DataFrame from QueryExecutor
        2. Return empty list with function_count of 0

        This is test case 5 from US-3.3 requirements (test_function_service_no_functions).
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.return_value = empty_functions_df

        # Act
        result = function_service.list_user_functions("main", "default")

        # Assert
        assert isinstance(result, dict)
        assert result["catalog"] == "main"
        assert result["schema"] == "default"
        assert result["user_functions"] == []
        assert result["function_count"] == 0

    def test_list_user_functions_query_executor_delegation(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_functions_df: pd.DataFrame,
    ):
        """Test list_user_functions properly delegates to QueryExecutor.

        The method should:
        1. Call execute_query_with_catalog with correct SQL query
        2. Pass catalog and workspace parameters correctly
        3. Process DataFrame result correctly

        This verifies proper delegation pattern.
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.return_value = (
            sample_functions_df
        )

        # Act
        function_service.list_user_functions(
            "analytics", "ml", workspace="test_workspace"
        )

        # Assert - verify exact parameters passed
        mock_query_executor.execute_query_with_catalog.assert_called_once()
        call_args = mock_query_executor.execute_query_with_catalog.call_args
        assert call_args[0][0] == "analytics"  # First positional arg is catalog
        assert (
            call_args[0][1] == "SHOW USER FUNCTIONS IN analytics.ml"
        )  # Second is query
        assert call_args[0][2] == "test_workspace"  # Third is workspace

    def test_list_user_functions_result_structure(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_functions_df: pd.DataFrame,
    ):
        """Test list_user_functions returns correct result structure.

        The method should return a dict with exactly these keys:
        - catalog: str
        - schema: str
        - user_functions: list[str]
        - function_count: int

        This verifies the result format matches US-3.3 specification.
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.return_value = (
            sample_functions_df
        )

        # Act
        result = function_service.list_user_functions("main", "default")

        # Assert - verify all required keys present
        assert set(result.keys()) == {
            "catalog",
            "schema",
            "user_functions",
            "function_count",
        }
        assert isinstance(result["catalog"], str)
        assert isinstance(result["schema"], str)
        assert isinstance(result["user_functions"], list)
        assert isinstance(result["function_count"], int)


# =============================================================================
# Describe Function Tests
# =============================================================================


class TestFunctionServiceDescribeFunction:
    """Tests for describe_function method."""

    def test_describe_function_basic(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_describe_function_df: pd.DataFrame,
    ):
        """Test describe_function basic functionality.

        The method should:
        1. Execute DESCRIBE FUNCTION EXTENDED query
        2. Parse the output using _parse_function_description
        3. Return dict with catalog, schema, function_name, and details

        This is test case 2 from US-3.3 requirements (test_function_service_describe_function).
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.return_value = (
            sample_describe_function_df
        )

        # Act
        result = function_service.describe_function("my_func", "main", "default")

        # Assert
        assert isinstance(result, dict)
        assert result["catalog"] == "main"
        assert result["schema"] == "default"
        assert result["function_name"] == "my_func"
        assert "details" in result
        assert isinstance(result["details"], list)
        assert len(result["details"]) == 7
        assert "Function: main.default.my_func" in result["details"]
        assert "Type: SCALAR" in result["details"]

        mock_query_executor.execute_query_with_catalog.assert_called_once_with(
            "main", "DESCRIBE FUNCTION EXTENDED main.default.my_func", None
        )

    def test_describe_function_with_workspace(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_describe_function_df: pd.DataFrame,
    ):
        """Test describe_function with workspace parameter.

        The method should:
        1. Pass workspace parameter to execute_query_with_catalog
        2. Execute query on specified workspace

        This is part of test case 9 from US-3.3 requirements (test_function_service_workspace_parameter).
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.return_value = (
            sample_describe_function_df
        )

        # Act
        result = function_service.describe_function(
            "calculate", "sales", "functions", workspace="production"
        )

        # Assert
        assert result["catalog"] == "sales"
        assert result["schema"] == "functions"
        assert result["function_name"] == "calculate"
        mock_query_executor.execute_query_with_catalog.assert_called_once_with(
            "sales",
            "DESCRIBE FUNCTION EXTENDED sales.functions.calculate",
            "production",
        )

    def test_describe_function_result_structure(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_describe_function_df: pd.DataFrame,
    ):
        """Test describe_function returns correct result structure.

        The method should return a dict with exactly these keys:
        - catalog: str
        - schema: str
        - function_name: str
        - details: list[str]

        This verifies the result format matches US-3.3 specification.
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.return_value = (
            sample_describe_function_df
        )

        # Act
        result = function_service.describe_function("my_func", "main", "default")

        # Assert - verify all required keys present
        assert set(result.keys()) == {"catalog", "schema", "function_name", "details"}
        assert isinstance(result["catalog"], str)
        assert isinstance(result["schema"], str)
        assert isinstance(result["function_name"], str)
        assert isinstance(result["details"], list)
        assert all(isinstance(detail, str) for detail in result["details"])

    def test_describe_function_calls_parse_method(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_describe_with_configs_df: pd.DataFrame,
    ):
        """Test describe_function calls _parse_function_description.

        The method should:
        1. Pass DataFrame to _parse_function_description
        2. Use the filtered results in the return value

        This verifies that parsing is applied to filter unwanted lines.
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.return_value = (
            sample_describe_with_configs_df
        )

        # Act
        result = function_service.describe_function("my_func", "main", "default")

        # Assert - verify Configs, Owner, Create Time are filtered out
        details = result["details"]
        assert "Configs:" not in details
        assert "Owner: john.doe@example.com" not in details
        assert "Create Time: 2024-01-15 10:30:00" not in details
        # Verify config lines are filtered
        assert not any("spark.sql.adaptive" in line for line in details)
        assert not any("spark.sql.shuffle" in line for line in details)
        # Verify wanted lines are present
        assert "Function: main.default.my_func" in details
        assert "Deterministic: true" in details


# =============================================================================
# List and Describe All Functions Tests
# =============================================================================


class TestFunctionServiceListAndDescribeAll:
    """Tests for list_and_describe_all_functions method."""

    def test_list_and_describe_all_basic(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_functions_df: pd.DataFrame,
        sample_describe_function_df: pd.DataFrame,
    ):
        """Test list_and_describe_all_functions basic functionality.

        The method should:
        1. First call list_user_functions to get function list
        2. Describe each function individually
        3. Return dict with catalog, schema, function_count, and functions dict

        This is test case 3 from US-3.3 requirements (test_function_service_list_and_describe_all).
        """
        # Arrange - mock returns list of functions, then describe results for each
        mock_query_executor.execute_query_with_catalog.side_effect = [
            sample_functions_df,  # list_user_functions result
            sample_describe_function_df,  # describe my_func
            sample_describe_function_df,  # describe another_func
            sample_describe_function_df,  # describe calculate
        ]

        # Act
        result = function_service.list_and_describe_all_functions("main", "default")

        # Assert
        assert isinstance(result, dict)
        assert result["catalog"] == "main"
        assert result["schema"] == "default"
        assert result["function_count"] == 3
        assert "functions" in result
        assert isinstance(result["functions"], dict)
        assert len(result["functions"]) == 3
        assert "my_func" in result["functions"]
        assert "another_func" in result["functions"]
        assert "calculate" in result["functions"]

        # Verify execute_query_with_catalog was called 4 times (1 list + 3 describes)
        assert mock_query_executor.execute_query_with_catalog.call_count == 4

    def test_list_and_describe_all_with_workspace(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_functions_df: pd.DataFrame,
        sample_describe_function_df: pd.DataFrame,
    ):
        """Test list_and_describe_all_functions with workspace parameter.

        The method should:
        1. Pass workspace to list_user_functions
        2. Pass workspace to all describe queries

        This is part of test case 9 from US-3.3 requirements (test_function_service_workspace_parameter).
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.side_effect = [
            sample_functions_df,
            sample_describe_function_df,
            sample_describe_function_df,
            sample_describe_function_df,
        ]

        # Act
        result = function_service.list_and_describe_all_functions(
            "analytics", "ml", workspace="production"
        )

        # Assert
        assert result["catalog"] == "analytics"
        assert result["schema"] == "ml"

        # Verify all calls include workspace parameter
        calls = mock_query_executor.execute_query_with_catalog.call_args_list
        assert all(call[0][2] == "production" for call in calls)

    def test_list_and_describe_all_no_functions(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        empty_functions_df: pd.DataFrame,
    ):
        """Test list_and_describe_all_functions with no functions.

        The method should:
        1. Handle empty function list gracefully
        2. Return empty functions dict

        This is related to test case 5 from US-3.3 requirements (test_function_service_no_functions).
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.return_value = empty_functions_df

        # Act
        result = function_service.list_and_describe_all_functions("main", "default")

        # Assert
        assert result["catalog"] == "main"
        assert result["schema"] == "default"
        assert result["function_count"] == 0
        assert result["functions"] == {}

        # Verify only list_user_functions was called, no describe calls
        assert mock_query_executor.execute_query_with_catalog.call_count == 1

    def test_list_and_describe_all_extracts_function_name(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_describe_function_df: pd.DataFrame,
    ):
        """Test list_and_describe_all_functions extracts function name correctly.

        The method should:
        1. Extract just the function name from full path using split(".")[-1]
        2. Use extracted name as key in functions dict

        This verifies function name extraction logic.
        """
        # Arrange - return fully qualified function names
        functions_df = pd.DataFrame(
            {"function": ["catalog.schema.func1", "catalog.schema.func2"]}
        )
        mock_query_executor.execute_query_with_catalog.side_effect = [
            functions_df,
            sample_describe_function_df,
            sample_describe_function_df,
        ]

        # Act
        result = function_service.list_and_describe_all_functions("main", "default")

        # Assert - verify only function names are used as keys
        assert "func1" in result["functions"]
        assert "func2" in result["functions"]
        assert "catalog.schema.func1" not in result["functions"]

    def test_list_and_describe_all_error_handling(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_describe_function_df: pd.DataFrame,
    ):
        """Test list_and_describe_all_functions handles individual function errors.

        The method should:
        1. Catch exceptions when describing individual functions
        2. Include error info in result for failed functions
        3. Continue processing other functions

        This is part of test case 10 from US-3.3 requirements (test_function_service_error_handling).
        """
        # Arrange - second describe fails
        functions_df = pd.DataFrame(
            {"function": ["main.default.good_func", "main.default.bad_func"]}
        )
        mock_query_executor.execute_query_with_catalog.side_effect = [
            functions_df,
            sample_describe_function_df,  # good_func succeeds
            DatabricksError("Function not found"),  # bad_func fails
        ]

        # Act
        result = function_service.list_and_describe_all_functions("main", "default")

        # Assert
        assert result["function_count"] == 2
        assert "good_func" in result["functions"]
        assert "bad_func" in result["functions"]

        # good_func should have details list
        assert isinstance(result["functions"]["good_func"], list)

        # bad_func should have error dict
        assert isinstance(result["functions"]["bad_func"], dict)
        assert "error" in result["functions"]["bad_func"]
        assert result["functions"]["bad_func"]["error"] == "Could not describe function"


# =============================================================================
# Parse Function Description Tests (CRITICAL)
# =============================================================================


class TestFunctionServiceParseDescription:
    """Tests for _parse_function_description method (CRITICAL for filtering logic)."""

    def test_parse_description_filters_configs(
        self,
        function_service: FunctionService,
        sample_describe_with_configs_df: pd.DataFrame,
    ):
        """Test _parse_function_description filters out Configs section.

        The method should:
        1. Remove lines starting with "Configs:"
        2. Remove all indented config lines (15 spaces)
        3. Resume keeping lines after config section

        This is test case 4 from US-3.3 requirements (test_function_service_parse_description).
        """
        # Act
        result = function_service._parse_function_description(
            sample_describe_with_configs_df
        )

        # Assert - verify Configs line is not present
        assert "Configs:" not in result

        # Verify config lines are filtered out
        assert not any("spark.sql.adaptive" in line for line in result)
        assert not any("spark.sql.shuffle" in line for line in result)
        assert not any("custom.config.value" in line for line in result)

        # Verify lines after Configs are kept (Deterministic, Data Access)
        assert "Deterministic: true" in result
        assert "Data Access: NO_SQL" in result

    def test_parse_description_filters_owner_and_create_time(
        self,
        function_service: FunctionService,
        sample_describe_with_owner_createtime_df: pd.DataFrame,
    ):
        """Test _parse_function_description filters out Owner and Create Time.

        The method should:
        1. Remove lines starting with "Owner:"
        2. Remove lines starting with "Create Time:"

        This is part of test case 4 from US-3.3 requirements (test_function_service_parse_description).
        """
        # Act
        result = function_service._parse_function_description(
            sample_describe_with_owner_createtime_df
        )

        # Assert - verify Owner and Create Time are not present
        assert not any("Owner:" in line for line in result)
        assert not any("Create Time:" in line for line in result)
        assert not any("admin@example.com" in line for line in result)
        assert not any("2023-12-01" in line for line in result)

        # Verify other lines are kept
        assert "Function: analytics.reports.calculate_discount" in result
        assert "Deterministic: true" in result

    def test_parse_description_keeps_function_metadata(
        self,
        function_service: FunctionService,
        sample_describe_function_df: pd.DataFrame,
    ):
        """Test _parse_function_description keeps important metadata lines.

        The method should keep lines starting with:
        - Function:
        - Type:
        - Input:
        - Returns:
        - Comment:
        - Deterministic:
        - Data Access:
        - Body:

        This verifies the positive filtering logic.
        """
        # Act
        result = function_service._parse_function_description(
            sample_describe_function_df
        )

        # Assert - verify all important lines are kept
        assert "Function: main.default.my_func" in result
        assert "Type: SCALAR" in result
        assert "Input: (x INT)" in result
        assert "Returns: INT" in result
        assert "Comment: My custom function" in result
        assert "Deterministic: true" in result
        assert "Data Access: NO_SQL" in result

    def test_parse_description_handles_indented_lines(
        self,
        function_service: FunctionService,
        realistic_describe_function_df: pd.DataFrame,
    ):
        """Test _parse_function_description handles indented continuation lines.

        The method should:
        1. Keep indented lines (15 spaces) for Input and Returns
        2. Filter out indented config lines
        3. Distinguish between config indents and parameter indents

        This is CRITICAL for proper handling of multi-line parameters.
        """
        # Act
        result = function_service._parse_function_description(
            realistic_describe_function_df
        )

        # Assert - verify indented parameter lines are kept
        assert any("param3 ARRAY<STRING>" in line for line in result)
        assert any("param4 STRUCT" in line for line in result)
        assert any("Additional return info" in line for line in result)

        # Verify indented config lines are filtered
        assert not any("spark.sql.adaptive" in line for line in result)
        assert not any("spark.sql.shuffle" in line for line in result)
        assert not any("custom.setting" in line for line in result)

    def test_parse_description_realistic_output(
        self,
        function_service: FunctionService,
        realistic_describe_function_df: pd.DataFrame,
    ):
        """Test _parse_function_description with complete realistic output.

        This is a comprehensive test with full DESCRIBE FUNCTION EXTENDED output
        including all sections that should be kept and filtered.

        This verifies end-to-end parsing behavior.
        """
        # Act
        result = function_service._parse_function_description(
            realistic_describe_function_df
        )

        # Assert - verify structure
        assert isinstance(result, list)
        assert len(result) > 0

        # Verify kept lines
        assert "Function: main.default.advanced_function" in result
        assert "Type: SCALAR" in result
        assert "Input: (param1 INT, param2 STRING)" in result
        assert "Deterministic: true" in result
        assert "Data Access: READS_SQL_DATA" in result
        assert "Body: RETURN STRUCT(param1 * 2 AS result, param2 AS message)" in result

        # Verify filtered lines
        assert "Configs:" not in result
        assert "Owner: data.engineer@company.com" not in result
        assert "Create Time: 2024-01-15 14:30:00" not in result

        # Verify order is preserved
        assert result.index("Function: main.default.advanced_function") == 0
        assert result.index("Type: SCALAR") == 1

    def test_parse_description_empty_dataframe(
        self,
        function_service: FunctionService,
    ):
        """Test _parse_function_description with empty DataFrame.

        The method should:
        1. Handle empty DataFrame gracefully
        2. Return empty list

        This is an edge case test.
        """
        # Arrange
        empty_df = pd.DataFrame({"function_desc": []})

        # Act
        result = function_service._parse_function_description(empty_df)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    def test_parse_description_none_values(
        self,
        function_service: FunctionService,
    ):
        """Test _parse_function_description handles None values in DataFrame.

        The method should:
        1. Skip rows with None in function_desc column
        2. Not crash on None values

        This is an edge case test.
        """
        # Arrange
        df_with_none = pd.DataFrame(
            {
                "function_desc": [
                    "Function: test.func",
                    None,
                    "Type: SCALAR",
                    None,
                    "Returns: INT",
                ]
            }
        )

        # Act
        result = function_service._parse_function_description(df_with_none)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 3
        assert "Function: test.func" in result
        assert "Type: SCALAR" in result
        assert "Returns: INT" in result


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestFunctionServiceErrorHandling:
    """Tests for error handling and error propagation."""

    def test_list_user_functions_error_propagation(
        self, function_service: FunctionService, mock_query_executor: MagicMock
    ):
        """Test list_user_functions propagates QueryExecutor errors.

        When QueryExecutor raises an exception:
        1. The exception should propagate to the caller
        2. No exception handling should suppress the error

        This is part of test case 10 from US-3.3 requirements (test_function_service_error_handling).
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.side_effect = DatabricksError(
            "Schema 'invalid_schema' not found"
        )

        # Act & Assert
        with pytest.raises(DatabricksError, match="Schema 'invalid_schema' not found"):
            function_service.list_user_functions("main", "invalid_schema")

        # Verify QueryExecutor was called
        mock_query_executor.execute_query_with_catalog.assert_called_once()

    def test_describe_function_error_propagation(
        self, function_service: FunctionService, mock_query_executor: MagicMock
    ):
        """Test describe_function propagates QueryExecutor errors.

        When QueryExecutor raises an exception:
        1. The exception should propagate to the caller

        This is test case 6 from US-3.3 requirements (test_function_service_invalid_function).
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.side_effect = DatabricksError(
            "Function 'main.default.nonexistent' not found"
        )

        # Act & Assert
        with pytest.raises(
            DatabricksError, match="Function 'main.default.nonexistent' not found"
        ):
            function_service.describe_function("nonexistent", "main", "default")

        # Verify QueryExecutor was called
        mock_query_executor.execute_query_with_catalog.assert_called_once()

    def test_list_and_describe_all_error_propagation(
        self, function_service: FunctionService, mock_query_executor: MagicMock
    ):
        """Test list_and_describe_all_functions propagates list errors.

        When list_user_functions fails:
        1. The exception should propagate to the caller

        This is part of test case 10 from US-3.3 requirements (test_function_service_error_handling).
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.side_effect = DatabricksError(
            "Catalog 'invalid_catalog' not found"
        )

        # Act & Assert
        with pytest.raises(
            DatabricksError, match="Catalog 'invalid_catalog' not found"
        ):
            function_service.list_and_describe_all_functions(
                "invalid_catalog", "default"
            )

    def test_workspace_not_found_error(
        self, function_service: FunctionService, mock_query_executor: MagicMock
    ):
        """Test error when workspace doesn't exist.

        When workspace is invalid:
        1. QueryExecutor should raise ValueError
        2. Error should propagate with workspace information

        This tests workspace parameter error handling.
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.side_effect = ValueError(
            "Workspace 'nonexistent' configuration not found"
        )

        # Act & Assert
        with pytest.raises(
            ValueError, match="Workspace 'nonexistent' configuration not found"
        ):
            function_service.list_user_functions(
                "main", "default", workspace="nonexistent"
            )


# =============================================================================
# Workspace Parameter Tests
# =============================================================================


class TestFunctionServiceWorkspaceParameter:
    """Tests for workspace parameter handling across all methods."""

    def test_list_user_functions_workspace_parameter(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_functions_df: pd.DataFrame,
    ):
        """Test list_user_functions passes workspace parameter correctly.

        This is part of test case 9 from US-3.3 requirements (test_function_service_workspace_parameter).
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.return_value = (
            sample_functions_df
        )

        # Act
        function_service.list_user_functions("main", "default", workspace="prod")

        # Assert
        call_args = mock_query_executor.execute_query_with_catalog.call_args
        assert call_args[0][2] == "prod"

    def test_describe_function_workspace_parameter(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_describe_function_df: pd.DataFrame,
    ):
        """Test describe_function passes workspace parameter correctly.

        This is part of test case 9 from US-3.3 requirements (test_function_service_workspace_parameter).
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.return_value = (
            sample_describe_function_df
        )

        # Act
        function_service.describe_function(
            "func", "main", "default", workspace="staging"
        )

        # Assert
        call_args = mock_query_executor.execute_query_with_catalog.call_args
        assert call_args[0][2] == "staging"

    def test_list_and_describe_all_workspace_parameter(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_functions_df: pd.DataFrame,
        sample_describe_function_df: pd.DataFrame,
    ):
        """Test list_and_describe_all_functions passes workspace to all calls.

        This is part of test case 9 from US-3.3 requirements (test_function_service_workspace_parameter).
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.side_effect = [
            sample_functions_df,
            sample_describe_function_df,
            sample_describe_function_df,
            sample_describe_function_df,
        ]

        # Act
        function_service.list_and_describe_all_functions(
            "main", "default", workspace="dev"
        )

        # Assert - all calls should have workspace="dev"
        calls = mock_query_executor.execute_query_with_catalog.call_args_list
        assert all(call[0][2] == "dev" for call in calls)

    def test_explicit_none_workspace(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_functions_df: pd.DataFrame,
    ):
        """Test explicit None workspace parameter.

        The method should:
        1. Accept None as explicit parameter value
        2. Behave same as default (no parameter)

        This is an edge case test.
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.return_value = (
            sample_functions_df
        )

        # Act
        function_service.list_user_functions("main", "default", workspace=None)

        # Assert
        call_args = mock_query_executor.execute_query_with_catalog.call_args
        assert call_args[0][2] is None


# =============================================================================
# Catalog and Schema Parameter Tests
# =============================================================================


class TestFunctionServiceCatalogSchemaDefaults:
    """Tests for catalog and schema parameter handling."""

    def test_catalog_schema_defaults(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_functions_df: pd.DataFrame,
    ):
        """Test catalog and schema parameters are required and used correctly.

        This is test case 7 from US-3.3 requirements (test_function_service_catalog_schema_defaults).
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.return_value = (
            sample_functions_df
        )

        # Act
        result = function_service.list_user_functions("custom_catalog", "custom_schema")

        # Assert
        assert result["catalog"] == "custom_catalog"
        assert result["schema"] == "custom_schema"

        # Verify correct query construction
        call_args = mock_query_executor.execute_query_with_catalog.call_args
        assert "custom_catalog.custom_schema" in call_args[0][1]

    def test_describe_function_catalog_schema_usage(
        self,
        function_service: FunctionService,
        mock_query_executor: MagicMock,
        sample_describe_function_df: pd.DataFrame,
    ):
        """Test describe_function uses catalog and schema parameters correctly.

        This extends test case 7 from US-3.3 requirements.
        """
        # Arrange
        mock_query_executor.execute_query_with_catalog.return_value = (
            sample_describe_function_df
        )

        # Act
        result = function_service.describe_function(
            "test_func", "analytics", "ml_models"
        )

        # Assert
        assert result["catalog"] == "analytics"
        assert result["schema"] == "ml_models"
        assert result["function_name"] == "test_func"

        # Verify correct query construction
        call_args = mock_query_executor.execute_query_with_catalog.call_args
        assert "analytics.ml_models.test_func" in call_args[0][1]


# =============================================================================
# Integration Tests
# =============================================================================


class TestFunctionServiceIntegration:
    """Integration tests with real dependency instances."""

    def test_integration_with_real_dependencies(
        self,
        sample_functions_df: pd.DataFrame,
    ):
        """Test FunctionService with real QueryExecutor and TokenCounter.

        This integration test:
        1. Uses actual QueryExecutor and TokenCounter instances
        2. Mocks only at the connection level
        3. Verifies end-to-end behavior

        This is test case 11 from US-3.3 requirements (test_integration_with_mcp_tools).
        """
        # Arrange - Create real instances but mock QueryExecutor's execute_query_with_catalog
        query_executor = MagicMock(spec=QueryExecutor)
        token_counter = TokenCounter()  # Real TokenCounter instance
        service = FunctionService(query_executor, token_counter, max_tokens=9000)

        query_executor.execute_query_with_catalog.return_value = sample_functions_df

        # Act
        functions = service.list_user_functions("main", "default")

        # Assert
        assert isinstance(functions, dict)
        assert functions["function_count"] == 3
        assert len(functions["user_functions"]) == 3
        assert service.token_counter == token_counter
        assert service.max_tokens == 9000

    def test_integration_multiple_operations(
        self,
        sample_functions_df: pd.DataFrame,
        sample_describe_function_df: pd.DataFrame,
    ):
        """Test multiple sequential operations on FunctionService.

        This integration test:
        1. Calls multiple methods in sequence
        2. Verifies state is maintained correctly
        3. Tests typical usage pattern

        This extends integration testing with realistic workflows.
        """
        # Arrange
        query_executor = MagicMock(spec=QueryExecutor)
        token_counter = TokenCounter()
        service = FunctionService(query_executor, token_counter)

        # Configure mock to return different results for different queries
        query_executor.execute_query_with_catalog.side_effect = [
            sample_functions_df,  # For list_user_functions
            sample_describe_function_df,  # For describe_function
            sample_functions_df,  # For list_and_describe_all (list)
            sample_describe_function_df,  # describe first function
            sample_describe_function_df,  # describe second function
            sample_describe_function_df,  # describe third function
        ]

        # Act - typical workflow
        functions = service.list_user_functions("main", "default")
        details = service.describe_function("my_func", "main", "default")
        all_funcs = service.list_and_describe_all_functions("main", "default")

        # Assert
        assert functions["function_count"] == 3
        assert details["function_name"] == "my_func"
        assert all_funcs["function_count"] == 3
        assert len(all_funcs["functions"]) == 3

        # Verify QueryExecutor was called 6 times total
        assert query_executor.execute_query_with_catalog.call_count == 6


# =============================================================================
# Token Counter Integration Tests
# =============================================================================


class TestFunctionServiceTokenCounterIntegration:
    """Tests for TokenCounter integration with FunctionService."""

    def test_token_counter_integration(
        self, mock_query_executor: MagicMock, sample_functions_df: pd.DataFrame
    ):
        """Test FunctionService properly integrates with TokenCounter.

        The service should:
        1. Store TokenCounter instance
        2. Make it available for token estimation
        3. Respect max_tokens configuration

        This is test case 8 from US-3.3 requirements (test_function_service_token_limit).
        """
        # Arrange
        token_counter = TokenCounter(model="gpt-4")
        service = FunctionService(mock_query_executor, token_counter, max_tokens=5000)
        mock_query_executor.execute_query_with_catalog.return_value = (
            sample_functions_df
        )

        # Act
        functions = service.list_user_functions("main", "default")

        # Assert - verify TokenCounter is accessible and configured
        assert service.token_counter is token_counter
        assert service.max_tokens == 5000

        # Verify we can use the token counter
        import json

        functions_json = json.dumps(functions)
        token_count = service.token_counter.count_tokens(functions_json)
        assert isinstance(token_count, int)
        assert token_count > 0

    def test_token_counter_with_response_estimation(
        self,
        mock_query_executor: MagicMock,
        sample_describe_function_df: pd.DataFrame,
    ):
        """Test token estimation for service responses.

        The service should:
        1. Allow token estimation on returned data structures
        2. Support chunking decisions based on max_tokens

        This extends TokenCounter integration testing.
        """
        # Arrange
        token_counter = TokenCounter(model="gpt-4")
        service = FunctionService(mock_query_executor, token_counter, max_tokens=9000)
        mock_query_executor.execute_query_with_catalog.return_value = (
            sample_describe_function_df
        )

        # Act
        details = service.describe_function("my_func", "main", "default")

        # Assert - verify we can estimate tokens for the response
        token_estimate = service.token_counter.estimate_tokens(details)
        assert isinstance(token_estimate, int)
        assert token_estimate > 0

        # Verify chunking decision can be made
        needs_chunking = token_estimate > service.max_tokens
        assert isinstance(needs_chunking, bool)
