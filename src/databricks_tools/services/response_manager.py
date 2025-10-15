"""Response management for MCP server tools.

This module provides a ResponseManager class for centralizing response formatting,
token validation, and automatic chunking across all MCP tools.
"""

import json

from databricks_tools.core.token_counter import TokenCounter
from databricks_tools.services.chunking_service import ChunkingService


class ResponseManager:
    """Manages response formatting and token validation for MCP tools.

    This class provides centralized methods for formatting responses with
    automatic token checking and chunking, as well as consistent error
    formatting across all MCP tools.

    Attributes:
        token_counter: TokenCounter instance for token estimation.
        chunking_service: ChunkingService instance for handling large responses.
        max_tokens: Maximum tokens allowed per response (default 9000).

    Example:
        >>> from databricks_tools.core.token_counter import TokenCounter
        >>> from databricks_tools.services.chunking_service import ChunkingService
        >>> token_counter = TokenCounter()
        >>> chunking_service = ChunkingService(token_counter)
        >>> rm = ResponseManager(token_counter, chunking_service)
        >>>
        >>> # Format small response
        >>> response = rm.format_response({"result": "success"})
        >>> print(response)
        {
          "result": "success"
        }
        >>>
        >>> # Format large response with auto-chunking
        >>> large_data = {"data": [{"id": i} for i in range(10000)], "schema": {...}}
        >>> chunked = rm.format_response(large_data)
        >>> # Returns chunking session metadata
    """

    def __init__(
        self,
        token_counter: TokenCounter,
        chunking_service: ChunkingService,
        max_tokens: int = 9000,
    ) -> None:
        """Initialize ResponseManager with dependencies and configuration.

        Args:
            token_counter: TokenCounter instance for token estimation.
            chunking_service: ChunkingService instance for chunking large responses.
            max_tokens: Maximum tokens allowed per response. Defaults to 9000.

        Example:
            >>> rm = ResponseManager(token_counter, chunking_service)
            >>> rm = ResponseManager(token_counter, chunking_service, max_tokens=5000)
        """
        self.token_counter = token_counter
        self.chunking_service = chunking_service
        self.max_tokens = max_tokens

    def format_response(self, data: dict | list, auto_chunk: bool = True) -> str:
        """Format response with automatic chunking if needed.

        Converts data to JSON format and checks token count. If the response
        exceeds the token limit and auto_chunk is enabled, automatically creates
        a chunked response using the ChunkingService.

        Args:
            data: Dictionary or list to format as JSON response.
            auto_chunk: If True, automatically chunk responses exceeding token limit.
                        Defaults to True.

        Returns:
            JSON string representation of data or chunked response metadata.

        Example:
            >>> rm = ResponseManager(token_counter, chunking_service)
            >>> # Small responses returned as-is
            >>> response = rm.format_response({"result": "success"})
            >>> print(response)
            {
              "result": "success"
            }
            >>>
            >>> # Large responses automatically chunked
            >>> large_data = {
            ...     "data": [{"id": i, "name": f"row_{i}"} for i in range(10000)],
            ...     "schema": {"fields": [{"name": "id", "type": "integer"}]}
            ... }
            >>> chunked = rm.format_response(large_data)
            >>> # Returns: {"chunked_response": True, "session_id": "...", ...}
        """
        # Convert to JSON with compact formatting for token estimation
        json_str = json.dumps(data, separators=(",", ":"))

        # Check token count
        token_count = self.token_counter.count_tokens(json_str)

        # AIDEV-NOTE: Auto-chunk if response exceeds token limit and is a dict
        if token_count > self.max_tokens and auto_chunk:
            # Only chunk dict responses (ChunkingService requires dict with 'data' key)
            if isinstance(data, dict):
                chunked = self.chunking_service.create_chunked_response(data)
                return json.dumps(chunked, indent=2, separators=(",", ":"))

        # Return formatted JSON (with indentation for readability)
        return json.dumps(data, indent=2, separators=(",", ":"))

    def format_error(
        self, error_type: str, message: str, **kwargs: str | int | list
    ) -> str:
        """Format error response consistently.

        Creates a standardized error response dictionary and formats it as JSON.
        Additional context fields can be provided via kwargs.

        Args:
            error_type: Type of error (e.g., "ValueError", "KeyError", "Session not found").
            message: Human-readable error message explaining the issue.
            **kwargs: Additional error context fields (e.g., table="invalid_table",
                     session_id="abc123", catalog="main").

        Returns:
            JSON formatted error response with error type, message, and any additional context.

        Example:
            >>> rm = ResponseManager(token_counter, chunking_service)
            >>> # Simple error
            >>> error = rm.format_error("ValueError", "Invalid table name")
            >>> print(error)
            {
              "error": "ValueError",
              "message": "Invalid table name"
            }
            >>>
            >>> # Error with context
            >>> error = rm.format_error(
            ...     "Session not found",
            ...     "The specified session ID does not exist or has expired.",
            ...     session_id="abc123"
            ... )
            >>> print(error)
            {
              "error": "Session not found",
              "message": "The specified session ID does not exist or has expired.",
              "session_id": "abc123"
            }
        """
        error_dict = {"error": error_type, "message": message, **kwargs}
        return json.dumps(error_dict, indent=2, separators=(",", ":"))
