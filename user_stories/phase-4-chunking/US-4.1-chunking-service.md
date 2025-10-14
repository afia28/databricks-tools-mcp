# US-4.1: Create Chunking Service

## Metadata
- **Story ID**: US-4.1
- **Title**: Create Chunking Service
- **Phase**: Phase 4 - Chunking & Response Management
- **Estimated LOC**: ~130 lines
- **Dependencies**: US-2.1 (TokenCounter)
- **Status**: ⬜ Not Started

## Overview
Extract chunking logic into ChunkingService class. Replaces global CHUNK_SESSIONS dict with proper class-based state management.

## User Story
**As a** developer
**I want** centralized response chunking management
**So that** large responses are consistently handled and session state is properly managed

## Acceptance Criteria
1. ✅ ChunkingService class created
2. ✅ create_chunked_response() method implemented
3. ✅ get_chunk() method implemented
4. ✅ get_session_info() method implemented
5. ✅ Session cleanup/expiry mechanism added
6. ✅ No global CHUNK_SESSIONS dict
7. ✅ MCP tools use service
8. ✅ All tests pass with 95%+ coverage

## Technical Requirements

### Class: ChunkingService

```python
from datetime import datetime, timedelta
import uuid

class ChunkingService:
    """Manages response chunking for large datasets."""

    def __init__(self, token_counter: TokenCounter, max_tokens: int = 9000, session_ttl_minutes: int = 60):
        self.token_counter = token_counter
        self.max_tokens = max_tokens
        self.session_ttl = timedelta(minutes=session_ttl_minutes)
        self._sessions: dict[str, dict] = {}

    def create_chunked_response(self, data: dict) -> dict:
        """Create chunked response for data exceeding token limits."""
        session_id = str(uuid.uuid4())
        # Extract and chunk data
        # Store session
        # Return chunk info
        pass

    def get_chunk(self, session_id: str, chunk_number: int) -> dict:
        """Retrieve specific chunk from session."""
        self._cleanup_expired_sessions()
        # Validate session
        # Return chunk
        pass

    def get_session_info(self, session_id: str) -> dict:
        """Get information about chunking session."""
        pass

    def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        now = datetime.now()
        expired = [sid for sid, session in self._sessions.items()
                   if now - session['created_at'] > self.session_ttl]
        for sid in expired:
            del self._sessions[sid]
```

## Test Cases (12 tests)
1. test_chunking_service_create_session
2. test_chunking_service_get_chunk
3. test_chunking_service_get_session_info
4. test_chunking_service_all_chunks_delivered
5. test_chunking_service_invalid_session
6. test_chunking_service_invalid_chunk_number
7. test_chunking_service_session_expiry
8. test_chunking_service_cleanup_expired
9. test_chunking_service_token_calculation
10. test_chunking_service_large_dataset
11. test_chunking_service_concurrent_sessions
12. test_integration_with_mcp_tools

## Files
- **Create**: `src/databricks_tools/services/chunking_service.py`
- **Modify**: `src/databricks_tools/server.py` (replace global, use service)
- **Test**: `tests/test_services/test_chunking_service.py`

## Related Stories
- **Depends on**: US-2.1
- **Blocks**: US-4.2
