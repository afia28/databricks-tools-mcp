# Role-Based Access Control

## Overview
The Databricks MCP server now supports two roles to control workspace access:

### Analyst Role (Default)
- **Access**: Limited to default workspace only
- **Workspace Parameter Handling**: IGNORED - All workspace parameters are ignored, always uses default
- **Environment Variables**: Uses only DATABRICKS_SERVER_HOSTNAME, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN
- **Use Case**: Business users who work with a single workspace
- **Command**: `uv run databricks_tools.py`

### Developer Role
- **Access**: Full access to all configured workspaces
- **Workspace Parameter Handling**: Uses specified workspace, falls back to default if not found
- **Environment Variables**: Can use prefixed variables (e.g., PRODUCTION_DATABRICKS_*, DEV_DATABRICKS_*)
- **Use Case**: Technical users who need to access multiple workspaces
- **Command**: `uv run databricks_tools.py --developer`

## Configuration

### Analyst Mode (Default)
```yaml
# app.yaml
command: [
  "uv",
  "run",
  "databricks_tools.py"
]

env:
  - name: "DATABRICKS_SERVER_HOSTNAME"
    value: "your-workspace.cloud.databricks.com"
  - name: "DATABRICKS_HTTP_PATH"
    value: "/sql/1.0/warehouses/your-warehouse-id"
  - name: "DATABRICKS_ACCESS_TOKEN"
    valueFrom: "databricks_access_token"
```

### Developer Mode
```yaml
# app_developer.yaml
command: [
  "uv",
  "run",
  "databricks_tools.py",
  "--developer"
]

env:
  # Default workspace
  - name: "DATABRICKS_SERVER_HOSTNAME"
    value: "default.cloud.databricks.com"
  - name: "DATABRICKS_HTTP_PATH"
    value: "/sql/1.0/warehouses/default-id"
  - name: "DATABRICKS_ACCESS_TOKEN"
    valueFrom: "databricks_access_token"

  # Production workspace (optional)
  - name: "PRODUCTION_DATABRICKS_SERVER_HOSTNAME"
    value: "production.cloud.databricks.com"
  - name: "PRODUCTION_DATABRICKS_HTTP_PATH"
    value: "/sql/1.0/warehouses/production-id"
  - name: "PRODUCTION_DATABRICKS_ACCESS_TOKEN"
    valueFrom: "production_token"
```

## Security Benefits
1. **Principle of Least Privilege**: Analysts only see what they need
2. **Reduced Risk**: Non-technical users can't accidentally access production data
3. **Explicit Permission**: Developer access requires explicit flag
4. **Audit Trail**: Mode selection is visible in server startup logs

## Workspace Parameter Behavior

### Analyst Mode
- **All workspace parameters are IGNORED**
- Tool calls always use the default workspace
- No errors thrown - seamless operation for non-technical users
- Example: `run_query("SELECT * FROM table", workspace="production")` → Uses default workspace

### Developer Mode
- **Workspace parameters are respected**
- If workspace not found, falls back to default with a warning
- Example: `run_query("SELECT * FROM table", workspace="production")` → Uses production workspace
- Example: `run_query("SELECT * FROM table", workspace="nonexistent")` → Falls back to default with warning

## Key Features
1. **No Exceptions in Analyst Mode**: Workspace parameters are silently ignored, ensuring smooth operation
2. **Graceful Fallback in Developer Mode**: Invalid workspaces fall back to default instead of throwing errors
3. **Clear Docstrings**: All functions document the role-based behavior for LLM tool calls
4. **Startup Notification**: Server prints the active mode on startup for transparency
