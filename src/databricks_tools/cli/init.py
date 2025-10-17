"""Interactive CLI initialization wizard for databricks-tools MCP server.

This module provides the main CLI entry point for setting up databricks-tools,
including interactive credential collection, connection validation, and
Claude Desktop integration.
"""

import sys

import click
from rich.console import Console

from databricks_tools.config.installer import ConfigInstaller

console = Console()


@click.command(name="init")  # type: ignore[misc]
@click.option(  # type: ignore[misc]
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing configuration without prompting",
)
@click.option(  # type: ignore[misc]
    "--mode",
    type=click.Choice(["analyst", "developer"], case_sensitive=False),
    help="Installation mode (analyst=single workspace, developer=multiple workspaces)",
)
def init_command(force: bool, mode: str | None) -> None:
    """Initialize databricks-tools MCP server configuration.

    This interactive wizard will:
    • Collect Databricks workspace credentials
    • Validate connection to Databricks
    • Update Claude Desktop configuration
    • Create .env file with credentials
    • Display next steps for using databricks-tools

    Examples:
        $ databricks-tools-init
        $ databricks-tools-init --mode analyst
        $ databricks-tools-init --mode developer --force
    """
    try:
        installer = ConfigInstaller()
        installer.run_installation(force=force, mode=mode)
        sys.exit(0)
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Installation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Installation failed: {e}[/red]")
        console.print("[yellow]Please check the error message and try again[/yellow]")
        sys.exit(1)


if __name__ == "__main__":
    init_command()
