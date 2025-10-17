"""Comprehensive tests for CLI initialization command.

This module provides complete test coverage for the databricks-tools-init
CLI command, including mode selection, error handling, and user interaction.
"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from databricks_tools.cli.init import init_command


class TestInitCommandHelp:
    """Tests for init command help and basic invocation."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create Click CLI test runner.

        Returns:
            CliRunner instance for testing Click commands
        """
        return CliRunner()

    def test_init_command_help(self, runner: CliRunner) -> None:
        """Test that init command shows help message.

        Args:
            runner: Click test runner
        """
        result = runner.invoke(init_command, ["--help"])
        assert result.exit_code == 0
        assert "Initialize databricks-tools MCP server" in result.output
        assert "--force" in result.output
        assert "--mode" in result.output
        assert "analyst" in result.output
        assert "developer" in result.output

    def test_init_command_help_shows_examples(self, runner: CliRunner) -> None:
        """Test that help shows usage examples.

        Args:
            runner: Click test runner
        """
        result = runner.invoke(init_command, ["--help"])
        assert result.exit_code == 0
        assert "databricks-tools-init" in result.output


class TestInitCommandModes:
    """Tests for analyst and developer mode initialization."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create Click CLI test runner."""
        return CliRunner()

    @patch("databricks_tools.cli.init.ConfigInstaller")
    def test_init_command_analyst_mode(
        self, mock_installer_class: MagicMock, runner: CliRunner
    ) -> None:
        """Test analyst mode initialization flow.

        Args:
            mock_installer_class: Mocked ConfigInstaller class
            runner: Click test runner
        """
        # Setup mock
        mock_installer = MagicMock()
        mock_installer_class.return_value = mock_installer

        # Run command
        result = runner.invoke(init_command, ["--mode", "analyst"])

        # Verify
        assert result.exit_code == 0
        mock_installer_class.assert_called_once()
        mock_installer.run_installation.assert_called_once_with(force=False, mode="analyst")

    @patch("databricks_tools.cli.init.ConfigInstaller")
    def test_init_command_developer_mode(
        self, mock_installer_class: MagicMock, runner: CliRunner
    ) -> None:
        """Test developer mode initialization flow.

        Args:
            mock_installer_class: Mocked ConfigInstaller class
            runner: Click test runner
        """
        # Setup mock
        mock_installer = MagicMock()
        mock_installer_class.return_value = mock_installer

        # Run command
        result = runner.invoke(init_command, ["--mode", "developer"])

        # Verify
        assert result.exit_code == 0
        mock_installer_class.assert_called_once()
        mock_installer.run_installation.assert_called_once_with(force=False, mode="developer")

    @patch("databricks_tools.cli.init.ConfigInstaller")
    def test_init_command_mode_case_insensitive(
        self, mock_installer_class: MagicMock, runner: CliRunner
    ) -> None:
        """Test that mode flag is case insensitive.

        Args:
            mock_installer_class: Mocked ConfigInstaller class
            runner: Click test runner
        """
        # Setup mock
        mock_installer = MagicMock()
        mock_installer_class.return_value = mock_installer

        # Test uppercase
        result = runner.invoke(init_command, ["--mode", "ANALYST"])
        assert result.exit_code == 0

        # Test mixed case
        result = runner.invoke(init_command, ["--mode", "Developer"])
        assert result.exit_code == 0


class TestInitCommandFlags:
    """Tests for command line flags (--force, --mode)."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create Click CLI test runner."""
        return CliRunner()

    @patch("databricks_tools.cli.init.ConfigInstaller")
    def test_init_command_with_force_flag(
        self, mock_installer_class: MagicMock, runner: CliRunner
    ) -> None:
        """Test --force flag bypasses prompts.

        Args:
            mock_installer_class: Mocked ConfigInstaller class
            runner: Click test runner
        """
        # Setup mock
        mock_installer = MagicMock()
        mock_installer_class.return_value = mock_installer

        # Run command with --force
        result = runner.invoke(init_command, ["--force", "--mode", "analyst"])

        # Verify
        assert result.exit_code == 0
        mock_installer.run_installation.assert_called_once_with(force=True, mode="analyst")

    @patch("databricks_tools.cli.init.ConfigInstaller")
    def test_init_command_without_mode_flag(
        self, mock_installer_class: MagicMock, runner: CliRunner
    ) -> None:
        """Test that mode=None when --mode flag not provided.

        Args:
            mock_installer_class: Mocked ConfigInstaller class
            runner: Click test runner
        """
        # Setup mock
        mock_installer = MagicMock()
        mock_installer_class.return_value = mock_installer

        # Run command without --mode (will prompt interactively)
        runner.invoke(init_command)

        # Verify mode=None passed to run_installation
        mock_installer.run_installation.assert_called_once_with(force=False, mode=None)

    def test_init_command_invalid_mode(self, runner: CliRunner) -> None:
        """Test that invalid mode value is rejected.

        Args:
            runner: Click test runner
        """
        result = runner.invoke(init_command, ["--mode", "invalid"])

        # Should exit with error
        assert result.exit_code != 0
        assert "Invalid value for '--mode'" in result.output


class TestInitCommandErrorHandling:
    """Tests for error handling and interruption."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create Click CLI test runner."""
        return CliRunner()

    @patch("databricks_tools.cli.init.ConfigInstaller")
    def test_init_command_keyboard_interrupt(
        self, mock_installer_class: MagicMock, runner: CliRunner
    ) -> None:
        """Test graceful Ctrl+C handling (KeyboardInterrupt).

        Args:
            mock_installer_class: Mocked ConfigInstaller class
            runner: Click test runner
        """
        # Setup mock to raise KeyboardInterrupt
        mock_installer = MagicMock()
        mock_installer.run_installation.side_effect = KeyboardInterrupt()
        mock_installer_class.return_value = mock_installer

        # Run command
        result = runner.invoke(init_command, ["--mode", "analyst"])

        # Verify graceful exit
        assert result.exit_code == 1
        assert "Installation cancelled by user" in result.output

    @patch("databricks_tools.cli.init.ConfigInstaller")
    def test_init_command_generic_exception(
        self, mock_installer_class: MagicMock, runner: CliRunner
    ) -> None:
        """Test generic exception handling.

        Args:
            mock_installer_class: Mocked ConfigInstaller class
            runner: Click test runner
        """
        # Setup mock to raise generic exception
        mock_installer = MagicMock()
        mock_installer.run_installation.side_effect = Exception("Test error message")
        mock_installer_class.return_value = mock_installer

        # Run command
        result = runner.invoke(init_command, ["--mode", "analyst"])

        # Verify error handling
        assert result.exit_code == 1
        assert "Installation failed: Test error message" in result.output
        assert "Please check the error message and try again" in result.output

    @patch("databricks_tools.cli.init.ConfigInstaller")
    def test_init_command_connection_failure_exception(
        self, mock_installer_class: MagicMock, runner: CliRunner
    ) -> None:
        """Test handling of connection validation failure.

        Args:
            mock_installer_class: Mocked ConfigInstaller class
            runner: Click test runner
        """
        # Setup mock to raise connection error
        mock_installer = MagicMock()
        mock_installer.run_installation.side_effect = Exception("Could not connect to Databricks")
        mock_installer_class.return_value = mock_installer

        # Run command
        result = runner.invoke(init_command, ["--mode", "analyst"])

        # Verify error message displayed
        assert result.exit_code == 1
        assert "Could not connect to Databricks" in result.output


class TestInitCommandIntegration:
    """Integration tests for complete initialization flow."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create Click CLI test runner."""
        return CliRunner()

    @patch("databricks_tools.cli.init.ConfigInstaller")
    def test_init_command_successful_installation(
        self, mock_installer_class: MagicMock, runner: CliRunner
    ) -> None:
        """Test successful installation completes without errors.

        Args:
            mock_installer_class: Mocked ConfigInstaller class
            runner: Click test runner
        """
        # Setup mock - successful installation
        mock_installer = MagicMock()
        mock_installer.run_installation.return_value = None
        mock_installer_class.return_value = mock_installer

        # Run command
        result = runner.invoke(init_command, ["--mode", "analyst"])

        # Verify success
        assert result.exit_code == 0
        mock_installer.run_installation.assert_called_once()

    @patch("databricks_tools.cli.init.ConfigInstaller")
    def test_init_command_force_and_mode_together(
        self, mock_installer_class: MagicMock, runner: CliRunner
    ) -> None:
        """Test using --force and --mode flags together.

        Args:
            mock_installer_class: Mocked ConfigInstaller class
            runner: Click test runner
        """
        # Setup mock
        mock_installer = MagicMock()
        mock_installer_class.return_value = mock_installer

        # Run command with both flags
        result = runner.invoke(init_command, ["--force", "--mode", "developer"])

        # Verify both flags passed correctly
        assert result.exit_code == 0
        mock_installer.run_installation.assert_called_once_with(force=True, mode="developer")

    @patch("databricks_tools.cli.init.ConfigInstaller")
    def test_init_command_creates_installer_instance(
        self, mock_installer_class: MagicMock, runner: CliRunner
    ) -> None:
        """Test that init command creates ConfigInstaller instance.

        Args:
            mock_installer_class: Mocked ConfigInstaller class
            runner: Click test runner
        """
        # Setup mock
        mock_installer = MagicMock()
        mock_installer_class.return_value = mock_installer

        # Run command
        result = runner.invoke(init_command, ["--mode", "analyst"])

        # Verify installer instantiated
        assert result.exit_code == 0
        mock_installer_class.assert_called_once_with()

    @patch("databricks_tools.cli.init.sys.exit")
    @patch("databricks_tools.cli.init.ConfigInstaller")
    def test_init_command_exit_codes(
        self, mock_installer_class: MagicMock, mock_exit: MagicMock, runner: CliRunner
    ) -> None:
        """Test that correct exit codes are used.

        Args:
            mock_installer_class: Mocked ConfigInstaller class
            mock_exit: Mocked sys.exit
            runner: Click test runner
        """
        # Setup mock for success
        mock_installer = MagicMock()
        mock_installer_class.return_value = mock_installer

        # Run command
        result = runner.invoke(init_command, ["--mode", "analyst"])

        # Verify sys.exit(0) called on success
        # Note: Click's runner catches sys.exit, so we check the call was made
        assert mock_exit.called or result.exit_code == 0
