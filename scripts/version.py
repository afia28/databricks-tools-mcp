#!/usr/bin/env python3
"""Semantic version management for databricks-tools.

This script handles semantic versioning following MAJOR.MINOR.PATCH format.
It updates the version in __init__.py, creates git commits and tags, and
maintains CHANGELOG.md with release notes.

Example:
    $ python scripts/version.py minor --tag
    Current version: 0.2.0
    New version: 0.3.0
    ✓ Updated CHANGELOG.md for version 0.3.0
    ✓ Created and pushed tag: v0.3.0

Semantic Versioning:
    MAJOR: Incompatible API changes (1.0.0 -> 2.0.0)
    MINOR: New features, backward compatible (1.0.0 -> 1.1.0)
    PATCH: Bug fixes, backward compatible (1.0.0 -> 1.0.1)
"""

import argparse
import re
import subprocess
import sys
from datetime import date
from enum import Enum
from pathlib import Path


class BumpType(Enum):
    """Version bump types following semantic versioning.

    Attributes:
        MAJOR: Major version bump for breaking changes (1.0.0 -> 2.0.0)
        MINOR: Minor version bump for new features (1.0.0 -> 1.1.0)
        PATCH: Patch version bump for bug fixes (1.0.0 -> 1.0.1)
    """

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


class VersionManager:
    """Handles semantic versioning for databricks-tools package.

    This class manages version updates across multiple files (__init__.py,
    CHANGELOG.md), creates git commits and tags, and enforces semantic
    versioning rules. It provides a single source of truth for version
    information.

    Attributes:
        root_dir: Project root directory
        version_file: Path to __init__.py containing __version__
        changelog_file: Path to CHANGELOG.md
    """

    def __init__(self) -> None:
        """Initialize VersionManager with project paths."""
        self.root_dir = Path(__file__).parent.parent
        self.version_file = self.root_dir / "src" / "databricks_tools" / "__init__.py"
        self.changelog_file = self.root_dir / "CHANGELOG.md"

    def get_current_version(self) -> str:
        """Read current version from __init__.py.

        Parses the __version__ variable from __init__.py using regex.
        This is the single source of truth for the package version.

        Returns:
            Current version string (e.g., "0.2.0")

        Raises:
            ValueError: If version not found in __init__.py
            FileNotFoundError: If __init__.py does not exist
        """
        if not self.version_file.exists():
            raise FileNotFoundError(f"Version file not found: {self.version_file}")

        content = self.version_file.read_text()
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)

        if not match:
            raise ValueError(
                f'Version not found in {self.version_file}. Expected format: __version__ = "X.Y.Z"'
            )

        return match.group(1)

    def bump_version(self, bump_type: BumpType) -> str:
        """Increment version based on semantic versioning rules.

        Args:
            bump_type: Type of version bump (MAJOR, MINOR, or PATCH)

        Returns:
            New version string after bump

        Raises:
            ValueError: If current version is not valid semantic version

        Examples:
            >>> manager = VersionManager()
            >>> # Assuming current version is 1.2.3
            >>> manager.bump_version(BumpType.MAJOR)  # Returns "2.0.0"
            >>> manager.bump_version(BumpType.MINOR)  # Returns "1.3.0"
            >>> manager.bump_version(BumpType.PATCH)  # Returns "1.2.4"
        """
        current = self.get_current_version()

        # Parse semantic version
        parts = current.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid semantic version: {current}. Expected format: X.Y.Z")

        try:
            major, minor, patch = map(int, parts)
        except ValueError as e:
            raise ValueError(f"Invalid semantic version components in {current}: {e}") from e

        # Apply bump rules
        if bump_type == BumpType.MAJOR:
            new_version = f"{major + 1}.0.0"
        elif bump_type == BumpType.MINOR:
            new_version = f"{major}.{minor + 1}.0"
        else:  # PATCH
            new_version = f"{major}.{minor}.{patch + 1}"

        return new_version

    def update_version(self, new_version: str) -> None:
        """Update version in __init__.py.

        Replaces the __version__ assignment with the new version using regex.
        Preserves file formatting and other content.

        Args:
            new_version: New version string (e.g., "0.3.0")

        Raises:
            FileNotFoundError: If __init__.py does not exist
            ValueError: If __version__ pattern not found
        """
        if not self.version_file.exists():
            raise FileNotFoundError(f"Version file not found: {self.version_file}")

        content = self.version_file.read_text()

        # Replace version using regex
        updated, num_subs = re.subn(
            r'__version__\s*=\s*["\'][^"\']+["\']',
            f'__version__ = "{new_version}"',
            content,
        )

        if num_subs == 0:
            raise ValueError(
                f"Version pattern not found in {self.version_file}. "
                'Expected format: __version__ = "X.Y.Z"'
            )

        self.version_file.write_text(updated)
        print(f"✓ Updated {self.version_file.relative_to(self.root_dir)} to {new_version}")

    def create_git_tag(self, version: str, message: str | None = None) -> None:
        """Create annotated git tag and push to remote.

        Creates a git tag with format "vX.Y.Z" and pushes it to origin.
        Annotated tags include metadata like author, date, and message.

        Args:
            version: Version to tag (e.g., "0.3.0")
            message: Optional tag message. Defaults to "Release version X.Y.Z"

        Raises:
            subprocess.CalledProcessError: If git commands fail
            RuntimeError: If not in a git repository

        Security:
            Uses subprocess.run with check=True to ensure commands succeed.
            Git credentials must be configured separately.
        """
        tag_name = f"v{version}"
        tag_message = message or f"Release version {version}"

        try:
            # Create annotated tag
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", tag_message],
                cwd=self.root_dir,
                check=True,
                capture_output=True,
                text=True,
            )

            # Push tag to remote
            subprocess.run(
                ["git", "push", "origin", tag_name],
                cwd=self.root_dir,
                check=True,
                capture_output=True,
                text=True,
            )

            print(f"✓ Created and pushed tag: {tag_name}")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to create/push git tag: {e.stderr if e.stderr else str(e)}"
            ) from e

    def update_changelog(self, version: str) -> None:
        """Update CHANGELOG.md with new version section.

        Adds a new version section with today's date and empty subsections
        for Added, Changed, and Fixed entries. Inserts the new section
        before the first existing version section.

        Args:
            version: Version to add to changelog (e.g., "0.3.0")

        Raises:
            FileNotFoundError: If CHANGELOG.md does not exist (warning only)

        Note:
            If version already exists in changelog, no action is taken.
        """
        if not self.changelog_file.exists():
            print(f"⚠ Warning: CHANGELOG.md not found at {self.changelog_file}")
            return

        content = self.changelog_file.read_text()

        # Check if version already exists
        if f"## [{version}]" in content:
            print(f"⚠ Version {version} already in CHANGELOG.md")
            return

        # Find insertion point (before first existing version section)
        lines = content.split("\n")
        insert_index = 0

        for i, line in enumerate(lines):
            if line.startswith("## [") and line[3].isdigit():
                insert_index = i
                break

        # If no version sections found, insert after header
        if insert_index == 0:
            for i, line in enumerate(lines):
                if line.startswith("# ") or line.startswith("## "):
                    insert_index = i + 2  # After header + blank line
                    break

        # Create new version section
        today = date.today().strftime("%Y-%m-%d")
        new_section = [
            f"## [{version}] - {today}",
            "",
            "### Added",
            "- ",
            "",
            "### Changed",
            "- ",
            "",
            "### Fixed",
            "- ",
            "",
        ]

        # Insert new section
        lines[insert_index:insert_index] = new_section

        self.changelog_file.write_text("\n".join(lines))
        print(f"✓ Updated CHANGELOG.md for version {version}")


def main() -> None:
    """Main version management process with CLI interface.

    Parses command line arguments, bumps version, updates files,
    creates git commit, and optionally creates/pushes git tag.

    Command Line Arguments:
        bump_type: Type of version bump (major, minor, patch)
        --tag: Create and push git tag after version bump
        --message: Custom message for git tag

    Raises:
        SystemExit: If any step fails

    Examples:
        $ python scripts/version.py patch
        $ python scripts/version.py minor --tag
        $ python scripts/version.py major --tag --message "Breaking changes"
    """
    parser = argparse.ArgumentParser(
        description="Manage databricks-tools version following semantic versioning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/version.py patch            # Bump patch version (0.2.0 -> 0.2.1)
  python scripts/version.py minor --tag      # Bump minor and create tag
  python scripts/version.py major --tag --message "Breaking changes"

After running this script:
  1. Review and update CHANGELOG.md with detailed release notes
  2. Run: python scripts/build.py
  3. Run: python scripts/publish.py
        """,
    )

    parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch"],
        help="Type of version bump (major: breaking, minor: features, patch: fixes)",
    )
    parser.add_argument(
        "--tag",
        action="store_true",
        help="Create and push git tag for the new version",
    )
    parser.add_argument(
        "--message",
        help="Custom message for git tag (default: 'Release version X.Y.Z')",
    )

    args = parser.parse_args()

    manager = VersionManager()

    print("=" * 60)
    print("Version Management for databricks-tools")
    print("=" * 60)

    # Get current version
    try:
        current = manager.get_current_version()
        print(f"\nCurrent version: {current}")
    except (FileNotFoundError, ValueError) as e:
        print(f"✗ Error reading current version: {e}")
        sys.exit(1)

    # Bump version
    bump_type = BumpType[args.bump_type.upper()]
    try:
        new_version = manager.bump_version(bump_type)
        print(f"New version: {new_version} ({bump_type.value} bump)")
    except ValueError as e:
        print(f"✗ Error bumping version: {e}")
        sys.exit(1)

    # Update files
    try:
        manager.update_version(new_version)
        manager.update_changelog(new_version)
    except (FileNotFoundError, ValueError, OSError) as e:
        print(f"✗ Error updating files: {e}")
        sys.exit(1)

    # Commit changes
    print("\nCommitting version changes...")
    try:
        subprocess.run(
            ["git", "add", str(manager.version_file), str(manager.changelog_file)],
            cwd=manager.root_dir,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", f"Bump version to {new_version}"],
            cwd=manager.root_dir,
            check=True,
        )
        print("✓ Committed version bump to git")
    except subprocess.CalledProcessError as e:
        print(f"✗ Git commit failed: {e}")
        sys.exit(1)

    # Create tag if requested
    if args.tag:
        print("\nCreating git tag...")
        try:
            manager.create_git_tag(new_version, args.message)
        except RuntimeError as e:
            print(f"✗ Error creating git tag: {e}")
            sys.exit(1)

    # Success message
    print("\n" + "=" * 60)
    print(f"✓ Version bumped to {new_version}")
    print("=" * 60)
    print("\nNext steps:")
    print(f"  1. Update CHANGELOG.md with detailed release notes for {new_version}")
    print("  2. Review changes: git log -1 -p")
    print("  3. Build package: python scripts/build.py")
    print("  4. Publish package: python scripts/publish.py")

    if not args.tag:
        print("\nTo create git tag later:")
        print(f"  python scripts/version.py {args.bump_type} --tag")


if __name__ == "__main__":
    main()
