#!/usr/bin/env python3
"""Build source and wheel distributions for databricks-tools.

This script handles package building, validation, and verification using the
hatchling build backend. It ensures all required files exist, builds both
source distribution (.tar.gz) and wheel (.whl), and validates the outputs
with twine.

Example:
    $ python scripts/build.py
    ✓ Created source distribution: databricks-tools-0.2.0.tar.gz
    ✓ Created wheel: databricks_tools-0.2.0-py3-none-any.whl
    ✓ Build complete!
"""

import shutil
import subprocess
import sys
from pathlib import Path


class PackageBuilder:
    """Handles package building and validation using Builder pattern.

    This class orchestrates the complex build process with validation,
    building, and verification steps. It ensures reproducible builds
    by cleaning old distributions and validating package structure.

    Attributes:
        root_dir: Project root directory containing pyproject.toml
        dist_dir: Distribution directory where built packages are stored
    """

    def __init__(self) -> None:
        """Initialize PackageBuilder with project paths."""
        self.root_dir = Path(__file__).parent.parent
        self.dist_dir = self.root_dir / "dist"

    def clean_dist(self) -> None:
        """Remove old distributions to ensure clean build.

        Removes the entire dist/ directory and recreates it empty.
        This prevents confusion from stale build artifacts.

        Raises:
            OSError: If directory removal or creation fails
        """
        if self.dist_dir.exists():
            print(f"Cleaning old distributions from {self.dist_dir}...")
            shutil.rmtree(self.dist_dir)
        self.dist_dir.mkdir(exist_ok=True)
        print("✓ Distribution directory cleaned")

    def validate_package(self) -> bool:
        """Validate package structure and metadata before building.

        Checks that all required files exist:
        - pyproject.toml: Package metadata and build configuration
        - README.md: Project documentation
        - LICENSE: License information
        - src/databricks_tools/__init__.py: Package entry point with version

        Returns:
            True if validation passes, False otherwise

        Raises:
            FileNotFoundError: If any required file is missing
        """
        print("Validating package structure...")

        # Check required files exist
        required_files = [
            "pyproject.toml",
            "README.md",
            "LICENSE",
            "src/databricks_tools/__init__.py",
        ]

        for file in required_files:
            file_path = self.root_dir / file
            if not file_path.exists():
                print(f"✗ Error: Required file {file} not found")
                return False

        print("✓ All required files present")
        return True

    def build_distributions(self) -> tuple[Path, Path]:
        """Build source distribution and wheel using python -m build.

        Executes the build process using the python build module with
        hatchling backend. Creates both .tar.gz (sdist) and .whl (wheel).

        Returns:
            Tuple of (sdist_path, wheel_path) for the built distributions

        Raises:
            RuntimeError: If build process fails
            IndexError: If expected distribution files not found
        """
        print("\nBuilding source distribution and wheel...")

        result = subprocess.run(
            [sys.executable, "-m", "build"],
            cwd=self.root_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Build failed: {result.stderr}")

        # Find created files
        sdist_files = list(self.dist_dir.glob("*.tar.gz"))
        wheel_files = list(self.dist_dir.glob("*.whl"))

        if not sdist_files or not wheel_files:
            raise RuntimeError("Expected distribution files not found in dist/")

        sdist = sdist_files[0]
        wheel = wheel_files[0]

        print(f"✓ Created source distribution: {sdist.name}")
        print(f"✓ Created wheel: {wheel.name}")

        return sdist, wheel

    def verify_distributions(self, sdist: Path, wheel: Path) -> bool:
        """Verify built distributions are valid and installable.

        Uses twine check to validate distribution metadata, long description
        rendering, and package structure according to PyPI standards.

        Args:
            sdist: Path to source distribution (.tar.gz)
            wheel: Path to wheel distribution (.whl)

        Returns:
            True if distributions pass all checks, False otherwise

        Raises:
            FileNotFoundError: If twine is not installed
        """
        print("\nVerifying distributions with twine...")

        result = subprocess.run(
            ["twine", "check", str(sdist), str(wheel)],
            cwd=self.root_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"✗ Distribution check failed: {result.stderr}")
            return False

        print("✓ Distributions passed twine checks")
        return True


def main() -> None:
    """Main build process orchestrating all steps.

    Executes the build pipeline:
    1. Clean old distributions
    2. Validate package structure
    3. Build source distribution and wheel
    4. Verify distributions with twine

    Exits with code 1 if any step fails.

    Raises:
        SystemExit: If validation or verification fails
    """
    builder = PackageBuilder()

    # Clean old distributions
    builder.clean_dist()

    # Validate package
    if not builder.validate_package():
        print("\n✗ Build failed: Package validation errors")
        sys.exit(1)

    # Build distributions
    try:
        sdist, wheel = builder.build_distributions()
    except RuntimeError as e:
        print(f"\n✗ Build failed: {e}")
        sys.exit(1)

    # Verify distributions
    if not builder.verify_distributions(sdist, wheel):
        print("\n✗ Build failed: Distribution verification errors")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✓ Build complete! Distributions ready for publishing.")
    print("=" * 60)
    print("\nBuilt packages:")
    print(f"  - {sdist.name}")
    print(f"  - {wheel.name}")
    print("\nNext step:")
    print("  python scripts/publish.py")


if __name__ == "__main__":
    main()
