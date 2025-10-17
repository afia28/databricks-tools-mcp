"""Comprehensive tests for ConfigInstaller class.

This module provides complete test coverage for the databricks-tools
configuration installer, including cross-platform support, credential
collection, connection validation, and file operations.
"""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from databricks_tools.config.installer import ConfigInstaller


class TestConfigInstallerInitialization:
    """Tests for ConfigInstaller initialization."""

    def test_installer_initialization(self) -> None:
        """Test ConfigInstaller initializes with correct project root."""
        installer = ConfigInstaller()
        assert installer.project_root.exists()
        assert installer.project_root.is_dir()
        # Verify project root is 4 levels up from installer.py
        expected_root = Path(__file__).parent.parent.parent
        assert installer.project_root == expected_root


class TestFindClaudeConfig:
    """Tests for find_claude_config method."""

    @pytest.fixture
    def installer(self) -> ConfigInstaller:
        """Create ConfigInstaller instance."""
        return ConfigInstaller()

    @patch("platform.system", return_value="Darwin")
    def test_find_claude_config_macos(
        self, mock_system: MagicMock, installer: ConfigInstaller, tmp_path: Path
    ) -> None:
        """Test finding Claude config on macOS.

        Args:
            mock_system: Mocked platform.system
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
        """
        # Create mock macOS config directory
        config_dir = tmp_path / "Library" / "Application Support" / "Claude"
        config_dir.mkdir(parents=True)

        with patch("pathlib.Path.home", return_value=tmp_path):
            config_path = installer.find_claude_config()
            assert config_path == config_dir / "claude_desktop_config.json"
            assert config_path.parent.exists()

    @patch("platform.system", return_value="Linux")
    def test_find_claude_config_linux(
        self, mock_system: MagicMock, installer: ConfigInstaller, tmp_path: Path
    ) -> None:
        """Test finding Claude config on Linux.

        Args:
            mock_system: Mocked platform.system
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
        """
        # Create mock Linux config directory
        config_dir = tmp_path / ".config" / "Claude"
        config_dir.mkdir(parents=True)

        with patch("pathlib.Path.home", return_value=tmp_path):
            config_path = installer.find_claude_config()
            assert config_path == config_dir / "claude_desktop_config.json"

    @patch("platform.system", return_value="Windows")
    def test_find_claude_config_windows(
        self, mock_system: MagicMock, installer: ConfigInstaller, tmp_path: Path
    ) -> None:
        """Test finding Claude config on Windows.

        Args:
            mock_system: Mocked platform.system
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
        """
        # Create mock Windows config directory
        config_dir = tmp_path / "Claude"
        config_dir.mkdir(parents=True)

        with patch.dict(os.environ, {"APPDATA": str(tmp_path)}):
            config_path = installer.find_claude_config()
            assert config_path == config_dir / "claude_desktop_config.json"

    @patch("platform.system", return_value="Windows")
    def test_find_claude_config_windows_no_appdata(
        self, mock_system: MagicMock, installer: ConfigInstaller
    ) -> None:
        """Test Windows without APPDATA environment variable.

        Args:
            mock_system: Mocked platform.system
            installer: ConfigInstaller instance
        """
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(FileNotFoundError, match="APPDATA environment variable"):
                installer.find_claude_config()

    @patch("platform.system", return_value="FreeBSD")
    def test_find_claude_config_unsupported_os(
        self, mock_system: MagicMock, installer: ConfigInstaller
    ) -> None:
        """Test error on unsupported operating system.

        Args:
            mock_system: Mocked platform.system
            installer: ConfigInstaller instance
        """
        with pytest.raises(FileNotFoundError, match="Unsupported platform: FreeBSD"):
            installer.find_claude_config()

    @patch("platform.system", return_value="Darwin")
    def test_find_claude_config_missing_directory(
        self, mock_system: MagicMock, installer: ConfigInstaller, tmp_path: Path
    ) -> None:
        """Test error when Claude config directory doesn't exist.

        Args:
            mock_system: Mocked platform.system
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
        """
        # Don't create the config directory
        with patch("pathlib.Path.home", return_value=tmp_path):
            with pytest.raises(
                FileNotFoundError, match="Claude Desktop config directory not found"
            ):
                installer.find_claude_config()


class TestBackupConfig:
    """Tests for backup_config method."""

    @pytest.fixture
    def installer(self) -> ConfigInstaller:
        """Create ConfigInstaller instance."""
        return ConfigInstaller()

    def test_backup_config_creates_backup(self, installer: ConfigInstaller, tmp_path: Path) -> None:
        """Test creating backup of existing config file.

        Args:
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
        """
        # Create original config file
        config_path = tmp_path / "claude_desktop_config.json"
        original_content = '{"mcpServers": {"test": {}}}'
        config_path.write_text(original_content)

        # Create backup
        backup_path = installer.backup_config(config_path)

        # Verify backup exists and has same content
        assert backup_path.exists()
        assert backup_path == tmp_path / "claude_desktop_config.json.backup"
        assert backup_path.read_text() == original_content

    def test_backup_config_nonexistent_file(
        self, installer: ConfigInstaller, tmp_path: Path
    ) -> None:
        """Test backup_config with non-existent file (no error).

        Args:
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
        """
        # Try to backup non-existent file
        config_path = tmp_path / "nonexistent.json"
        backup_path = installer.backup_config(config_path)

        # Should return backup path but not create file
        assert backup_path == tmp_path / "nonexistent.json.backup"
        assert not backup_path.exists()

    def test_backup_config_preserves_timestamps(
        self, installer: ConfigInstaller, tmp_path: Path
    ) -> None:
        """Test that backup preserves file metadata.

        Args:
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
        """
        # Create original file
        config_path = tmp_path / "config.json"
        config_path.write_text('{"test": true}')
        original_mtime = config_path.stat().st_mtime

        # Create backup (shutil.copy2 preserves metadata)
        backup_path = installer.backup_config(config_path)

        # Verify timestamps preserved (within small delta)
        assert abs(backup_path.stat().st_mtime - original_mtime) < 0.1


class TestUpdateClaudeConfig:
    """Tests for update_claude_config method."""

    @pytest.fixture
    def installer(self) -> ConfigInstaller:
        """Create ConfigInstaller instance."""
        return ConfigInstaller()

    @pytest.fixture
    def mock_claude_dir(self, tmp_path: Path) -> Path:
        """Create mock Claude config directory (macOS structure)."""
        config_dir = tmp_path / "Library" / "Application Support" / "Claude"
        config_dir.mkdir(parents=True)
        return config_dir

    @patch("databricks_tools.config.installer.Confirm.ask", return_value=True)
    @patch("platform.system", return_value="Darwin")
    def test_update_claude_config_new_file(
        self,
        mock_system: MagicMock,
        mock_confirm: MagicMock,
        installer: ConfigInstaller,
        tmp_path: Path,
        mock_claude_dir: Path,
    ) -> None:
        """Test creating new Claude config file.

        Args:
            mock_system: Mocked platform.system
            mock_confirm: Mocked Confirm.ask
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
            mock_claude_dir: Mock Claude config directory
        """
        with patch("pathlib.Path.home", return_value=tmp_path):
            project_path = Path("/test/project")
            installer.update_claude_config(project_path)

            # Verify config file created
            config_path = mock_claude_dir / "claude_desktop_config.json"
            assert config_path.exists()

            # Verify content
            config = json.loads(config_path.read_text())
            assert "mcpServers" in config
            assert "databricks-tools" in config["mcpServers"]
            assert config["mcpServers"]["databricks-tools"]["command"] == "uv"
            assert project_path.as_posix() in str(config["mcpServers"]["databricks-tools"]["args"])

    @patch("databricks_tools.config.installer.Confirm.ask", return_value=True)
    @patch("platform.system", return_value="Darwin")
    def test_update_claude_config_preserve_existing(
        self,
        mock_system: MagicMock,
        mock_confirm: MagicMock,
        installer: ConfigInstaller,
        tmp_path: Path,
        mock_claude_dir: Path,
    ) -> None:
        """Test preserving existing MCP servers when updating config.

        Args:
            mock_system: Mocked platform.system
            mock_confirm: Mocked Confirm.ask
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
            mock_claude_dir: Mock Claude config directory
        """
        # Create config with existing servers
        config_path = mock_claude_dir / "claude_desktop_config.json"
        existing_config = {
            "mcpServers": {
                "other-server": {"command": "other", "args": ["--test"]},
                "another-server": {"command": "another"},
            }
        }
        config_path.write_text(json.dumps(existing_config))

        with patch("pathlib.Path.home", return_value=tmp_path):
            project_path = Path("/test/project")
            installer.update_claude_config(project_path)

            # Verify existing servers preserved
            config = json.loads(config_path.read_text())
            assert "other-server" in config["mcpServers"]
            assert "another-server" in config["mcpServers"]
            assert "databricks-tools" in config["mcpServers"]
            assert len(config["mcpServers"]) == 3

    @patch("databricks_tools.config.installer.Confirm.ask", return_value=True)
    @patch("platform.system", return_value="Darwin")
    def test_update_claude_config_update_existing_entry(
        self,
        mock_system: MagicMock,
        mock_confirm: MagicMock,
        installer: ConfigInstaller,
        tmp_path: Path,
        mock_claude_dir: Path,
    ) -> None:
        """Test updating existing databricks-tools entry.

        Args:
            mock_system: Mocked platform.system
            mock_confirm: Mocked Confirm.ask
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
            mock_claude_dir: Mock Claude config directory
        """
        # Create config with old databricks-tools entry
        config_path = mock_claude_dir / "claude_desktop_config.json"
        old_config = {
            "mcpServers": {"databricks-tools": {"command": "old-command", "args": ["--old"]}}
        }
        config_path.write_text(json.dumps(old_config))

        with patch("pathlib.Path.home", return_value=tmp_path):
            project_path = Path("/new/project")
            installer.update_claude_config(project_path)

            # Verify entry updated
            config = json.loads(config_path.read_text())
            assert config["mcpServers"]["databricks-tools"]["command"] == "uv"
            assert "--old" not in str(config["mcpServers"]["databricks-tools"]["args"])

    @patch("databricks_tools.config.installer.Confirm.ask", return_value=False)
    @patch("platform.system", return_value="Darwin")
    def test_update_claude_config_user_declines_update(
        self,
        mock_system: MagicMock,
        mock_confirm: MagicMock,
        installer: ConfigInstaller,
        tmp_path: Path,
        mock_claude_dir: Path,
    ) -> None:
        """Test skipping update when user declines.

        Args:
            mock_system: Mocked platform.system
            mock_confirm: Mocked Confirm.ask
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
            mock_claude_dir: Mock Claude config directory
        """
        # Create config with existing databricks-tools
        config_path = mock_claude_dir / "claude_desktop_config.json"
        original_config = {"mcpServers": {"databricks-tools": {"command": "old", "args": []}}}
        config_path.write_text(json.dumps(original_config))

        with patch("pathlib.Path.home", return_value=tmp_path):
            installer.update_claude_config(Path("/test"))

            # Verify config unchanged
            config = json.loads(config_path.read_text())
            assert config["mcpServers"]["databricks-tools"]["command"] == "old"

    @patch("databricks_tools.config.installer.Confirm.ask", return_value=True)
    @patch("platform.system", return_value="Darwin")
    def test_update_claude_config_restores_backup_on_error(
        self,
        mock_system: MagicMock,
        mock_confirm: MagicMock,
        installer: ConfigInstaller,
        tmp_path: Path,
        mock_claude_dir: Path,
    ) -> None:
        """Test backup restoration when update fails.

        Args:
            mock_system: Mocked platform.system
            mock_confirm: Mocked Confirm.ask
            installer: ConfigInstaller instance
            tmp_path: Path temporary directory
            mock_claude_dir: Mock Claude config directory
        """
        # Create valid config
        config_path = mock_claude_dir / "claude_desktop_config.json"
        original_content = '{"mcpServers": {"original": true}}'
        config_path.write_text(original_content)

        with patch("pathlib.Path.home", return_value=tmp_path):
            # Mock json.dump to raise exception during write
            with patch("json.dump", side_effect=Exception("Write failed")):
                with pytest.raises(Exception, match="Write failed"):
                    installer.update_claude_config(Path("/test"))

            # Verify backup exists
            backup_path = config_path.with_suffix(".json.backup")
            assert backup_path.exists()

            # Verify original config was restored from backup
            assert config_path.read_text() == original_content

    @patch("platform.system", return_value="Darwin")
    def test_update_claude_config_handles_invalid_json(
        self,
        mock_system: MagicMock,
        installer: ConfigInstaller,
        tmp_path: Path,
        mock_claude_dir: Path,
    ) -> None:
        """Test handling of invalid JSON in existing config.

        Args:
            mock_system: Mocked platform.system
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
            mock_claude_dir: Mock Claude config directory
        """
        # Create config with invalid JSON
        config_path = mock_claude_dir / "claude_desktop_config.json"
        config_path.write_text("invalid json {{{")

        with patch("pathlib.Path.home", return_value=tmp_path):
            with pytest.raises(json.JSONDecodeError):
                installer.update_claude_config(Path("/test"))


class TestCollectCredentials:
    """Tests for credential collection methods."""

    @pytest.fixture
    def installer(self) -> ConfigInstaller:
        """Create ConfigInstaller instance."""
        return ConfigInstaller()

    @patch("databricks_tools.config.installer.Prompt.ask")
    def test_collect_credentials_analyst_mode(
        self, mock_prompt: MagicMock, installer: ConfigInstaller
    ) -> None:
        """Test collecting credentials in analyst mode.

        Args:
            mock_prompt: Mocked Prompt.ask
            installer: ConfigInstaller instance
        """
        # Mock user inputs
        mock_prompt.side_effect = [
            "https://test.databricks.com",
            "/sql/1.0/warehouses/test123",
            "dapi1234567890",
        ]

        credentials = installer.collect_credentials("analyst")

        # Verify correct credentials collected
        assert credentials["DATABRICKS_SERVER_HOSTNAME"] == "https://test.databricks.com"
        assert credentials["DATABRICKS_HTTP_PATH"] == "/sql/1.0/warehouses/test123"
        assert credentials["DATABRICKS_TOKEN"] == "dapi1234567890"
        assert len(credentials) == 3

    @patch("databricks_tools.config.installer.Prompt.ask")
    def test_collect_credentials_developer_mode_multiple(
        self, mock_prompt: MagicMock, installer: ConfigInstaller
    ) -> None:
        """Test collecting multiple workspace credentials in developer mode.

        Args:
            mock_prompt: Mocked Prompt.ask
            installer: ConfigInstaller instance
        """
        # Mock inputs for two workspaces
        mock_prompt.side_effect = [
            "production",  # First workspace name
            "https://prod.databricks.com",
            "/sql/1.0/warehouses/prod",
            "dapiprod123",
            "staging",  # Second workspace name
            "https://staging.databricks.com",
            "/sql/1.0/warehouses/staging",
            "dapistaging123",
            "",  # Empty to finish
        ]

        credentials = installer.collect_credentials("developer")

        # Verify both workspaces configured
        assert credentials["PRODUCTION_DATABRICKS_SERVER_HOSTNAME"] == "https://prod.databricks.com"
        assert credentials["PRODUCTION_DATABRICKS_HTTP_PATH"] == "/sql/1.0/warehouses/prod"
        assert credentials["PRODUCTION_DATABRICKS_TOKEN"] == "dapiprod123"
        assert credentials["STAGING_DATABRICKS_SERVER_HOSTNAME"] == "https://staging.databricks.com"
        assert credentials["STAGING_DATABRICKS_HTTP_PATH"] == "/sql/1.0/warehouses/staging"
        assert credentials["STAGING_DATABRICKS_TOKEN"] == "dapistaging123"
        assert len(credentials) == 6

    @patch("databricks_tools.config.installer.Prompt.ask")
    def test_collect_credentials_developer_mode_single_workspace(
        self, mock_prompt: MagicMock, installer: ConfigInstaller
    ) -> None:
        """Test developer mode with only one workspace configured.

        Args:
            mock_prompt: Mocked Prompt.ask
            installer: ConfigInstaller instance
        """
        # Mock inputs for one workspace then finish
        mock_prompt.side_effect = [
            "production",
            "https://prod.databricks.com",
            "/sql/1.0/warehouses/prod",
            "dapiprod123",
            "",  # Empty to finish after first workspace
        ]

        credentials = installer.collect_credentials("developer")

        # Verify single workspace configured
        assert len(credentials) == 3
        assert "PRODUCTION_DATABRICKS_SERVER_HOSTNAME" in credentials

    @patch("databricks_tools.config.installer.Prompt.ask")
    def test_collect_workspace_credentials_token_validation(
        self, mock_prompt: MagicMock, installer: ConfigInstaller
    ) -> None:
        """Test token format validation (must start with 'dapi').

        Args:
            mock_prompt: Mocked Prompt.ask
            installer: ConfigInstaller instance
        """
        # Mock invalid token, then valid token
        mock_prompt.side_effect = [
            "https://test.databricks.com",
            "/sql/1.0/warehouses/test",
            "invalid_token",  # Invalid - doesn't start with dapi
            "dapivalid123",  # Valid token
        ]

        credentials = installer._collect_workspace_credentials()

        # Verify valid token accepted
        assert credentials["DATABRICKS_TOKEN"] == "dapivalid123"

    @patch("databricks_tools.config.installer.Prompt.ask")
    def test_collect_workspace_credentials_with_prefix(
        self, mock_prompt: MagicMock, installer: ConfigInstaller
    ) -> None:
        """Test collecting credentials with environment variable prefix.

        Args:
            mock_prompt: Mocked Prompt.ask
            installer: ConfigInstaller instance
        """
        # Mock inputs
        mock_prompt.side_effect = [
            "https://test.databricks.com",
            "/sql/1.0/warehouses/test",
            "dapi123",
        ]

        credentials = installer._collect_workspace_credentials(prefix="PRODUCTION")

        # Verify prefixed variable names
        assert "PRODUCTION_DATABRICKS_SERVER_HOSTNAME" in credentials
        assert "PRODUCTION_DATABRICKS_HTTP_PATH" in credentials
        assert "PRODUCTION_DATABRICKS_TOKEN" in credentials
        assert "DATABRICKS_SERVER_HOSTNAME" not in credentials


class TestValidateConnection:
    """Tests for connection validation."""

    @pytest.fixture
    def installer(self) -> ConfigInstaller:
        """Create ConfigInstaller instance."""
        return ConfigInstaller()

    @pytest.fixture
    def valid_credentials(self) -> dict[str, str]:
        """Sample valid credentials."""
        return {
            "DATABRICKS_SERVER_HOSTNAME": "https://test.databricks.com",
            "DATABRICKS_HTTP_PATH": "/sql/1.0/warehouses/test123",
            "DATABRICKS_TOKEN": "dapi1234567890",
        }

    @patch("databricks_tools.config.installer.sql.connect")
    def test_validate_connection_success(
        self,
        mock_connect: MagicMock,
        installer: ConfigInstaller,
        valid_credentials: dict[str, str],
    ) -> None:
        """Test successful connection validation.

        Args:
            mock_connect: Mocked databricks.sql.connect
            installer: ConfigInstaller instance
            valid_credentials: Valid credential dictionary
        """
        # Mock successful connection
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection = MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.__exit__.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        result = installer.validate_connection(valid_credentials)

        # Verify success
        assert result is True
        mock_connect.assert_called_once()
        mock_cursor.execute.assert_called_once_with("SELECT 1 AS test")

    @patch("databricks_tools.config.installer.sql.connect")
    def test_validate_connection_invalid_credentials(
        self, mock_connect: MagicMock, installer: ConfigInstaller
    ) -> None:
        """Test validation failure with invalid credentials.

        Args:
            mock_connect: Mocked databricks.sql.connect
            installer: ConfigInstaller instance
        """
        # Mock connection failure
        mock_connect.side_effect = Exception("Invalid access token")

        credentials = {
            "DATABRICKS_SERVER_HOSTNAME": "https://test.databricks.com",
            "DATABRICKS_HTTP_PATH": "/sql/1.0/warehouses/test",
            "DATABRICKS_TOKEN": "invalid_token",
        }

        result = installer.validate_connection(credentials)

        # Verify failure
        assert result is False

    def test_validate_connection_missing_credentials(self, installer: ConfigInstaller) -> None:
        """Test validation with missing required credentials.

        Args:
            installer: ConfigInstaller instance
        """
        # Missing token
        incomplete_credentials = {
            "DATABRICKS_SERVER_HOSTNAME": "https://test.databricks.com",
            "DATABRICKS_HTTP_PATH": "/sql/1.0/warehouses/test",
        }

        result = installer.validate_connection(incomplete_credentials)

        # Verify failure
        assert result is False

    @patch("databricks_tools.config.installer.sql.connect")
    def test_validate_connection_query_failure(
        self,
        mock_connect: MagicMock,
        installer: ConfigInstaller,
        valid_credentials: dict[str, str],
    ) -> None:
        """Test validation when test query fails.

        Args:
            mock_connect: Mocked databricks.sql.connect
            installer: ConfigInstaller instance
            valid_credentials: Valid credential dictionary
        """
        # Mock connection succeeds but query returns unexpected result
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_connection = MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.__exit__.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        result = installer.validate_connection(valid_credentials)

        # Verify failure
        assert result is False

    @patch("databricks_tools.config.installer.sql.connect")
    def test_validate_connection_strips_https(
        self,
        mock_connect: MagicMock,
        installer: ConfigInstaller,
        valid_credentials: dict[str, str],
    ) -> None:
        """Test that https:// is stripped from hostname.

        Args:
            mock_connect: Mocked databricks.sql.connect
            installer: ConfigInstaller instance
            valid_credentials: Valid credential dictionary
        """
        # Mock successful connection
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection = MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.__exit__.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection

        installer.validate_connection(valid_credentials)

        # Verify https:// stripped from hostname
        call_args = mock_connect.call_args
        assert call_args[1]["server_hostname"] == "test.databricks.com"


class TestCreateEnvFile:
    """Tests for .env file creation."""

    @pytest.fixture
    def installer(self) -> ConfigInstaller:
        """Create ConfigInstaller instance."""
        return ConfigInstaller()

    @pytest.fixture
    def sample_credentials(self) -> dict[str, str]:
        """Sample credentials for testing."""
        return {
            "DATABRICKS_SERVER_HOSTNAME": "https://test.databricks.com",
            "DATABRICKS_HTTP_PATH": "/sql/1.0/warehouses/test",
            "DATABRICKS_TOKEN": "dapi1234567890",
        }

    def test_create_env_file_new(
        self, installer: ConfigInstaller, tmp_path: Path, sample_credentials: dict[str, str]
    ) -> None:
        """Test creating new .env file.

        Args:
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
            sample_credentials: Sample credential dictionary
        """
        installer.create_env_file(sample_credentials, tmp_path)

        # Verify .env created
        env_path = tmp_path / ".env"
        assert env_path.exists()

        # Verify content
        env_content = env_path.read_text()
        assert "DATABRICKS_SERVER_HOSTNAME=https://test.databricks.com" in env_content
        assert "DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/test" in env_content
        assert "DATABRICKS_TOKEN=dapi1234567890" in env_content

    def test_create_env_file_permissions(
        self, installer: ConfigInstaller, tmp_path: Path, sample_credentials: dict[str, str]
    ) -> None:
        """Test .env file has correct permissions (0600).

        Args:
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
            sample_credentials: Sample credential dictionary
        """
        installer.create_env_file(sample_credentials, tmp_path)

        # Verify permissions (owner read/write only)
        env_path = tmp_path / ".env"
        assert oct(env_path.stat().st_mode)[-3:] == "600"

    @patch("databricks_tools.config.installer.Confirm.ask", return_value=True)
    def test_create_env_file_overwrite_with_confirmation(
        self,
        mock_confirm: MagicMock,
        installer: ConfigInstaller,
        tmp_path: Path,
        sample_credentials: dict[str, str],
    ) -> None:
        """Test overwriting existing .env file with user confirmation.

        Args:
            mock_confirm: Mocked Confirm.ask
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
            sample_credentials: Sample credential dictionary
        """
        # Create existing .env
        env_path = tmp_path / ".env"
        env_path.write_text("OLD_VAR=old_value\n")

        # Create with confirmation
        installer.create_env_file(sample_credentials, tmp_path)

        # Verify overwritten
        env_content = env_path.read_text()
        assert "OLD_VAR" not in env_content
        assert "DATABRICKS_SERVER_HOSTNAME" in env_content
        mock_confirm.assert_called_once()

    @patch("databricks_tools.config.installer.Confirm.ask", return_value=False)
    def test_create_env_file_skip_on_user_decline(
        self,
        mock_confirm: MagicMock,
        installer: ConfigInstaller,
        tmp_path: Path,
        sample_credentials: dict[str, str],
    ) -> None:
        """Test skipping .env creation when user declines.

        Args:
            mock_confirm: Mocked Confirm.ask
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
            sample_credentials: Sample credential dictionary
        """
        # Create existing .env
        env_path = tmp_path / ".env"
        original_content = "OLD_VAR=old_value\n"
        env_path.write_text(original_content)

        # Try to create, user declines
        installer.create_env_file(sample_credentials, tmp_path)

        # Verify not overwritten
        assert env_path.read_text() == original_content

    def test_create_env_file_force_flag(
        self, installer: ConfigInstaller, tmp_path: Path, sample_credentials: dict[str, str]
    ) -> None:
        """Test force flag bypasses confirmation prompt.

        Args:
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
            sample_credentials: Sample credential dictionary
        """
        # Create existing .env
        env_path = tmp_path / ".env"
        env_path.write_text("OLD_VAR=old_value\n")

        # Create with force=True (no prompt)
        installer.create_env_file(sample_credentials, tmp_path, force=True)

        # Verify overwritten without prompting
        env_content = env_path.read_text()
        assert "OLD_VAR" not in env_content
        assert "DATABRICKS_SERVER_HOSTNAME" in env_content

    def test_create_env_file_sorted_keys(self, installer: ConfigInstaller, tmp_path: Path) -> None:
        """Test that environment variables are sorted in .env file.

        Args:
            installer: ConfigInstaller instance
            tmp_path: Pytest temporary directory
        """
        # Credentials in unsorted order
        credentials = {
            "Z_VAR": "z",
            "A_VAR": "a",
            "M_VAR": "m",
        }

        installer.create_env_file(credentials, tmp_path)

        # Verify sorted
        env_content = tmp_path.joinpath(".env").read_text()
        lines = [line for line in env_content.split("\n") if "=" in line]
        assert lines[0].startswith("A_VAR")
        assert lines[1].startswith("M_VAR")
        assert lines[2].startswith("Z_VAR")


class TestShowNextSteps:
    """Tests for show_next_steps method."""

    @pytest.fixture
    def installer(self) -> ConfigInstaller:
        """Create ConfigInstaller instance."""
        return ConfigInstaller()

    def test_show_next_steps_output(
        self, installer: ConfigInstaller, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that next steps message is displayed.

        Args:
            installer: ConfigInstaller instance
            capsys: Pytest stdout/stderr capture
        """
        installer.show_next_steps()

        # Capture output
        captured = capsys.readouterr()

        # Verify key messages present
        assert "Installation Complete!" in captured.out
        assert "Next Steps:" in captured.out
        assert "Restart Claude Desktop" in captured.out
        assert "list_workspaces" in captured.out
        assert "uv run databricks-tools" in captured.out


class TestRunInstallation:
    """Tests for complete installation flow."""

    @pytest.fixture
    def installer(self) -> ConfigInstaller:
        """Create ConfigInstaller instance."""
        return ConfigInstaller()

    @pytest.fixture
    def sample_credentials(self) -> dict[str, str]:
        """Sample credentials."""
        return {
            "DATABRICKS_SERVER_HOSTNAME": "https://test.databricks.com",
            "DATABRICKS_HTTP_PATH": "/sql/1.0/warehouses/test",
            "DATABRICKS_TOKEN": "dapi123",
        }

    @patch("databricks_tools.config.installer.Prompt.ask")
    @patch("databricks_tools.config.installer.ConfigInstaller.validate_connection")
    @patch("databricks_tools.config.installer.ConfigInstaller.update_claude_config")
    @patch("databricks_tools.config.installer.ConfigInstaller.create_env_file")
    @patch("databricks_tools.config.installer.ConfigInstaller.show_next_steps")
    def test_run_installation_analyst_mode_full_flow(
        self,
        mock_next_steps: MagicMock,
        mock_env: MagicMock,
        mock_config: MagicMock,
        mock_validate: MagicMock,
        mock_prompt: MagicMock,
        installer: ConfigInstaller,
    ) -> None:
        """Test complete analyst mode installation flow.

        Args:
            mock_next_steps: Mocked show_next_steps
            mock_env: Mocked create_env_file
            mock_config: Mocked update_claude_config
            mock_validate: Mocked validate_connection
            mock_prompt: Mocked Prompt.ask
            installer: ConfigInstaller instance
        """
        # Setup mocks
        mock_prompt.side_effect = [
            "https://test.databricks.com",
            "/sql/1.0/warehouses/test",
            "dapi123",
        ]
        mock_validate.return_value = True

        # Run installation with mode specified
        installer.run_installation(force=False, mode="analyst")

        # Verify all steps called
        assert mock_validate.called
        assert mock_config.called
        assert mock_env.called
        assert mock_next_steps.called

    @patch("databricks_tools.config.installer.Prompt.ask")
    @patch("databricks_tools.config.installer.ConfigInstaller.validate_connection")
    def test_run_installation_validation_failure(
        self,
        mock_validate: MagicMock,
        mock_prompt: MagicMock,
        installer: ConfigInstaller,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test installation stops on connection validation failure.

        Args:
            mock_validate: Mocked validate_connection
            mock_prompt: Mocked Prompt.ask
            installer: ConfigInstaller instance
            capsys: Pytest stdout/stderr capture
        """
        # Setup mocks
        mock_prompt.side_effect = [
            "https://test.databricks.com",
            "/sql/1.0/warehouses/test",
            "dapi_invalid",
        ]
        mock_validate.return_value = False

        # Run installation
        installer.run_installation(force=False, mode="analyst")

        # Verify error message
        captured = capsys.readouterr()
        assert "Could not connect to Databricks" in captured.out

    @patch("databricks_tools.config.installer.Prompt.ask")
    @patch("databricks_tools.config.installer.ConfigInstaller.validate_connection")
    @patch("databricks_tools.config.installer.ConfigInstaller.update_claude_config")
    @patch("databricks_tools.config.installer.ConfigInstaller.create_env_file")
    @patch("databricks_tools.config.installer.ConfigInstaller.show_next_steps")
    def test_run_installation_continues_on_config_error(
        self,
        mock_next_steps: MagicMock,
        mock_env: MagicMock,
        mock_config: MagicMock,
        mock_validate: MagicMock,
        mock_prompt: MagicMock,
        installer: ConfigInstaller,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test installation continues if Claude config update fails.

        Args:
            mock_next_steps: Mocked show_next_steps
            mock_env: Mocked create_env_file
            mock_config: Mocked update_claude_config
            mock_validate: Mocked validate_connection
            mock_prompt: Mocked Prompt.ask
            installer: ConfigInstaller instance
            capsys: Pytest stdout/stderr capture
        """
        # Setup mocks
        mock_prompt.side_effect = [
            "https://test.databricks.com",
            "/sql/1.0/warehouses/test",
            "dapi123",
        ]
        mock_validate.return_value = True
        mock_config.side_effect = FileNotFoundError("Claude not found")

        # Run installation
        installer.run_installation(force=False, mode="analyst")

        # Verify continued with .env creation
        assert mock_env.called
        assert mock_next_steps.called
        captured = capsys.readouterr()
        assert "Continuing with .env creation" in captured.out

    @patch("databricks_tools.config.installer.Prompt.ask")
    @patch("databricks_tools.config.installer.ConfigInstaller.validate_connection")
    @patch("databricks_tools.config.installer.ConfigInstaller.update_claude_config")
    @patch("databricks_tools.config.installer.ConfigInstaller.create_env_file")
    @patch("databricks_tools.config.installer.ConfigInstaller.show_next_steps")
    def test_run_installation_mode_prompt_when_none(
        self,
        mock_next_steps: MagicMock,
        mock_env: MagicMock,
        mock_config: MagicMock,
        mock_validate: MagicMock,
        mock_prompt: MagicMock,
        installer: ConfigInstaller,
    ) -> None:
        """Test that mode is prompted when not provided.

        Args:
            mock_next_steps: Mocked show_next_steps
            mock_env: Mocked create_env_file
            mock_config: Mocked update_claude_config
            mock_validate: Mocked validate_connection
            mock_prompt: Mocked Prompt.ask
            installer: ConfigInstaller instance
        """
        # Setup mocks - first call is mode selection, rest are credentials
        mock_prompt.side_effect = [
            "analyst",  # Mode selection
            "https://test.databricks.com",
            "/sql/1.0/warehouses/test",
            "dapi123",
        ]
        mock_validate.return_value = True

        # Run without mode specified
        installer.run_installation(force=False, mode=None)

        # Verify mode prompted
        assert mock_prompt.call_count >= 4  # Mode + 3 credential fields


class TestConfigInstallerIdempotency:
    """Tests for installation idempotency and safety."""

    @pytest.fixture
    def installer(self) -> ConfigInstaller:
        """Create ConfigInstaller instance."""
        return ConfigInstaller()

    @patch("databricks_tools.config.installer.Prompt.ask")
    @patch("databricks_tools.config.installer.ConfigInstaller.validate_connection")
    @patch("databricks_tools.config.installer.ConfigInstaller.update_claude_config")
    @patch("databricks_tools.config.installer.ConfigInstaller.create_env_file")
    @patch("databricks_tools.config.installer.ConfigInstaller.show_next_steps")
    def test_installation_idempotency(
        self,
        mock_next_steps: MagicMock,
        mock_env: MagicMock,
        mock_config: MagicMock,
        mock_validate: MagicMock,
        mock_prompt: MagicMock,
        installer: ConfigInstaller,
    ) -> None:
        """Test running installation multiple times is safe.

        Args:
            mock_next_steps: Mocked show_next_steps
            mock_env: Mocked create_env_file
            mock_config: Mocked update_claude_config
            mock_validate: Mocked validate_connection
            mock_prompt: Mocked Prompt.ask
            installer: ConfigInstaller instance
        """
        # Setup mocks
        mock_prompt.side_effect = [
            "https://test.databricks.com",
            "/sql/1.0/warehouses/test",
            "dapi123",
        ] * 3  # Repeat for 3 runs
        mock_validate.return_value = True

        # Run installation 3 times
        for _ in range(3):
            installer.run_installation(force=True, mode="analyst")

        # Verify no errors and methods called correct number of times
        assert mock_validate.call_count == 3
        assert mock_config.call_count == 3
        assert mock_env.call_count == 3
