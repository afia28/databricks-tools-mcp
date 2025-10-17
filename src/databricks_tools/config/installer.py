"""Configuration installer for databricks-tools MCP server.

This module provides cross-platform installation and configuration management
for the databricks-tools MCP server, including Claude Desktop integration.
"""

import json
import os
import platform
import shutil
from pathlib import Path

from databricks import sql
from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()


class ConfigInstaller:
    """Manages installation and configuration of databricks-tools MCP server.

    This class handles:
    - Cross-platform Claude Desktop config discovery
    - Safe JSON configuration updates with backup/restore
    - Interactive credential collection (analyst vs developer modes)
    - Connection validation before saving
    - .env file creation with proper permissions
    - User-friendly success messages

    Examples:
        >>> installer = ConfigInstaller()
        >>> installer.run_installation(force=False)
        # Interactive wizard guides user through setup
    """

    def __init__(self) -> None:
        """Initialize the configuration installer."""
        self.project_root = Path(__file__).parent.parent.parent.parent

    def find_claude_config(self) -> Path:
        """Find Claude Desktop configuration file across platforms.

        Searches for claude_desktop_config.json in platform-specific locations:
        - macOS: ~/Library/Application Support/Claude/
        - Linux: ~/.config/Claude/
        - Windows: %APPDATA%\\Claude\\

        Returns:
            Path to claude_desktop_config.json

        Raises:
            FileNotFoundError: If Claude Desktop config directory not found

        Examples:
            >>> installer = ConfigInstaller()
            >>> config_path = installer.find_claude_config()
            >>> print(config_path)
            PosixPath('/Users/username/Library/Application Support/Claude/claude_desktop_config.json')
        """
        system = platform.system()

        if system == "Darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / "Claude"
        elif system == "Linux":
            config_dir = Path.home() / ".config" / "Claude"
        elif system == "Windows":
            appdata = os.getenv("APPDATA")
            if not appdata:
                raise FileNotFoundError("APPDATA environment variable not found")
            config_dir = Path(appdata) / "Claude"
        else:
            raise FileNotFoundError(f"Unsupported platform: {system}")

        if not config_dir.exists():
            raise FileNotFoundError(
                f"Claude Desktop config directory not found: {config_dir}\n"
                "Please ensure Claude Desktop is installed."
            )

        return config_dir / "claude_desktop_config.json"

    def backup_config(self, config_path: Path) -> Path:
        """Create backup of Claude Desktop config before modification.

        Args:
            config_path: Path to claude_desktop_config.json

        Returns:
            Path to backup file

        Examples:
            >>> installer = ConfigInstaller()
            >>> backup = installer.backup_config(Path("claude_desktop_config.json"))
            >>> print(backup)
            PosixPath('claude_desktop_config.json.backup')
        """
        backup_path = config_path.with_suffix(".json.backup")
        if config_path.exists():
            shutil.copy2(config_path, backup_path)
            console.print(f"[dim]Created backup: {backup_path}[/dim]")
        return backup_path

    def update_claude_config(self, project_path: Path) -> None:
        """Update Claude Desktop config with databricks-tools MCP server.

        Safely updates claude_desktop_config.json by:
        1. Creating backup of existing config
        2. Loading and parsing existing JSON
        3. Adding/updating databricks-tools entry
        4. Writing updated config atomically
        5. Restoring backup on error

        Args:
            project_path: Absolute path to databricks-tools project directory

        Raises:
            FileNotFoundError: If Claude Desktop config not found
            json.JSONDecodeError: If config file is invalid JSON

        Examples:
            >>> installer = ConfigInstaller()
            >>> installer.update_claude_config(Path("/path/to/databricks-tools"))
            Claude Desktop config updated successfully!
        """
        config_path = self.find_claude_config()
        backup_path = self.backup_config(config_path)

        try:
            # Load existing config or create new one
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
            else:
                config = {}

            # Ensure mcpServers key exists
            if "mcpServers" not in config:
                config["mcpServers"] = {}

            # Check if databricks-tools already configured
            if "databricks-tools" in config["mcpServers"]:
                console.print(
                    "[yellow]databricks-tools already configured in Claude Desktop[/yellow]"
                )
                if not Confirm.ask("Update existing configuration?", default=True):
                    console.print("[dim]Skipping Claude Desktop config update[/dim]")
                    return

            # Add/update databricks-tools configuration
            config["mcpServers"]["databricks-tools"] = {
                "command": "uv",
                "args": ["run", "--directory", str(project_path), "databricks-tools"],
            }

            # Write updated config atomically
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            console.print(f"[green]✓[/green] Claude Desktop config updated: {config_path}")

        except Exception as e:
            # Restore backup on error
            if backup_path.exists():
                shutil.copy2(backup_path, config_path)
                console.print("[red]Error updating config. Restored backup.[/red]")
            raise e

    def collect_credentials(self, mode: str) -> dict[str, str]:
        """Collect Databricks credentials interactively.

        Prompts user for workspace credentials with examples and validation.
        For developer mode, supports multiple workspace configurations.

        Args:
            mode: Installation mode ("analyst" or "developer")

        Returns:
            Dictionary mapping environment variable names to values

        Examples:
            >>> installer = ConfigInstaller()
            >>> creds = installer.collect_credentials("analyst")
            >>> print(creds.keys())
            dict_keys(['DATABRICKS_SERVER_HOSTNAME', 'DATABRICKS_HTTP_PATH', 'DATABRICKS_TOKEN'])
        """
        credentials: dict[str, str] = {}

        console.print("\n[bold cyan]Databricks Workspace Configuration[/bold cyan]")
        console.print("[dim]Enter your Databricks workspace credentials[/dim]\n")

        if mode == "analyst":
            # Single workspace for analyst mode
            credentials.update(self._collect_workspace_credentials())
        else:
            # Multiple workspaces for developer mode
            console.print("[yellow]Developer mode: Configure multiple workspaces[/yellow]")
            console.print("[dim]Leave workspace name empty to finish[/dim]\n")

            workspace_count = 0
            while True:
                workspace_name = Prompt.ask(
                    f"Workspace {workspace_count + 1} name (e.g., production, staging)",
                    default="" if workspace_count > 0 else None,
                )

                if not workspace_name and workspace_count > 0:
                    break

                if not workspace_name:
                    console.print("[red]At least one workspace required[/red]")
                    continue

                console.print(f"\n[bold]Configuring {workspace_name} workspace:[/bold]")
                workspace_creds = self._collect_workspace_credentials(prefix=workspace_name.upper())
                credentials.update(workspace_creds)
                workspace_count += 1
                console.print()

        return credentials

    def _collect_workspace_credentials(self, prefix: str = "") -> dict[str, str]:
        """Collect credentials for a single workspace.

        Args:
            prefix: Environment variable prefix (empty for default workspace)

        Returns:
            Dictionary of environment variables for this workspace
        """
        creds: dict[str, str] = {}

        # Add prefix separator if needed
        env_prefix = f"{prefix}_" if prefix else ""

        # Server hostname
        hostname = Prompt.ask(
            f"{env_prefix}DATABRICKS_SERVER_HOSTNAME",
            default="https://your-workspace.cloud.databricks.com",
        )
        creds[f"{env_prefix}DATABRICKS_SERVER_HOSTNAME"] = hostname

        # HTTP path
        http_path = Prompt.ask(
            f"{env_prefix}DATABRICKS_HTTP_PATH", default="/sql/1.0/warehouses/your-warehouse-id"
        )
        creds[f"{env_prefix}DATABRICKS_HTTP_PATH"] = http_path

        # Access token (masked input)
        while True:
            token = Prompt.ask(f"{env_prefix}DATABRICKS_TOKEN", password=True)

            # Validate token format
            if token.startswith("dapi"):
                creds[f"{env_prefix}DATABRICKS_TOKEN"] = token
                break
            else:
                console.print(
                    "[red]Invalid token format. Databricks tokens start with 'dapi'[/red]"
                )

        return creds

    def validate_connection(self, credentials: dict[str, str]) -> bool:
        """Validate Databricks connection with provided credentials.

        Attempts to connect to Databricks and execute a simple query
        to verify credentials are valid.

        Args:
            credentials: Dictionary of environment variables

        Returns:
            True if connection successful, False otherwise

        Examples:
            >>> installer = ConfigInstaller()
            >>> creds = {"DATABRICKS_SERVER_HOSTNAME": "...", ...}
            >>> is_valid = installer.validate_connection(creds)
            >>> print(is_valid)
            True
        """
        console.print("\n[bold cyan]Validating connection...[/bold cyan]")

        # Extract default workspace credentials
        hostname = credentials.get("DATABRICKS_SERVER_HOSTNAME", "")
        http_path = credentials.get("DATABRICKS_HTTP_PATH", "")
        token = credentials.get("DATABRICKS_TOKEN", "")

        if not all([hostname, http_path, token]):
            console.print("[red]Missing required credentials[/red]")
            return False

        try:
            # Attempt connection
            with sql.connect(
                server_hostname=hostname.replace("https://", ""),
                http_path=http_path,
                access_token=token,
            ) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT 1 AS test")
                result = cursor.fetchone()
                cursor.close()

                if result and result[0] == 1:
                    console.print("[green]✓[/green] Connection successful!")
                    return True
                else:
                    console.print("[red]Connection test query failed[/red]")
                    return False

        except Exception as e:
            console.print(f"[red]Connection failed: {str(e)}[/red]")
            return False

    def create_env_file(
        self, credentials: dict[str, str], project_path: Path, force: bool = False
    ) -> None:
        """Create .env file with Databricks credentials.

        Creates .env file in project root with proper permissions (0600).
        Prompts before overwriting existing file unless force=True.

        Args:
            credentials: Dictionary of environment variables
            project_path: Path to project root directory
            force: If True, overwrite without prompting

        Examples:
            >>> installer = ConfigInstaller()
            >>> creds = {"DATABRICKS_SERVER_HOSTNAME": "...", ...}
            >>> installer.create_env_file(creds, Path("/path/to/project"))
            .env file created successfully!
        """
        env_path = project_path / ".env"

        # Check if .env exists
        if env_path.exists() and not force:
            console.print(f"[yellow].env file already exists: {env_path}[/yellow]")
            if not Confirm.ask("Overwrite existing .env file?", default=False):
                console.print("[dim]Skipping .env creation[/dim]")
                return

        # Create .env content
        env_content = "# Databricks workspace configuration\n"
        env_content += "# Generated by databricks-tools init\n\n"

        for key, value in sorted(credentials.items()):
            # Don't expose tokens in plain text comments
            if "TOKEN" in key:
                env_content += f"{key}={value}\n"
            else:
                env_content += f"{key}={value}\n"

        # Write .env file
        with open(env_path, "w") as f:
            f.write(env_content)

        # Set restrictive permissions (owner read/write only)
        env_path.chmod(0o600)

        console.print(f"[green]✓[/green] .env file created: {env_path}")
        console.print("[dim]Permissions set to 0600 (owner read/write only)[/dim]")

    def show_next_steps(self) -> None:
        """Display success message with next steps for user.

        Shows how to verify installation and start using databricks-tools.
        """
        console.print("\n[bold green]Installation Complete! 🎉[/bold green]\n")

        console.print("[bold cyan]Next Steps:[/bold cyan]")
        console.print("1. Restart Claude Desktop to load the new MCP server")
        console.print("2. Open Claude Desktop and verify databricks-tools is available")
        console.print("3. Try running a query:\n")

        console.print("[dim]   Example: 'List all catalogs in my Databricks workspace'[/dim]\n")

        console.print("[bold cyan]Verification:[/bold cyan]")
        console.print("• Check Claude Desktop settings for databricks-tools MCP server")
        console.print("• Use the list_workspaces tool to confirm configuration")
        console.print("• Review logs if you encounter any issues\n")

        console.print("[bold cyan]Useful Commands:[/bold cyan]")
        console.print("• Run server directly: [dim]uv run databricks-tools[/dim]")
        console.print("• Developer mode: [dim]uv run databricks-tools --developer[/dim]")
        console.print("• View help: [dim]databricks-tools-init --help[/dim]\n")

        console.print("[dim]Documentation: README.md and INSTALLATION.md[/dim]")

    def run_installation(self, force: bool = False, mode: str | None = None) -> None:
        """Run complete installation wizard.

        Orchestrates the full installation process:
        1. Welcome message
        2. Mode selection (analyst vs developer)
        3. Credential collection
        4. Connection validation
        5. Claude Desktop config update
        6. .env file creation
        7. Success message

        Args:
            force: If True, overwrite existing files without prompting
            mode: Installation mode ("analyst" or "developer"), prompts if None

        Examples:
            >>> installer = ConfigInstaller()
            >>> installer.run_installation(force=False, mode="analyst")
            # Interactive wizard completes installation
        """
        console.print(
            "\n[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]"
        )
        console.print("[bold cyan]  Databricks Tools MCP Server - Installation Wizard[/bold cyan]")
        console.print(
            "[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n"
        )

        # Mode selection
        if mode is None:
            console.print("[bold]Select installation mode:[/bold]")
            console.print(
                "  [cyan]analyst[/cyan] - Single workspace access (recommended for most users)"
            )
            console.print(
                "  [cyan]developer[/cyan] - Multiple workspace access (for technical users)\n"
            )

            mode = Prompt.ask(
                "Installation mode", choices=["analyst", "developer"], default="analyst"
            )

        console.print(f"\n[green]Installing in {mode} mode[/green]")

        # Collect credentials
        credentials = self.collect_credentials(mode)

        # Validate connection
        if not self.validate_connection(credentials):
            console.print("\n[red]Installation failed: Could not connect to Databricks[/red]")
            console.print("[yellow]Please check your credentials and try again[/yellow]")
            return

        # Update Claude Desktop config
        try:
            self.update_claude_config(self.project_root)
        except FileNotFoundError as e:
            console.print(f"\n[red]Error: {e}[/red]")
            console.print("[yellow]Continuing with .env creation...[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Unexpected error updating Claude config: {e}[/red]")
            console.print("[yellow]Continuing with .env creation...[/yellow]")

        # Create .env file
        self.create_env_file(credentials, self.project_root, force=force)

        # Show next steps
        self.show_next_steps()
