# Contributing to Databricks Tools

Thank you for your interest in contributing to databricks-tools! This document provides guidelines for releasing new versions and publishing to private PyPI.

## Prerequisites

Before releasing a new version, ensure you have:

- **Git**: Configured with commit and push access to the repository
- **Python 3.10+**: With `uv` package manager installed
- **Development dependencies**: Installed via `uv sync --group dev`
- **PyPI access token**: For your organization's private PyPI server
- **Environment variables**: Configured for your PyPI backend (see Publishing section)

## Release Workflow

Follow this step-by-step process for releasing a new version:

### 1. Prepare Release

```bash
# Ensure working directory is clean
git status

# Pull latest changes
git pull origin main

# Run all quality checks
uv run pre-commit run --all-files

# Ensure all tests pass
uv run pytest tests/
```

### 2. Bump Version

Use semantic versioning (MAJOR.MINOR.PATCH):

```bash
# Patch release for bug fixes (0.2.0 -> 0.2.1)
python scripts/version.py patch

# Minor release for new features (0.2.0 -> 0.3.0)
python scripts/version.py minor

# Major release for breaking changes (0.2.0 -> 1.0.0)
python scripts/version.py major

# Add --tag flag to create and push git tag immediately
python scripts/version.py minor --tag
```

The script automatically:
- Updates `src/databricks_tools/__init__.py`
- Adds new version section to `CHANGELOG.md`
- Creates git commit with changes
- (Optional) Creates annotated git tag and pushes to remote

### 3. Update Changelog

Edit `CHANGELOG.md` to add detailed release notes:

```markdown
## [0.3.0] - 2025-10-17

### Added
- New feature X that does Y
- Support for Z configuration

### Changed
- Improved performance of ABC operation
- Updated dependencies to latest versions

### Fixed
- Bug where XYZ was not working correctly
- Memory leak in ABC component
```

Commit changelog updates:

```bash
git add CHANGELOG.md
git commit -m "Update CHANGELOG.md for v0.3.0"
git push origin main
```

### 4. Build Packages

Build source distribution and wheel:

```bash
python scripts/build.py
```

This script:
- Cleans old distributions from `dist/`
- Validates package structure
- Builds `.tar.gz` source distribution and `.whl` wheel
- Verifies distributions with `twine check`

### 5. Publish to Private PyPI

Configure environment variables for your PyPI backend:

```bash
# For devpi (default)
export PYPI_BACKEND=devpi
export DEVPI_INDEX_URL="https://pypi.company.com/root/prod/+simple/"
export DEVPI_TOKEN="your-token-here"

# For Artifactory
export PYPI_BACKEND=artifactory
export ARTIFACTORY_PYPI_URL="https://artifactory.company.com/artifactory/api/pypi/pypi-local"
export ARTIFACTORY_TOKEN="your-token-here"

# For AWS CodeArtifact
export PYPI_BACKEND=aws_codeartifact
export CODEARTIFACT_DOMAIN="my-domain"
export CODEARTIFACT_REPOSITORY="python-packages"
export AWS_CODEARTIFACT_TOKEN="your-token-here"
```

Publish packages:

```bash
python scripts/publish.py
```

The script displays installation commands for users after successful upload.

## Rollback Procedures

If a release has critical issues:

### 1. Revert Git Tag

```bash
# Delete local tag
git tag -d v0.3.0

# Delete remote tag
git push origin :refs/tags/v0.3.0
```

### 2. Revert Version Commits

```bash
# Find commit hash of version bump
git log --oneline

# Revert the commit
git revert <commit-hash>
git push origin main
```

### 3. Unpublish from PyPI (if possible)

Some private PyPI servers allow version deletion. Consult your server's documentation.

For most servers, you'll need to:
1. Delete the package version through the web UI
2. Or contact your PyPI administrator

## Troubleshooting

### Build Fails with "Required file not found"

Ensure all required files exist:
- `pyproject.toml`
- `README.md`
- `LICENSE`
- `src/databricks_tools/__init__.py`

### Twine Check Fails

Common issues:
- Missing long description in `pyproject.toml`
- Invalid reStructuredText in README
- Missing required metadata fields

### Publish Fails with "Authentication error"

Check:
- Environment variables are set correctly
- Token has not expired
- Token has upload permissions for the repository
- PyPI backend URL is correct

### Git Tag Already Exists

If you see "tag already exists":

```bash
# Delete existing tag locally and remotely
git tag -d v0.3.0
git push origin :refs/tags/v0.3.0

# Re-run version script with --tag
python scripts/version.py <bump_type> --tag
```

## Best Practices

1. **Always test before releasing**: Run full test suite and quality checks
2. **Update documentation**: Keep README, CHANGELOG, and docs up to date
3. **Use semantic versioning**: Follow MAJOR.MINOR.PATCH conventions strictly
4. **Tag releases**: Always create git tags for releases (use `--tag` flag)
5. **Write clear changelog entries**: Help users understand what changed
6. **Test installation**: Verify packages install correctly from private PyPI
7. **Communicate releases**: Notify team about new versions and breaking changes

## Getting Help

If you encounter issues not covered here:
1. Check the error message carefully
2. Review script source code (`scripts/build.py`, `scripts/publish.py`, `scripts/version.py`)
3. Consult your organization's internal documentation
4. Contact the databricks-tools maintainers

## Security

- **Never commit tokens**: Always use environment variables
- **Rotate tokens regularly**: Update PyPI tokens periodically
- **Use minimal permissions**: Tokens should only have upload permissions
- **Review .pypirc**: Ensure the publish script cleans up after itself
