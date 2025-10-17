"""Comprehensive tests for version management and publishing.

This module provides complete test coverage for the databricks-tools
version management (VersionManager) and package publishing (PackagePublisher)
infrastructure.
"""

import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Import from scripts
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from publish import PackagePublisher, PyPIBackend
from version import BumpType, VersionManager


class TestVersionManagerInitialization:
    """Tests for VersionManager initialization."""

    def test_version_manager_initialization(self) -> None:
        """Test VersionManager initializes with correct project paths."""
        manager = VersionManager()
        assert manager.root_dir.exists()
        assert manager.root_dir.is_dir()
        assert manager.version_file.name == "__init__.py"
        assert manager.changelog_file.name == "CHANGELOG.md"


class TestGetCurrentVersion:
    """Tests for get_current_version method."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> VersionManager:
        """Create VersionManager with temporary directory.

        Args:
            tmp_path: Pytest temporary directory

        Returns:
            VersionManager instance configured for testing
        """
        manager = VersionManager()
        manager.root_dir = tmp_path
        version_dir = tmp_path / "src" / "databricks_tools"
        version_dir.mkdir(parents=True)
        manager.version_file = version_dir / "__init__.py"
        manager.changelog_file = tmp_path / "CHANGELOG.md"
        return manager

    def test_get_current_version(self, manager: VersionManager) -> None:
        """Test reading current version from __init__.py.

        Args:
            manager: VersionManager instance
        """
        # Arrange: Create version file
        manager.version_file.write_text('__version__ = "0.2.0"\n')

        # Act: Get version
        version = manager.get_current_version()

        # Assert: Version correct
        assert version == "0.2.0"

    def test_get_current_version_with_single_quotes(self, manager: VersionManager) -> None:
        """Test reading version with single quotes.

        Args:
            manager: VersionManager instance
        """
        # Arrange: Create version file with single quotes
        manager.version_file.write_text("__version__ = '1.2.3'\n")

        # Act: Get version
        version = manager.get_current_version()

        # Assert: Version correct
        assert version == "1.2.3"

    def test_get_current_version_missing_file(self, manager: VersionManager) -> None:
        """Test error when version file doesn't exist.

        Args:
            manager: VersionManager instance
        """
        # Arrange: Ensure file doesn't exist
        assert not manager.version_file.exists()

        # Act & Assert: Raises FileNotFoundError
        with pytest.raises(FileNotFoundError, match="Version file not found"):
            manager.get_current_version()

    def test_get_current_version_no_version_pattern(self, manager: VersionManager) -> None:
        """Test error when __version__ not found in file.

        Args:
            manager: VersionManager instance
        """
        # Arrange: Create file without version
        manager.version_file.write_text("# No version here\n")

        # Act & Assert: Raises ValueError
        with pytest.raises(ValueError, match="Version not found"):
            manager.get_current_version()


class TestBumpVersion:
    """Tests for bump_version method."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> VersionManager:
        """Create VersionManager with temporary directory.

        Args:
            tmp_path: Pytest temporary directory

        Returns:
            VersionManager instance configured for testing
        """
        manager = VersionManager()
        manager.root_dir = tmp_path
        version_dir = tmp_path / "src" / "databricks_tools"
        version_dir.mkdir(parents=True)
        manager.version_file = version_dir / "__init__.py"
        return manager

    @pytest.mark.parametrize(
        "bump_type,current,expected",
        [
            (BumpType.MAJOR, "1.0.0", "2.0.0"),
            (BumpType.MAJOR, "0.2.5", "1.0.0"),
            (BumpType.MINOR, "1.0.0", "1.1.0"),
            (BumpType.MINOR, "2.3.4", "2.4.0"),
            (BumpType.PATCH, "1.0.0", "1.0.1"),
            (BumpType.PATCH, "2.3.4", "2.3.5"),
        ],
    )
    def test_bump_version(
        self, manager: VersionManager, bump_type: BumpType, current: str, expected: str
    ) -> None:
        """Test version bumping for different bump types.

        Args:
            manager: VersionManager instance
            bump_type: Type of version bump
            current: Current version string
            expected: Expected new version string
        """
        # Arrange: Set current version
        manager.version_file.write_text(f'__version__ = "{current}"\n')

        # Act: Bump version
        new_version = manager.bump_version(bump_type)

        # Assert: New version correct
        assert new_version == expected

    def test_bump_version_invalid_format(self, manager: VersionManager) -> None:
        """Test error with invalid semantic version format.

        Args:
            manager: VersionManager instance
        """
        # Arrange: Create invalid version (missing patch)
        manager.version_file.write_text('__version__ = "1.0"\n')

        # Act & Assert: Raises ValueError
        with pytest.raises(ValueError, match="Invalid semantic version"):
            manager.bump_version(BumpType.MINOR)

    def test_bump_version_non_numeric(self, manager: VersionManager) -> None:
        """Test error with non-numeric version components.

        Args:
            manager: VersionManager instance
        """
        # Arrange: Create version with non-numeric components
        manager.version_file.write_text('__version__ = "1.x.0"\n')

        # Act & Assert: Raises ValueError
        with pytest.raises(ValueError, match="Invalid semantic version components"):
            manager.bump_version(BumpType.PATCH)


class TestUpdateVersion:
    """Tests for update_version method."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> VersionManager:
        """Create VersionManager with temporary directory.

        Args:
            tmp_path: Pytest temporary directory

        Returns:
            VersionManager instance configured for testing
        """
        manager = VersionManager()
        manager.root_dir = tmp_path
        version_dir = tmp_path / "src" / "databricks_tools"
        version_dir.mkdir(parents=True)
        manager.version_file = version_dir / "__init__.py"
        return manager

    def test_update_version_writes_file(self, manager: VersionManager) -> None:
        """Test that update_version writes new version to file.

        Args:
            manager: VersionManager instance
        """
        # Arrange: Create file with old version
        manager.version_file.write_text('__version__ = "0.1.0"\n')

        # Act: Update version
        manager.update_version("0.2.0")

        # Assert: File updated
        content = manager.version_file.read_text()
        assert '__version__ = "0.2.0"' in content

    def test_update_version_preserves_formatting(self, manager: VersionManager) -> None:
        """Test that update_version preserves file structure.

        Args:
            manager: VersionManager instance
        """
        # Arrange: Create file with comments and multiple lines
        original = '"""Package init."""\n__version__ = "0.1.0"\n# Other content\n'
        manager.version_file.write_text(original)

        # Act: Update version
        manager.update_version("0.2.0")

        # Assert: Structure preserved
        content = manager.version_file.read_text()
        assert '"""Package init."""' in content
        assert "# Other content" in content
        assert '__version__ = "0.2.0"' in content

    def test_update_version_missing_file(self, manager: VersionManager) -> None:
        """Test error when version file doesn't exist.

        Args:
            manager: VersionManager instance
        """
        # Arrange: Ensure file doesn't exist
        assert not manager.version_file.exists()

        # Act & Assert: Raises FileNotFoundError
        with pytest.raises(FileNotFoundError, match="Version file not found"):
            manager.update_version("1.0.0")

    def test_update_version_no_pattern(self, manager: VersionManager) -> None:
        """Test error when __version__ pattern not found.

        Args:
            manager: VersionManager instance
        """
        # Arrange: Create file without version pattern
        manager.version_file.write_text("# No version\n")

        # Act & Assert: Raises ValueError
        with pytest.raises(ValueError, match="Version pattern not found"):
            manager.update_version("1.0.0")


class TestCreateGitTag:
    """Tests for create_git_tag method."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> VersionManager:
        """Create VersionManager with temporary directory.

        Args:
            tmp_path: Pytest temporary directory

        Returns:
            VersionManager instance configured for testing
        """
        manager = VersionManager()
        manager.root_dir = tmp_path
        return manager

    @patch("subprocess.run")
    def test_create_git_tag_success(self, mock_run: MagicMock, manager: VersionManager) -> None:
        """Test successful git tag creation and push.

        Args:
            mock_run: Mocked subprocess.run
            manager: VersionManager instance
        """
        # Arrange: Mock successful git commands
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        # Act: Create tag
        manager.create_git_tag("0.3.0")

        # Assert: Both git commands called
        assert mock_run.call_count == 2
        calls = mock_run.call_args_list

        # Verify tag creation
        assert calls[0][0][0] == ["git", "tag", "-a", "v0.3.0", "-m", "Release version 0.3.0"]
        assert calls[0][1]["check"] is True

        # Verify tag push
        assert calls[1][0][0] == ["git", "push", "origin", "v0.3.0"]

    @patch("subprocess.run")
    def test_create_git_tag_with_custom_message(
        self, mock_run: MagicMock, manager: VersionManager
    ) -> None:
        """Test git tag creation with custom message.

        Args:
            mock_run: Mocked subprocess.run
            manager: VersionManager instance
        """
        # Arrange: Mock successful git commands
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        # Act: Create tag with custom message
        manager.create_git_tag("0.3.0", "Custom release message")

        # Assert: Custom message used
        calls = mock_run.call_args_list
        assert calls[0][0][0] == ["git", "tag", "-a", "v0.3.0", "-m", "Custom release message"]

    @patch("subprocess.run")
    def test_create_git_tag_failure(self, mock_run: MagicMock, manager: VersionManager) -> None:
        """Test error handling when git tag fails.

        Args:
            mock_run: Mocked subprocess.run
            manager: VersionManager instance
        """
        # Arrange: Mock git failure
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["git"], stderr="Tag already exists"
        )

        # Act & Assert: Raises RuntimeError
        with pytest.raises(RuntimeError, match="Failed to create/push git tag"):
            manager.create_git_tag("0.3.0")


class TestUpdateChangelog:
    """Tests for update_changelog method."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> VersionManager:
        """Create VersionManager with temporary directory.

        Args:
            tmp_path: Pytest temporary directory

        Returns:
            VersionManager instance configured for testing
        """
        manager = VersionManager()
        manager.root_dir = tmp_path
        manager.changelog_file = tmp_path / "CHANGELOG.md"
        return manager

    def test_update_changelog_adds_version(self, manager: VersionManager) -> None:
        """Test that update_changelog adds new version section.

        Args:
            manager: VersionManager instance
        """
        # Arrange: Create basic changelog
        manager.changelog_file.write_text("# Changelog\n\n## [0.1.0] - 2024-01-01\n")

        # Act: Update changelog
        manager.update_changelog("0.2.0")

        # Assert: New version added
        content = manager.changelog_file.read_text()
        today = date.today().strftime("%Y-%m-%d")
        assert f"## [0.2.0] - {today}" in content
        assert "### Added" in content
        assert "### Changed" in content
        assert "### Fixed" in content
        # Old version still present
        assert "## [0.1.0]" in content

    def test_update_changelog_skips_existing_version(self, manager: VersionManager) -> None:
        """Test that existing version is not duplicated.

        Args:
            manager: VersionManager instance
        """
        # Arrange: Create changelog with version already present
        original_content = "# Changelog\n\n## [0.2.0] - 2024-01-01\n### Added\n- Feature\n"
        manager.changelog_file.write_text(original_content)

        # Act: Try to add same version
        manager.update_changelog("0.2.0")

        # Assert: Content unchanged
        content = manager.changelog_file.read_text()
        assert content.count("## [0.2.0]") == 1

    def test_update_changelog_missing_file_warning(
        self, manager: VersionManager, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test warning when CHANGELOG.md doesn't exist.

        Args:
            manager: VersionManager instance
            capsys: Pytest stdout/stderr capture
        """
        # Arrange: Ensure changelog doesn't exist
        assert not manager.changelog_file.exists()

        # Act: Update changelog
        manager.update_changelog("0.2.0")

        # Assert: Warning printed
        captured = capsys.readouterr()
        assert "Warning: CHANGELOG.md not found" in captured.out

    def test_update_changelog_insertion_order(self, manager: VersionManager) -> None:
        """Test that new version is inserted before existing versions.

        Args:
            manager: VersionManager instance
        """
        # Arrange: Create changelog with existing versions
        manager.changelog_file.write_text(
            "# Changelog\n\n## [0.2.0] - 2024-02-01\n\n## [0.1.0] - 2024-01-01\n"
        )

        # Act: Add new version
        manager.update_changelog("0.3.0")

        # Assert: New version is first
        content = manager.changelog_file.read_text()
        lines = content.split("\n")
        version_lines = [i for i, line in enumerate(lines) if line.startswith("## [")]
        assert "0.3.0" in lines[version_lines[0]]
        assert "0.2.0" in lines[version_lines[1]]
        assert "0.1.0" in lines[version_lines[2]]


class TestPackagePublisherInitialization:
    """Tests for PackagePublisher initialization."""

    def test_publisher_initialization(self) -> None:
        """Test PackagePublisher initializes with backend."""
        publisher = PackagePublisher(PyPIBackend.DEVPI)
        assert publisher.backend == PyPIBackend.DEVPI
        assert publisher.root_dir.exists()
        assert publisher.dist_dir == publisher.root_dir / "dist"


class TestGetRepositoryUrl:
    """Tests for get_repository_url method."""

    @pytest.mark.parametrize(
        "backend,env_var,env_value,expected_substring",
        [
            (
                PyPIBackend.DEVPI,
                "DEVPI_INDEX_URL",
                "https://pypi.company.com/root/prod",
                "pypi.company.com",
            ),
            (
                PyPIBackend.ARTIFACTORY,
                "ARTIFACTORY_PYPI_URL",
                "https://artifactory.company.com",
                "artifactory",
            ),
            (PyPIBackend.AWS_CODEARTIFACT, "CODEARTIFACT_DOMAIN", "my-domain", "aws.codeartifact"),
            (PyPIBackend.GITLAB, "GITLAB_PROJECT_ID", "12345", "gitlab.company.com"),
            (PyPIBackend.AZURE_ARTIFACTS, "AZURE_ORG", "myorg", "pkgs.dev.azure.com"),
        ],
    )
    def test_get_repository_url_with_env(
        self, backend: PyPIBackend, env_var: str, env_value: str, expected_substring: str
    ) -> None:
        """Test repository URL generation for different backends.

        Args:
            backend: PyPI backend enum
            env_var: Environment variable name
            env_value: Environment variable value
            expected_substring: Expected substring in URL
        """
        # Arrange: Create publisher and set environment
        publisher = PackagePublisher(backend)

        with patch.dict(os.environ, {env_var: env_value}):
            # Act: Get URL
            url = publisher.get_repository_url()

            # Assert: URL contains expected substring
            assert expected_substring in url

    def test_get_repository_url_devpi_default(self) -> None:
        """Test devpi URL with default value."""
        # Arrange: Create devpi publisher
        publisher = PackagePublisher(PyPIBackend.DEVPI)

        with patch.dict(os.environ, {}, clear=True):
            # Act: Get URL
            url = publisher.get_repository_url()

            # Assert: Default URL returned
            assert "pypi.company.com" in url

    def test_get_repository_url_aws_codeartifact_composite(self) -> None:
        """Test AWS CodeArtifact URL with domain and repository.

        This backend requires multiple environment variables.
        """
        # Arrange: Create AWS publisher
        publisher = PackagePublisher(PyPIBackend.AWS_CODEARTIFACT)

        with patch.dict(
            os.environ,
            {"CODEARTIFACT_DOMAIN": "test-domain", "CODEARTIFACT_REPOSITORY": "test-repo"},
        ):
            # Act: Get URL
            url = publisher.get_repository_url()

            # Assert: URL contains both domain and repository
            assert "test-domain" in url
            assert "test-repo" in url


class TestGetAuthToken:
    """Tests for get_auth_token method."""

    def test_get_auth_token_success(self) -> None:
        """Test successful token retrieval from environment."""
        # Arrange: Create publisher and set token
        publisher = PackagePublisher(PyPIBackend.DEVPI)

        with patch.dict(os.environ, {"DEVPI_TOKEN": "test-token-123"}):
            # Act: Get token
            token = publisher.get_auth_token()

            # Assert: Token retrieved
            assert token == "test-token-123"

    def test_get_auth_token_missing(self) -> None:
        """Test error when token environment variable not set."""
        # Arrange: Create publisher without token
        publisher = PackagePublisher(PyPIBackend.ARTIFACTORY)

        with patch.dict(os.environ, {}, clear=True):
            # Act & Assert: Raises ValueError
            with pytest.raises(ValueError, match="Authentication token not found"):
                publisher.get_auth_token()

    @pytest.mark.parametrize(
        "backend,expected_env_var",
        [
            (PyPIBackend.DEVPI, "DEVPI_TOKEN"),
            (PyPIBackend.ARTIFACTORY, "ARTIFACTORY_TOKEN"),
            (PyPIBackend.AWS_CODEARTIFACT, "AWS_CODEARTIFACT_TOKEN"),
            (PyPIBackend.GITLAB, "GITLAB_TOKEN"),
            (PyPIBackend.AZURE_ARTIFACTS, "AZURE_ARTIFACTS_TOKEN"),
        ],
    )
    def test_get_auth_token_backend_specific(
        self, backend: PyPIBackend, expected_env_var: str
    ) -> None:
        """Test that correct token variable is used for each backend.

        Args:
            backend: PyPI backend enum
            expected_env_var: Expected environment variable name
        """
        # Arrange: Create publisher and set token
        publisher = PackagePublisher(backend)

        with patch.dict(os.environ, {expected_env_var: "test-token"}):
            # Act: Get token
            token = publisher.get_auth_token()

            # Assert: Token retrieved
            assert token == "test-token"


class TestConfigurePypirc:
    """Tests for configure_pypirc method."""

    @pytest.fixture
    def publisher(self) -> PackagePublisher:
        """Create PackagePublisher instance.

        Returns:
            PackagePublisher configured for devpi
        """
        return PackagePublisher(PyPIBackend.DEVPI)

    @patch("pathlib.Path.home")
    @patch.dict(
        os.environ, {"DEVPI_TOKEN": "test-token", "DEVPI_INDEX_URL": "https://test.pypi.com"}
    )
    def test_configure_pypirc_creates_file(
        self, mock_home: MagicMock, publisher: PackagePublisher, tmp_path: Path
    ) -> None:
        """Test that .pypirc file is created with correct content.

        Args:
            mock_home: Mocked Path.home
            publisher: PackagePublisher instance
            tmp_path: Pytest temporary directory
        """
        # Arrange: Mock home directory
        mock_home.return_value = tmp_path

        # Act: Configure .pypirc
        backup_path = publisher.configure_pypirc()

        # Assert: File created
        pypirc_path = tmp_path / ".pypirc"
        assert pypirc_path.exists()
        assert backup_path is None

        # Verify content
        content = pypirc_path.read_text()
        assert "[distutils]" in content
        assert "index-servers = private" in content
        assert "[private]" in content
        assert "repository = https://test.pypi.com" in content
        assert "username = __token__" in content
        assert "password = test-token" in content

    @patch("pathlib.Path.home")
    @patch.dict(os.environ, {"DEVPI_TOKEN": "test-token"})
    def test_configure_pypirc_backs_up_existing(
        self, mock_home: MagicMock, publisher: PackagePublisher, tmp_path: Path
    ) -> None:
        """Test that existing .pypirc is backed up before replacement.

        Args:
            mock_home: Mocked Path.home
            publisher: PackagePublisher instance
            tmp_path: Pytest temporary directory
        """
        # Arrange: Create existing .pypirc
        mock_home.return_value = tmp_path
        pypirc_path = tmp_path / ".pypirc"
        original_content = "[distutils]\nindex-servers = old\n"
        pypirc_path.write_text(original_content)

        # Act: Configure .pypirc
        backup_path = publisher.configure_pypirc()

        # Assert: Backup created
        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == original_content
        # New .pypirc has different content
        assert pypirc_path.read_text() != original_content

    @patch("pathlib.Path.home")
    @patch.dict(os.environ, {"DEVPI_TOKEN": "test-token"})
    def test_configure_pypirc_secure_permissions(
        self, mock_home: MagicMock, publisher: PackagePublisher, tmp_path: Path
    ) -> None:
        """Test that .pypirc has secure permissions (0600).

        Args:
            mock_home: Mocked Path.home
            publisher: PackagePublisher instance
            tmp_path: Pytest temporary directory
        """
        # Arrange: Mock home directory
        mock_home.return_value = tmp_path

        # Act: Configure .pypirc
        publisher.configure_pypirc()

        # Assert: Permissions are 0600 (owner read/write only)
        pypirc_path = tmp_path / ".pypirc"
        assert oct(pypirc_path.stat().st_mode)[-3:] == "600"


class TestVersionManagerMain:
    """Tests for version.py main function."""

    @patch("version.VersionManager.create_git_tag")
    @patch("version.VersionManager.update_changelog")
    @patch("version.VersionManager.update_version")
    @patch("version.VersionManager.bump_version")
    @patch("version.VersionManager.get_current_version")
    @patch("subprocess.run")
    def test_main_patch_version_no_tag(
        self,
        mock_subprocess: MagicMock,
        mock_get_version: MagicMock,
        mock_bump: MagicMock,
        mock_update_version: MagicMock,
        mock_update_changelog: MagicMock,
        mock_create_tag: MagicMock,
    ) -> None:
        """Test main function with patch version bump and no tag.

        Args:
            mock_subprocess: Mocked subprocess.run
            mock_get_version: Mocked get_current_version
            mock_bump: Mocked bump_version
            mock_update_version: Mocked update_version
            mock_update_changelog: Mocked update_changelog
            mock_create_tag: Mocked create_git_tag
        """
        # Arrange: Mock version operations
        mock_get_version.return_value = "0.2.0"
        mock_bump.return_value = "0.2.1"
        mock_subprocess.return_value = Mock(returncode=0)

        # Act: Run main with patch argument (no tag)
        import sys

        original_argv = sys.argv
        try:
            sys.argv = ["version.py", "patch"]
            from version import main

            main()
        finally:
            sys.argv = original_argv

        # Assert: Version updated but tag not created
        assert mock_get_version.called
        assert mock_bump.called
        assert mock_update_version.called
        assert mock_update_changelog.called
        assert not mock_create_tag.called

    @patch("version.VersionManager.create_git_tag")
    @patch("version.VersionManager.update_changelog")
    @patch("version.VersionManager.update_version")
    @patch("version.VersionManager.bump_version")
    @patch("version.VersionManager.get_current_version")
    @patch("subprocess.run")
    def test_main_minor_version_with_tag(
        self,
        mock_subprocess: MagicMock,
        mock_get_version: MagicMock,
        mock_bump: MagicMock,
        mock_update_version: MagicMock,
        mock_update_changelog: MagicMock,
        mock_create_tag: MagicMock,
    ) -> None:
        """Test main function with minor version bump and tag creation.

        Args:
            mock_subprocess: Mocked subprocess.run
            mock_get_version: Mocked get_current_version
            mock_bump: Mocked bump_version
            mock_update_version: Mocked update_version
            mock_update_changelog: Mocked update_changelog
            mock_create_tag: Mocked create_git_tag
        """
        # Arrange: Mock version operations
        mock_get_version.return_value = "0.2.0"
        mock_bump.return_value = "0.3.0"
        mock_subprocess.return_value = Mock(returncode=0)

        # Act: Run main with minor and --tag
        import sys

        original_argv = sys.argv
        try:
            sys.argv = ["version.py", "minor", "--tag"]
            from version import main

            main()
        finally:
            sys.argv = original_argv

        # Assert: Tag created
        assert mock_create_tag.called
        mock_create_tag.assert_called_once_with("0.3.0", None)


class TestPublishPackagesMain:
    """Tests for publish.py main function."""

    @patch("publish.PackagePublisher.publish_packages")
    @patch.dict(os.environ, {"PYPI_BACKEND": "devpi"})
    def test_main_devpi_backend(self, mock_publish: MagicMock) -> None:
        """Test main function with devpi backend.

        Args:
            mock_publish: Mocked publish_packages
        """
        # Arrange: Mock successful publish
        mock_publish.return_value = True

        # Act: Run main
        import sys

        original_argv = sys.argv
        try:
            sys.argv = ["publish.py"]
            from publish import main

            main()
        finally:
            sys.argv = original_argv

        # Assert: Publish called
        assert mock_publish.called

    @patch.dict(os.environ, {"PYPI_BACKEND": "invalid_backend"})
    def test_main_invalid_backend(self) -> None:
        """Test main function with invalid backend exits with code 1."""
        # Act & Assert: Run main and expect SystemExit
        import sys

        original_argv = sys.argv
        try:
            sys.argv = ["publish.py"]
            from publish import main

            with pytest.raises(SystemExit) as exc_info:
                main()

            # Assert: Exit code is 1
            assert exc_info.value.code == 1
        finally:
            sys.argv = original_argv

    @patch("publish.PackagePublisher.publish_packages")
    @patch.dict(os.environ, {"PYPI_BACKEND": "artifactory"})
    def test_main_publish_failure(self, mock_publish: MagicMock) -> None:
        """Test main function exits when publish fails.

        Args:
            mock_publish: Mocked publish_packages
        """
        # Arrange: Mock failed publish
        mock_publish.return_value = False

        # Act & Assert: Run main and expect SystemExit
        import sys

        original_argv = sys.argv
        try:
            sys.argv = ["publish.py"]
            from publish import main

            with pytest.raises(SystemExit) as exc_info:
                main()

            # Assert: Exit code is 1
            assert exc_info.value.code == 1
        finally:
            sys.argv = original_argv


class TestPublishPackages:
    """Tests for publish_packages method."""

    @pytest.fixture
    def publisher(self, tmp_path: Path) -> PackagePublisher:
        """Create PackagePublisher with temporary directory.

        Args:
            tmp_path: Pytest temporary directory

        Returns:
            PackagePublisher instance configured for testing
        """
        publisher = PackagePublisher(PyPIBackend.DEVPI)
        publisher.root_dir = tmp_path
        publisher.dist_dir = tmp_path / "dist"
        publisher.dist_dir.mkdir()
        return publisher

    @patch("publish.PackagePublisher.configure_pypirc")
    @patch("subprocess.run")
    @patch.dict(os.environ, {"DEVPI_TOKEN": "test-token"})
    def test_publish_packages_success(
        self,
        mock_run: MagicMock,
        mock_configure: MagicMock,
        publisher: PackagePublisher,
        tmp_path: Path,
    ) -> None:
        """Test successful package publishing.

        Args:
            mock_run: Mocked subprocess.run
            mock_configure: Mocked configure_pypirc
            publisher: PackagePublisher instance
            tmp_path: Pytest temporary directory
        """
        # Arrange: Create distributions
        dist_dir = tmp_path / "dist"
        sdist = dist_dir / "test-0.1.0.tar.gz"
        wheel = dist_dir / "test-0.1.0-py3-none-any.whl"
        sdist.write_text("sdist")
        wheel.write_text("wheel")

        mock_configure.return_value = None
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        # Act: Publish packages
        result = publisher.publish_packages()

        # Assert: Success
        assert result is True
        mock_run.assert_called_once()
        # Verify twine command
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "twine"
        assert call_args[1] == "upload"
        assert "-r" in call_args
        assert "private" in call_args

    def test_publish_packages_no_distributions(
        self, publisher: PackagePublisher, tmp_path: Path
    ) -> None:
        """Test error when no distributions found in dist/.

        Args:
            publisher: PackagePublisher instance
            tmp_path: Pytest temporary directory
        """
        # Arrange: Empty dist directory
        assert len(list(publisher.dist_dir.glob("*"))) == 0

        # Act: Try to publish
        result = publisher.publish_packages()

        # Assert: Failure
        assert result is False

    @patch("pathlib.Path.home")
    @patch("publish.PackagePublisher.configure_pypirc")
    @patch("subprocess.run")
    @patch.dict(os.environ, {"DEVPI_TOKEN": "test-token"})
    def test_publish_packages_restores_pypirc_on_success(
        self,
        mock_run: MagicMock,
        mock_configure: MagicMock,
        mock_home: MagicMock,
        publisher: PackagePublisher,
        tmp_path: Path,
    ) -> None:
        """Test that .pypirc is cleaned up after successful publish.

        Args:
            mock_run: Mocked subprocess.run
            mock_configure: Mocked configure_pypirc
            mock_home: Mocked Path.home
            publisher: PackagePublisher instance
            tmp_path: Pytest temporary directory
        """
        # Arrange: Create distributions and backup
        mock_home.return_value = tmp_path
        dist_dir = tmp_path / "dist"
        sdist = dist_dir / "test.tar.gz"
        wheel = dist_dir / "test.whl"
        sdist.write_text("sdist")
        wheel.write_text("wheel")

        # Create backup file
        backup_path = tmp_path / ".pypirc.backup"
        backup_path.write_text("original backup")
        mock_configure.return_value = backup_path

        # Create .pypirc that should be cleaned up
        pypirc_path = tmp_path / ".pypirc"
        pypirc_path.write_text("temp pypirc")

        mock_run.return_value = Mock(returncode=0)

        # Act: Publish packages
        publisher.publish_packages()

        # Assert: .pypirc restored from backup
        assert pypirc_path.read_text() == "original backup"
        assert not backup_path.exists()

    @patch("pathlib.Path.home")
    @patch("publish.PackagePublisher.configure_pypirc")
    @patch("subprocess.run")
    @patch.dict(os.environ, {"DEVPI_TOKEN": "test-token"})
    def test_publish_packages_restores_pypirc_on_failure(
        self,
        mock_run: MagicMock,
        mock_configure: MagicMock,
        mock_home: MagicMock,
        publisher: PackagePublisher,
        tmp_path: Path,
    ) -> None:
        """Test that .pypirc is cleaned up even when publish fails.

        Args:
            mock_run: Mocked subprocess.run
            mock_configure: Mocked configure_pypirc
            mock_home: Mocked Path.home
            publisher: PackagePublisher instance
            tmp_path: Pytest temporary directory
        """
        # Arrange: Create distributions
        mock_home.return_value = tmp_path
        dist_dir = tmp_path / "dist"
        sdist = dist_dir / "test.tar.gz"
        wheel = dist_dir / "test.whl"
        sdist.write_text("sdist")
        wheel.write_text("wheel")

        backup_path = tmp_path / ".pypirc.backup"
        backup_path.write_text("backup")
        mock_configure.return_value = backup_path

        pypirc_path = tmp_path / ".pypirc"
        pypirc_path.write_text("temp")

        # Mock upload failure
        mock_run.return_value = Mock(returncode=1, stderr="Upload failed")

        # Act: Try to publish (will fail)
        result = publisher.publish_packages()

        # Assert: Failure, but .pypirc still restored
        assert result is False
        assert pypirc_path.read_text() == "backup"
        assert not backup_path.exists()
