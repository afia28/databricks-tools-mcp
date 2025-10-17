"""Comprehensive tests for PackageBuilder class.

This module provides complete test coverage for the databricks-tools
package building infrastructure, including validation, building, and
verification of distributions.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Import PackageBuilder from scripts
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from build import PackageBuilder


class TestPackageBuilderInitialization:
    """Tests for PackageBuilder initialization."""

    def test_builder_initialization(self) -> None:
        """Test PackageBuilder initializes with correct project paths."""
        builder = PackageBuilder()
        assert builder.root_dir.exists()
        assert builder.root_dir.is_dir()
        assert builder.dist_dir == builder.root_dir / "dist"


class TestCleanDist:
    """Tests for clean_dist method."""

    @pytest.fixture
    def builder(self, tmp_path: Path) -> PackageBuilder:
        """Create PackageBuilder with temporary directory.

        Args:
            tmp_path: Pytest temporary directory

        Returns:
            PackageBuilder instance configured for testing
        """
        builder = PackageBuilder()
        builder.root_dir = tmp_path
        builder.dist_dir = tmp_path / "dist"
        return builder

    def test_clean_dist_removes_existing_directory(
        self, builder: PackageBuilder, tmp_path: Path
    ) -> None:
        """Test that clean_dist removes existing dist directory.

        Args:
            builder: PackageBuilder instance
            tmp_path: Pytest temporary directory
        """
        # Arrange: Create dist directory with old files
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        old_file = dist_dir / "old_file.txt"
        old_file.write_text("old content")

        # Act: Clean dist
        builder.clean_dist()

        # Assert: Directory recreated without old files
        assert dist_dir.exists()
        assert not old_file.exists()

    def test_clean_dist_creates_directory_if_missing(
        self, builder: PackageBuilder, tmp_path: Path
    ) -> None:
        """Test that clean_dist creates dist directory when doesn't exist.

        Args:
            builder: PackageBuilder instance
            tmp_path: Pytest temporary directory
        """
        # Arrange: Ensure dist doesn't exist
        dist_dir = tmp_path / "dist"
        assert not dist_dir.exists()

        # Act: Clean dist
        builder.clean_dist()

        # Assert: Directory created
        assert dist_dir.exists()
        assert dist_dir.is_dir()


class TestValidatePackage:
    """Tests for validate_package method."""

    @pytest.fixture
    def builder(self, tmp_path: Path) -> PackageBuilder:
        """Create PackageBuilder with temporary directory.

        Args:
            tmp_path: Pytest temporary directory

        Returns:
            PackageBuilder instance configured for testing
        """
        builder = PackageBuilder()
        builder.root_dir = tmp_path
        builder.dist_dir = tmp_path / "dist"
        return builder

    def test_validate_package_success(self, builder: PackageBuilder, tmp_path: Path) -> None:
        """Test validation passes with all required files present.

        Args:
            builder: PackageBuilder instance
            tmp_path: Pytest temporary directory
        """
        # Arrange: Create all required files
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")
        (tmp_path / "README.md").write_text("# Test")
        (tmp_path / "LICENSE").write_text("MIT License")
        src_dir = tmp_path / "src" / "databricks_tools"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text('__version__ = "0.1.0"')

        # Act: Validate
        result = builder.validate_package()

        # Assert: Validation passes
        assert result is True

    @pytest.mark.parametrize(
        "missing_file",
        [
            "pyproject.toml",
            "README.md",
            "LICENSE",
            "src/databricks_tools/__init__.py",
        ],
    )
    def test_validate_package_missing_file(
        self, builder: PackageBuilder, tmp_path: Path, missing_file: str
    ) -> None:
        """Test validation fails when required file is missing.

        Args:
            builder: PackageBuilder instance
            tmp_path: Pytest temporary directory
            missing_file: Name of file to omit
        """
        # Arrange: Create all files except the missing one
        files = [
            "pyproject.toml",
            "README.md",
            "LICENSE",
            "src/databricks_tools/__init__.py",
        ]
        for file in files:
            if file != missing_file:
                file_path = tmp_path / file
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text("content")

        # Act: Validate
        result = builder.validate_package()

        # Assert: Validation fails
        assert result is False


class TestBuildDistributions:
    """Tests for build_distributions method."""

    @pytest.fixture
    def builder(self, tmp_path: Path) -> PackageBuilder:
        """Create PackageBuilder with temporary directory.

        Args:
            tmp_path: Pytest temporary directory

        Returns:
            PackageBuilder instance configured for testing
        """
        builder = PackageBuilder()
        builder.root_dir = tmp_path
        builder.dist_dir = tmp_path / "dist"
        builder.dist_dir.mkdir()
        return builder

    @patch("subprocess.run")
    def test_build_distributions_success(
        self, mock_run: MagicMock, builder: PackageBuilder, tmp_path: Path
    ) -> None:
        """Test successful build creates source and wheel distributions.

        Args:
            mock_run: Mocked subprocess.run
            builder: PackageBuilder instance
            tmp_path: Pytest temporary directory
        """
        # Arrange: Mock successful build
        mock_run.return_value = Mock(returncode=0, stderr="")

        # Create expected distribution files
        dist_dir = tmp_path / "dist"
        sdist = dist_dir / "databricks-tools-0.2.0.tar.gz"
        wheel = dist_dir / "databricks_tools-0.2.0-py3-none-any.whl"
        sdist.write_text("sdist content")
        wheel.write_text("wheel content")

        # Act: Build distributions
        result_sdist, result_wheel = builder.build_distributions()

        # Assert: Build succeeded
        assert result_sdist == sdist
        assert result_wheel == wheel
        mock_run.assert_called_once_with(
            [sys.executable, "-m", "build"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

    @patch("subprocess.run")
    def test_build_distributions_failure(
        self, mock_run: MagicMock, builder: PackageBuilder
    ) -> None:
        """Test build failure raises RuntimeError.

        Args:
            mock_run: Mocked subprocess.run
            builder: PackageBuilder instance
        """
        # Arrange: Mock failed build
        mock_run.return_value = Mock(returncode=1, stderr="Build error")

        # Act & Assert: Build raises RuntimeError
        with pytest.raises(RuntimeError, match="Build failed: Build error"):
            builder.build_distributions()

    @patch("subprocess.run")
    def test_build_distributions_missing_sdist(
        self, mock_run: MagicMock, builder: PackageBuilder, tmp_path: Path
    ) -> None:
        """Test error when source distribution not found after build.

        Args:
            mock_run: Mocked subprocess.run
            builder: PackageBuilder instance
            tmp_path: Pytest temporary directory
        """
        # Arrange: Mock successful build but only wheel created
        mock_run.return_value = Mock(returncode=0, stderr="")
        dist_dir = tmp_path / "dist"
        wheel = dist_dir / "databricks_tools-0.2.0-py3-none-any.whl"
        wheel.write_text("wheel content")
        # Note: No sdist created

        # Act & Assert: Raises RuntimeError
        with pytest.raises(RuntimeError, match="Expected distribution files not found"):
            builder.build_distributions()

    @patch("subprocess.run")
    def test_build_distributions_missing_wheel(
        self, mock_run: MagicMock, builder: PackageBuilder, tmp_path: Path
    ) -> None:
        """Test error when wheel not found after build.

        Args:
            mock_run: Mocked subprocess.run
            builder: PackageBuilder instance
            tmp_path: Pytest temporary directory
        """
        # Arrange: Mock successful build but only sdist created
        mock_run.return_value = Mock(returncode=0, stderr="")
        dist_dir = tmp_path / "dist"
        sdist = dist_dir / "databricks-tools-0.2.0.tar.gz"
        sdist.write_text("sdist content")
        # Note: No wheel created

        # Act & Assert: Raises RuntimeError
        with pytest.raises(RuntimeError, match="Expected distribution files not found"):
            builder.build_distributions()


class TestVerifyDistributions:
    """Tests for verify_distributions method."""

    @pytest.fixture
    def builder(self, tmp_path: Path) -> PackageBuilder:
        """Create PackageBuilder with temporary directory.

        Args:
            tmp_path: Pytest temporary directory

        Returns:
            PackageBuilder instance configured for testing
        """
        builder = PackageBuilder()
        builder.root_dir = tmp_path
        builder.dist_dir = tmp_path / "dist"
        return builder

    @pytest.fixture
    def mock_distributions(self, tmp_path: Path) -> tuple[Path, Path]:
        """Create mock distribution files.

        Args:
            tmp_path: Pytest temporary directory

        Returns:
            Tuple of (sdist_path, wheel_path)
        """
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        sdist = dist_dir / "test-0.1.0.tar.gz"
        wheel = dist_dir / "test-0.1.0-py3-none-any.whl"
        sdist.write_text("sdist")
        wheel.write_text("wheel")
        return sdist, wheel

    @patch("subprocess.run")
    def test_verify_distributions_success(
        self,
        mock_run: MagicMock,
        builder: PackageBuilder,
        mock_distributions: tuple[Path, Path],
    ) -> None:
        """Test successful verification with twine check.

        Args:
            mock_run: Mocked subprocess.run
            builder: PackageBuilder instance
            mock_distributions: Mock sdist and wheel files
        """
        # Arrange: Mock successful twine check
        mock_run.return_value = Mock(returncode=0, stderr="")
        sdist, wheel = mock_distributions

        # Act: Verify distributions
        result = builder.verify_distributions(sdist, wheel)

        # Assert: Verification succeeded
        assert result is True
        mock_run.assert_called_once_with(
            ["twine", "check", str(sdist), str(wheel)],
            cwd=builder.root_dir,
            capture_output=True,
            text=True,
        )

    @patch("subprocess.run")
    def test_verify_distributions_failure(
        self,
        mock_run: MagicMock,
        builder: PackageBuilder,
        mock_distributions: tuple[Path, Path],
    ) -> None:
        """Test verification failure returns False.

        Args:
            mock_run: Mocked subprocess.run
            builder: PackageBuilder instance
            mock_distributions: Mock sdist and wheel files
        """
        # Arrange: Mock failed twine check
        mock_run.return_value = Mock(returncode=1, stderr="Verification failed")
        sdist, wheel = mock_distributions

        # Act: Verify distributions
        result = builder.verify_distributions(sdist, wheel)

        # Assert: Verification failed
        assert result is False


class TestMainWorkflow:
    """Tests for main build workflow."""

    @patch("build.PackageBuilder.verify_distributions")
    @patch("build.PackageBuilder.build_distributions")
    @patch("build.PackageBuilder.validate_package")
    @patch("build.PackageBuilder.clean_dist")
    def test_main_workflow_success(
        self,
        mock_clean: MagicMock,
        mock_validate: MagicMock,
        mock_build: MagicMock,
        mock_verify: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test complete main workflow executes all steps successfully.

        Args:
            mock_clean: Mocked clean_dist
            mock_validate: Mocked validate_package
            mock_build: Mocked build_distributions
            mock_verify: Mocked verify_distributions
            tmp_path: Pytest temporary directory
        """
        # Arrange: Mock all methods to succeed
        mock_validate.return_value = True
        sdist = tmp_path / "test.tar.gz"
        wheel = tmp_path / "test.whl"
        mock_build.return_value = (sdist, wheel)
        mock_verify.return_value = True

        # Act: Import and run main (with mocking to prevent sys.exit)
        from build import main

        main()

        # Assert: All steps called in order
        mock_clean.assert_called_once()
        mock_validate.assert_called_once()
        mock_build.assert_called_once()
        mock_verify.assert_called_once()

    @patch("build.PackageBuilder.validate_package")
    @patch("build.PackageBuilder.clean_dist")
    def test_main_workflow_validation_failure(
        self,
        mock_clean: MagicMock,
        mock_validate: MagicMock,
    ) -> None:
        """Test main exits with code 1 when validation fails.

        Args:
            mock_clean: Mocked clean_dist
            mock_validate: Mocked validate_package
        """
        # Arrange: Mock validation failure
        mock_validate.return_value = False

        # Act & Assert: Run main and expect SystemExit
        from build import main

        with pytest.raises(SystemExit) as exc_info:
            main()

        # Assert: Exit code is 1
        assert exc_info.value.code == 1

    @patch("build.PackageBuilder.build_distributions")
    @patch("build.PackageBuilder.validate_package")
    @patch("build.PackageBuilder.clean_dist")
    def test_main_workflow_build_failure(
        self,
        mock_clean: MagicMock,
        mock_validate: MagicMock,
        mock_build: MagicMock,
    ) -> None:
        """Test main exits with code 1 when build fails.

        Args:
            mock_clean: Mocked clean_dist
            mock_validate: Mocked validate_package
            mock_build: Mocked build_distributions
        """
        # Arrange: Mock validation succeeds, build fails
        mock_validate.return_value = True
        mock_build.side_effect = RuntimeError("Build failed")

        # Act & Assert: Run main and expect SystemExit
        from build import main

        with pytest.raises(SystemExit) as exc_info:
            main()

        # Assert: Exit code is 1
        assert exc_info.value.code == 1

    @patch("build.PackageBuilder.verify_distributions")
    @patch("build.PackageBuilder.build_distributions")
    @patch("build.PackageBuilder.validate_package")
    @patch("build.PackageBuilder.clean_dist")
    @patch("sys.exit")
    def test_main_workflow_verification_failure(
        self,
        mock_exit: MagicMock,
        mock_clean: MagicMock,
        mock_validate: MagicMock,
        mock_build: MagicMock,
        mock_verify: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test main exits with code 1 when verification fails.

        Args:
            mock_exit: Mocked sys.exit
            mock_clean: Mocked clean_dist
            mock_validate: Mocked validate_package
            mock_build: Mocked build_distributions
            mock_verify: Mocked verify_distributions
            tmp_path: Pytest temporary directory
        """
        # Arrange: Mock validation and build succeed, verify fails
        mock_validate.return_value = True
        sdist = tmp_path / "test.tar.gz"
        wheel = tmp_path / "test.whl"
        mock_build.return_value = (sdist, wheel)
        mock_verify.return_value = False

        # Act: Run main
        from build import main

        main()

        # Assert: Exit called with code 1
        mock_exit.assert_called_once_with(1)
