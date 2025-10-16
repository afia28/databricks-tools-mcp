"""Chunking service for managing large response data.

This module provides a ChunkingService class for splitting large responses into
manageable chunks, managing chunking sessions, and handling session cleanup.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any

from databricks_tools.core.token_counter import TokenCounter


class ChunkingService:
    """Service for managing response chunking for large datasets.

    This class handles splitting large responses into chunks to stay within
    token limits, manages chunking sessions with automatic expiry, and provides
    methods for retrieving chunks and session information.

    Attributes:
        token_counter: TokenCounter instance for token estimation.
        max_tokens: Maximum tokens allowed per chunk (default 9000).
        session_ttl: Session time-to-live as timedelta.

    Example:
        >>> from databricks_tools.core.token_counter import TokenCounter
        >>> token_counter = TokenCounter()
        >>> service = ChunkingService(token_counter)
        >>>
        >>> # Create chunked response for large data
        >>> data = {"data": [{"id": i} for i in range(10000)], "schema": {...}}
        >>> response = service.create_chunked_response(data)
        >>> print(response["session_id"])
        '123e4567-e89b-12d3-a456-426614174000'
        >>>
        >>> # Retrieve specific chunk
        >>> chunk = service.get_chunk(response["session_id"], 1)
        >>> print(chunk["chunk_number"])
        1
    """

    def __init__(
        self,
        token_counter: TokenCounter,
        max_tokens: int = 9000,
        session_ttl_minutes: int = 60,
    ) -> None:
        """Initialize ChunkingService with dependencies and configuration.

        Args:
            token_counter: TokenCounter instance for token estimation.
            max_tokens: Maximum tokens allowed per chunk. Defaults to 9000.
            session_ttl_minutes: Session time-to-live in minutes. Defaults to 60.

        Example:
            >>> service = ChunkingService(token_counter)
            >>> service = ChunkingService(token_counter, max_tokens=5000)
            >>> service = ChunkingService(token_counter, session_ttl_minutes=120)
        """
        self.token_counter = token_counter
        self.max_tokens = max_tokens
        self.session_ttl = timedelta(minutes=session_ttl_minutes)
        self._sessions: dict[str, dict[str, Any]] = {}

    def create_chunked_response(
        self, data: dict[str, Any], max_tokens: int | None = None
    ) -> dict[str, Any]:
        """Create a chunked response for data that exceeds token limits.

        Splits large response data into manageable chunks, creates a session
        to track the chunks, and returns metadata about the chunking session.

        Args:
            data: The full response data dictionary containing 'data' and 'schema' keys.
            max_tokens: Maximum tokens allowed per chunk. If None, uses self.max_tokens.

        Returns:
            Dictionary containing:
                - chunked_response (bool): Always True
                - session_id (str): Unique session identifier
                - total_chunks (int): Number of chunks created
                - chunk_token_amounts (dict): Token count for each chunk
                - message (str): User-friendly message
                - instructions (str): Instructions for retrieving chunks

        Example:
            >>> data = {
            ...     "data": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
            ...     "schema": {"fields": [{"name": "id", "type": "integer"}]},
            ...     "table_name": "users"
            ... }
            >>> response = service.create_chunked_response(data)
            >>> print(response["total_chunks"])
            2
            >>> print(response["session_id"])
            '123e4567-e89b-12d3-a456-426614174000'
        """
        if max_tokens is None:
            max_tokens = self.max_tokens

        # Generate session ID for this chunked response
        session_id = str(uuid.uuid4())

        # Extract data rows and metadata
        rows = data.get("data", [])
        schema = data.get("schema", {})
        metadata = {k: v for k, v in data.items() if k not in ["data", "schema"]}

        # Create base response structure
        base_response = {"schema": schema, **metadata}

        # Calculate how many rows can fit in each chunk
        base_tokens = self.token_counter.estimate_tokens(base_response)
        available_tokens = max_tokens - base_tokens - 500  # Reserve 500 tokens for chunk metadata

        # Estimate tokens per row (using first few rows as sample)
        if rows:
            sample_rows = rows[: min(3, len(rows))]
            sample_tokens = self.token_counter.estimate_tokens({"data": sample_rows})
            tokens_per_row = max(1, sample_tokens // len(sample_rows))
            rows_per_chunk = max(1, available_tokens // tokens_per_row)
        else:
            rows_per_chunk = 1

        # Split data into chunks
        chunks = []
        total_chunks = (len(rows) + rows_per_chunk - 1) // rows_per_chunk

        for i in range(0, len(rows), rows_per_chunk):
            chunk_rows = rows[i : i + rows_per_chunk]
            chunk_number = (i // rows_per_chunk) + 1

            chunk_response = {
                **base_response,
                "data": chunk_rows,
                "chunking_info": {
                    "session_id": session_id,
                    "chunk_number": chunk_number,
                    "total_chunks": total_chunks,
                    "rows_in_chunk": len(chunk_rows),
                    "total_rows": len(rows),
                    "is_chunked": True,
                    "reconstruction_instructions": (
                        "This response is chunked due to token limits. "
                        f"Collect all {total_chunks} chunks with session_id '{session_id}' "
                        "and combine the 'data' arrays to reconstruct the full dataset."
                    ),
                },
            }
            chunks.append(chunk_response)

        # Calculate token counts for each chunk
        chunk_token_amounts = {}
        for i, chunk in enumerate(chunks):
            chunk_number = i + 1
            chunk_tokens = self.token_counter.estimate_tokens(chunk)
            chunk_token_amounts[str(chunk_number)] = chunk_tokens

        # Store session info
        self._sessions[session_id] = {
            "chunks": chunks,
            "created_at": datetime.now(),
            "total_chunks": total_chunks,
            "chunks_delivered": 0,
            "chunk_token_amounts": chunk_token_amounts,
        }

        return {
            "chunked_response": True,
            "session_id": session_id,
            "total_chunks": total_chunks,
            "chunk_token_amounts": chunk_token_amounts,
            "message": f"Response exceeds token limit. Data will be delivered in {total_chunks} chunks.",
            "instructions": f"Use get_chunk(session_id='{session_id}', chunk_number=N) to retrieve each chunk (1-{total_chunks})",
        }

    def get_chunk(self, session_id: str, chunk_number: int) -> dict[str, Any]:
        """Retrieve a specific chunk from a chunking session.

        Validates the session and chunk number, retrieves the requested chunk,
        and updates delivery tracking. Automatically cleans up expired sessions
        before processing the request.

        Args:
            session_id: The session ID from the chunked response.
            chunk_number: The chunk number to retrieve (1-indexed).

        Returns:
            Dictionary containing the chunk data with chunking metadata.

        Raises:
            ValueError: If session_id is not found or chunk_number is invalid.

        Example:
            >>> chunk = service.get_chunk(session_id, 1)
            >>> print(chunk["data"])
            [{"id": 1, "name": "Alice"}, ...]
            >>> print(chunk["chunking_info"]["chunk_number"])
            1
            >>> print(chunk["chunking_info"]["chunks_delivered"])
            1
        """
        # Clean up expired sessions first
        self._cleanup_expired_sessions()

        # Validate session exists
        if session_id not in self._sessions:
            raise ValueError(
                f"Session not found: {session_id}. The session may have expired or does not exist."
            )

        session = self._sessions[session_id]
        chunks = session["chunks"]

        # Validate chunk number
        if chunk_number < 1 or chunk_number > len(chunks):
            raise ValueError(
                f"Invalid chunk number: {chunk_number}. Must be between 1 and {len(chunks)}."
            )

        # Get the requested chunk (convert to 0-indexed)
        chunk: dict[str, Any] = chunks[chunk_number - 1].copy()  # Create copy to avoid mutation

        # Update delivery tracking
        session["chunks_delivered"] += 1

        # Add completion status to chunk
        chunk["chunking_info"]["chunks_delivered"] = session["chunks_delivered"]
        chunk["chunking_info"]["all_chunks_delivered"] = (
            session["chunks_delivered"] >= session["total_chunks"]
        )

        return chunk

    def get_session_info(self, session_id: str) -> dict[str, Any]:
        """Get information about a chunking session.

        Retrieves metadata about the chunking session including total chunks,
        delivery progress, and instructions for reconstruction. Automatically
        cleans up expired sessions before processing the request.

        Args:
            session_id: The session ID to get information about.

        Returns:
            Dictionary containing session metadata:
                - session_id (str): Session identifier
                - total_chunks (int): Total number of chunks
                - chunks_delivered (int): Number of chunks delivered so far
                - chunks_remaining (int): Number of chunks not yet delivered
                - created_at (str): ISO format timestamp of session creation
                - all_chunks_delivered (bool): Whether all chunks have been delivered
                - next_chunk_to_request (int | None): Next chunk number to request
                - chunk_token_amounts (dict): Token count for each chunk
                - reconstruction_instructions (str): Instructions for combining chunks

        Raises:
            ValueError: If session_id is not found.

        Example:
            >>> info = service.get_session_info(session_id)
            >>> print(info["total_chunks"])
            5
            >>> print(info["chunks_delivered"])
            2
            >>> print(info["next_chunk_to_request"])
            3
        """
        # Clean up expired sessions first
        self._cleanup_expired_sessions()

        # Validate session exists
        if session_id not in self._sessions:
            raise ValueError(
                f"Session not found: {session_id}. The session may have expired or does not exist."
            )

        session = self._sessions[session_id]

        return {
            "session_id": session_id,
            "total_chunks": session["total_chunks"],
            "chunks_delivered": session["chunks_delivered"],
            "chunks_remaining": session["total_chunks"] - session["chunks_delivered"],
            "created_at": session["created_at"].isoformat(),
            "all_chunks_delivered": session["chunks_delivered"] >= session["total_chunks"],
            "next_chunk_to_request": (
                min(session["chunks_delivered"] + 1, session["total_chunks"])
                if session["chunks_delivered"] < session["total_chunks"]
                else None
            ),
            "chunk_token_amounts": session.get("chunk_token_amounts", {}),
            "reconstruction_instructions": (
                f"Use get_chunk(session_id='{session_id}', chunk_number=N) "
                f"to retrieve chunks 1 through {session['total_chunks']}. "
                "Combine all 'data' arrays to reconstruct the full dataset."
            ),
        }

    def _cleanup_expired_sessions(self) -> None:
        """Remove expired sessions from storage.

        Iterates through all active sessions and removes those that have
        exceeded their time-to-live (TTL). This is called automatically
        by get_chunk() and get_session_info() to prevent memory buildup.

        Example:
            >>> # Called automatically, but can be invoked manually
            >>> service._cleanup_expired_sessions()
        """
        now = datetime.now()
        expired_session_ids = [
            session_id
            for session_id, session in self._sessions.items()
            if session["created_at"] + self.session_ttl < now
        ]

        for session_id in expired_session_ids:
            del self._sessions[session_id]
