"""Comprehensive test suite for TokenCounter utility class.

This module contains comprehensive tests for the TokenCounter class, covering:
- Token counting in text strings (simple, empty, long, special characters)
- Token estimation in JSON structures (dicts, lists, nested structures)
- Response token estimation with formatting options
- Encoding cache behavior (@lru_cache verification)
- Fallback to cl100k_base for unknown models
- Different model support (gpt-4, gpt-3.5-turbo, etc.)
- Wrapper function integration in server.py

Test coverage goal: 100% for src/databricks_tools/core/token_counter.py
"""

import json
from typing import Any

import pytest
import tiktoken

from databricks_tools.core.token_counter import TokenCounter
from databricks_tools.server import count_tokens, estimate_response_tokens

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def default_counter() -> TokenCounter:
    """Provide a TokenCounter instance with default model (gpt-4)."""
    return TokenCounter()


@pytest.fixture
def gpt35_counter() -> TokenCounter:
    """Provide a TokenCounter instance with gpt-3.5-turbo model."""
    return TokenCounter(model="gpt-3.5-turbo")


@pytest.fixture
def simple_dict() -> dict[str, str]:
    """Provide a simple dictionary for testing token estimation."""
    return {"key": "value"}


@pytest.fixture
def nested_dict() -> dict[str, Any]:
    """Provide a complex nested dictionary for testing token estimation."""
    return {
        "catalog": "analytics",
        "schema": "core",
        "tables": ["users", "orders", "products"],
        "metadata": {
            "row_count": 1000,
            "created_at": "2024-01-01",
            "columns": [
                {"name": "id", "type": "int"},
                {"name": "name", "type": "string"},
                {"name": "value", "type": "decimal"},
            ],
        },
        "flags": {"is_active": True, "has_partitions": False},
    }


@pytest.fixture
def long_text() -> str:
    """Generate a long text (approximately 1000 words) for testing token counting."""
    # Generate 1000 words of lorem ipsum-style text
    words = [
        "the",
        "quick",
        "brown",
        "fox",
        "jumps",
        "over",
        "lazy",
        "dog",
        "data",
        "science",
        "machine",
        "learning",
        "artificial",
        "intelligence",
        "python",
        "pandas",
        "numpy",
        "databricks",
        "spark",
        "sql",
    ]
    # Repeat pattern to get ~1000 words
    text_words = (words * 50)[:1000]
    return " ".join(text_words)


# =============================================================================
# TokenCounter Initialization Tests
# =============================================================================


class TestTokenCounterInitialization:
    """Tests for TokenCounter initialization."""

    def test_token_counter_default_initialization(self, default_counter: TokenCounter):
        """Test TokenCounter initializes with default model (gpt-4).

        The default model should be 'gpt-4' when no model is specified.
        The encoding should be initialized correctly.
        """
        assert default_counter.model == "gpt-4"
        assert default_counter._encoding is not None
        assert isinstance(default_counter._encoding, tiktoken.Encoding)

    def test_token_counter_custom_model_initialization(self, gpt35_counter: TokenCounter):
        """Test TokenCounter initializes with custom model.

        TokenCounter should accept custom model names like 'gpt-3.5-turbo'
        and initialize with the appropriate encoding.
        """
        assert gpt35_counter.model == "gpt-3.5-turbo"
        assert gpt35_counter._encoding is not None
        assert isinstance(gpt35_counter._encoding, tiktoken.Encoding)

    def test_token_counter_model_attribute_set(self):
        """Test that model attribute is correctly set during initialization.

        The model attribute should exactly match the value passed to __init__.
        """
        custom_model = "gpt-4-turbo-preview"
        counter = TokenCounter(model=custom_model)
        assert counter.model == custom_model


# =============================================================================
# Token Counting Tests
# =============================================================================


class TestTokenCounting:
    """Tests for count_tokens method."""

    def test_count_tokens_simple_text(self, default_counter: TokenCounter):
        """Test token counting for simple text string.

        The text "Hello, world!" should return a positive integer token count
        that is reasonable (less than 10 tokens for such short text).
        """
        text = "Hello, world!"
        token_count = default_counter.count_tokens(text)

        assert isinstance(token_count, int)
        assert token_count > 0
        assert token_count < 10  # Reasonable upper bound for short text

    def test_count_tokens_empty_string(self, default_counter: TokenCounter):
        """Test token counting for empty string.

        An empty string should return exactly 0 tokens.
        """
        text = ""
        token_count = default_counter.count_tokens(text)

        assert token_count == 0

    def test_count_tokens_long_text(self, default_counter: TokenCounter, long_text: str):
        """Test token counting for long text (approximately 1000 words).

        For 1000 words, we expect approximately 750-1500 tokens
        (typical ratio is 0.75-1.5 tokens per word).
        """
        token_count = default_counter.count_tokens(long_text)

        # Verify it's in a reasonable range for 1000 words
        assert isinstance(token_count, int)
        assert 750 <= token_count <= 1500

    def test_count_tokens_with_special_characters(self, default_counter: TokenCounter):
        """Test token counting with Unicode characters and emojis.

        Special characters, emojis, and Unicode should be handled correctly.
        """
        text_with_emoji = "Hello 👋 World 🌍"
        text_with_unicode = "Café résumé naïve"
        text_with_symbols = "Math: ∑(x²) = ∫f(x)dx"

        # All should return positive token counts
        assert default_counter.count_tokens(text_with_emoji) > 0
        assert default_counter.count_tokens(text_with_unicode) > 0
        assert default_counter.count_tokens(text_with_symbols) > 0

    def test_count_tokens_consistency(self, default_counter: TokenCounter):
        """Test that count_tokens returns consistent results for same input.

        Multiple calls with the same text should return identical token counts.
        """
        text = "This is a test of consistency in token counting."

        count1 = default_counter.count_tokens(text)
        count2 = default_counter.count_tokens(text)
        count3 = default_counter.count_tokens(text)

        assert count1 == count2 == count3


# =============================================================================
# Token Estimation Tests
# =============================================================================


class TestTokenEstimation:
    """Tests for estimate_tokens and estimate_response_tokens methods."""

    def test_estimate_tokens_simple_dict(
        self, default_counter: TokenCounter, simple_dict: dict[str, str]
    ):
        """Test token estimation for simple dictionary.

        The estimated tokens should match the token count of the
        compact JSON string representation.
        """
        token_count = default_counter.estimate_tokens(simple_dict)

        # Verify against compact JSON token count
        json_string = json.dumps(simple_dict, separators=(",", ":"))
        expected_count = default_counter.count_tokens(json_string)

        assert token_count == expected_count
        assert token_count > 0

    def test_estimate_tokens_nested_structure(
        self, default_counter: TokenCounter, nested_dict: dict[str, Any]
    ):
        """Test token estimation for complex nested dictionary.

        The estimation should accurately account for all nested structure,
        including lists, nested dicts, and various data types.
        """
        token_count = default_counter.estimate_tokens(nested_dict)

        # Should return a reasonable token count for this structure
        assert isinstance(token_count, int)
        assert token_count > 50  # Should be substantial for nested structure

        # Verify it matches compact JSON representation
        json_string = json.dumps(nested_dict, separators=(",", ":"))
        expected_count = default_counter.count_tokens(json_string)
        assert token_count == expected_count

    def test_estimate_tokens_with_list(self, default_counter: TokenCounter):
        """Test token estimation with list input.

        The method accepts both dict and list, so we should test list input.
        """
        test_list = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ]

        token_count = default_counter.estimate_tokens(test_list)

        # Verify against compact JSON token count
        json_string = json.dumps(test_list, separators=(",", ":"))
        expected_count = default_counter.count_tokens(json_string)

        assert token_count == expected_count
        assert token_count > 0

    def test_estimate_response_tokens_formatted(
        self, default_counter: TokenCounter, simple_dict: dict[str, str]
    ):
        """Test response token estimation with formatting enabled.

        When include_formatting=True, the token count should be higher
        due to indentation and additional whitespace.
        """
        formatted_count = default_counter.estimate_response_tokens(
            simple_dict, include_formatting=True
        )

        # Verify against formatted JSON
        formatted_json = json.dumps(simple_dict, indent=2, separators=(",", ":"))
        expected_count = default_counter.count_tokens(formatted_json)

        assert formatted_count == expected_count
        assert formatted_count > 0

    def test_estimate_response_tokens_compact(
        self, default_counter: TokenCounter, simple_dict: dict[str, str]
    ):
        """Test response token estimation with formatting disabled.

        When include_formatting=False, the token count should be minimal
        (same as compact JSON).
        """
        compact_count = default_counter.estimate_response_tokens(
            simple_dict, include_formatting=False
        )

        # Verify against compact JSON
        compact_json = json.dumps(simple_dict, separators=(",", ":"))
        expected_count = default_counter.count_tokens(compact_json)

        assert compact_count == expected_count
        assert compact_count > 0

    def test_estimate_response_tokens_formatting_difference(
        self, default_counter: TokenCounter, nested_dict: dict[str, Any]
    ):
        """Test that formatted responses use more tokens than compact ones.

        For a complex nested structure, formatted JSON should always
        use more tokens than compact JSON due to indentation.
        """
        formatted_count = default_counter.estimate_response_tokens(
            nested_dict, include_formatting=True
        )
        compact_count = default_counter.estimate_response_tokens(
            nested_dict, include_formatting=False
        )

        # Formatted should be greater than compact for nested structures
        assert formatted_count > compact_count

    def test_estimate_response_tokens_default_formatting(
        self, default_counter: TokenCounter, simple_dict: dict[str, str]
    ):
        """Test that include_formatting defaults to True.

        When not specified, include_formatting should default to True.
        """
        default_count = default_counter.estimate_response_tokens(simple_dict)
        formatted_count = default_counter.estimate_response_tokens(
            simple_dict, include_formatting=True
        )

        # Default should match formatted
        assert default_count == formatted_count


# =============================================================================
# Caching and Performance Tests
# =============================================================================


class TestCachingAndPerformance:
    """Tests for encoding caching and performance."""

    def test_encoding_cache_reuse(self):
        """Test that @lru_cache causes encoding objects to be reused.

        Multiple TokenCounter instances with the same model should
        share the same cached encoding object.
        """
        # Create multiple instances with same model
        counter1 = TokenCounter(model="gpt-4")
        counter2 = TokenCounter(model="gpt-4")
        counter3 = TokenCounter(model="gpt-4")

        # They should all use the same encoding object (cached)
        assert counter1._encoding is counter2._encoding
        assert counter2._encoding is counter3._encoding

        # Verify cache is working by checking cache_info
        cache_info = TokenCounter._get_encoding.cache_info()
        assert cache_info.hits > 0  # Should have cache hits

    def test_encoding_cache_different_models(self):
        """Test that different models may share encodings.

        Some models (like gpt-4 and gpt-3.5-turbo) use the same encoding
        (cl100k_base), so they will share the cached encoding object.
        Models with truly different encodings will have different objects.
        """
        counter_gpt4 = TokenCounter(model="gpt-4")
        counter_gpt35 = TokenCounter(model="gpt-3.5-turbo")

        # gpt-4 and gpt-3.5-turbo both use cl100k_base, so they share encoding
        assert counter_gpt4._encoding is counter_gpt35._encoding

        # However, text-davinci-003 uses p50k_base (different encoding)
        counter_davinci = TokenCounter(model="text-davinci-003")

        # This should be a different encoding object
        assert counter_gpt4._encoding is not counter_davinci._encoding

    def test_encoding_cache_info_accessible(self):
        """Test that cache_info() can be called to inspect cache statistics.

        The @lru_cache decorator provides cache_info() for monitoring.
        """
        # Clear cache first to get consistent results
        TokenCounter._get_encoding.cache_clear()

        # Create instances and check cache info
        _ = TokenCounter(model="gpt-4")
        cache_info = TokenCounter._get_encoding.cache_info()

        # Should have cache statistics
        assert hasattr(cache_info, "hits")
        assert hasattr(cache_info, "misses")
        assert hasattr(cache_info, "maxsize")
        assert hasattr(cache_info, "currsize")
        assert cache_info.maxsize == 4  # As specified in decorator


# =============================================================================
# Fallback and Error Handling Tests
# =============================================================================


class TestFallbackAndErrorHandling:
    """Tests for fallback behavior and error handling."""

    def test_fallback_to_cl100k_base_invalid_model(self):
        """Test fallback to cl100k_base for invalid model name.

        When an invalid model name is provided, the TokenCounter should
        fall back to cl100k_base encoding without raising an error.
        """
        invalid_model = "invalid-model-xyz-does-not-exist"
        counter = TokenCounter(model=invalid_model)

        # Should not raise an error
        assert counter.model == invalid_model

        # Should be able to count tokens (using cl100k_base fallback)
        test_text = "Hello, world!"
        token_count = counter.count_tokens(test_text)
        assert token_count > 0

        # Verify it uses cl100k_base by comparing with explicit cl100k_base
        cl100k_encoding = tiktoken.get_encoding("cl100k_base")
        expected_count = len(cl100k_encoding.encode(test_text))
        assert token_count == expected_count

    def test_fallback_consistent_results(self):
        """Test that fallback encoding provides consistent results.

        Multiple invalid models should all fall back to the same encoding
        and provide consistent token counts.
        """
        counter1 = TokenCounter(model="invalid-model-1")
        counter2 = TokenCounter(model="invalid-model-2")

        test_text = "This is a test of fallback consistency."

        count1 = counter1.count_tokens(test_text)
        count2 = counter2.count_tokens(test_text)

        # Both should produce the same count (both using cl100k_base)
        assert count1 == count2


# =============================================================================
# Different Models Tests
# =============================================================================


class TestDifferentModels:
    """Tests for token counting with different model encodings."""

    def test_token_counter_different_models(self):
        """Test TokenCounter works with different valid model names.

        All valid model names should work correctly and produce reasonable
        token counts.
        """
        models_to_test = ["gpt-4", "gpt-3.5-turbo", "text-davinci-003"]
        test_text = "This is a test of different model encodings."

        counts = {}
        for model in models_to_test:
            counter = TokenCounter(model=model)
            counts[model] = counter.count_tokens(test_text)

            # All should produce positive, reasonable token counts
            assert counts[model] > 0
            assert counts[model] < 50  # Reasonable upper bound

        # Counts may differ slightly between models, but should be similar
        # We just verify they're all in a reasonable range
        assert all(5 < count < 50 for count in counts.values())

    def test_token_counter_model_specific_differences(self):
        """Test that different models can produce different token counts.

        While similar, different encodings may tokenize text differently.
        """
        text = "Hello, world!"

        counter_gpt4 = TokenCounter(model="gpt-4")
        counter_gpt35 = TokenCounter(model="gpt-3.5-turbo")

        count_gpt4 = counter_gpt4.count_tokens(text)
        count_gpt35 = counter_gpt35.count_tokens(text)

        # Both should be positive
        assert count_gpt4 > 0
        assert count_gpt35 > 0

        # They should be close (within reasonable range)
        # Note: gpt-4 and gpt-3.5-turbo often use same encoding, so may be equal
        assert abs(count_gpt4 - count_gpt35) <= 2


# =============================================================================
# Wrapper Function Tests
# =============================================================================


class TestWrapperFunctions:
    """Tests for server.py wrapper functions."""

    def test_count_tokens_wrapper_default_model(self):
        """Test count_tokens wrapper function with default model.

        The wrapper function should delegate to TokenCounter and return
        correct token counts using the default gpt-4 model.
        """
        text = "Hello, world!"
        token_count = count_tokens(text)

        # Should match TokenCounter with gpt-4
        counter = TokenCounter(model="gpt-4")
        expected_count = counter.count_tokens(text)

        assert token_count == expected_count
        assert token_count > 0

    def test_count_tokens_wrapper_custom_model(self):
        """Test count_tokens wrapper function with custom model.

        The wrapper should accept a model parameter and create appropriate
        TokenCounter instance.
        """
        text = "Hello, world!"
        model = "gpt-3.5-turbo"
        token_count = count_tokens(text, model=model)

        # Should match TokenCounter with specified model
        counter = TokenCounter(model=model)
        expected_count = counter.count_tokens(text)

        assert token_count == expected_count
        assert token_count > 0

    def test_estimate_response_tokens_wrapper(self, simple_dict: dict[str, str]):
        """Test estimate_response_tokens wrapper function.

        The wrapper should delegate to TokenCounter.estimate_tokens and
        return correct token estimates for dictionaries.
        """
        token_count = estimate_response_tokens(simple_dict)

        # Should match TokenCounter with gpt-4 (default in server.py)
        counter = TokenCounter(model="gpt-4")
        expected_count = counter.estimate_tokens(simple_dict)

        assert token_count == expected_count
        assert token_count > 0

    def test_wrapper_functions_consistency(self):
        """Test that wrapper functions provide consistent results.

        Multiple calls should return identical results for same input.
        """
        text = "Consistency test"
        data = {"key": "value", "count": 42}

        # count_tokens wrapper
        count1 = count_tokens(text)
        count2 = count_tokens(text)
        assert count1 == count2

        # estimate_response_tokens wrapper
        estimate1 = estimate_response_tokens(data)
        estimate2 = estimate_response_tokens(data)
        assert estimate1 == estimate2


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for real-world usage scenarios."""

    def test_databricks_response_token_estimation(self, default_counter: TokenCounter):
        """Test token estimation for realistic Databricks response structure.

        This simulates a typical response from get_table_details.
        """
        databricks_response = {
            "table_name": "analytics.core.users",
            "schema": {
                "fields": [
                    {"name": "user_id", "type": "integer"},
                    {"name": "username", "type": "string"},
                    {"name": "email", "type": "string"},
                    {"name": "created_at", "type": "timestamp"},
                ],
                "primaryKey": ["user_id"],
            },
            "data": [
                {
                    "user_id": 1,
                    "username": "alice",
                    "email": "alice@example.com",
                    "created_at": "2024-01-01",
                },
                {
                    "user_id": 2,
                    "username": "bob",
                    "email": "bob@example.com",
                    "created_at": "2024-01-02",
                },
                {
                    "user_id": 3,
                    "username": "charlie",
                    "email": "charlie@example.com",
                    "created_at": "2024-01-03",
                },
            ],
        }

        # Should be able to estimate tokens for this structure
        token_count = default_counter.estimate_tokens(databricks_response)
        assert token_count > 0
        assert isinstance(token_count, int)

    def test_chunking_decision_scenario(self, default_counter: TokenCounter):
        """Test token estimation for making chunking decisions.

        This simulates checking if a response needs to be chunked.
        """
        max_tokens = 9000
        large_data = {
            "data": [{"id": i, "value": f"row_{i}"} for i in range(1000)],
            "schema": {"fields": [{"name": "id"}, {"name": "value"}]},
        }

        token_count = default_counter.estimate_tokens(large_data)

        # Should be able to make chunking decision
        needs_chunking = token_count > max_tokens
        assert isinstance(needs_chunking, bool)
        assert isinstance(token_count, int)
