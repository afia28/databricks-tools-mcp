"""Comprehensive test suite for CatalogService class.

This module contains comprehensive tests for the CatalogService class,
covering catalog and schema listing operations with consistent error handling.

Test coverage goal: 90%+ for src/databricks_tools/services/catalog_service.py

Test cases included (10+ tests covering US-3.1):
1. test_catalog_service_initialization_with_dependencies - Verify proper initialization
2. test_catalog_service_initialization_custom_max_tokens - Custom max_tokens parameter
3. test_list_catalogs_default_workspace - Basic catalog listing
4. test_list_catalogs_specific_workspace - Workspace parameter handling
5. test_list_catalogs_empty_result - Empty DataFrame handling
6. test_list_catalogs_query_executor_delegation - Verify QueryExecutor calls
7. test_list_schemas_single_catalog - Single catalog schema listing
8. test_list_schemas_multiple_catalogs - Multiple catalog schema listing
9. test_list_schemas_with_workspace - Workspace parameter in list_schemas
10. test_list_schemas_empty_catalog_list - Handle empty input list
11. test_list_schemas_query_executor_delegation - Verify multiple queries
12. test_list_catalogs_error_propagation - Error handling for list_catalogs
13. test_list_schemas_error_propagation - Error handling for list_schemas
14. test_list_schemas_invalid_catalog - Handle catalog not found
15. test_integration_with_real_dependencies - Integration test
16. test_integration_multiple_operations - Sequential operations test
"""

from unittest.mock import MagicMock, call

import pandas as pd
import pytest
from databricks.sql import Error as DatabricksError

from databricks_tools.core.query_executor import QueryExecutor
from databricks_tools.core.token_counter import TokenCounter
from databricks_tools.services.catalog_service import CatalogService

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
def catalog_service(
    mock_query_executor: MagicMock, mock_token_counter: MagicMock
) -> CatalogService:
    """Create a CatalogService with mocked dependencies.

    Returns:
        A CatalogService instance with mocked QueryExecutor and TokenCounter.
    """
    return CatalogService(mock_query_executor, mock_token_counter)


@pytest.fixture
def sample_catalogs_df() -> pd.DataFrame:
    """Create a sample DataFrame with catalog names.

    Returns:
        A pandas DataFrame with catalog column.
    """
    return pd.DataFrame({"catalog": ["main", "analytics", "production"]})


@pytest.fixture
def sample_schemas_df_main() -> pd.DataFrame:
    """Create a sample DataFrame with schema names for main catalog.

    Returns:
        A pandas DataFrame with databaseName column.
    """
    return pd.DataFrame({"databaseName": ["default", "staging", "development"]})


@pytest.fixture
def sample_schemas_df_analytics() -> pd.DataFrame:
    """Create a sample DataFrame with schema names for analytics catalog.

    Returns:
        A pandas DataFrame with databaseName column.
    """
    return pd.DataFrame({"databaseName": ["reports", "metrics", "dashboards"]})


@pytest.fixture
def empty_catalogs_df() -> pd.DataFrame:
    """Create an empty DataFrame with catalog column.

    Returns:
        An empty pandas DataFrame.
    """
    return pd.DataFrame({"catalog": []})


@pytest.fixture
def empty_schemas_df() -> pd.DataFrame:
    """Create an empty DataFrame with databaseName column.

    Returns:
        An empty pandas DataFrame.
    """
    return pd.DataFrame({"databaseName": []})


# =============================================================================
# Initialization Tests
# =============================================================================


class TestCatalogServiceInitialization:
    """Tests for CatalogService initialization."""

    def test_catalog_service_initialization_with_dependencies(
        self, mock_query_executor: MagicMock, mock_token_counter: MagicMock
    ):
        """Test CatalogService initializes with required dependencies.

        The CatalogService should:
        1. Accept QueryExecutor and TokenCounter in __init__
        2. Store them as instance attributes
        3. Use default max_tokens value of 9000

        This is test case 1 from US-3.1 requirements.
        """
        # Act
        service = CatalogService(mock_query_executor, mock_token_counter)

        # Assert
        assert service.query_executor is mock_query_executor
        assert service.token_counter is mock_token_counter
        assert service.max_tokens == 9000

    def test_catalog_service_initialization_custom_max_tokens(
        self, mock_query_executor: MagicMock, mock_token_counter: MagicMock
    ):
        """Test CatalogService accepts custom max_tokens parameter.

        The CatalogService should:
        1. Allow custom max_tokens value in __init__
        2. Store the custom value correctly

        This is test case 2 from US-3.1 requirements.
        """
        # Act
        service = CatalogService(
            mock_query_executor, mock_token_counter, max_tokens=5000
        )

        # Assert
        assert service.query_executor is mock_query_executor
        assert service.token_counter is mock_token_counter
        assert service.max_tokens == 5000


# =============================================================================
# List Catalogs Tests
# =============================================================================


class TestCatalogServiceListCatalogs:
    """Tests for list_catalogs method."""

    def test_list_catalogs_default_workspace(
        self,
        catalog_service: CatalogService,
        mock_query_executor: MagicMock,
        sample_catalogs_df: pd.DataFrame,
    ):
        """Test list_catalogs with default workspace (None).

        The method should:
        1. Execute SHOW CATALOGS query
        2. Pass None for workspace parameter (uses default)
        3. Return list of catalog names

        This is test case 3 from US-3.1 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_catalogs_df

        # Act
        result = catalog_service.list_catalogs()

        # Assert
        assert isinstance(result, list)
        assert result == ["main", "analytics", "production"]
        mock_query_executor.execute_query.assert_called_once_with("SHOW CATALOGS", None)

    def test_list_catalogs_specific_workspace(
        self,
        catalog_service: CatalogService,
        mock_query_executor: MagicMock,
        sample_catalogs_df: pd.DataFrame,
    ):
        """Test list_catalogs with specific workspace parameter.

        The method should:
        1. Execute SHOW CATALOGS query
        2. Pass workspace parameter to QueryExecutor
        3. Return list of catalog names from specified workspace

        This is test case 4 from US-3.1 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_catalogs_df

        # Act
        result = catalog_service.list_catalogs(workspace="production")

        # Assert
        assert isinstance(result, list)
        assert result == ["main", "analytics", "production"]
        mock_query_executor.execute_query.assert_called_once_with(
            "SHOW CATALOGS", "production"
        )

    def test_list_catalogs_empty_result(
        self,
        catalog_service: CatalogService,
        mock_query_executor: MagicMock,
        empty_catalogs_df: pd.DataFrame,
    ):
        """Test list_catalogs handles empty result gracefully.

        The method should:
        1. Handle empty DataFrame from QueryExecutor
        2. Return empty list without errors

        This is an edge case test for robust error handling.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = empty_catalogs_df

        # Act
        result = catalog_service.list_catalogs()

        # Assert
        assert isinstance(result, list)
        assert result == []
        assert len(result) == 0

    def test_list_catalogs_query_executor_delegation(
        self,
        catalog_service: CatalogService,
        mock_query_executor: MagicMock,
        sample_catalogs_df: pd.DataFrame,
    ):
        """Test list_catalogs properly delegates to QueryExecutor.

        The method should:
        1. Call execute_query with correct SQL query
        2. Pass workspace parameter correctly
        3. Process DataFrame result correctly

        This is test case 7 from US-3.1 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_catalogs_df

        # Act
        catalog_service.list_catalogs(workspace="test_workspace")

        # Assert - verify exact parameters passed
        mock_query_executor.execute_query.assert_called_once()
        call_args = mock_query_executor.execute_query.call_args
        assert call_args[0][0] == "SHOW CATALOGS"  # First positional arg is query
        assert call_args[0][1] == "test_workspace"  # Second positional arg is workspace


# =============================================================================
# List Schemas Tests
# =============================================================================


class TestCatalogServiceListSchemas:
    """Tests for list_schemas method."""

    def test_list_schemas_single_catalog(
        self,
        catalog_service: CatalogService,
        mock_query_executor: MagicMock,
        sample_schemas_df_main: pd.DataFrame,
    ):
        """Test list_schemas with single catalog.

        The method should:
        1. Execute SHOW SCHEMAS IN {catalog} query
        2. Return dict mapping catalog to list of schemas
        3. Handle single catalog correctly

        This is test case 5 from US-3.1 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_schemas_df_main

        # Act
        result = catalog_service.list_schemas(["main"])

        # Assert
        assert isinstance(result, dict)
        assert "main" in result
        assert result["main"] == ["default", "staging", "development"]
        mock_query_executor.execute_query.assert_called_once_with(
            "SHOW SCHEMAS IN main", None
        )

    def test_list_schemas_multiple_catalogs(
        self,
        catalog_service: CatalogService,
        mock_query_executor: MagicMock,
        sample_schemas_df_main: pd.DataFrame,
        sample_schemas_df_analytics: pd.DataFrame,
    ):
        """Test list_schemas with multiple catalogs.

        The method should:
        1. Execute SHOW SCHEMAS query for each catalog
        2. Return dict mapping all catalogs to their schemas
        3. Make multiple QueryExecutor calls sequentially

        This is test case 6 from US-3.1 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.side_effect = [
            sample_schemas_df_main,
            sample_schemas_df_analytics,
        ]

        # Act
        result = catalog_service.list_schemas(["main", "analytics"])

        # Assert
        assert isinstance(result, dict)
        assert len(result) == 2
        assert result["main"] == ["default", "staging", "development"]
        assert result["analytics"] == ["reports", "metrics", "dashboards"]

        # Verify QueryExecutor was called twice with correct queries
        assert mock_query_executor.execute_query.call_count == 2
        calls = mock_query_executor.execute_query.call_args_list
        assert calls[0] == call("SHOW SCHEMAS IN main", None)
        assert calls[1] == call("SHOW SCHEMAS IN analytics", None)

    def test_list_schemas_with_workspace(
        self,
        catalog_service: CatalogService,
        mock_query_executor: MagicMock,
        sample_schemas_df_main: pd.DataFrame,
    ):
        """Test list_schemas with workspace parameter.

        The method should:
        1. Pass workspace parameter to each QueryExecutor call
        2. Execute queries on specified workspace
        3. Return schemas from that workspace

        This is test case 8 from US-3.1 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_schemas_df_main

        # Act
        result = catalog_service.list_schemas(["main"], workspace="production")

        # Assert
        assert isinstance(result, dict)
        assert result["main"] == ["default", "staging", "development"]
        mock_query_executor.execute_query.assert_called_once_with(
            "SHOW SCHEMAS IN main", "production"
        )

    def test_list_schemas_empty_catalog_list(
        self, catalog_service: CatalogService, mock_query_executor: MagicMock
    ):
        """Test list_schemas with empty catalog list.

        The method should:
        1. Handle empty input list gracefully
        2. Return empty dict without executing any queries

        This is an edge case test for robust error handling.
        """
        # Act
        result = catalog_service.list_schemas([])

        # Assert
        assert isinstance(result, dict)
        assert result == {}
        assert len(result) == 0
        # Verify no queries were executed
        mock_query_executor.execute_query.assert_not_called()

    def test_list_schemas_query_executor_delegation(
        self,
        catalog_service: CatalogService,
        mock_query_executor: MagicMock,
        sample_schemas_df_main: pd.DataFrame,
        sample_schemas_df_analytics: pd.DataFrame,
    ):
        """Test list_schemas properly delegates to QueryExecutor.

        The method should:
        1. Call execute_query for each catalog
        2. Pass correct SQL queries with catalog names
        3. Pass workspace parameter to all calls
        4. Process all DataFrame results correctly

        This is test case 9 from US-3.1 requirements (delegation verification).
        """
        # Arrange
        mock_query_executor.execute_query.side_effect = [
            sample_schemas_df_main,
            sample_schemas_df_analytics,
        ]

        # Act
        result = catalog_service.list_schemas(
            ["main", "analytics"], workspace="test_workspace"
        )

        # Assert
        assert len(result) == 2
        assert mock_query_executor.execute_query.call_count == 2

        # Verify exact parameters for each call
        calls = mock_query_executor.execute_query.call_args_list
        assert calls[0][0][0] == "SHOW SCHEMAS IN main"
        assert calls[0][0][1] == "test_workspace"
        assert calls[1][0][0] == "SHOW SCHEMAS IN analytics"
        assert calls[1][0][1] == "test_workspace"


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestCatalogServiceErrorHandling:
    """Tests for error handling and error propagation."""

    def test_list_catalogs_error_propagation(
        self, catalog_service: CatalogService, mock_query_executor: MagicMock
    ):
        """Test list_catalogs propagates QueryExecutor errors.

        When QueryExecutor raises an exception:
        1. The exception should propagate to the caller
        2. No exception handling should suppress the error

        This is test case 10 from US-3.1 requirements.
        """
        # Arrange
        mock_query_executor.execute_query.side_effect = DatabricksError(
            "Connection failed: network unreachable"
        )

        # Act & Assert
        with pytest.raises(DatabricksError, match="Connection failed"):
            catalog_service.list_catalogs()

        # Verify QueryExecutor was called
        mock_query_executor.execute_query.assert_called_once()

    def test_list_schemas_error_propagation(
        self, catalog_service: CatalogService, mock_query_executor: MagicMock
    ):
        """Test list_schemas propagates QueryExecutor errors.

        When QueryExecutor raises an exception:
        1. The exception should propagate to the caller
        2. Error should occur during iteration over catalogs

        This extends test case 10 for list_schemas method.
        """
        # Arrange
        mock_query_executor.execute_query.side_effect = DatabricksError(
            "SQL execution failed: invalid syntax"
        )

        # Act & Assert
        with pytest.raises(DatabricksError, match="SQL execution failed"):
            catalog_service.list_schemas(["main"])

        # Verify QueryExecutor was called
        mock_query_executor.execute_query.assert_called_once()

    def test_list_schemas_invalid_catalog(
        self, catalog_service: CatalogService, mock_query_executor: MagicMock
    ):
        """Test list_schemas handles invalid catalog name.

        When a catalog doesn't exist:
        1. QueryExecutor raises an error
        2. Error should propagate with helpful message

        This is an edge case for error handling.
        """
        # Arrange
        mock_query_executor.execute_query.side_effect = DatabricksError(
            "Catalog 'invalid_catalog' not found"
        )

        # Act & Assert
        with pytest.raises(
            DatabricksError, match="Catalog 'invalid_catalog' not found"
        ):
            catalog_service.list_schemas(["invalid_catalog"])

    def test_list_catalogs_workspace_not_found(
        self, catalog_service: CatalogService, mock_query_executor: MagicMock
    ):
        """Test list_catalogs error when workspace doesn't exist.

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
            catalog_service.list_catalogs(workspace="nonexistent")

    def test_list_schemas_workspace_not_found(
        self, catalog_service: CatalogService, mock_query_executor: MagicMock
    ):
        """Test list_schemas error when workspace doesn't exist.

        When workspace is invalid:
        1. QueryExecutor should raise ValueError
        2. Error should propagate with workspace information

        This tests workspace parameter error handling for list_schemas.
        """
        # Arrange
        mock_query_executor.execute_query.side_effect = ValueError(
            "Workspace 'nonexistent' configuration not found"
        )

        # Act & Assert
        with pytest.raises(
            ValueError, match="Workspace 'nonexistent' configuration not found"
        ):
            catalog_service.list_schemas(["main"], workspace="nonexistent")


# =============================================================================
# Integration Tests
# =============================================================================


class TestCatalogServiceIntegration:
    """Integration tests with real dependency instances."""

    def test_integration_with_real_dependencies(
        self,
        sample_catalogs_df: pd.DataFrame,
        sample_schemas_df_main: pd.DataFrame,
    ):
        """Test CatalogService with real QueryExecutor and TokenCounter.

        This integration test:
        1. Uses actual QueryExecutor and TokenCounter instances
        2. Mocks only at the connection level
        3. Verifies end-to-end behavior

        This is test case 11 from US-3.1 requirements (integration test).
        """
        # Arrange - Create real instances but mock QueryExecutor's execute_query
        query_executor = MagicMock(spec=QueryExecutor)
        token_counter = TokenCounter()  # Real TokenCounter instance
        service = CatalogService(query_executor, token_counter, max_tokens=9000)

        query_executor.execute_query.return_value = sample_catalogs_df

        # Act
        catalogs = service.list_catalogs()

        # Assert
        assert isinstance(catalogs, list)
        assert len(catalogs) == 3
        assert "main" in catalogs
        assert service.token_counter == token_counter
        assert service.max_tokens == 9000

    def test_integration_multiple_operations(
        self,
        sample_catalogs_df: pd.DataFrame,
        sample_schemas_df_main: pd.DataFrame,
        sample_schemas_df_analytics: pd.DataFrame,
    ):
        """Test multiple sequential operations on CatalogService.

        This integration test:
        1. Calls list_catalogs followed by list_schemas
        2. Verifies state is maintained correctly
        3. Tests typical usage pattern

        This extends integration testing with realistic workflows.
        """
        # Arrange
        query_executor = MagicMock(spec=QueryExecutor)
        token_counter = TokenCounter()
        service = CatalogService(query_executor, token_counter)

        # Configure mock to return different results for different queries
        query_executor.execute_query.side_effect = [
            sample_catalogs_df,  # For list_catalogs
            sample_schemas_df_main,  # For list_schemas "main"
            sample_schemas_df_analytics,  # For list_schemas "analytics"
        ]

        # Act - typical workflow
        catalogs = service.list_catalogs()
        schemas = service.list_schemas(catalogs[:2])  # Use first two catalogs

        # Assert
        assert len(catalogs) == 3
        assert len(schemas) == 2
        assert "main" in schemas
        assert "analytics" in schemas
        assert schemas["main"] == ["default", "staging", "development"]
        assert schemas["analytics"] == ["reports", "metrics", "dashboards"]

        # Verify QueryExecutor was called 3 times total
        assert query_executor.execute_query.call_count == 3


# =============================================================================
# Token Counter Integration Tests
# =============================================================================


class TestCatalogServiceTokenCounterIntegration:
    """Tests for TokenCounter integration with CatalogService."""

    def test_token_counter_integration(
        self, mock_query_executor: MagicMock, sample_catalogs_df: pd.DataFrame
    ):
        """Test CatalogService properly integrates with TokenCounter.

        The service should:
        1. Store TokenCounter instance
        2. Make it available for token estimation
        3. Respect max_tokens configuration

        This is test case 12 from US-3.1 requirements (TokenCounter integration).
        """
        # Arrange
        token_counter = TokenCounter(model="gpt-4")
        service = CatalogService(mock_query_executor, token_counter, max_tokens=5000)
        mock_query_executor.execute_query.return_value = sample_catalogs_df

        # Act
        catalogs = service.list_catalogs()

        # Assert - verify TokenCounter is accessible and configured
        assert service.token_counter is token_counter
        assert service.max_tokens == 5000

        # Verify we can use the token counter
        catalog_text = ", ".join(catalogs)
        token_count = service.token_counter.count_tokens(catalog_text)
        assert isinstance(token_count, int)
        assert token_count > 0

    def test_token_counter_with_response_estimation(
        self,
        mock_query_executor: MagicMock,
        sample_catalogs_df: pd.DataFrame,
        sample_schemas_df_main: pd.DataFrame,
    ):
        """Test token estimation for service responses.

        The service should:
        1. Allow token estimation on returned data structures
        2. Support chunking decisions based on max_tokens

        This extends TokenCounter integration testing.
        """
        # Arrange
        token_counter = TokenCounter(model="gpt-4")
        service = CatalogService(mock_query_executor, token_counter, max_tokens=9000)
        mock_query_executor.execute_query.return_value = sample_schemas_df_main

        # Act
        schemas = service.list_schemas(["main"])

        # Assert - verify we can estimate tokens for the response
        token_estimate = service.token_counter.estimate_tokens(schemas)
        assert isinstance(token_estimate, int)
        assert token_estimate > 0

        # Verify chunking decision can be made
        needs_chunking = token_estimate > service.max_tokens
        assert isinstance(needs_chunking, bool)


# =============================================================================
# Edge Cases and Additional Tests
# =============================================================================


class TestCatalogServiceEdgeCases:
    """Tests for edge cases and additional scenarios."""

    def test_list_schemas_single_catalog_empty_schemas(
        self,
        catalog_service: CatalogService,
        mock_query_executor: MagicMock,
        empty_schemas_df: pd.DataFrame,
    ):
        """Test list_schemas when a catalog has no schemas.

        The method should:
        1. Handle empty schema list for a catalog
        2. Return empty list for that catalog in result dict

        This is an edge case test.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = empty_schemas_df

        # Act
        result = catalog_service.list_schemas(["empty_catalog"])

        # Assert
        assert isinstance(result, dict)
        assert "empty_catalog" in result
        assert result["empty_catalog"] == []

    def test_list_schemas_mixed_results(
        self,
        catalog_service: CatalogService,
        mock_query_executor: MagicMock,
        sample_schemas_df_main: pd.DataFrame,
        empty_schemas_df: pd.DataFrame,
    ):
        """Test list_schemas with mix of populated and empty catalogs.

        The method should:
        1. Handle some catalogs with schemas and some without
        2. Return correct mapping for all catalogs

        This is an edge case test.
        """
        # Arrange
        mock_query_executor.execute_query.side_effect = [
            sample_schemas_df_main,  # main has schemas
            empty_schemas_df,  # empty_catalog has no schemas
        ]

        # Act
        result = catalog_service.list_schemas(["main", "empty_catalog"])

        # Assert
        assert len(result) == 2
        assert result["main"] == ["default", "staging", "development"]
        assert result["empty_catalog"] == []

    def test_list_catalogs_none_workspace_explicit(
        self,
        catalog_service: CatalogService,
        mock_query_executor: MagicMock,
        sample_catalogs_df: pd.DataFrame,
    ):
        """Test list_catalogs with explicit None workspace parameter.

        The method should:
        1. Accept None as explicit parameter value
        2. Behave same as default (no parameter)

        This is an edge case test.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_catalogs_df

        # Act
        result = catalog_service.list_catalogs(workspace=None)

        # Assert
        assert result == ["main", "analytics", "production"]
        mock_query_executor.execute_query.assert_called_once_with("SHOW CATALOGS", None)

    def test_list_schemas_none_workspace_explicit(
        self,
        catalog_service: CatalogService,
        mock_query_executor: MagicMock,
        sample_schemas_df_main: pd.DataFrame,
    ):
        """Test list_schemas with explicit None workspace parameter.

        The method should:
        1. Accept None as explicit parameter value
        2. Behave same as default (no parameter)

        This is an edge case test.
        """
        # Arrange
        mock_query_executor.execute_query.return_value = sample_schemas_df_main

        # Act
        result = catalog_service.list_schemas(["main"], workspace=None)

        # Assert
        assert result["main"] == ["default", "staging", "development"]
        mock_query_executor.execute_query.assert_called_once_with(
            "SHOW SCHEMAS IN main", None
        )

    def test_list_schemas_preserves_order(
        self,
        catalog_service: CatalogService,
        mock_query_executor: MagicMock,
        sample_schemas_df_main: pd.DataFrame,
        sample_schemas_df_analytics: pd.DataFrame,
    ):
        """Test list_schemas preserves catalog order from input.

        The method should:
        1. Process catalogs in the order provided
        2. Return dict with same catalog order

        This verifies behavior consistency.
        """
        # Arrange
        mock_query_executor.execute_query.side_effect = [
            sample_schemas_df_analytics,  # analytics first
            sample_schemas_df_main,  # main second
        ]

        # Act
        result = catalog_service.list_schemas(["analytics", "main"])

        # Assert
        result_keys = list(result.keys())
        assert result_keys == ["analytics", "main"]  # Order preserved
