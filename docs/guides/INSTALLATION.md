# Installation Guide - Databricks Tools MCP Server

This guide provides step-by-step instructions for installing and configuring the databricks-tools MCP server for Claude Desktop.

## Prerequisites

Before installing databricks-tools, ensure you have:

1. **Claude Desktop** installed on your system
   - Download from: https://claude.ai/desktop

2. **Python 3.10 or higher**
   ```bash
   python --version  # Should show 3.10 or higher
   ```

3. **uv package manager** (recommended)
   ```bash
   # Install uv (if not already installed)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

4. **Databricks workspace credentials**
   - Server hostname (e.g., `https://your-workspace.cloud.databricks.com`)
   - HTTP path to SQL warehouse (e.g., `/sql/1.0/warehouses/your-warehouse-id`)
   - Personal access token (starts with `dapi`)

## Installation Methods

### Method 1: Interactive Installation Wizard (Recommended)

The interactive wizard is the easiest way to install databricks-tools. It will guide you through credential collection, validation, and configuration.

1. **Clone the repository**
   ```bash
   git clone https://github.com/afia28/databricks-tools.git
   cd databricks-tools
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Run the installation wizard**
   ```bash
   uv run databricks-tools-init
   ```

4. **Follow the prompts**
   - Choose installation mode (analyst or developer)
   - Enter Databricks workspace credentials
   - Wait for connection validation
   - Confirm Claude Desktop configuration update

5. **Restart Claude Desktop**

The wizard will:
- Validate your credentials before saving
- Update Claude Desktop configuration automatically
- Create a secure `.env` file with proper permissions
- Show next steps for verification

### Method 2: Manual Installation

If you prefer manual configuration or the wizard isn't working:

1. **Clone and install**
   ```bash
   git clone https://github.com/afia28/databricks-tools.git
   cd databricks-tools
   uv sync
   ```

2. **Create .env file**
   ```bash
   cp .env.example .env
   ```

3. **Edit .env with your credentials**
   ```bash
   # For analyst mode (single workspace)
   DATABRICKS_SERVER_HOSTNAME=https://your-workspace.cloud.databricks.com
   DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
   DATABRICKS_TOKEN=dapi_your_token_here
   ```

   For developer mode (multiple workspaces), add prefixed variables:
   ```bash
   # Production workspace
   PRODUCTION_DATABRICKS_SERVER_HOSTNAME=https://prod.cloud.databricks.com
   PRODUCTION_DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/prod-id
   PRODUCTION_DATABRICKS_TOKEN=dapi_prod_token

   # Staging workspace
   STAGING_DATABRICKS_SERVER_HOSTNAME=https://staging.cloud.databricks.com
   STAGING_DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/staging-id
   STAGING_DATABRICKS_TOKEN=dapi_staging_token
   ```

4. **Set secure permissions**
   ```bash
   chmod 600 .env
   ```

5. **Update Claude Desktop configuration**

   Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):
   ```json
   {
     "mcpServers": {
       "databricks-tools": {
         "command": "uv",
         "args": [
           "run",
           "--directory",
           "/absolute/path/to/databricks-tools",
           "databricks-tools"
         ]
       }
     }
   }
   ```

   **Note:** Replace `/absolute/path/to/databricks-tools` with the actual path.

   Linux: `~/.config/Claude/claude_desktop_config.json`
   Windows: `%APPDATA%\Claude\claude_desktop_config.json`

6. **Restart Claude Desktop**

## Installation Modes

### Analyst Mode (Default)

Recommended for most users. Provides access to a single Databricks workspace.

**Features:**
- Simple configuration (3 environment variables)
- Single workspace access
- Workspace parameter ignored in all tools
- Ideal for business analysts and data scientists

**Installation:**
```bash
uv run databricks-tools-init --mode analyst
```

**Running:**
```bash
uv run databricks-tools  # No --developer flag needed
```

### Developer Mode

For technical users who need access to multiple Databricks workspaces.

**Features:**
- Multiple workspace configuration
- Switch between workspaces using workspace parameter
- Ideal for data engineers and platform engineers

**Installation:**
```bash
uv run databricks-tools-init --mode developer
```

**Running:**
```bash
uv run databricks-tools --developer
```

## Verification

After installation, verify databricks-tools is working:

1. **Open Claude Desktop**

2. **Check MCP servers in settings**
   - Look for "databricks-tools" in the MCP servers list
   - Ensure it shows as connected (green indicator)

3. **Test with a simple query**
   ```
   Ask Claude: "List all workspaces configured in databricks-tools"
   ```

   Expected response:
   ```
   Available workspaces:
   - default (or your configured workspace names)
   ```

4. **Test catalog access**
   ```
   Ask Claude: "List all catalogs in my Databricks workspace"
   ```

   Should return a list of Unity Catalog catalogs.

## Troubleshooting

### Claude Desktop doesn't show databricks-tools

**Possible causes:**
- Claude Desktop config file not updated correctly
- Invalid JSON in claude_desktop_config.json
- Incorrect project path in configuration

**Solutions:**
1. Check Claude Desktop config file exists
2. Validate JSON syntax (use `jq` or online validator)
3. Verify absolute path in config is correct
4. Restart Claude Desktop completely (quit and reopen)

### Connection validation fails during installation

**Possible causes:**
- Invalid Databricks credentials
- Network connectivity issues
- Incorrect server hostname or HTTP path
- Expired access token

**Solutions:**
1. Verify credentials in Databricks workspace settings
2. Check token hasn't expired (regenerate if needed)
3. Ensure server hostname starts with `https://`
4. Verify HTTP path format: `/sql/1.0/warehouses/<id>`
5. Test connection manually:
   ```bash
   uv run python -c "
   from databricks import sql
   conn = sql.connect(
       server_hostname='your-workspace.cloud.databricks.com',
       http_path='/sql/1.0/warehouses/your-id',
       access_token='dapi_your_token'
   )
   cursor = conn.cursor()
   cursor.execute('SELECT 1')
   print(cursor.fetchone())
   "
   ```

### Permission denied error on .env file

**Cause:** File permissions too restrictive or .env owned by different user

**Solution:**
```bash
chmod 600 .env
chown $USER .env
```

### databricks-tools-init command not found

**Possible causes:**
- Dependencies not installed
- Entry point not registered

**Solutions:**
1. Run `uv sync` to install dependencies
2. Use full command: `uv run databricks-tools-init`

### MCP server crashes or disconnects

**Possible causes:**
- Invalid environment variables
- Missing dependencies
- Python version incompatibility

**Solutions:**
1. Check `.env` file format
2. Verify Python version: `python --version`
3. Reinstall dependencies: `uv sync --force`
4. Check Claude Desktop logs for error messages

## Getting Databricks Credentials

### Server Hostname

1. Log into your Databricks workspace
2. Copy the URL from your browser
3. Format: `https://your-workspace.cloud.databricks.com`
4. Remove any trailing path (e.g., `/workspace`, `/sql/editor`)

### HTTP Path

1. In Databricks, go to **SQL Warehouses**
2. Select your warehouse
3. Click **Connection Details** tab
4. Copy the **HTTP Path**
5. Format: `/sql/1.0/warehouses/abc123def456`

### Access Token

1. In Databricks, click your **user icon** (top right)
2. Select **User Settings**
3. Go to **Developer** → **Access Tokens**
4. Click **Generate New Token**
5. Set a comment (e.g., "Claude Desktop MCP")
6. Set lifetime (recommended: 90 days)
7. Click **Generate**
8. **Copy the token immediately** (you won't see it again)
9. Token format: `dapi...` (starts with "dapi")

**Security Best Practices:**
- Store token securely (never commit to git)
- Set reasonable token lifetime (30-90 days)
- Rotate tokens regularly
- Use service principals for production environments

## Updating Configuration

To update your configuration after initial installation:

```bash
# Run installation wizard again (will prompt before overwriting)
uv run databricks-tools-init

# Force overwrite without prompting
uv run databricks-tools-init --force

# Change mode
uv run databricks-tools-init --mode developer
```

The wizard is idempotent - safe to run multiple times.

## Uninstallation

To remove databricks-tools:

1. **Remove from Claude Desktop config**

   Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       // Remove "databricks-tools" entry
     }
   }
   ```

2. **Delete project directory**
   ```bash
   rm -rf /path/to/databricks-tools
   ```

3. **Restart Claude Desktop**

## Next Steps

After successful installation:

1. **Read the documentation**
   - [README.md](README.md) - Overview and features
   - [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture
   - [ROLES.md](ROLES.md) - Role-based access control

2. **Explore examples**
   - [examples/basic_usage.py](examples/basic_usage.py)
   - [examples/advanced_queries.py](examples/advanced_queries.py)

3. **Try common tasks**
   - List catalogs and schemas
   - Query table metadata
   - Execute SQL queries
   - Explore UDFs

## Support

For issues or questions:

- Check [Troubleshooting](#troubleshooting) section above
- Review [CLAUDE.md](CLAUDE.md) for development guidance
- Open an issue on GitHub: https://github.com/afia28/databricks-tools/issues

## Security Notes

- Never commit `.env` file to version control (already in `.gitignore`)
- Use `.env` file permissions of 0600 (owner read/write only)
- Rotate Databricks tokens regularly
- Consider using Databricks service principals for production
- Review Databricks audit logs periodically
