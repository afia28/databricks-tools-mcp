"""Token counting utility for MCP server responses.

This module provides a centralized TokenCounter class for estimating token counts
in text strings and JSON data structures using tiktoken.
"""

import json
from functools import lru_cache

import tiktoken


class TokenCounter:
    """Utility for counting tokens in text and data structures.

    This class provides methods to count tokens using tiktoken encodings,
    with caching for performance optimization.

    Attributes:
        model: The model name used for token counting (e.g., "gpt-4").
        _encoding: The cached tiktoken encoding object.

    Example:
        >>> counter = TokenCounter(model="gpt-4")
        >>> tokens = counter.count_tokens("Hello, world!")
        >>> print(f"Token count: {tokens}")
        Token count: 4

        >>> data = {"key": "value", "list": [1, 2, 3]}
        >>> tokens = counter.estimate_tokens(data)
        >>> print(f"Data tokens: {tokens}")
        Data tokens: 15
    """

    def __init__(self, model: str = "gpt-4") -> None:
        """Initialize TokenCounter with a specific model.

        Args:
            model: The model name for token counting. Defaults to "gpt-4".
                   Falls back to "cl100k_base" if model not found.

        Example:
            >>> counter = TokenCounter(model="gpt-4")
            >>> counter.model
            'gpt-4'
        """
        self.model = model
        self._encoding = self._get_encoding(model)

    @staticmethod
    @lru_cache(maxsize=4)
    def _get_encoding(model: str = "gpt-4") -> tiktoken.Encoding:
        """Get tiktoken encoding with caching.

        This method caches encoding objects to avoid expensive recreation.
        Cache size of 4 handles typical use cases (gpt-4, gpt-3.5-turbo,
        cl100k_base, p50k_base).

        Args:
            model: The model name to get encoding for.

        Returns:
            A tiktoken.Encoding object for the specified model.
            Falls back to cl100k_base if model not found.

        Example:
            >>> encoding = TokenCounter._get_encoding("gpt-4")
            >>> isinstance(encoding, tiktoken.Encoding)
            True
        """
        try:
            return tiktoken.encoding_for_model(model)
        except (KeyError, ValueError):
            # Fallback to cl100k_base for unknown models
            return tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string.

        Args:
            text: The text string to count tokens in.

        Returns:
            The number of tokens in the text.

        Example:
            >>> counter = TokenCounter()
            >>> counter.count_tokens("Hello, world!")
            4
            >>> counter.count_tokens("")
            0
        """
        return len(self._encoding.encode(text))

    def estimate_tokens(self, data: dict | list) -> int:
        """Estimate tokens in a JSON-serializable data structure.

        Converts the data to compact JSON and counts tokens in the result.
        Uses minimal separators for accurate estimation.

        Args:
            data: A dictionary or list to estimate tokens for.

        Returns:
            The estimated number of tokens in the JSON representation.

        Example:
            >>> counter = TokenCounter()
            >>> data = {"key": "value"}
            >>> counter.estimate_tokens(data)
            7
        """
        json_string = json.dumps(data, separators=(",", ":"))
        return self.count_tokens(json_string)

    def estimate_response_tokens(
        self, data: dict, include_formatting: bool = True
    ) -> int:
        """Estimate tokens for a complete response with optional formatting.

        When include_formatting is True, uses indented JSON which is more
        human-readable but uses more tokens. When False, uses compact JSON.

        Args:
            data: The dictionary to estimate tokens for.
            include_formatting: Whether to include indentation (default True).

        Returns:
            The estimated number of tokens in the response.

        Example:
            >>> counter = TokenCounter()
            >>> data = {"key": "value"}
            >>> formatted = counter.estimate_response_tokens(data, include_formatting=True)
            >>> compact = counter.estimate_response_tokens(data, include_formatting=False)
            >>> formatted > compact
            True
        """
        if include_formatting:
            json_string = json.dumps(data, indent=2, separators=(",", ":"))
        else:
            json_string = json.dumps(data, separators=(",", ":"))
        return self.count_tokens(json_string)
