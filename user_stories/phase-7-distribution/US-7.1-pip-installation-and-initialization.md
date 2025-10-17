# US-7.1: Pip Installation and Initialization

## Metadata
- **Story ID**: US-7.1
- **Title**: Pip Installation and User-Friendly Initialization
- **Phase**: Phase 7 - Distribution & Deployment
- **Estimated LOC**: ~350 lines
- **Dependencies**: None (extends existing project)
- **Status**: ⬜ Not Started

## Overview
Create a pip-installable package with user-friendly CLI initialization command that guides non-technical users through setup, automatically configures Claude Desktop, and creates the required environment files.

## User Story
**As a** non-technical user in the organization
**I want** to install databricks-tools via pip and run a simple initialization command
**So that** I can set up the MCP server without manual configuration or technical knowledge

## Acceptance Criteria
1. ✅ Project is pip-installable from private GitHub repo using `pip install git+https://github.com/org/databricks-tools.git`
2. ✅ CLI command `databricks-tools init` launches interactive setup wizard
3. ✅ Wizard prompts for Databricks credentials with clear instructions and examples
4. ✅ Claude Desktop config file is automatically located across macOS/Linux/Windows
5. ✅ MCP server configuration is added/updated in claude_desktop_config.json preserving existing entries
6. ✅ Project .env file is created with user-provided credentials (never overwrites without confirmation)
7. ✅ User can choose between analyst mode (single workspace) or developer mode (multiple workspaces)
8. ✅ Setup validates credentials by attempting a test connection before saving
9. ✅ Clear success message shows next steps and how to verify installation
10. ✅ Idempotent operation - safe to run multiple times without breaking existing config

## Technical Requirements

### Package Configuration (pyproject.toml)
```python
[project]
name = "databricks-tools"
version = "0.2.0"  # Bump version for distribution
# ... existing config ...

dependencies = [
    # ... existing dependencies ...
    "click>=8.1.0",  # CLI framework
    "rich>=13.0.0",  # Pretty terminal output
]

[project.scripts]
databricks-tools = "databricks_tools.server:main"
databricks-tools-init = "databricks_tools.cli.init:init_command"
```

### CLI Initialization Module (src/databricks_tools/cli/init.py)
```python
import click
import json
import platform
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from databricks_tools.config.installer import ConfigInstaller

console = Console()

@click.command()
@click.option('--mode', type=click.Choice(['analyst', 'developer']),
              help='Configuration mode (analyst=single workspace, developer=multiple)')
def init_command(mode: Optional[str] = None):
    """Initialize Databricks Tools MCP server configuration."""
    console.print("[bold blue]Welcome to Databricks Tools Setup Wizard![/bold blue]")

    # Step 1: Determine mode
    if not mode:
        mode = Prompt.ask(
            "Select configuration mode",
            choices=["analyst", "developer"],
            default="analyst"
        )

    # Step 2: Collect credentials
    installer = ConfigInstaller()
    credentials = installer.collect_credentials(mode)

    # Step 3: Validate connection
    if installer.validate_connection(credentials):
        console.print("[green]✓ Connection successful![/green]")
    else:
        if not Confirm.ask("[yellow]Connection failed. Continue anyway?[/yellow]"):
            return

    # Step 4: Update Claude Desktop config
    installer.update_claude_config()

    # Step 5: Create .env file
    installer.create_env_file(credentials)

    console.print("[bold green]Setup complete![/bold green]")
    installer.show_next_steps()
```

### Configuration Installer (src/databricks_tools/config/installer.py)
```python
class ConfigInstaller:
    """Handles installation and configuration of databricks-tools."""

    def find_claude_config(self) -> Path:
        """Locate Claude Desktop config file based on OS."""
        system = platform.system()

        if system == "Darwin":  # macOS
            paths = [
                Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
                Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
            ]
        elif system == "Linux":
            paths = [
                Path.home() / ".config" / "Claude" / "claude_desktop_config.json",
                Path.home() / ".local" / "share" / "Claude" / "claude_desktop_config.json"
            ]
        elif system == "Windows":
            paths = [
                Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json",
                Path.home() / "AppData" / "Local" / "Claude" / "claude_desktop_config.json"
            ]
        else:
            raise OSError(f"Unsupported operating system: {system}")

        for path in paths:
            if path.exists():
                return path

        # If not found, create in first location
        first_path = paths[0]
        first_path.parent.mkdir(parents=True, exist_ok=True)
        return first_path

    def update_claude_config(self) -> None:
        """Add or update MCP server configuration in Claude Desktop."""
        config_path = self.find_claude_config()

        # Load existing config or create new
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}

        # Ensure mcpServers exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        # Add databricks-tools configuration
        project_dir = Path.cwd().absolute()
        config["mcpServers"]["databricks-tools"] = {
            "command": "uv",
            "args": [
                "run",
                "--directory",
                str(project_dir),
                "databricks-tools"
            ]
        }

        # Write config with proper formatting
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

    def collect_credentials(self, mode: str) -> dict[str, str]:
        """Interactively collect Databricks credentials."""
        credentials = {}

        console.print("\n[bold]Enter your Databricks credentials:[/bold]")
        console.print("[dim]Example: https://your-workspace.cloud.databricks.com[/dim]")

        if mode == "analyst":
            # Single workspace configuration
            credentials["DATABRICKS_SERVER_HOSTNAME"] = Prompt.ask("Server hostname")
            credentials["DATABRICKS_HTTP_PATH"] = Prompt.ask(
                "HTTP path",
                default="/sql/1.0/warehouses/your-warehouse-id"
            )
            credentials["DATABRICKS_TOKEN"] = Prompt.ask("Access token", password=True)
        else:
            # Multiple workspace configuration
            console.print("\n[bold]Configure multiple workspaces:[/bold]")
            workspaces = ["PRODUCTION", "DEV", "STAGING"]

            for workspace in workspaces:
                if Confirm.ask(f"Configure {workspace} workspace?"):
                    prefix = f"{workspace}_DATABRICKS"
                    credentials[f"{prefix}_SERVER_HOSTNAME"] = Prompt.ask(
                        f"{workspace} server hostname"
                    )
                    credentials[f"{prefix}_HTTP_PATH"] = Prompt.ask(
                        f"{workspace} HTTP path",
                        default="/sql/1.0/warehouses/your-warehouse-id"
                    )
                    credentials[f"{prefix}_TOKEN"] = Prompt.ask(
                        f"{workspace} access token",
                        password=True
                    )

        return credentials
```

## Design Patterns Used

1. **Command Pattern**: Click commands encapsulate initialization logic as discrete, testable operations
2. **Template Method Pattern**: ConfigInstaller defines the initialization workflow with customizable steps for different OS platforms
3. **Strategy Pattern**: Different credential collection strategies for analyst vs developer modes
4. **Builder Pattern**: Progressive construction of configuration through wizard steps

## Key Implementation Notes

### Security Considerations
- Never log or display access tokens in plain text
- Use click's password=True for token input to mask characters
- Validate tokens are in correct format (start with "dapi")
- Store credentials only in local .env file with appropriate permissions

### Cross-Platform File Discovery
```python
# Claude Desktop config locations by OS
macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
Linux: ~/.config/Claude/claude_desktop_config.json
Windows: %APPDATA%\Claude\claude_desktop_config.json
```

### User Experience Guidelines
- Use Rich library for colored, formatted output
- Provide examples for every input field
- Show progress indicators during validation
- Offer rollback if any step fails
- Clear success/error messages with next steps

### JSON Manipulation Safety
- Always preserve existing mcpServers entries
- Create backup before modifying claude_desktop_config.json
- Validate JSON structure before writing
- Handle missing directories gracefully

### Idempotency Requirements
- Check if .env exists before overwriting (prompt user)
- Detect existing MCP server entry and update vs add
- Support --force flag for automation scenarios
- Log all changes made for audit trail

## Files to Create/Modify

**Files to Create:**
- `src/databricks_tools/cli/__init__.py` - CLI package marker
- `src/databricks_tools/cli/init.py` - Main initialization command (~150 lines)
- `src/databricks_tools/config/installer.py` - Configuration installer class (~200 lines)
- `INSTALLATION.md` - Detailed installation guide for users (~100 lines)
- `tests/test_cli/__init__.py` - Test package marker
- `tests/test_cli/test_init.py` - CLI initialization tests (~200 lines)
- `tests/test_config/test_installer.py` - Installer tests (~250 lines)

**Files to Modify:**
- `pyproject.toml` - Add CLI dependencies and entry point (~10 lines)
- `README.md` - Add installation section (~30 lines)
- `src/databricks_tools/__init__.py` - Export version info (~5 lines)

## Test Cases

### CLI Command Tests
1. `test_init_command_analyst_mode` - Test analyst mode initialization flow
2. `test_init_command_developer_mode` - Test developer mode with multiple workspaces
3. `test_init_command_with_mode_flag` - Test --mode flag bypasses prompt
4. `test_init_command_keyboard_interrupt` - Test graceful Ctrl+C handling
5. `test_init_command_validation_failure_continue` - Test continuing after connection failure

### Config Discovery Tests
6. `test_find_claude_config_macos` - Test macOS config path discovery
7. `test_find_claude_config_linux` - Test Linux config path discovery
8. `test_find_claude_config_windows` - Test Windows config path discovery
9. `test_find_claude_config_creates_if_missing` - Test directory creation
10. `test_find_claude_config_unsupported_os` - Test error on unsupported OS

### Config Update Tests
11. `test_update_claude_config_new_file` - Test creating new config file
12. `test_update_claude_config_preserve_existing` - Test preserving other MCP servers
13. `test_update_claude_config_update_existing_entry` - Test updating databricks-tools entry
14. `test_update_claude_config_json_validation` - Test JSON structure validation
15. `test_update_claude_config_backup_creation` - Test backup before modification

### Credential Collection Tests
16. `test_collect_credentials_analyst_mode` - Test single workspace credential collection
17. `test_collect_credentials_developer_mode_all` - Test multiple workspace collection
18. `test_collect_credentials_developer_mode_selective` - Test skipping workspaces
19. `test_validate_connection_success` - Test successful connection validation
20. `test_validate_connection_invalid_token` - Test invalid token detection

### Installation Flow Tests
21. `test_create_env_file_new` - Test creating new .env file
22. `test_create_env_file_exists_prompt` - Test prompting when .env exists
23. `test_installation_idempotency` - Test running init multiple times safely
24. `test_installation_rollback_on_error` - Test cleanup on failure
25. `test_show_next_steps_output` - Test success message and instructions

## Definition of Done

- [ ] Package is pip-installable with all dependencies resolved
- [ ] `databricks-tools init` command launches interactive wizard
- [ ] Wizard collects credentials with proper validation and masking
- [ ] Claude Desktop config automatically discovered on macOS/Linux/Windows
- [ ] MCP server entry added/updated in claude_desktop_config.json
- [ ] .env file created with correct format and permissions (0600)
- [ ] Connection validation attempts test query before saving
- [ ] All 25 test cases passing with 90%+ coverage
- [ ] Installation guide (INSTALLATION.md) with screenshots/examples
- [ ] README.md updated with installation instructions
- [ ] Type hints added for all new functions
- [ ] Pre-commit hooks pass (ruff, mypy, pytest)
- [ ] Error messages are clear and actionable for non-technical users
- [ ] Tested on macOS, Linux, and Windows platforms
- [ ] Package version bumped to 0.2.0

## Expected Outcome

After running `pip install git+https://github.com/org/databricks-tools.git` and `databricks-tools init`, non-technical users will have:

1. **Fully configured MCP server** in Claude Desktop without manual JSON editing
2. **Working .env file** with their Databricks credentials properly formatted
3. **Validated connection** confirming their credentials work
4. **Clear next steps** showing how to test the integration

Example success output:
```
$ databricks-tools init

Welcome to Databricks Tools Setup Wizard!

Select configuration mode [analyst/developer]: analyst
Enter your Databricks credentials:
Server hostname: https://mycompany.cloud.databricks.com
HTTP path [/sql/1.0/warehouses/your-warehouse-id]: /sql/1.0/warehouses/abc123
Access token: ****

Validating connection... ✓ Connection successful!
Updating Claude Desktop configuration... ✓
Creating environment file... ✓

Setup complete!

Next steps:
1. Restart Claude Desktop to load the new configuration
2. Look for "databricks-tools" in Claude's MCP servers
3. Try asking Claude: "List my Databricks workspaces"

Need help? See INSTALLATION.md for troubleshooting.
```

## Related Stories
- **Depends on**: None (extends existing project)
- **Blocks**: Future distribution enhancements (US-7.2+)
- **Related**: All existing stories (makes their functionality accessible)
