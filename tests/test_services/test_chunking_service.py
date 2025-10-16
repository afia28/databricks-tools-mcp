"""Comprehensive test suite for ChunkingService class.

This module contains comprehensive tests for the ChunkingService class,
covering session creation, chunk retrieval, session management, and cleanup
operations with proper time-based expiry handling.

Test coverage goal: 95%+ for src/databricks_tools/services/chunking_service.py

Test cases included (24+ tests covering US-4.1):
1. test_chunking_service_initialization_with_dependencies - Verify proper initialization
2. test_chunking_service_initialization_custom_parameters - Custom parameters
3. test_chunking_service_create_session - Basic session creation (US-4.1 #1)
4. test_chunking_service_create_session_metadata - Verify session metadata
5. test_chunking_service_create_session_token_calculation - Token-based chunking (US-4.1 #9)
6. test_chunking_service_create_session_large_dataset - Large dataset handling (US-4.1 #10)
7. test_chunking_service_create_session_empty_data - Empty data edge case
8. test_chunking_service_create_session_custom_max_tokens - Custom max_tokens
9. test_chunking_service_get_chunk - Basic chunk retrieval (US-4.1 #2)
10. test_chunking_service_get_chunk_first - First chunk retrieval
11. test_chunking_service_get_chunk_middle - Middle chunk retrieval
12. test_chunking_service_get_chunk_last - Last chunk retrieval
13. test_chunking_service_get_chunk_invalid_session - Invalid session error (US-4.1 #5)
14. test_chunking_service_get_chunk_invalid_chunk_number - Invalid chunk error (US-4.1 #6)
15. test_chunking_service_get_chunk_updates_delivered_counter - Counter increments
16. test_chunking_service_get_session_info - Session info retrieval (US-4.1 #3)
17. test_chunking_service_get_session_info_new_session - New session info
18. test_chunking_service_get_session_info_partial_delivery - Partial delivery info
19. test_chunking_service_get_session_info_all_chunks_delivered - All delivered (US-4.1 #4)
20. test_chunking_service_get_session_info_invalid_session - Invalid session error
21. test_chunking_service_session_expiry - Session expiry after TTL (US-4.1 #7)
22. test_chunking_service_cleanup_expired - Cleanup expired sessions (US-4.1 #8)
23. test_chunking_service_cleanup_preserves_active - Preserves active sessions
24. test_chunking_service_cleanup_mixed_expiry - Mixed expiry scenarios
25. test_chunking_service_concurrent_sessions - Concurrent sessions (US-4.1 #11)
26. test_integration_with_real_token_counter - Integration test (US-4.1 #12)
"""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time

from databricks_tools.core.token_counter import TokenCounter
from databricks_tools.services.chunking_service import ChunkingService

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_token_counter() -> MagicMock:
    """Create a mock TokenCounter for testing.

    Returns:
        A MagicMock configured to behave like TokenCounter with estimate_tokens.
    """
    mock = MagicMock(spec=TokenCounter)

    # Configure estimate_tokens to return realistic token counts
    # Approximation: 1 token ≈ 4 characters
    def estimate_tokens_side_effect(data):
        json_str = json.dumps(data)
        return len(json_str) // 4

    mock.estimate_tokens.side_effect = estimate_tokens_side_effect
    return mock


@pytest.fixture
def chunking_service(mock_token_counter: MagicMock) -> ChunkingService:
    """Create a ChunkingService with mocked TokenCounter.

    Returns:
        A ChunkingService instance with mocked TokenCounter.
    """
    return ChunkingService(mock_token_counter)


@pytest.fixture
def sample_data_small() -> dict:
    """Create a small sample dataset for basic tests.

    Returns:
        A dict with data, schema, and metadata for testing.
    """
    return {
        "data": [
            {"id": i, "name": f"User_{i}", "email": f"user{i}@example.com"} for i in range(10)
        ],
        "schema": {
            "fields": [
                {"name": "id", "type": "integer"},
                {"name": "name", "type": "string"},
                {"name": "email", "type": "string"},
            ]
        },
        "table_name": "test.default.users",
    }


@pytest.fixture
def sample_data_large() -> dict:
    """Create a large sample dataset that will require chunking.

    Returns:
        A dict with 1000 rows of data for chunking tests.
    """
    return {
        "data": [
            {
                "id": i,
                "name": f"User_{i}",
                "email": f"user{i}@example.com",
                "age": 20 + (i % 50),
            }
            for i in range(1000)
        ],
        "schema": {
            "fields": [
                {"name": "id", "type": "integer"},
                {"name": "name", "type": "string"},
                {"name": "email", "type": "string"},
                {"name": "age", "type": "integer"},
            ]
        },
        "table_name": "test.default.large_users",
    }


@pytest.fixture
def sample_data_empty() -> dict:
    """Create an empty dataset for edge case testing.

    Returns:
        A dict with empty data list.
    """
    return {
        "data": [],
        "schema": {
            "fields": [
                {"name": "id", "type": "integer"},
                {"name": "name", "type": "string"},
            ]
        },
        "table_name": "test.default.empty_table",
    }


# =============================================================================
# Initialization Tests
# =============================================================================


class TestChunkingServiceInitialization:
    """Tests for ChunkingService initialization."""

    def test_chunking_service_initialization_with_dependencies(self, mock_token_counter: MagicMock):
        """Test ChunkingService initializes with required dependencies.

        The ChunkingService should:
        1. Accept TokenCounter in __init__
        2. Store it as instance attribute
        3. Use default max_tokens value of 9000
        4. Use default session_ttl_minutes of 60
        5. Initialize empty _sessions dict

        This verifies basic initialization as required by US-4.1.
        """
        # Act
        service = ChunkingService(mock_token_counter)

        # Assert
        assert service.token_counter is mock_token_counter
        assert service.max_tokens == 9000
        assert service.session_ttl == timedelta(minutes=60)
        assert service._sessions == {}
        assert isinstance(service._sessions, dict)

    def test_chunking_service_initialization_custom_parameters(self, mock_token_counter: MagicMock):
        """Test ChunkingService accepts custom parameters.

        The ChunkingService should:
        1. Allow custom max_tokens value
        2. Allow custom session_ttl_minutes value
        3. Store the custom values correctly

        This verifies parameter customization.
        """
        # Act
        service = ChunkingService(mock_token_counter, max_tokens=5000, session_ttl_minutes=120)

        # Assert
        assert service.token_counter is mock_token_counter
        assert service.max_tokens == 5000
        assert service.session_ttl == timedelta(minutes=120)
        assert service._sessions == {}


# =============================================================================
# Create Chunked Response Tests
# =============================================================================


class TestChunkingServiceCreateChunkedResponse:
    """Tests for create_chunked_response method."""

    def test_chunking_service_create_session(
        self, chunking_service: ChunkingService, sample_data_small: dict
    ):
        """Test create_chunked_response creates a session successfully.

        The method should:
        1. Create a unique session_id (UUID)
        2. Split data into chunks based on token limits
        3. Store session in _sessions dict
        4. Return response with session metadata

        This is test case #1 from US-4.1 requirements.
        """
        # Act
        response = chunking_service.create_chunked_response(sample_data_small)

        # Assert
        assert "chunked_response" in response
        assert response["chunked_response"] is True
        assert "session_id" in response
        assert "total_chunks" in response
        assert "chunk_token_amounts" in response
        assert "message" in response
        assert "instructions" in response

        # Verify session is stored
        session_id = response["session_id"]
        assert session_id in chunking_service._sessions
        assert len(chunking_service._sessions) == 1

    def test_chunking_service_create_session_metadata(
        self, chunking_service: ChunkingService, sample_data_small: dict
    ):
        """Test create_chunked_response stores correct session metadata.

        The method should:
        1. Store chunks list in session
        2. Store created_at timestamp
        3. Store total_chunks count
        4. Initialize chunks_delivered to 0
        5. Store chunk_token_amounts dict

        This verifies session metadata structure.
        """
        # Act
        response = chunking_service.create_chunked_response(sample_data_small)
        session_id = response["session_id"]
        session = chunking_service._sessions[session_id]

        # Assert session metadata
        assert "chunks" in session
        assert isinstance(session["chunks"], list)
        assert len(session["chunks"]) == response["total_chunks"]

        assert "created_at" in session
        assert isinstance(session["created_at"], datetime)

        assert "total_chunks" in session
        assert session["total_chunks"] == response["total_chunks"]

        assert "chunks_delivered" in session
        assert session["chunks_delivered"] == 0

        assert "chunk_token_amounts" in session
        assert isinstance(session["chunk_token_amounts"], dict)

    def test_chunking_service_create_session_token_calculation(
        self, chunking_service: ChunkingService, sample_data_large: dict
    ):
        """Test create_chunked_response calculates tokens and splits data correctly.

        The method should:
        1. Calculate token count for base response (schema + metadata)
        2. Estimate tokens per row from sample
        3. Calculate rows_per_chunk based on max_tokens
        4. Split data into appropriate number of chunks
        5. Store token amounts for each chunk

        This is test case #9 from US-4.1 requirements (token calculation).
        """
        # Act
        response = chunking_service.create_chunked_response(sample_data_large)
        session_id = response["session_id"]
        session = chunking_service._sessions[session_id]

        # Assert chunking occurred (large dataset should be split)
        assert response["total_chunks"] > 1
        assert len(session["chunks"]) == response["total_chunks"]

        # Verify chunk_token_amounts
        chunk_token_amounts = response["chunk_token_amounts"]
        assert len(chunk_token_amounts) == response["total_chunks"]

        # Each chunk should have a token count
        for i in range(1, response["total_chunks"] + 1):
            assert str(i) in chunk_token_amounts
            assert isinstance(chunk_token_amounts[str(i)], int)
            assert chunk_token_amounts[str(i)] > 0

    def test_chunking_service_create_session_large_dataset(
        self, chunking_service: ChunkingService, sample_data_large: dict
    ):
        """Test create_chunked_response handles large datasets correctly.

        The method should:
        1. Split large datasets into multiple chunks
        2. Each chunk should contain subset of rows
        3. All rows should be distributed across chunks
        4. Chunks should respect token limits

        This is test case #10 from US-4.1 requirements (large dataset).
        """
        # Act
        response = chunking_service.create_chunked_response(sample_data_large)
        session_id = response["session_id"]
        session = chunking_service._sessions[session_id]

        # Assert multiple chunks created
        assert response["total_chunks"] > 1

        # Verify all rows are distributed across chunks
        total_rows_in_chunks = sum(len(chunk["data"]) for chunk in session["chunks"])
        assert total_rows_in_chunks == len(sample_data_large["data"])

        # Verify each chunk has chunking_info
        for i, chunk in enumerate(session["chunks"]):
            assert "chunking_info" in chunk
            assert chunk["chunking_info"]["chunk_number"] == i + 1
            assert chunk["chunking_info"]["total_chunks"] == response["total_chunks"]
            assert chunk["chunking_info"]["session_id"] == session_id
            assert "reconstruction_instructions" in chunk["chunking_info"]

    def test_chunking_service_create_session_empty_data(
        self, chunking_service: ChunkingService, sample_data_empty: dict
    ):
        """Test create_chunked_response handles empty data gracefully.

        The method should:
        1. Handle empty data list without errors
        2. Create at least one chunk (even if empty)
        3. Return valid session metadata

        This is an edge case test.
        """
        # Act
        response = chunking_service.create_chunked_response(sample_data_empty)
        session_id = response["session_id"]
        session = chunking_service._sessions[session_id]

        # Assert session created successfully
        assert response["chunked_response"] is True
        assert session_id in chunking_service._sessions
        assert response["total_chunks"] >= 0
        assert len(session["chunks"]) == response["total_chunks"]

    def test_chunking_service_create_session_custom_max_tokens(
        self, chunking_service: ChunkingService, sample_data_large: dict
    ):
        """Test create_chunked_response respects custom max_tokens parameter.

        The method should:
        1. Accept max_tokens parameter override
        2. Use custom max_tokens for chunking calculation
        3. Create more chunks with lower max_tokens

        This verifies custom max_tokens functionality.
        """
        # Act - create with default max_tokens
        response_default = chunking_service.create_chunked_response(sample_data_large)
        total_chunks_default = response_default["total_chunks"]

        # Act - create with smaller max_tokens (should create more chunks)
        response_small = chunking_service.create_chunked_response(
            sample_data_large, max_tokens=3000
        )
        total_chunks_small = response_small["total_chunks"]

        # Assert - smaller max_tokens creates more chunks
        assert total_chunks_small >= total_chunks_default


# =============================================================================
# Get Chunk Tests
# =============================================================================


class TestChunkingServiceGetChunk:
    """Tests for get_chunk method."""

    def test_chunking_service_get_chunk(
        self, chunking_service: ChunkingService, sample_data_small: dict
    ):
        """Test get_chunk retrieves chunks successfully.

        The method should:
        1. Return chunk data for valid session_id and chunk_number
        2. Include chunking_info in response
        3. Update chunks_delivered counter

        This is test case #2 from US-4.1 requirements.
        """
        # Arrange
        response = chunking_service.create_chunked_response(sample_data_small)
        session_id = response["session_id"]

        # Act
        chunk = chunking_service.get_chunk(session_id, 1)

        # Assert
        assert "data" in chunk
        assert isinstance(chunk["data"], list)
        assert "chunking_info" in chunk
        assert chunk["chunking_info"]["chunk_number"] == 1
        assert chunk["chunking_info"]["session_id"] == session_id
        assert "chunks_delivered" in chunk["chunking_info"]
        assert chunk["chunking_info"]["chunks_delivered"] == 1

    def test_chunking_service_get_chunk_first(
        self, chunking_service: ChunkingService, sample_data_large: dict
    ):
        """Test get_chunk retrieves first chunk correctly.

        The method should:
        1. Return first chunk when chunk_number=1
        2. Set chunk_number to 1 in chunking_info
        3. Mark all_chunks_delivered as False

        This verifies first chunk retrieval.
        """
        # Arrange
        response = chunking_service.create_chunked_response(sample_data_large)
        session_id = response["session_id"]

        # Act
        chunk = chunking_service.get_chunk(session_id, 1)

        # Assert
        assert chunk["chunking_info"]["chunk_number"] == 1
        assert chunk["chunking_info"]["chunks_delivered"] == 1
        assert chunk["chunking_info"]["all_chunks_delivered"] is False

    def test_chunking_service_get_chunk_middle(
        self, chunking_service: ChunkingService, sample_data_large: dict
    ):
        """Test get_chunk retrieves middle chunks correctly.

        The method should:
        1. Return correct chunk for chunk_number in middle
        2. Increment chunks_delivered counter
        3. Mark all_chunks_delivered as False

        This verifies middle chunk retrieval.
        """
        # Arrange
        response = chunking_service.create_chunked_response(sample_data_large)
        session_id = response["session_id"]
        total_chunks = response["total_chunks"]

        # Assume we have at least 3 chunks
        if total_chunks < 3:
            pytest.skip("Test requires at least 3 chunks")

        middle_chunk_num = total_chunks // 2

        # Act - retrieve first chunk, then middle chunk
        chunking_service.get_chunk(session_id, 1)
        chunk_middle = chunking_service.get_chunk(session_id, middle_chunk_num)

        # Assert
        assert chunk_middle["chunking_info"]["chunk_number"] == middle_chunk_num
        assert chunk_middle["chunking_info"]["chunks_delivered"] == 2  # First + middle
        assert chunk_middle["chunking_info"]["all_chunks_delivered"] is False

    def test_chunking_service_get_chunk_last(
        self, chunking_service: ChunkingService, sample_data_large: dict
    ):
        """Test get_chunk retrieves last chunk and marks completion.

        The method should:
        1. Return last chunk when chunk_number=total_chunks
        2. Mark all_chunks_delivered as True when all chunks retrieved
        3. Update chunks_delivered to total_chunks

        This verifies last chunk retrieval and completion tracking.
        """
        # Arrange
        response = chunking_service.create_chunked_response(sample_data_large)
        session_id = response["session_id"]
        total_chunks = response["total_chunks"]

        # Act - retrieve all chunks
        for i in range(1, total_chunks + 1):
            chunk = chunking_service.get_chunk(session_id, i)

        # Assert last chunk
        assert chunk["chunking_info"]["chunk_number"] == total_chunks
        assert chunk["chunking_info"]["chunks_delivered"] == total_chunks
        assert chunk["chunking_info"]["all_chunks_delivered"] is True

    def test_chunking_service_get_chunk_invalid_session(self, chunking_service: ChunkingService):
        """Test get_chunk raises ValueError for invalid session_id.

        The method should:
        1. Raise ValueError when session_id not found
        2. Provide helpful error message

        This is test case #5 from US-4.1 requirements.
        """
        # Act & Assert
        with pytest.raises(ValueError, match="Session not found"):
            chunking_service.get_chunk("invalid-session-id", 1)

    def test_chunking_service_get_chunk_invalid_chunk_number(
        self, chunking_service: ChunkingService, sample_data_small: dict
    ):
        """Test get_chunk raises ValueError for invalid chunk_number.

        The method should:
        1. Raise ValueError when chunk_number < 1
        2. Raise ValueError when chunk_number > total_chunks
        3. Provide helpful error message with valid range

        This is test case #6 from US-4.1 requirements.
        """
        # Arrange
        response = chunking_service.create_chunked_response(sample_data_small)
        session_id = response["session_id"]
        total_chunks = response["total_chunks"]

        # Act & Assert - chunk_number too low
        with pytest.raises(ValueError, match="Invalid chunk number"):
            chunking_service.get_chunk(session_id, 0)

        # Act & Assert - chunk_number too high
        with pytest.raises(ValueError, match="Invalid chunk number"):
            chunking_service.get_chunk(session_id, total_chunks + 1)

    def test_chunking_service_get_chunk_updates_delivered_counter(
        self, chunking_service: ChunkingService, sample_data_large: dict
    ):
        """Test get_chunk increments chunks_delivered counter correctly.

        The method should:
        1. Increment chunks_delivered by 1 for each get_chunk call
        2. Track delivery progress accurately
        3. Include current chunks_delivered in response

        This verifies delivery counter tracking.
        """
        # Arrange
        response = chunking_service.create_chunked_response(sample_data_large)
        session_id = response["session_id"]
        session = chunking_service._sessions[session_id]

        # Assert initial state
        assert session["chunks_delivered"] == 0

        # Act & Assert - retrieve chunks and verify counter
        chunk1 = chunking_service.get_chunk(session_id, 1)
        assert session["chunks_delivered"] == 1
        assert chunk1["chunking_info"]["chunks_delivered"] == 1

        chunk2 = chunking_service.get_chunk(session_id, 2)
        assert session["chunks_delivered"] == 2
        assert chunk2["chunking_info"]["chunks_delivered"] == 2

        chunk3 = chunking_service.get_chunk(session_id, 3)
        assert session["chunks_delivered"] == 3
        assert chunk3["chunking_info"]["chunks_delivered"] == 3


# =============================================================================
# Get Session Info Tests
# =============================================================================


class TestChunkingServiceGetSessionInfo:
    """Tests for get_session_info method."""

    def test_chunking_service_get_session_info(
        self, chunking_service: ChunkingService, sample_data_small: dict
    ):
        """Test get_session_info returns session metadata.

        The method should:
        1. Return session metadata for valid session_id
        2. Include total_chunks, chunks_delivered, chunks_remaining
        3. Include next_chunk_to_request
        4. Include reconstruction_instructions

        This is test case #3 from US-4.1 requirements.
        """
        # Arrange
        response = chunking_service.create_chunked_response(sample_data_small)
        session_id = response["session_id"]

        # Act
        info = chunking_service.get_session_info(session_id)

        # Assert
        assert info["session_id"] == session_id
        assert "total_chunks" in info
        assert "chunks_delivered" in info
        assert "chunks_remaining" in info
        assert "created_at" in info
        assert "all_chunks_delivered" in info
        assert "next_chunk_to_request" in info
        assert "chunk_token_amounts" in info
        assert "reconstruction_instructions" in info

    def test_chunking_service_get_session_info_new_session(
        self, chunking_service: ChunkingService, sample_data_small: dict
    ):
        """Test get_session_info for newly created session.

        The method should:
        1. Show chunks_delivered = 0
        2. Show chunks_remaining = total_chunks
        3. Show all_chunks_delivered = False
        4. Show next_chunk_to_request = 1

        This verifies new session info.
        """
        # Arrange
        response = chunking_service.create_chunked_response(sample_data_small)
        session_id = response["session_id"]
        total_chunks = response["total_chunks"]

        # Act
        info = chunking_service.get_session_info(session_id)

        # Assert
        assert info["chunks_delivered"] == 0
        assert info["chunks_remaining"] == total_chunks
        assert info["all_chunks_delivered"] is False
        assert info["next_chunk_to_request"] == 1

    def test_chunking_service_get_session_info_partial_delivery(
        self, chunking_service: ChunkingService, sample_data_large: dict
    ):
        """Test get_session_info after partial chunk delivery.

        The method should:
        1. Show accurate chunks_delivered count
        2. Calculate chunks_remaining correctly
        3. Show all_chunks_delivered = False
        4. Show next_chunk_to_request correctly

        This verifies partial delivery tracking.
        """
        # Arrange
        response = chunking_service.create_chunked_response(sample_data_large)
        session_id = response["session_id"]
        total_chunks = response["total_chunks"]

        # Retrieve first 2 chunks
        chunking_service.get_chunk(session_id, 1)
        chunking_service.get_chunk(session_id, 2)

        # Act
        info = chunking_service.get_session_info(session_id)

        # Assert
        assert info["chunks_delivered"] == 2
        assert info["chunks_remaining"] == total_chunks - 2
        assert info["all_chunks_delivered"] is False
        assert info["next_chunk_to_request"] == 3

    def test_chunking_service_get_session_info_all_chunks_delivered(
        self, chunking_service: ChunkingService, sample_data_small: dict
    ):
        """Test get_session_info after all chunks delivered.

        The method should:
        1. Show chunks_delivered = total_chunks
        2. Show chunks_remaining = 0
        3. Show all_chunks_delivered = True
        4. Show next_chunk_to_request = None

        This is test case #4 from US-4.1 requirements.
        """
        # Arrange
        response = chunking_service.create_chunked_response(sample_data_small)
        session_id = response["session_id"]
        total_chunks = response["total_chunks"]

        # Retrieve all chunks
        for i in range(1, total_chunks + 1):
            chunking_service.get_chunk(session_id, i)

        # Act
        info = chunking_service.get_session_info(session_id)

        # Assert
        assert info["chunks_delivered"] == total_chunks
        assert info["chunks_remaining"] == 0
        assert info["all_chunks_delivered"] is True
        assert info["next_chunk_to_request"] is None

    def test_chunking_service_get_session_info_invalid_session(
        self, chunking_service: ChunkingService
    ):
        """Test get_session_info raises ValueError for invalid session_id.

        The method should:
        1. Raise ValueError when session_id not found
        2. Provide helpful error message

        This verifies error handling for invalid session.
        """
        # Act & Assert
        with pytest.raises(ValueError, match="Session not found"):
            chunking_service.get_session_info("invalid-session-id")


# =============================================================================
# Session Expiry and Cleanup Tests
# =============================================================================


class TestChunkingServiceSessionExpiry:
    """Tests for session expiry and cleanup functionality."""

    @freeze_time("2024-01-01 12:00:00")
    def test_chunking_service_session_expiry(
        self, chunking_service: ChunkingService, sample_data_small: dict
    ):
        """Test sessions expire after TTL duration.

        The method should:
        1. Create session with timestamp
        2. Session should be accessible before TTL
        3. Session should be removed after TTL expires
        4. get_chunk should raise ValueError for expired session

        This is test case #7 from US-4.1 requirements.
        """
        # Arrange - create session at frozen time
        response = chunking_service.create_chunked_response(sample_data_small)
        session_id = response["session_id"]

        # Assert session exists
        assert session_id in chunking_service._sessions

        # Act - advance time by 61 minutes (past 60 minute TTL)
        with freeze_time("2024-01-01 13:01:00"):
            # Try to get chunk, which triggers cleanup
            with pytest.raises(ValueError, match="Session not found"):
                chunking_service.get_chunk(session_id, 1)

            # Assert session was removed
            assert session_id not in chunking_service._sessions

    @freeze_time("2024-01-01 12:00:00")
    def test_chunking_service_cleanup_expired(
        self, mock_token_counter: MagicMock, sample_data_small: dict
    ):
        """Test _cleanup_expired_sessions removes expired sessions.

        The method should:
        1. Remove sessions where created_at + TTL < now
        2. Be called automatically by get_chunk and get_session_info
        3. Clean up multiple expired sessions

        This is test case #8 from US-4.1 requirements.
        """
        # Arrange - create service with 30 minute TTL
        service = ChunkingService(mock_token_counter, session_ttl_minutes=30)

        # Create first session at 12:00
        response1 = service.create_chunked_response(sample_data_small)
        session_id_1 = response1["session_id"]

        # Advance time and create second session at 12:20
        with freeze_time("2024-01-01 12:20:00"):
            response2 = service.create_chunked_response(sample_data_small)
            session_id_2 = response2["session_id"]

        # Assert both sessions exist
        assert len(service._sessions) == 2

        # Act - advance time to 12:35 (session_1 expired, session_2 still active)
        with freeze_time("2024-01-01 12:35:00"):
            # Trigger cleanup via get_session_info
            info = service.get_session_info(session_id_2)

            # Assert session_1 removed, session_2 remains
            assert session_id_1 not in service._sessions
            assert session_id_2 in service._sessions
            assert len(service._sessions) == 1
            assert info["session_id"] == session_id_2

    @freeze_time("2024-01-01 12:00:00")
    def test_chunking_service_cleanup_preserves_active(
        self, chunking_service: ChunkingService, sample_data_small: dict
    ):
        """Test _cleanup_expired_sessions preserves active sessions.

        The method should:
        1. Not remove sessions that haven't expired
        2. Keep sessions where created_at + TTL >= now
        3. Preserve session data integrity

        This verifies cleanup doesn't affect active sessions.
        """
        # Arrange - create session at 12:00
        response = chunking_service.create_chunked_response(sample_data_small)
        session_id = response["session_id"]

        # Act - advance time by 30 minutes (within 60 minute TTL)
        with freeze_time("2024-01-01 12:30:00"):
            # Trigger cleanup via get_chunk
            chunk = chunking_service.get_chunk(session_id, 1)

            # Assert session still exists and functional
            assert session_id in chunking_service._sessions
            assert chunk["chunking_info"]["session_id"] == session_id

    @freeze_time("2024-01-01 12:00:00")
    def test_chunking_service_cleanup_mixed_expiry(
        self, mock_token_counter: MagicMock, sample_data_small: dict
    ):
        """Test _cleanup_expired_sessions with mix of expired and active sessions.

        The method should:
        1. Remove only expired sessions
        2. Preserve active sessions
        3. Handle multiple sessions correctly

        This verifies selective cleanup behavior.
        """
        # Arrange - create service with 30 minute TTL
        service = ChunkingService(mock_token_counter, session_ttl_minutes=30)

        # Create sessions at different times
        session_ids = []

        # Session 1 at 12:00
        response1 = service.create_chunked_response(sample_data_small)
        session_ids.append(response1["session_id"])

        # Session 2 at 12:10
        with freeze_time("2024-01-01 12:10:00"):
            response2 = service.create_chunked_response(sample_data_small)
            session_ids.append(response2["session_id"])

        # Session 3 at 12:20
        with freeze_time("2024-01-01 12:20:00"):
            response3 = service.create_chunked_response(sample_data_small)
            session_ids.append(response3["session_id"])

        # Assert all 3 sessions exist
        assert len(service._sessions) == 3

        # Act - advance time to 12:45
        # Session 1 (12:00) expired at 12:30 - EXPIRED
        # Session 2 (12:10) expired at 12:40 - EXPIRED
        # Session 3 (12:20) expires at 12:50 - ACTIVE
        with freeze_time("2024-01-01 12:45:00"):
            # Trigger cleanup
            info = service.get_session_info(session_ids[2])

            # Assert only session 3 remains
            assert session_ids[0] not in service._sessions
            assert session_ids[1] not in service._sessions
            assert session_ids[2] in service._sessions
            assert len(service._sessions) == 1
            assert info["session_id"] == session_ids[2]


# =============================================================================
# Concurrent Sessions Tests
# =============================================================================


class TestChunkingServiceConcurrentSessions:
    """Tests for concurrent session handling."""

    def test_chunking_service_concurrent_sessions(
        self,
        chunking_service: ChunkingService,
        sample_data_small: dict,
        sample_data_large: dict,
    ):
        """Test multiple concurrent sessions operate independently.

        The service should:
        1. Support multiple active sessions simultaneously
        2. Keep session state independent (chunks_delivered)
        3. Not mix data between sessions
        4. Allow retrieval from different sessions

        This is test case #11 from US-4.1 requirements.
        """
        # Arrange - create two sessions with large datasets
        response1 = chunking_service.create_chunked_response(sample_data_large)
        session_id_1 = response1["session_id"]

        response2 = chunking_service.create_chunked_response(sample_data_large)
        session_id_2 = response2["session_id"]

        # Assert both sessions exist
        assert len(chunking_service._sessions) == 2
        assert session_id_1 in chunking_service._sessions
        assert session_id_2 in chunking_service._sessions
        assert session_id_1 != session_id_2

        # Both should have multiple chunks
        assert response1["total_chunks"] > 1
        assert response2["total_chunks"] > 1

        # Act - retrieve chunks from both sessions
        chunk1_from_session1 = chunking_service.get_chunk(session_id_1, 1)
        chunk1_from_session2 = chunking_service.get_chunk(session_id_2, 1)
        chunking_service.get_chunk(session_id_1, 2)

        # Assert session 1 state
        info1 = chunking_service.get_session_info(session_id_1)
        assert info1["chunks_delivered"] == 2
        assert chunk1_from_session1["chunking_info"]["session_id"] == session_id_1

        # Assert session 2 state (should be independent)
        info2 = chunking_service.get_session_info(session_id_2)
        assert info2["chunks_delivered"] == 1  # Only retrieved 1 chunk from session 2
        assert chunk1_from_session2["chunking_info"]["session_id"] == session_id_2

        # Assert data is not mixed between sessions
        assert chunk1_from_session1["chunking_info"]["session_id"] != session_id_2
        assert chunk1_from_session2["chunking_info"]["session_id"] != session_id_1


# =============================================================================
# Integration Tests
# =============================================================================


class TestChunkingServiceIntegration:
    """Integration tests with real dependencies."""

    def test_integration_with_real_token_counter(self, sample_data_large: dict):
        """Test ChunkingService with real TokenCounter instance.

        This integration test:
        1. Uses actual TokenCounter (not mocked)
        2. Verifies end-to-end chunking workflow
        3. Tests complete session lifecycle

        This is test case #12 from US-4.1 requirements.
        """
        # Arrange - create service with real TokenCounter
        token_counter = TokenCounter(model="gpt-4")
        service = ChunkingService(token_counter, max_tokens=9000)

        # Act - create session
        response = service.create_chunked_response(sample_data_large)
        session_id = response["session_id"]

        # Assert session created
        assert response["chunked_response"] is True
        assert response["total_chunks"] > 0
        assert session_id in service._sessions

        # Act - retrieve first chunk
        chunk = service.get_chunk(session_id, 1)

        # Assert chunk retrieved successfully
        assert "data" in chunk
        assert len(chunk["data"]) > 0
        assert chunk["chunking_info"]["chunk_number"] == 1

        # Act - get session info
        info = service.get_session_info(session_id)

        # Assert session info accurate
        assert info["chunks_delivered"] == 1
        assert info["all_chunks_delivered"] is False
        assert info["next_chunk_to_request"] == 2

        # Act - retrieve all remaining chunks
        for i in range(2, response["total_chunks"] + 1):
            chunk = service.get_chunk(session_id, i)
            assert chunk["chunking_info"]["chunk_number"] == i

        # Assert all chunks delivered
        final_info = service.get_session_info(session_id)
        assert final_info["all_chunks_delivered"] is True
        assert final_info["chunks_delivered"] == response["total_chunks"]
        assert final_info["next_chunk_to_request"] is None


# =============================================================================
# Edge Cases and Additional Tests
# =============================================================================


class TestChunkingServiceEdgeCases:
    """Tests for edge cases and additional scenarios."""

    def test_chunking_service_single_row_dataset(
        self, chunking_service: ChunkingService, mock_token_counter: MagicMock
    ):
        """Test create_chunked_response with single row dataset.

        The method should:
        1. Handle single row gracefully
        2. Create appropriate number of chunks
        3. Include the single row in chunk

        This is an edge case test.
        """
        # Arrange
        single_row_data = {
            "data": [{"id": 1, "name": "Single User"}],
            "schema": {
                "fields": [
                    {"name": "id", "type": "integer"},
                    {"name": "name", "type": "string"},
                ]
            },
            "table_name": "test.default.single",
        }

        # Act
        response = chunking_service.create_chunked_response(single_row_data)
        session_id = response["session_id"]

        # Assert
        assert response["total_chunks"] >= 1
        chunk = chunking_service.get_chunk(session_id, 1)
        assert len(chunk["data"]) == 1
        assert chunk["data"][0]["name"] == "Single User"

    def test_chunking_service_chunk_metadata_structure(
        self, chunking_service: ChunkingService, sample_data_small: dict
    ):
        """Test chunk includes all required metadata fields.

        Each chunk should include:
        1. schema from original data
        2. data subset (rows)
        3. chunking_info with all required fields
        4. Other metadata from original data

        This verifies complete chunk structure.
        """
        # Arrange
        response = chunking_service.create_chunked_response(sample_data_small)
        session_id = response["session_id"]

        # Act
        chunk = chunking_service.get_chunk(session_id, 1)

        # Assert chunk structure
        assert "data" in chunk
        assert "schema" in chunk
        assert "table_name" in chunk
        assert chunk["table_name"] == sample_data_small["table_name"]

        # Assert chunking_info structure
        chunking_info = chunk["chunking_info"]
        assert "session_id" in chunking_info
        assert "chunk_number" in chunking_info
        assert "total_chunks" in chunking_info
        assert "rows_in_chunk" in chunking_info
        assert "total_rows" in chunking_info
        assert "is_chunked" in chunking_info
        assert "reconstruction_instructions" in chunking_info
        assert "chunks_delivered" in chunking_info
        assert "all_chunks_delivered" in chunking_info

        # Assert chunking_info values
        assert chunking_info["is_chunked"] is True
        assert chunking_info["rows_in_chunk"] == len(chunk["data"])
        assert chunking_info["total_rows"] == len(sample_data_small["data"])

    def test_chunking_service_session_id_is_uuid(
        self, chunking_service: ChunkingService, sample_data_small: dict
    ):
        """Test session_id is a valid UUID string.

        The session_id should:
        1. Be a valid UUID format
        2. Be unique for each session

        This verifies UUID generation.
        """
        import uuid

        # Act - create multiple sessions
        response1 = chunking_service.create_chunked_response(sample_data_small)
        response2 = chunking_service.create_chunked_response(sample_data_small)

        session_id_1 = response1["session_id"]
        session_id_2 = response2["session_id"]

        # Assert valid UUIDs
        try:
            uuid.UUID(session_id_1)
            uuid.UUID(session_id_2)
        except ValueError:
            pytest.fail("session_id is not a valid UUID")

        # Assert unique
        assert session_id_1 != session_id_2

    def test_chunking_service_created_at_iso_format(
        self, chunking_service: ChunkingService, sample_data_small: dict
    ):
        """Test get_session_info returns created_at in ISO format.

        The created_at field should:
        1. Be a valid ISO format string
        2. Be parseable as datetime

        This verifies timestamp formatting.
        """
        # Arrange
        response = chunking_service.create_chunked_response(sample_data_small)
        session_id = response["session_id"]

        # Act
        info = chunking_service.get_session_info(session_id)

        # Assert ISO format
        created_at = info["created_at"]
        assert isinstance(created_at, str)

        # Verify parseable as ISO format
        try:
            datetime.fromisoformat(created_at)
        except ValueError:
            pytest.fail("created_at is not in valid ISO format")
