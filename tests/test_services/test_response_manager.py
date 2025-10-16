"""Comprehensive test suite for ResponseManager class.

This module contains comprehensive tests for the ResponseManager class,
covering response formatting, error formatting, token validation, automatic
chunking, and integration with TokenCounter and ChunkingService.

Test coverage goal: 95%+ for src/databricks_tools/services/response_manager.py

Test cases included (35+ tests covering US-4.2):
1. test_response_manager_initialization_with_dependencies - Verify proper initialization
2. test_response_manager_initialization_custom_max_tokens - Custom max_tokens
3. test_response_manager_initialization_default_max_tokens - Default max_tokens value
4. test_format_response_small_dict - Small dict response (no chunking)
5. test_format_response_small_list - Small list response (no chunking)
6. test_format_response_large_dict_auto_chunk - Large dict with auto_chunk=True
7. test_format_response_large_dict_disable_auto_chunk - Large dict with auto_chunk=False
8. test_format_response_list_exceeds_limit - Large list (can't chunk)
9. test_format_response_empty_dict - Empty dict edge case
10. test_format_response_empty_list - Empty list edge case
11. test_format_response_nested_structures - Nested dicts/lists
12. test_format_response_special_characters - Special chars in strings
13. test_format_response_token_count_boundary_below - Below max_tokens
14. test_format_response_token_count_boundary_at - At max_tokens
15. test_format_response_token_count_boundary_above - Above max_tokens
16. test_format_error_basic - Basic error formatting
17. test_format_error_with_kwargs - Error with additional kwargs
18. test_format_error_with_multiple_kwargs - Multiple kwargs
19. test_format_error_with_nested_kwargs - Complex kwargs
20. test_format_error_json_structure - Verify JSON structure
21. test_custom_max_tokens_lower - Lower max_tokens value
22. test_custom_max_tokens_higher - Higher max_tokens value
23. test_token_limit_boundary_testing - Parametrized boundary testing
24. test_token_counter_integration - Integration with real TokenCounter
25. test_chunking_service_called_when_needed - Verify chunking triggered
26. test_chunking_service_not_called_small_response - No chunking for small data
27. test_chunking_service_not_called_when_disabled - auto_chunk=False
28. test_chunking_metadata_returned - Verify chunked response structure
29. test_integration_with_real_dependencies - Full integration test
30. test_integration_end_to_end_chunking - E2E chunking workflow
31. test_integration_error_formatting - Error formatting integration
32. test_none_values_in_dict - None values handling
33. test_unicode_characters - Unicode handling
34. test_very_large_strings - Very long string values
35. test_deeply_nested_structures - Deep nesting
"""

import json
from unittest.mock import MagicMock

import pytest

from databricks_tools.core.token_counter import TokenCounter
from databricks_tools.services.chunking_service import ChunkingService
from databricks_tools.services.response_manager import ResponseManager

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_token_counter() -> MagicMock:
    """Create a mock TokenCounter for testing.

    Returns:
        A MagicMock configured to behave like TokenCounter with count_tokens.
    """
    mock = MagicMock(spec=TokenCounter)

    # Configure count_tokens to return realistic token counts
    # Approximation: 1 token ≈ 4 characters
    def count_tokens_side_effect(text):
        return len(text) // 4

    mock.count_tokens.side_effect = count_tokens_side_effect
    return mock


@pytest.fixture
def mock_chunking_service() -> MagicMock:
    """Create a mock ChunkingService for testing.

    Returns:
        A MagicMock configured to behave like ChunkingService.
    """
    mock = MagicMock(spec=ChunkingService)

    # Configure create_chunked_response to return session metadata
    def create_chunked_response_side_effect(data, max_tokens=None):
        return {
            "chunked_response": True,
            "session_id": "test-session-id-12345",
            "total_chunks": 3,
            "chunk_token_amounts": {"1": 3000, "2": 3000, "3": 2000},
            "message": "Response exceeds token limit. Data will be delivered in 3 chunks.",
            "instructions": "Use get_chunk(session_id='test-session-id-12345', chunk_number=N) to retrieve each chunk (1-3)",
        }

    mock.create_chunked_response.side_effect = create_chunked_response_side_effect
    return mock


@pytest.fixture
def response_manager(
    mock_token_counter: MagicMock, mock_chunking_service: MagicMock
) -> ResponseManager:
    """Create a ResponseManager with mocked dependencies.

    Returns:
        A ResponseManager instance with mocked TokenCounter and ChunkingService.
    """
    return ResponseManager(mock_token_counter, mock_chunking_service)


@pytest.fixture
def sample_data_small() -> dict:
    """Create a small sample dataset that won't trigger chunking.

    Returns:
        A small dict for testing non-chunked responses.
    """
    return {
        "result": "success",
        "count": 10,
        "data": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
    }


@pytest.fixture
def sample_data_large() -> dict:
    """Create a large sample dataset that will trigger chunking.

    Returns:
        A large dict for testing chunked responses.
    """
    return {
        "data": [
            {
                "id": i,
                "name": f"User_{i}",
                "email": f"user{i}@example.com",
                "description": "A" * 100,  # Make each row larger
            }
            for i in range(1000)
        ],
        "schema": {
            "fields": [
                {"name": "id", "type": "integer"},
                {"name": "name", "type": "string"},
                {"name": "email", "type": "string"},
                {"name": "description", "type": "string"},
            ]
        },
        "table_name": "test.default.large_table",
    }


@pytest.fixture
def sample_data_list() -> list:
    """Create a list dataset for testing list responses.

    Returns:
        A list for testing list response handling.
    """
    return [{"id": i, "value": f"item_{i}"} for i in range(100)]


# =============================================================================
# Initialization Tests
# =============================================================================


class TestResponseManagerInitialization:
    """Tests for ResponseManager initialization."""

    def test_response_manager_initialization_with_dependencies(
        self, mock_token_counter: MagicMock, mock_chunking_service: MagicMock
    ):
        """Test ResponseManager initializes with required dependencies.

        The ResponseManager should:
        1. Accept TokenCounter and ChunkingService in __init__
        2. Store them as instance attributes
        3. Use default max_tokens value of 9000

        This verifies basic initialization as required by US-4.2.
        """
        # Act
        rm = ResponseManager(mock_token_counter, mock_chunking_service)

        # Assert
        assert rm.token_counter is mock_token_counter
        assert rm.chunking_service is mock_chunking_service
        assert rm.max_tokens == 9000

    def test_response_manager_initialization_custom_max_tokens(
        self, mock_token_counter: MagicMock, mock_chunking_service: MagicMock
    ):
        """Test ResponseManager accepts custom max_tokens parameter.

        The ResponseManager should:
        1. Allow custom max_tokens value
        2. Store the custom value correctly

        This verifies parameter customization.
        """
        # Act
        rm = ResponseManager(mock_token_counter, mock_chunking_service, max_tokens=5000)

        # Assert
        assert rm.token_counter is mock_token_counter
        assert rm.chunking_service is mock_chunking_service
        assert rm.max_tokens == 5000

    def test_response_manager_initialization_default_max_tokens(
        self, mock_token_counter: MagicMock, mock_chunking_service: MagicMock
    ):
        """Test ResponseManager uses default max_tokens of 9000.

        The ResponseManager should:
        1. Default to max_tokens=9000 when not specified

        This verifies default configuration.
        """
        # Act
        rm = ResponseManager(mock_token_counter, mock_chunking_service)

        # Assert
        assert rm.max_tokens == 9000


# =============================================================================
# Format Response Tests
# =============================================================================


class TestResponseManagerFormatResponse:
    """Tests for format_response method."""

    def test_format_response_small_dict(
        self, response_manager: ResponseManager, sample_data_small: dict
    ):
        """Test format_response with small dict that doesn't exceed token limit.

        The method should:
        1. Convert dict to JSON with indent=2
        2. Not trigger chunking (token count < max_tokens)
        3. Return formatted JSON string

        This is test case #1 from US-4.2 requirements.
        """
        # Act
        result = response_manager.format_response(sample_data_small)

        # Assert
        assert isinstance(result, str)
        # Verify it's valid JSON
        parsed = json.loads(result)
        assert parsed == sample_data_small
        # Verify formatted with indent
        assert "\n" in result
        # Verify chunking service NOT called
        response_manager.chunking_service.create_chunked_response.assert_not_called()

    def test_format_response_small_list(
        self, response_manager: ResponseManager, sample_data_list: list
    ):
        """Test format_response with small list that doesn't exceed token limit.

        The method should:
        1. Convert list to JSON with indent=2
        2. Not trigger chunking (token count < max_tokens)
        3. Return formatted JSON string

        This verifies list handling.
        """
        # Use a smaller list to avoid triggering chunking
        small_list = sample_data_list[:5]

        # Act
        result = response_manager.format_response(small_list)

        # Assert
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == small_list
        assert "\n" in result
        response_manager.chunking_service.create_chunked_response.assert_not_called()

    def test_format_response_large_dict_auto_chunk(
        self,
        mock_token_counter: MagicMock,
        mock_chunking_service: MagicMock,
        sample_data_large: dict,
    ):
        """Test format_response with large dict exceeding token limit.

        The method should:
        1. Detect token count exceeds max_tokens
        2. Call chunking_service.create_chunked_response()
        3. Return formatted JSON of chunked response metadata

        This is test case #2 from US-4.2 requirements.
        """
        # Arrange - configure mock to return high token count
        mock_token_counter.count_tokens.return_value = 15000  # Exceeds 9000
        rm = ResponseManager(mock_token_counter, mock_chunking_service)

        # Act
        result = rm.format_response(sample_data_large, auto_chunk=True)

        # Assert
        parsed = json.loads(result)
        assert parsed["chunked_response"] is True
        assert "session_id" in parsed
        assert "total_chunks" in parsed
        # Verify chunking service WAS called
        mock_chunking_service.create_chunked_response.assert_called_once_with(sample_data_large)

    def test_format_response_large_dict_disable_auto_chunk(
        self,
        mock_token_counter: MagicMock,
        mock_chunking_service: MagicMock,
        sample_data_large: dict,
    ):
        """Test format_response with auto_chunk=False doesn't chunk large responses.

        The method should:
        1. Not trigger chunking even if token count exceeds limit
        2. Return full JSON string of original data

        This is test case #3 from US-4.2 requirements.
        """
        # Arrange - configure mock to return high token count
        mock_token_counter.count_tokens.return_value = 15000  # Exceeds 9000
        rm = ResponseManager(mock_token_counter, mock_chunking_service)

        # Act
        result = rm.format_response(sample_data_large, auto_chunk=False)

        # Assert
        parsed = json.loads(result)
        assert parsed == sample_data_large
        # Verify chunking service NOT called
        mock_chunking_service.create_chunked_response.assert_not_called()

    def test_format_response_list_exceeds_limit(
        self,
        mock_token_counter: MagicMock,
        mock_chunking_service: MagicMock,
        sample_data_list: list,
    ):
        """Test format_response with large list doesn't chunk (lists not supported).

        The method should:
        1. Not chunk list responses even if exceeding token limit
        2. Return full JSON string (ChunkingService requires dict with 'data' key)

        This verifies list limitation.
        """
        # Arrange - configure mock to return high token count
        mock_token_counter.count_tokens.return_value = 15000  # Exceeds 9000
        rm = ResponseManager(mock_token_counter, mock_chunking_service)

        # Act
        result = rm.format_response(sample_data_list, auto_chunk=True)

        # Assert
        parsed = json.loads(result)
        assert parsed == sample_data_list
        # Verify chunking service NOT called (lists can't be chunked)
        mock_chunking_service.create_chunked_response.assert_not_called()

    def test_format_response_empty_dict(self, response_manager: ResponseManager):
        """Test format_response with empty dict.

        The method should:
        1. Handle empty dict gracefully
        2. Return valid JSON string

        This is an edge case test.
        """
        # Act
        result = response_manager.format_response({})

        # Assert
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == {}

    def test_format_response_empty_list(self, response_manager: ResponseManager):
        """Test format_response with empty list.

        The method should:
        1. Handle empty list gracefully
        2. Return valid JSON string

        This is an edge case test.
        """
        # Act
        result = response_manager.format_response([])

        # Assert
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == []

    def test_format_response_nested_structures(self, response_manager: ResponseManager):
        """Test format_response with nested dicts and lists.

        The method should:
        1. Handle nested structures correctly
        2. Preserve structure in JSON output

        This verifies complex structure handling.
        """
        # Arrange
        nested_data = {
            "level1": {
                "level2": {
                    "level3": {"value": "deep"},
                    "list": [1, 2, 3],
                },
                "items": [{"id": 1}, {"id": 2}],
            }
        }

        # Act
        result = response_manager.format_response(nested_data)

        # Assert
        parsed = json.loads(result)
        assert parsed == nested_data
        assert parsed["level1"]["level2"]["level3"]["value"] == "deep"

    def test_format_response_special_characters(self, response_manager: ResponseManager):
        """Test format_response with special characters in strings.

        The method should:
        1. Handle special characters correctly
        2. Properly escape JSON special chars

        This verifies string handling.
        """
        # Arrange
        data_with_special_chars = {
            "quotes": 'He said "hello"',
            "newlines": "Line 1\nLine 2",
            "tabs": "Col1\tCol2",
            "backslash": "path\\to\\file",
        }

        # Act
        result = response_manager.format_response(data_with_special_chars)

        # Assert
        parsed = json.loads(result)
        assert parsed == data_with_special_chars

    def test_format_response_token_count_boundary_below(
        self, mock_token_counter: MagicMock, mock_chunking_service: MagicMock
    ):
        """Test format_response with token count just below max_tokens.

        The method should:
        1. Not trigger chunking when token_count = max_tokens - 1
        2. Return full JSON string

        This is test case #5 from US-4.2 requirements (boundary testing).
        """
        # Arrange
        mock_token_counter.count_tokens.return_value = 8999  # Just below 9000
        rm = ResponseManager(mock_token_counter, mock_chunking_service)
        data = {"test": "data"}

        # Act
        result = rm.format_response(data)

        # Assert
        parsed = json.loads(result)
        assert parsed == data
        mock_chunking_service.create_chunked_response.assert_not_called()

    def test_format_response_token_count_boundary_at(
        self, mock_token_counter: MagicMock, mock_chunking_service: MagicMock
    ):
        """Test format_response with token count exactly at max_tokens.

        The method should:
        1. Not trigger chunking when token_count = max_tokens (not exceeding)
        2. Return full JSON string

        This is test case #5 from US-4.2 requirements (boundary testing).
        """
        # Arrange
        mock_token_counter.count_tokens.return_value = 9000  # Exactly at limit
        rm = ResponseManager(mock_token_counter, mock_chunking_service)
        data = {"test": "data"}

        # Act
        result = rm.format_response(data)

        # Assert
        parsed = json.loads(result)
        assert parsed == data
        mock_chunking_service.create_chunked_response.assert_not_called()

    def test_format_response_token_count_boundary_above(self, mock_chunking_service: MagicMock):
        """Test format_response with token count just above max_tokens.

        The method should:
        1. Trigger chunking when token_count = max_tokens + 1
        2. Return chunked response metadata

        This is test case #5 from US-4.2 requirements (boundary testing).
        """
        # Arrange - create fresh mock with specific return value
        mock_tc = MagicMock(spec=TokenCounter)
        mock_tc.count_tokens.return_value = 9001  # Just above 9000
        rm = ResponseManager(mock_tc, mock_chunking_service)
        data = {"test": "data"}

        # Act
        result = rm.format_response(data)

        # Assert
        parsed = json.loads(result)
        assert parsed["chunked_response"] is True
        mock_chunking_service.create_chunked_response.assert_called_once()


# =============================================================================
# Format Error Tests
# =============================================================================


class TestResponseManagerFormatError:
    """Tests for format_error method."""

    def test_format_error_basic(self, response_manager: ResponseManager):
        """Test format_error with basic error type and message.

        The method should:
        1. Create error dict with error and message keys
        2. Return formatted JSON string

        This is test case #4 from US-4.2 requirements.
        """
        # Act
        result = response_manager.format_error("ValueError", "Invalid table name")

        # Assert
        parsed = json.loads(result)
        assert parsed["error"] == "ValueError"
        assert parsed["message"] == "Invalid table name"
        assert len(parsed) == 2  # Only error and message

    def test_format_error_with_kwargs(self, response_manager: ResponseManager):
        """Test format_error with additional kwargs.

        The method should:
        1. Include kwargs in error dict
        2. Return formatted JSON with all fields

        This verifies kwargs handling.
        """
        # Act
        result = response_manager.format_error(
            "Session not found",
            "The session ID does not exist",
            session_id="abc123",
        )

        # Assert
        parsed = json.loads(result)
        assert parsed["error"] == "Session not found"
        assert parsed["message"] == "The session ID does not exist"
        assert parsed["session_id"] == "abc123"

    def test_format_error_with_multiple_kwargs(self, response_manager: ResponseManager):
        """Test format_error with multiple kwargs.

        The method should:
        1. Include all kwargs in error dict
        2. Support different value types (str, int, list)

        This verifies multiple kwargs handling.
        """
        # Act
        result = response_manager.format_error(
            "QueryError",
            "Query execution failed",
            query_id=12345,
            table="test.default.users",
            affected_columns=["col1", "col2"],
        )

        # Assert
        parsed = json.loads(result)
        assert parsed["error"] == "QueryError"
        assert parsed["message"] == "Query execution failed"
        assert parsed["query_id"] == 12345
        assert parsed["table"] == "test.default.users"
        assert parsed["affected_columns"] == ["col1", "col2"]

    def test_format_error_with_nested_kwargs(self, response_manager: ResponseManager):
        """Test format_error with nested dict/list kwargs.

        The method should:
        1. Handle nested structures in kwargs
        2. Preserve structure in JSON output

        This verifies complex kwargs handling.
        """
        # Act
        result = response_manager.format_error(
            "ConfigError",
            "Invalid configuration",
            config={"host": "localhost", "port": 8080},
            errors=[{"field": "host", "issue": "unreachable"}],
        )

        # Assert
        parsed = json.loads(result)
        assert parsed["error"] == "ConfigError"
        assert parsed["config"]["host"] == "localhost"
        assert parsed["errors"][0]["field"] == "host"

    def test_format_error_json_structure(self, response_manager: ResponseManager):
        """Test format_error returns properly formatted JSON.

        The method should:
        1. Return JSON with indent=2
        2. Use correct separators (",", ":")

        This verifies JSON formatting.
        """
        # Act
        result = response_manager.format_error("TestError", "Test message")

        # Assert
        assert isinstance(result, str)
        assert "\n" in result  # Formatted with indentation
        # Verify can be parsed
        parsed = json.loads(result)
        assert parsed["error"] == "TestError"


# =============================================================================
# Token Limit Tests
# =============================================================================


class TestResponseManagerTokenLimits:
    """Tests for token limit handling and validation."""

    def test_custom_max_tokens_lower(self, mock_chunking_service: MagicMock):
        """Test ResponseManager with lower custom max_tokens.

        The method should:
        1. Use custom max_tokens for chunking threshold
        2. Trigger chunking at lower token count

        This verifies custom max_tokens functionality.
        """
        # Arrange - create fresh mock with specific return value
        mock_tc = MagicMock(spec=TokenCounter)
        mock_tc.count_tokens.return_value = 5000
        rm = ResponseManager(mock_tc, mock_chunking_service, max_tokens=3000)
        data = {"test": "data"}

        # Act
        result = rm.format_response(data)

        # Assert - should chunk because 5000 > 3000
        parsed = json.loads(result)
        assert parsed["chunked_response"] is True
        mock_chunking_service.create_chunked_response.assert_called_once()

    def test_custom_max_tokens_higher(
        self, mock_token_counter: MagicMock, mock_chunking_service: MagicMock
    ):
        """Test ResponseManager with higher custom max_tokens.

        The method should:
        1. Use custom max_tokens for chunking threshold
        2. Not trigger chunking at higher token count

        This verifies custom max_tokens functionality.
        """
        # Arrange - create RM with max_tokens=20000
        mock_token_counter.count_tokens.return_value = 15000
        rm = ResponseManager(mock_token_counter, mock_chunking_service, max_tokens=20000)
        data = {"test": "data"}

        # Act
        result = rm.format_response(data)

        # Assert - should NOT chunk because 15000 < 20000
        parsed = json.loads(result)
        assert parsed == data
        mock_chunking_service.create_chunked_response.assert_not_called()

    @pytest.mark.parametrize(
        "token_count,should_chunk",
        [
            (8999, False),  # Below limit
            (9000, False),  # At limit
            (9001, True),  # Above limit
            (10000, True),  # Well above limit
            (5000, False),  # Well below limit
        ],
    )
    def test_token_limit_boundary_testing(
        self,
        mock_chunking_service: MagicMock,
        token_count: int,
        should_chunk: bool,
    ):
        """Test token limit boundaries with parametrized token counts.

        The method should:
        1. Chunk only when token_count > max_tokens
        2. Handle boundary cases correctly

        This is parametrized boundary testing.
        """
        # Arrange - create fresh mock for each parametrized run
        mock_tc = MagicMock(spec=TokenCounter)
        mock_tc.count_tokens.return_value = token_count
        rm = ResponseManager(mock_tc, mock_chunking_service)
        data = {"test": "data"}

        # Act
        result = rm.format_response(data)

        # Assert
        parsed = json.loads(result)
        if should_chunk:
            assert parsed["chunked_response"] is True
            mock_chunking_service.create_chunked_response.assert_called()
        else:
            assert parsed == data
            mock_chunking_service.create_chunked_response.assert_not_called()

    def test_token_counter_integration(self, sample_data_small: dict):
        """Test ResponseManager with real TokenCounter.

        This integration test:
        1. Uses actual TokenCounter (not mocked)
        2. Verifies token counting works correctly
        3. Tests real token estimation

        This verifies integration with TokenCounter.
        """
        # Arrange
        token_counter = TokenCounter(model="gpt-4")
        mock_chunking = MagicMock(spec=ChunkingService)
        rm = ResponseManager(token_counter, mock_chunking)

        # Act
        result = rm.format_response(sample_data_small)

        # Assert
        parsed = json.loads(result)
        assert parsed == sample_data_small
        # Small data should not trigger chunking
        mock_chunking.create_chunked_response.assert_not_called()


# =============================================================================
# Chunking Behavior Tests
# =============================================================================


class TestResponseManagerChunkingBehavior:
    """Tests for chunking behavior verification."""

    def test_chunking_service_called_when_needed(self, mock_chunking_service: MagicMock):
        """Test chunking_service.create_chunked_response is called when needed.

        The method should:
        1. Call chunking_service when token_count > max_tokens
        2. Pass correct data to chunking_service

        This verifies chunking trigger.
        """
        # Arrange - create fresh mock with specific return value
        mock_tc = MagicMock(spec=TokenCounter)
        mock_tc.count_tokens.return_value = 15000
        rm = ResponseManager(mock_tc, mock_chunking_service)
        data = {"large": "data"}

        # Act
        rm.format_response(data)

        # Assert
        mock_chunking_service.create_chunked_response.assert_called_once_with(data)

    def test_chunking_service_not_called_small_response(
        self, mock_token_counter: MagicMock, mock_chunking_service: MagicMock
    ):
        """Test chunking_service is not called for small responses.

        The method should:
        1. Not call chunking_service when token_count <= max_tokens
        2. Return original data

        This verifies no unnecessary chunking.
        """
        # Arrange
        mock_token_counter.count_tokens.return_value = 5000
        rm = ResponseManager(mock_token_counter, mock_chunking_service)
        data = {"small": "data"}

        # Act
        rm.format_response(data)

        # Assert
        mock_chunking_service.create_chunked_response.assert_not_called()

    def test_chunking_service_not_called_when_disabled(
        self, mock_token_counter: MagicMock, mock_chunking_service: MagicMock
    ):
        """Test chunking_service is not called when auto_chunk=False.

        The method should:
        1. Not call chunking_service when auto_chunk=False
        2. Return original data even if exceeding token limit

        This verifies auto_chunk parameter.
        """
        # Arrange
        mock_token_counter.count_tokens.return_value = 15000
        rm = ResponseManager(mock_token_counter, mock_chunking_service)
        data = {"large": "data"}

        # Act
        rm.format_response(data, auto_chunk=False)

        # Assert
        mock_chunking_service.create_chunked_response.assert_not_called()

    def test_chunking_metadata_returned(self, mock_chunking_service: MagicMock):
        """Test format_response returns chunking metadata when chunked.

        The method should:
        1. Return session metadata from chunking_service
        2. Include all required metadata fields

        This verifies metadata structure.
        """
        # Arrange - create fresh mock with specific return value
        mock_tc = MagicMock(spec=TokenCounter)
        mock_tc.count_tokens.return_value = 15000
        rm = ResponseManager(mock_tc, mock_chunking_service)
        data = {"large": "data"}

        # Act
        result = rm.format_response(data)

        # Assert
        parsed = json.loads(result)
        assert parsed["chunked_response"] is True
        assert "session_id" in parsed
        assert "total_chunks" in parsed
        assert "chunk_token_amounts" in parsed
        assert "message" in parsed
        assert "instructions" in parsed


# =============================================================================
# Integration Tests
# =============================================================================


class TestResponseManagerIntegration:
    """Integration tests with real dependencies."""

    def test_integration_with_real_dependencies(self, sample_data_small: dict):
        """Test ResponseManager with real TokenCounter and ChunkingService.

        This integration test:
        1. Uses actual TokenCounter
        2. Uses actual ChunkingService
        3. Verifies end-to-end workflow

        This is test case #9 from US-4.2 requirements.
        """
        # Arrange - create with real dependencies
        token_counter = TokenCounter(model="gpt-4")
        chunking_service = ChunkingService(token_counter)
        rm = ResponseManager(token_counter, chunking_service)

        # Act
        result = rm.format_response(sample_data_small)

        # Assert
        parsed = json.loads(result)
        assert parsed == sample_data_small

    def test_integration_end_to_end_chunking(self):
        """Test end-to-end chunking workflow with real dependencies.

        This integration test:
        1. Creates large dataset
        2. Triggers chunking with real services
        3. Verifies chunked response structure

        This is test case #10 from US-4.2 requirements.
        """
        # Arrange - create with real dependencies
        token_counter = TokenCounter(model="gpt-4")
        chunking_service = ChunkingService(token_counter, max_tokens=5000)
        rm = ResponseManager(token_counter, chunking_service, max_tokens=5000)

        large_data = {
            "data": [{"id": i, "name": f"User_{i}", "description": "X" * 100} for i in range(500)],
            "schema": {"fields": [{"name": "id", "type": "integer"}]},
        }

        # Act
        result = rm.format_response(large_data)

        # Assert
        parsed = json.loads(result)
        assert parsed["chunked_response"] is True
        assert "session_id" in parsed
        assert parsed["total_chunks"] > 1

        # Verify can retrieve chunks
        session_id = parsed["session_id"]
        chunk = chunking_service.get_chunk(session_id, 1)
        assert "data" in chunk
        assert len(chunk["data"]) > 0

    def test_integration_error_formatting(self):
        """Test error formatting with real dependencies.

        This integration test:
        1. Creates ResponseManager with real dependencies
        2. Tests format_error functionality
        3. Verifies error structure

        This verifies error handling integration.
        """
        # Arrange
        token_counter = TokenCounter(model="gpt-4")
        chunking_service = ChunkingService(token_counter)
        rm = ResponseManager(token_counter, chunking_service)

        # Act
        result = rm.format_error(
            "DatabaseError",
            "Connection failed",
            host="localhost",
            port=3306,
        )

        # Assert
        parsed = json.loads(result)
        assert parsed["error"] == "DatabaseError"
        assert parsed["message"] == "Connection failed"
        assert parsed["host"] == "localhost"
        assert parsed["port"] == 3306


# =============================================================================
# Edge Cases Tests
# =============================================================================


class TestResponseManagerEdgeCases:
    """Tests for edge cases and unusual scenarios."""

    def test_none_values_in_dict(self, response_manager: ResponseManager):
        """Test format_response with None values in dict.

        The method should:
        1. Handle None values correctly
        2. Include None in JSON output as null

        This is an edge case test.
        """
        # Arrange
        data_with_none = {
            "value": None,
            "nested": {"inner": None},
            "list": [None, 1, None],
        }

        # Act
        result = response_manager.format_response(data_with_none)

        # Assert
        parsed = json.loads(result)
        assert parsed == data_with_none
        assert parsed["value"] is None
        assert parsed["nested"]["inner"] is None

    def test_unicode_characters(self, response_manager: ResponseManager):
        """Test format_response with Unicode characters.

        The method should:
        1. Handle Unicode correctly
        2. Preserve Unicode in JSON output

        This is an edge case test.
        """
        # Arrange
        unicode_data = {
            "english": "Hello",
            "chinese": "你好",
            "arabic": "مرحبا",
            "emoji": "🎉🚀",
            "mixed": "Test 测试 🔥",
        }

        # Act
        result = response_manager.format_response(unicode_data)

        # Assert
        parsed = json.loads(result)
        assert parsed == unicode_data
        assert parsed["chinese"] == "你好"
        assert parsed["emoji"] == "🎉🚀"

    def test_very_large_strings(
        self, mock_token_counter: MagicMock, mock_chunking_service: MagicMock
    ):
        """Test format_response with very large string values.

        The method should:
        1. Handle large strings correctly
        2. Trigger chunking if total exceeds limit

        This is an edge case test.
        """
        # Arrange
        mock_token_counter.count_tokens.return_value = 15000
        rm = ResponseManager(mock_token_counter, mock_chunking_service)
        data = {"large_text": "A" * 50000}  # Very large string

        # Act
        result = rm.format_response(data)

        # Assert
        parsed = json.loads(result)
        # Should trigger chunking due to token count
        assert parsed["chunked_response"] is True

    def test_deeply_nested_structures(self, response_manager: ResponseManager):
        """Test format_response with deeply nested structures.

        The method should:
        1. Handle deep nesting correctly
        2. Preserve structure at all levels

        This is an edge case test.
        """

        # Arrange - create 10 levels of nesting
        def create_nested(depth):
            if depth == 0:
                return {"value": "leaf"}
            return {"level": depth, "child": create_nested(depth - 1)}

        deeply_nested = create_nested(10)

        # Act
        result = response_manager.format_response(deeply_nested)

        # Assert
        parsed = json.loads(result)
        assert parsed == deeply_nested
        # Verify can access deep value
        current = parsed
        for _ in range(10):
            current = current["child"]
        assert current["value"] == "leaf"
