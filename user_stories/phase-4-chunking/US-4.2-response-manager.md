# US-4.2: Create Response Manager

## Metadata
- **Story ID**: US-4.2
- **Title**: Create Response Manager
- **Phase**: Phase 4 - Chunking & Response Management
- **Estimated LOC**: ~80 lines
- **Dependencies**: US-2.1 (TokenCounter), US-4.1 (ChunkingService)
- **Status**: ⬜ Not Started

## Overview
Create ResponseManager to centralize response formatting and token validation. Eliminates duplicated token checking across all MCP tools.

## User Story
**As a** developer
**I want** centralized response management
**So that** token validation and formatting are consistent across all MCP tools

## Acceptance Criteria
1. ✅ ResponseManager class created
2. ✅ format_response() handles token checking
3. ✅ Automatically chunks large responses
4. ✅ Consistent error response formatting
5. ✅ Eliminates all duplicated token checking code
6. ✅ All MCP tools use ResponseManager
7. ✅ All tests pass with 95%+ coverage

## Technical Requirements

### Class: ResponseManager

```python
import json

class ResponseManager:
    """Manages response formatting and token validation."""

    def __init__(self, token_counter: TokenCounter, chunking_service: ChunkingService, max_tokens: int = 9000):
        self.token_counter = token_counter
        self.chunking_service = chunking_service
        self.max_tokens = max_tokens

    def format_response(self, data: dict | list, auto_chunk: bool = True) -> str:
        """Format response with automatic chunking if needed."""
        # Convert to JSON
        json_str = json.dumps(data, indent=2, separators=(",", ":"))

        # Check token count
        token_count = self.token_counter.count_tokens(json_str)

        if token_count > self.max_tokens and auto_chunk:
            # Create chunked response
            if isinstance(data, dict):
                chunked = self.chunking_service.create_chunked_response(data)
                return json.dumps(chunked, indent=2)

        return json_str

    def format_error(self, error_type: str, message: str, **kwargs) -> str:
        """Format error response consistently."""
        error_dict = {
            "error": error_type,
            "message": message,
            **kwargs
        }
        return json.dumps(error_dict, indent=2)
```

## Test Cases (10 tests)
1. test_response_manager_small_response
2. test_response_manager_large_response_auto_chunk
3. test_response_manager_disable_auto_chunk
4. test_response_manager_format_error
5. test_response_manager_token_limit
6. test_response_manager_list_response
7. test_response_manager_dict_response
8. test_response_manager_edge_cases
9. test_response_manager_integration
10. test_response_manager_performance

## Files
- **Create**: `src/databricks_tools/services/response_manager.py`
- **Modify**: `src/databricks_tools/server.py` (all MCP tools use this)
- **Test**: `tests/test_services/test_response_manager.py`

## Expected Outcome
All response handling centralized, Phase 4 complete.

## Related Stories
- **Depends on**: US-2.1, US-4.1
- **Completes**: Phase 4 - Chunking & Response Management
