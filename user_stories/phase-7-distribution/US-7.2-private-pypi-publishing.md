# US-7.2: Private PyPI Publishing and Version Management

## Metadata
- **Story ID**: US-7.2
- **Title**: Private PyPI Publishing and Version Management
- **Phase**: Phase 7 - Distribution & Deployment
- **Estimated LOC**: ~250 lines
- **Dependencies**: US-7.1 (Pip Installation and Initialization)
- **Status**: ⬜ Not Started

## Overview
Configure automated package publishing to private PyPI server with version management, build pipeline automation, and git tag integration to enable organization-wide distribution through simplified `pip install databricks-tools` workflow.

## User Story
**As a** release engineer or team lead
**I want** automated package publishing to our private PyPI server with proper versioning
**So that** team members can install databricks-tools via standard pip workflow without accessing source code

## Acceptance Criteria
1. ✅ Package builds successfully as both source distribution (.tar.gz) and wheel (.whl) using hatchling
2. ✅ Build script validates package metadata and contents before creating distributions
3. ✅ Private PyPI server configuration supports multiple backends (devpi, Artifactory, AWS CodeArtifact)
4. ✅ Publishing script authenticates securely using API tokens stored in environment variables
5. ✅ Version management follows semantic versioning with automatic version bumping
6. ✅ Git tags are automatically created and pushed for each published version
7. ✅ Users can install via `pip install databricks-tools` from private PyPI after publishing
8. ✅ Rollback procedure documented and tested for reverting problematic releases
9. ✅ CI/CD workflow automates build and publish on tagged releases
10. ✅ Package upgrade path tested (`pip install --upgrade databricks-tools` works correctly)

## Technical Requirements

### Package Metadata Enhancement (pyproject.toml)
```python
[project]
name = "databricks-tools"
version = "0.2.0"  # Managed by scripts/version.py
description = "MCP server for Databricks Unity Catalog with role-based access control"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Ahmed Afia", email = "afia.ahmed.28@gmail.com"}
]
keywords = ["databricks", "mcp", "sql", "unity-catalog", "mcp-server", "data-tools"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Operating System :: OS Independent",
    "Topic :: Database :: Database Engines/Servers",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

[project.urls]
Homepage = "https://github.com/org/databricks-tools"
Repository = "https://github.com/org/databricks-tools"
Documentation = "https://github.com/org/databricks-tools#readme"
Issues = "https://github.com/org/databricks-tools/issues"
Changelog = "https://github.com/org/databricks-tools/blob/main/CHANGELOG.md"

[build-system]
requires = ["hatchling>=1.18.0"]
build-backend = "hatchling.build"

[tool.hatch.version]
path = "src/databricks_tools/__init__.py"

[tool.hatch.build]
include = [
    "src/databricks_tools",
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
]
exclude = [
    "*.pyc",
    "__pycache__",
    ".git",
    ".env*",
    "tests/",
]

[tool.hatch.build.targets.wheel]
packages = ["src/databricks_tools"]
```

### Build Script (scripts/build.py)
```python
#!/usr/bin/env python3
"""Build source and wheel distributions for databricks-tools."""

import shutil
import subprocess
import sys
from pathlib import Path

class PackageBuilder:
    """Handles package building and validation."""

    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.dist_dir = self.root_dir / "dist"

    def clean_dist(self) -> None:
        """Remove old distributions."""
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        self.dist_dir.mkdir(exist_ok=True)

    def validate_package(self) -> bool:
        """Validate package structure and metadata."""
        # Check required files exist
        required_files = ["pyproject.toml", "README.md", "LICENSE", "src/databricks_tools/__init__.py"]
        for file in required_files:
            if not (self.root_dir / file).exists():
                print(f"Error: Required file {file} not found")
                return False

        # Run package checks
        result = subprocess.run([sys.executable, "-m", "build", "--check"],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Package validation failed: {result.stderr}")
            return False

        return True

    def build_distributions(self) -> tuple[Path, Path]:
        """Build source distribution and wheel."""
        print("Building source distribution and wheel...")
        result = subprocess.run([sys.executable, "-m", "build"],
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Build failed: {result.stderr}")

        # Find created files
        sdist = list(self.dist_dir.glob("*.tar.gz"))[0]
        wheel = list(self.dist_dir.glob("*.whl"))[0]

        print(f"✓ Created source distribution: {sdist.name}")
        print(f"✓ Created wheel: {wheel.name}")

        return sdist, wheel

    def verify_distributions(self, sdist: Path, wheel: Path) -> bool:
        """Verify built distributions are installable."""
        # Check with twine
        result = subprocess.run(["twine", "check", str(sdist), str(wheel)],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Distribution check failed: {result.stderr}")
            return False

        print("✓ Distributions passed twine checks")
        return True

def main():
    """Main build process."""
    builder = PackageBuilder()

    # Clean old distributions
    builder.clean_dist()

    # Validate package
    if not builder.validate_package():
        sys.exit(1)

    # Build distributions
    try:
        sdist, wheel = builder.build_distributions()
    except RuntimeError as e:
        print(f"Build failed: {e}")
        sys.exit(1)

    # Verify distributions
    if not builder.verify_distributions(sdist, wheel):
        sys.exit(1)

    print("\n✓ Build complete! Distributions ready for publishing.")
    print(f"  Next step: python scripts/publish.py")

if __name__ == "__main__":
    main()
```

### Publishing Script (scripts/publish.py)
```python
#!/usr/bin/env python3
"""Publish databricks-tools to private PyPI server."""

import os
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

class PyPIBackend(Enum):
    """Supported private PyPI backends."""
    DEVPI = "devpi"
    ARTIFACTORY = "artifactory"
    AWS_CODEARTIFACT = "aws_codeartifact"
    GITLAB = "gitlab"
    AZURE_ARTIFACTS = "azure_artifacts"

class PackagePublisher:
    """Handles package publishing to private PyPI."""

    def __init__(self, backend: PyPIBackend):
        self.backend = backend
        self.root_dir = Path(__file__).parent.parent
        self.dist_dir = self.root_dir / "dist"

    def get_repository_url(self) -> str:
        """Get repository URL based on backend."""
        if self.backend == PyPIBackend.DEVPI:
            return os.getenv("DEVPI_INDEX_URL", "https://pypi.company.com/root/prod/+simple/")
        elif self.backend == PyPIBackend.ARTIFACTORY:
            return os.getenv("ARTIFACTORY_PYPI_URL", "https://artifactory.company.com/artifactory/api/pypi/pypi-local")
        elif self.backend == PyPIBackend.AWS_CODEARTIFACT:
            domain = os.getenv("CODEARTIFACT_DOMAIN", "my-domain")
            repo = os.getenv("CODEARTIFACT_REPOSITORY", "python-packages")
            return f"https://aws.codeartifact.com/{domain}/{repo}/pypi/simple/"
        elif self.backend == PyPIBackend.GITLAB:
            project_id = os.getenv("GITLAB_PROJECT_ID", "12345")
            return f"https://gitlab.company.com/api/v4/projects/{project_id}/packages/pypi"
        elif self.backend == PyPIBackend.AZURE_ARTIFACTS:
            org = os.getenv("AZURE_ORG", "myorg")
            project = os.getenv("AZURE_PROJECT", "myproject")
            feed = os.getenv("AZURE_FEED", "python-packages")
            return f"https://pkgs.dev.azure.com/{org}/{project}/_packaging/{feed}/pypi/upload"
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")

    def get_auth_token(self) -> str:
        """Get authentication token for PyPI backend."""
        token_env_var = f"{self.backend.value.upper()}_TOKEN"
        token = os.getenv(token_env_var)
        if not token:
            raise ValueError(f"Authentication token not found. Set {token_env_var} environment variable.")
        return token

    def configure_pypirc(self) -> Path:
        """Create temporary .pypirc for authentication."""
        pypirc_path = Path.home() / ".pypirc"

        # Backup existing .pypirc if it exists
        backup_path = None
        if pypirc_path.exists():
            backup_path = pypirc_path.with_suffix(".backup")
            pypirc_path.rename(backup_path)

        # Write new .pypirc
        repository_url = self.get_repository_url()
        token = self.get_auth_token()

        pypirc_content = f"""[distutils]
index-servers = private

[private]
repository = {repository_url}
username = __token__
password = {token}
"""
        pypirc_path.write_text(pypirc_content)
        pypirc_path.chmod(0o600)  # Secure permissions

        return backup_path

    def publish_packages(self) -> bool:
        """Upload packages to private PyPI."""
        # Find distributions
        distributions = list(self.dist_dir.glob("*.tar.gz")) + list(self.dist_dir.glob("*.whl"))
        if not distributions:
            print("No distributions found in dist/. Run scripts/build.py first.")
            return False

        print(f"Publishing to {self.backend.value}...")

        # Configure authentication
        backup_path = self.configure_pypirc()

        try:
            # Upload with twine
            cmd = ["twine", "upload", "-r", "private"] + [str(d) for d in distributions]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"Upload failed: {result.stderr}")
                return False

            print("✓ Successfully published to private PyPI!")
            print(f"\nInstallation command for users:")
            print(f"  pip install databricks-tools --index-url {self.get_repository_url()}")

            return True

        finally:
            # Restore original .pypirc
            pypirc_path = Path.home() / ".pypirc"
            pypirc_path.unlink(missing_ok=True)
            if backup_path and backup_path.exists():
                backup_path.rename(pypirc_path)

def main():
    """Main publishing process."""
    # Detect backend from environment or use default
    backend_name = os.getenv("PYPI_BACKEND", "devpi").lower()

    try:
        backend = PyPIBackend[backend_name.upper()]
    except KeyError:
        print(f"Unknown PyPI backend: {backend_name}")
        print(f"Supported backends: {', '.join([b.value for b in PyPIBackend])}")
        sys.exit(1)

    publisher = PackagePublisher(backend)

    if not publisher.publish_packages():
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Version Management Script (scripts/version.py)
```python
#!/usr/bin/env python3
"""Semantic version management for databricks-tools."""

import re
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

class BumpType(Enum):
    """Version bump types."""
    MAJOR = "major"  # 1.0.0 -> 2.0.0
    MINOR = "minor"  # 1.0.0 -> 1.1.0
    PATCH = "patch"  # 1.0.0 -> 1.0.1

class VersionManager:
    """Handles semantic versioning."""

    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.version_file = self.root_dir / "src" / "databricks_tools" / "__init__.py"

    def get_current_version(self) -> str:
        """Read current version from __init__.py."""
        content = self.version_file.read_text()
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        if not match:
            raise ValueError("Version not found in __init__.py")
        return match.group(1)

    def bump_version(self, bump_type: BumpType) -> str:
        """Increment version based on bump type."""
        current = self.get_current_version()
        major, minor, patch = map(int, current.split('.'))

        if bump_type == BumpType.MAJOR:
            new_version = f"{major + 1}.0.0"
        elif bump_type == BumpType.MINOR:
            new_version = f"{major}.{minor + 1}.0"
        else:  # PATCH
            new_version = f"{major}.{minor}.{patch + 1}"

        return new_version

    def update_version(self, new_version: str) -> None:
        """Update version in __init__.py."""
        content = self.version_file.read_text()
        updated = re.sub(
            r'__version__\s*=\s*["\'][^"\']+["\']',
            f'__version__ = "{new_version}"',
            content
        )
        self.version_file.write_text(updated)

    def create_git_tag(self, version: str, message: Optional[str] = None) -> None:
        """Create and push git tag."""
        tag_name = f"v{version}"
        tag_message = message or f"Release version {version}"

        # Create annotated tag
        subprocess.run(["git", "tag", "-a", tag_name, "-m", tag_message], check=True)

        # Push tag to remote
        subprocess.run(["git", "push", "origin", tag_name], check=True)

        print(f"✓ Created and pushed tag: {tag_name}")

    def update_changelog(self, version: str) -> None:
        """Update CHANGELOG.md with new version."""
        changelog_path = self.root_dir / "CHANGELOG.md"
        if not changelog_path.exists():
            print("Warning: CHANGELOG.md not found")
            return

        # Add new version section at the top
        from datetime import date
        today = date.today().strftime("%Y-%m-%d")

        content = changelog_path.read_text()
        if f"## [{version}]" in content:
            print(f"Version {version} already in CHANGELOG.md")
            return

        # Insert new version section after header
        lines = content.split('\n')
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith('## ['):
                insert_index = i
                break

        new_section = f"\n## [{version}] - {today}\n\n### Added\n- \n\n### Changed\n- \n\n### Fixed\n- \n"
        lines.insert(insert_index, new_section)

        changelog_path.write_text('\n'.join(lines))
        print(f"✓ Updated CHANGELOG.md for version {version}")

def main():
    """Main version management process."""
    import argparse

    parser = argparse.ArgumentParser(description="Manage databricks-tools version")
    parser.add_argument("bump_type", choices=["major", "minor", "patch"],
                       help="Type of version bump")
    parser.add_argument("--tag", action="store_true",
                       help="Create and push git tag")
    parser.add_argument("--message", help="Tag message")

    args = parser.parse_args()

    manager = VersionManager()

    # Get current version
    current = manager.get_current_version()
    print(f"Current version: {current}")

    # Bump version
    bump_type = BumpType[args.bump_type.upper()]
    new_version = manager.bump_version(bump_type)
    print(f"New version: {new_version}")

    # Update files
    manager.update_version(new_version)
    manager.update_changelog(new_version)

    # Commit changes
    subprocess.run(["git", "add", "src/databricks_tools/__init__.py", "CHANGELOG.md"], check=True)
    subprocess.run(["git", "commit", "-m", f"Bump version to {new_version}"], check=True)

    # Create tag if requested
    if args.tag:
        manager.create_git_tag(new_version, args.message)

    print(f"\n✓ Version bumped to {new_version}")
    print("Next steps:")
    print(f"  1. Update CHANGELOG.md with release notes")
    print(f"  2. Run: python scripts/build.py")
    print(f"  3. Run: python scripts/publish.py")

if __name__ == "__main__":
    main()
```

### CI/CD Workflow (.github/workflows/publish.yml)
```yaml
name: Publish to Private PyPI

on:
  push:
    tags:
      - 'v*'  # Trigger on version tags
  workflow_dispatch:  # Allow manual trigger

jobs:
  publish:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine

    - name: Build distributions
      run: python scripts/build.py

    - name: Publish to private PyPI
      env:
        PYPI_BACKEND: ${{ vars.PYPI_BACKEND }}
        DEVPI_INDEX_URL: ${{ secrets.DEVPI_INDEX_URL }}
        DEVPI_TOKEN: ${{ secrets.DEVPI_TOKEN }}
      run: python scripts/publish.py

    - name: Create GitHub Release
      if: startsWith(github.ref, 'refs/tags/')
      uses: softprops/action-gh-release@v1
      with:
        files: |
          dist/*.whl
          dist/*.tar.gz
        body: |
          Release ${{ github.ref_name }}

          Install from private PyPI:
          ```bash
          pip install databricks-tools --index-url ${{ secrets.DEVPI_INDEX_URL }}
          ```
```

## Design Patterns Used

1. **Builder Pattern**: PackageBuilder orchestrates the complex build process with validation, building, and verification steps
2. **Strategy Pattern**: PyPIBackend enum with backend-specific repository URLs and authentication methods
3. **Template Method Pattern**: Publishing workflow with customizable steps for different PyPI backends

## Key Implementation Notes

### Security Considerations
- API tokens stored in environment variables, never in code
- .pypirc created with 0600 permissions and cleaned up after use
- Backup existing .pypirc to prevent data loss
- Use __token__ username for token-based authentication
- Validate SSL certificates when connecting to PyPI servers

### Private PyPI Backend Comparison
```
| Backend         | Pros                          | Cons                      | Best For               |
|-----------------|-------------------------------|---------------------------|------------------------|
| devpi           | Simple, lightweight, fast     | Limited features          | Small teams            |
| Artifactory     | Enterprise features, HA       | Complex, expensive        | Large enterprises      |
| AWS CodeArtifact| AWS integration, managed      | AWS lock-in, costs        | AWS-heavy orgs         |
| GitLab          | Integrated with GitLab        | GitLab required           | GitLab users           |
| Azure Artifacts | Azure integration             | Azure lock-in             | Azure-heavy orgs       |
```

### Version Management Best Practices
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update __version__ in single source of truth
- Create annotated git tags for releases
- Maintain CHANGELOG.md with all changes
- Never reuse version numbers
- Test upgrade path before publishing

### Build Reproducibility
- Pin build dependencies in pyproject.toml
- Use deterministic build process
- Include all necessary files in source distribution
- Exclude test files and development configs
- Verify distributions with twine check

### Rollback Procedures
1. **Remove from PyPI**: Contact PyPI admin to yank version
2. **Git revert**: `git revert <commit>` and tag new patch version
3. **Notify users**: Send communication about bad version
4. **Force downgrade**: Users run `pip install databricks-tools==<previous-version>`

## Files to Create/Modify

**Files to Create:**
- `scripts/build.py` - Package build script (~100 lines)
- `scripts/publish.py` - Publishing script with multi-backend support (~150 lines)
- `scripts/version.py` - Version management utility (~120 lines)
- `.github/workflows/publish.yml` - CI/CD workflow for automated publishing (~40 lines)
- `CONTRIBUTING.md` - Release process documentation (~80 lines)
- `tests/test_packaging/test_build.py` - Build process tests (~100 lines)
- `tests/test_packaging/test_metadata.py` - Package metadata tests (~80 lines)

**Files to Modify:**
- `pyproject.toml` - Enhanced metadata, build configuration (~20 lines modified)
- `src/databricks_tools/__init__.py` - Add __version__ attribute (~2 lines)
- `README.md` - Update installation instructions for PyPI (~15 lines)
- `.gitignore` - Add dist/ and build/ directories (~2 lines)

## Test Cases

### Build Process Tests
1. `test_clean_dist_removes_old_files` - Verify dist/ directory is cleaned before build
2. `test_validate_package_checks_required_files` - Test validation of package structure
3. `test_build_creates_sdist_and_wheel` - Verify both distribution types are created
4. `test_build_fails_on_invalid_metadata` - Test build failure with bad pyproject.toml
5. `test_verify_distributions_with_twine` - Test twine check passes on built packages

### Publishing Tests
6. `test_get_repository_url_for_each_backend` - Test URL generation for all backends
7. `test_get_auth_token_from_environment` - Test token retrieval from env vars
8. `test_configure_pypirc_creates_valid_config` - Test .pypirc generation
9. `test_pypirc_backup_and_restore` - Test existing .pypirc is preserved
10. `test_publish_with_missing_distributions` - Test error when dist/ is empty

### Version Management Tests
11. `test_get_current_version_from_init` - Test reading version from __init__.py
12. `test_bump_major_version` - Test major version increment (1.0.0 -> 2.0.0)
13. `test_bump_minor_version` - Test minor version increment (1.0.0 -> 1.1.0)
14. `test_bump_patch_version` - Test patch version increment (1.0.0 -> 1.0.1)
15. `test_create_git_tag_with_annotation` - Test git tag creation and pushing

### Integration Tests
16. `test_end_to_end_build_and_publish` - Full workflow from build to publish
17. `test_installation_from_private_pypi` - Test pip install after publishing
18. `test_upgrade_from_previous_version` - Test pip install --upgrade
19. `test_rollback_to_previous_version` - Test downgrading to older version
20. `test_ci_workflow_on_tag_push` - Test GitHub Actions workflow triggers

## Definition of Done

- [ ] Package metadata enhanced in pyproject.toml with all classifiers and URLs
- [ ] Build script validates and creates both sdist and wheel distributions
- [ ] Publishing script supports at least 3 PyPI backends (devpi, Artifactory, AWS)
- [ ] Version management script implements semantic versioning with git tagging
- [ ] CI/CD workflow triggers on version tags and publishes automatically
- [ ] Authentication uses secure token storage in environment variables
- [ ] Installation tested: `pip install databricks-tools` works from private PyPI
- [ ] Upgrade tested: `pip install --upgrade databricks-tools` updates correctly
- [ ] Rollback procedure documented and tested successfully
- [ ] All 20 test cases passing with 90%+ coverage
- [ ] CONTRIBUTING.md documents complete release process
- [ ] README.md updated with PyPI installation instructions
- [ ] Pre-commit hooks pass (ruff, mypy, pytest)
- [ ] Package installable on Python 3.10, 3.11, and 3.12
- [ ] Distributions pass twine check validation

## Expected Outcome

After implementing this story, the team will have:

1. **Automated build pipeline** creating consistent, valid distributions
2. **Private PyPI publishing** with support for multiple backend options
3. **Simplified installation** via `pip install databricks-tools` from private index
4. **Version management** with semantic versioning and git tag integration
5. **CI/CD automation** publishing on every tagged release

Example release workflow:
```bash
# 1. Developer bumps version and creates tag
$ python scripts/version.py minor --tag
Current version: 0.2.0
New version: 0.3.0
✓ Updated CHANGELOG.md for version 0.3.0
✓ Created and pushed tag: v0.3.0

# 2. CI/CD automatically builds and publishes (or manual)
$ python scripts/build.py
✓ Created source distribution: databricks-tools-0.3.0.tar.gz
✓ Created wheel: databricks_tools-0.3.0-py3-none-any.whl
✓ Build complete! Distributions ready for publishing.

$ python scripts/publish.py
Publishing to devpi...
✓ Successfully published to private PyPI!

Installation command for users:
  pip install databricks-tools --index-url https://pypi.company.com/root/prod/+simple/

# 3. Users install from private PyPI
$ pip install databricks-tools --index-url https://pypi.company.com/root/prod/+simple/
Collecting databricks-tools
  Downloading databricks_tools-0.3.0-py3-none-any.whl (45 kB)
Successfully installed databricks-tools-0.3.0

$ databricks-tools --version
databricks-tools version 0.3.0
```

## Related Stories
- **Depends on**: US-7.1 (Pip Installation and Initialization - must be complete)
- **Blocks**: Future distribution enhancements (US-7.3+)
- **Related**: US-6.4 (Documentation - CHANGELOG.md structure)
