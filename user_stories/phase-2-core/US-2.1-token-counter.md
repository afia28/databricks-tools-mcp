# US-2.1: Create Token Counter Utility

## Metadata
- **Story ID**: US-2.1
- **Title**: Create Token Counter Utility
- **Phase**: Phase 2 - Core Services
- **Estimated LOC**: ~70 lines
- **Dependencies**: None (standalone utility)
- **Status**: ⬜ Not Started

## Overview
Extract token counting logic into a dedicated TokenCounter utility class. This provides centralized token estimation for response management and chunking decisions.

## User Story
**As a** developer
**I want** a reusable token counting utility
**So that** token limits are consistently enforced across all MCP tools

## Acceptance Criteria
1. ✅ TokenCounter class created with caching
2. ✅ Can count tokens in text strings
3. ✅ Can estimate tokens in JSON/dict objects
4. ✅ Caches tiktoken encodings for performance
5. ✅ Supports different models (gpt-4, cl100k_base)
6. ✅ Original functions in server.py wrapped (no breaking changes)
7. ✅ All tests pass with 100% coverage
8. ✅ Performance is equal or better than original

## Technical Requirements

### Class: TokenCounter

```python
import tiktoken
import json
from functools import lru_cache

class TokenCounter:
    """Utility for counting tokens in text and data structures."""

    def __init__(self, model: str = "gpt-4"):
        """Initialize with model name for token counting."""
        self.model = model
        self._encoding = self._get_encoding()

    @staticmethod
    @lru_cache(maxsize=4)
    def _get_encoding(model: str = "gpt-4") -> tiktoken.Encoding:
        """Get tiktoken encoding with caching."""
        try:
            return tiktoken.encoding_for_model(model)
        except (KeyError, ValueError):
            # Fallback to cl100k_base
            return tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        return len(self._encoding.encode(text))

    def estimate_tokens(self, data: dict | list) -> int:
        """Estimate tokens in a JSON-serializable data structure."""
        json_string = json.dumps(data, separators=(",", ":"))
        return self.count_tokens(json_string)

    def estimate_response_tokens(
        self,
        data: dict,
        include_formatting: bool = True
    ) -> int:
        """Estimate tokens for a complete response with optional formatting."""
        if include_formatting:
            json_string = json.dumps(data, indent=2, separators=(",", ":"))
        else:
            json_string = json.dumps(data, separators=(",", ":"))
        return self.count_tokens(json_string)
```

## Design Patterns Used
- **Singleton/Caching**: LRU cache for encoding objects
- **Utility Class**: Stateless operations with shared cached resources
- **Strategy Pattern** (future): Could support different tokenizers

## Key Implementation Notes

### Caching Strategy
- Use `@lru_cache` on `_get_encoding()` to cache tiktoken encoding objects
- Encoding objects are expensive to create but reusable
- Cache size of 4 handles typical use cases (gpt-4, gpt-3.5-turbo, cl100k_base, p50k_base)

### Performance Considerations
- Avoid recreating encoding objects
- Use compact JSON (separators=(",", ":")) for estimation
- Consider adding method to count tokens in pandas DataFrame

### Integration with Existing Code
```python
# In server.py - create global instance
_token_counter = TokenCounter(model="gpt-4")

# Wrapper functions for backward compatibility
def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Legacy function - wrapper around TokenCounter."""
    if model != "gpt-4":
        counter = TokenCounter(model=model)
        return counter.count_tokens(text)
    return _token_counter.count_tokens(text)

def estimate_response_tokens(data: dict) -> int:
    """Legacy function - wrapper around TokenCounter."""
    return _token_counter.estimate_tokens(data)
```

## Files to Create/Modify

### Create
- `src/databricks_tools/core/__init__.py`
- `src/databricks_tools/core/token_counter.py`

### Modify
- `src/databricks_tools/server.py` (add wrappers)

## Test Cases

### File: `tests/test_core/test_token_counter.py`

1. **test_token_counter_initialization**
   - Verify TokenCounter initializes with default model
   - Assertions: model attribute set correctly

2. **test_count_tokens_simple_text**
   - Input: "Hello, world!"
   - Expected: Positive integer token count
   - Assertions: Count > 0, count < 10

3. **test_count_tokens_empty_string**
   - Input: ""
   - Expected: 0 tokens
   - Assertions: count == 0

4. **test_count_tokens_long_text**
   - Input: 1000-word text
   - Expected: Reasonable token count (~750-1500)
   - Assertions: Count in expected range

5. **test_estimate_tokens_simple_dict**
   - Input: {"key": "value"}
   - Expected: Token count matches JSON string
   - Assertions: Consistent with count_tokens

6. **test_estimate_tokens_nested_structure**
   - Input: Complex nested dict with lists
   - Expected: Accurate token count
   - Assertions: Count accounts for all structure

7. **test_estimate_response_tokens_formatted**
   - Input: Dict, include_formatting=True
   - Expected: Higher count due to indentation
   - Assertions: Formatted > unformatted

8. **test_estimate_response_tokens_compact**
   - Input: Dict, include_formatting=False
   - Expected: Minimal token count
   - Assertions: Matches compact JSON

9. **test_encoding_cache_reuse**
   - Input: Multiple TokenCounter instances with same model
   - Expected: Same encoding object reused
   - Assertions: Encoding is cached

10. **test_fallback_to_cl100k_base**
    - Input: Invalid model name
    - Expected: Falls back to cl100k_base
    - Assertions: No exception, encoding works

11. **test_token_counter_different_models**
    - Input: Different model names
    - Expected: Different token counts (slight variations)
    - Assertions: Counts are reasonable

## Definition of Done

- [ ] TokenCounter class implemented
- [ ] Caching implemented with lru_cache
- [ ] count_tokens() method works correctly
- [ ] estimate_tokens() method works correctly
- [ ] estimate_response_tokens() with formatting options
- [ ] Legacy wrapper functions in server.py
- [ ] All 11 test cases pass
- [ ] Test coverage is 100%
- [ ] Performance benchmarks show no regression
- [ ] Type hints on all methods
- [ ] Docstrings added
- [ ] Code passes ruff checks
- [ ] Code reviewed and approved

## Expected Outcome

After completing this story:

1. **Centralized Logic**: All token counting in one place
2. **Performance**: Caching improves performance
3. **Reusability**: Can be used by all services
4. **Testability**: Easy to test independently
5. **Foundation**: Ready for chunking service (US-4.1)

### Example Usage
```python
from databricks_tools.core.token_counter import TokenCounter

# Create counter
counter = TokenCounter(model="gpt-4")

# Count tokens in text
text_tokens = counter.count_tokens("This is some text")

# Estimate tokens in data
data = {"results": [{"id": 1, "name": "test"}]}
data_tokens = counter.estimate_tokens(data)

# Estimate with formatting
formatted_tokens = counter.estimate_response_tokens(data, include_formatting=True)
```

## Related User Stories
- **Depends on**: None
- **Blocks**: US-4.1 (Chunking Service), US-4.2 (Response Manager)
- **Related to**: All Phase 3+ stories will use this utility

## Notes
- This is standalone and can be developed/tested independently
- Consider adding DataFrame support in future
- Could add async methods if needed for performance
