# US-1.1: Create Pydantic Configuration Models

## Metadata
- **Story ID**: US-1.1
- **Title**: Create Pydantic Configuration Models
- **Phase**: Phase 1 - Foundation
- **Estimated LOC**: ~50 lines
- **Dependencies**: None (foundation story)
- **Status**: ⬜ Not Started

## Overview
Create Pydantic models for type-safe configuration management. This provides validation, serialization, and clear data contracts for workspace configurations.

## User Story
**As a** developer
**I want** strongly-typed configuration models with automatic validation
**So that** configuration errors are caught early and the system is more maintainable

## Acceptance Criteria
1. ✅ WorkspaceConfig model created with all required Databricks fields
2. ✅ ServerConfig model created for overall server settings
3. ✅ All fields have appropriate Pydantic validators
4. ✅ Field descriptions added for documentation
5. ✅ Default values provided where appropriate
6. ✅ Model can be instantiated from environment variables
7. ✅ Validation errors provide clear, actionable messages
8. ✅ Models support JSON serialization/deserialization
9. ✅ All tests pass with 100% coverage for models

## Technical Requirements

### Models to Create

#### 1. WorkspaceConfig
Represents a single Databricks workspace configuration.

**Fields**:
- `server_hostname`: str (required) - Databricks workspace URL
- `http_path`: str (required) - SQL warehouse HTTP path
- `access_token`: str (required) - API access token
- `workspace_name`: str (optional, default="default") - Workspace identifier

**Validations**:
- `server_hostname` must start with `https://`
- `http_path` must start with `/sql/`
- `access_token` must start with `dapi` or be at least 32 characters
- All required fields must not be empty strings

#### 2. ServerConfig
Represents overall server configuration.

**Fields**:
- `max_response_tokens`: int (default=9000) - Maximum tokens per response
- `default_catalog`: str | None (optional) - Default catalog for UDF operations
- `default_schema`: str | None (optional) - Default schema for UDF operations

**Validations**:
- `max_response_tokens` must be between 1000 and 25000

## Design Patterns Used
- **Data Transfer Object (DTO)**: Models act as DTOs for configuration
- **Validation Pattern**: Pydantic provides declarative validation
- **Immutability**: Models should be immutable (frozen=True)

## Key Implementation Notes

### Pydantic Best Practices
```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional

class WorkspaceConfig(BaseModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    server_hostname: str = Field(..., description="Databricks workspace URL")
    http_path: str = Field(..., description="SQL warehouse HTTP path")
    access_token: str = Field(..., description="Databricks API token", repr=False)
    workspace_name: str = Field(default="default", description="Workspace identifier")

    @field_validator('server_hostname')
    @classmethod
    def validate_hostname(cls, v: str) -> str:
        if not v.startswith('https://'):
            raise ValueError('server_hostname must start with https://')
        return v
```

### Security Considerations
- `access_token` should have `repr=False` to prevent logging
- Consider using `SecretStr` for sensitive fields
- Never log or print the access_token value

### Environment Variable Integration
```python
@classmethod
def from_env(cls, prefix: str = "") -> "WorkspaceConfig":
    """Create config from environment variables."""
    import os
    return cls(
        server_hostname=os.getenv(f"{prefix}DATABRICKS_SERVER_HOSTNAME"),
        http_path=os.getenv(f"{prefix}DATABRICKS_HTTP_PATH"),
        access_token=os.getenv(f"{prefix}DATABRICKS_TOKEN"),
        workspace_name=prefix.lower().rstrip('_') if prefix else "default"
    )
```

## Files to Create/Modify

### Create
- `src/databricks_tools/config/__init__.py` (package init)
- `src/databricks_tools/config/models.py` (main implementation)

### File Structure
```
src/databricks_tools/
└── config/
    ├── __init__.py
    └── models.py
```

## Test Cases

### File: `tests/test_config/test_models.py`

#### Test Cases for WorkspaceConfig

1. **test_workspace_config_valid_creation**
   - Input: Valid hostname, http_path, token
   - Expected: WorkspaceConfig instance created successfully
   - Assertions: All fields match input values

2. **test_workspace_config_invalid_hostname**
   - Input: hostname without https://
   - Expected: ValidationError raised
   - Assertions: Error message mentions https://

3. **test_workspace_config_invalid_http_path**
   - Input: http_path not starting with /sql/
   - Expected: ValidationError raised
   - Assertions: Error message mentions /sql/

4. **test_workspace_config_invalid_token**
   - Input: Very short token (< 10 chars)
   - Expected: ValidationError raised
   - Assertions: Error message about token format

5. **test_workspace_config_empty_required_fields**
   - Input: Empty strings for required fields
   - Expected: ValidationError raised
   - Assertions: All empty fields reported

6. **test_workspace_config_default_workspace_name**
   - Input: No workspace_name provided
   - Expected: workspace_name defaults to "default"
   - Assertions: workspace_name == "default"

7. **test_workspace_config_from_env**
   - Input: Environment variables set
   - Expected: Config created from env vars
   - Assertions: Values match environment

8. **test_workspace_config_from_env_with_prefix**
   - Input: Environment variables with PRODUCTION_ prefix
   - Expected: Config created with production workspace name
   - Assertions: workspace_name == "production"

9. **test_workspace_config_immutable**
   - Input: Valid config
   - Expected: Cannot modify fields after creation
   - Assertions: FrozenInstanceError raised on modification

10. **test_workspace_config_token_not_in_repr**
    - Input: Valid config with token
    - Expected: repr() doesn't include token value
    - Assertions: Token value not in str(config)

#### Test Cases for ServerConfig

11. **test_server_config_default_values**
    - Input: No arguments
    - Expected: Config with default values
    - Assertions: max_response_tokens == 9000

12. **test_server_config_custom_values**
    - Input: Custom max_response_tokens
    - Expected: Config with custom values
    - Assertions: Values match input

13. **test_server_config_invalid_max_tokens_too_low**
    - Input: max_response_tokens < 1000
    - Expected: ValidationError raised
    - Assertions: Error message about minimum

14. **test_server_config_invalid_max_tokens_too_high**
    - Input: max_response_tokens > 25000
    - Expected: ValidationError raised
    - Assertions: Error message about maximum

15. **test_server_config_optional_catalog_schema**
    - Input: Catalog and schema provided
    - Expected: Config with catalog/schema set
    - Assertions: Values match input

16. **test_server_config_json_serialization**
    - Input: Valid ServerConfig
    - Expected: Can convert to/from JSON
    - Assertions: Round-trip preserves values

## Definition of Done

- [ ] All models implemented with proper Pydantic configuration
- [ ] All validators implemented and working
- [ ] `from_env()` class method works for WorkspaceConfig
- [ ] All 16 test cases pass
- [ ] Test coverage is 100% for config/models.py
- [ ] Type hints present on all functions/methods
- [ ] Docstrings added to all classes and methods
- [ ] Code passes `ruff check` and `ruff format`
- [ ] Code reviewed and approved
- [ ] No breaking changes to existing functionality

## Expected Outcome

After completing this story:

1. **Type Safety**: Configuration is strongly typed with Pydantic
2. **Validation**: Invalid configurations are caught at instantiation
3. **Testability**: Easy to create test fixtures with known valid/invalid configs
4. **Documentation**: Models serve as living documentation
5. **Foundation**: Ready for WorkspaceConfigManager (US-1.2) to use these models

### Example Usage
```python
from databricks_tools.config.models import WorkspaceConfig, ServerConfig

# Create from explicit values
config = WorkspaceConfig(
    server_hostname="https://my-workspace.cloud.databricks.com",
    http_path="/sql/1.0/warehouses/abc123",
    access_token="dapi_my_secret_token_here",
    workspace_name="production"
)

# Create from environment variables
prod_config = WorkspaceConfig.from_env(prefix="PRODUCTION_")

# Server configuration
server_config = ServerConfig(
    max_response_tokens=9000,
    default_catalog="analytics",
    default_schema="core"
)
```

## Related User Stories
- **Depends on**: None
- **Blocks**: US-1.2 (Workspace Configuration Manager)
- **Related to**: US-2.2 (Connection Manager will use these models)

## Notes
- This is a foundational story - keep it simple and focused
- No dependencies on existing server.py code yet
- Can be developed and tested in complete isolation
- Sets the pattern for all future configuration handling
