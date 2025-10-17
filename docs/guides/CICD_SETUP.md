# CI/CD Setup Guide

This guide explains how to set up and use the automated CI/CD pipeline for databricks-tools, including automated testing, linting, and publishing to private PyPI.

## Table of Contents

1. [Overview](#overview)
2. [GitHub Actions Workflows](#github-actions-workflows)
3. [Setting Up Private PyPI Publishing](#setting-up-private-pypi-publishing)
4. [Creating a Release](#creating-a-release)
5. [Troubleshooting](#troubleshooting)

## Overview

The databricks-tools project uses GitHub Actions for automated CI/CD with three main workflows:

1. **CI Workflow** (`ci.yml`) - Runs on every push/PR to validate code quality
2. **Publish Workflow** (`publish.yml`) - Publishes releases to private PyPI when tags are pushed
3. **Claude Code Review** (`claude-code-review.yml`) - Automated code review using Claude

## GitHub Actions Workflows

### CI Workflow

**Triggers:**
- Push to `main` branch
- Pull requests targeting `main` branch

**What it does:**
- Lints code with ruff
- Checks code formatting
- Tests installation on multiple OS (Ubuntu, macOS) and Python versions (3.10, 3.11, 3.12)

**File:** `.github/workflows/ci.yml`

### Publish Workflow

**Triggers:**
- Push of version tags (e.g., `v0.2.0`, `v1.0.0`)
- Manual trigger via workflow_dispatch

**What it does:**
1. Checks out code
2. Sets up Python 3.10
3. Installs build dependencies (`build`, `twine`)
4. Builds source distribution (.tar.gz) and wheel (.whl) using `scripts/build.py`
5. Publishes to private PyPI using `scripts/publish.py`
6. Creates GitHub release with distribution files attached

**File:** `.github/workflows/publish.yml`

### Claude Code Review Workflow

**Triggers:**
- Pull requests
- Manual trigger

**What it does:**
- Automated code review using Claude AI
- Provides intelligent feedback on code quality and best practices

**File:** `.github/workflows/claude-code-review.yml`

## Setting Up Private PyPI Publishing

### Step 1: Choose Your PyPI Backend

The publish workflow supports multiple private PyPI backends:

- **devpi** - Lightweight PyPI server (recommended for small teams)
- **artifactory** - JFrog Artifactory enterprise repository
- **aws_codeartifact** - AWS managed artifact repository
- **gitlab** - GitLab package registry
- **azure_artifacts** - Azure DevOps artifact feeds

### Step 2: Configure Repository Variables

Add the following **repository variable** in GitHub Settings → Secrets and variables → Actions → Variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `PYPI_BACKEND` | `devpi` \| `artifactory` \| `aws_codeartifact` \| `gitlab` \| `azure_artifacts` | PyPI backend to use |

**How to add:**
1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click the **Variables** tab
4. Click **New repository variable**
5. Add `PYPI_BACKEND` with your chosen backend value

### Step 3: Configure Repository Secrets

Add the required **secrets** for your chosen backend in GitHub Settings → Secrets and variables → Actions → Secrets:

#### For devpi:

| Secret | Description | Example |
|--------|-------------|---------|
| `DEVPI_INDEX_URL` | devpi index URL | `https://pypi.company.com/root/prod/+simple/` |
| `DEVPI_TOKEN` | devpi authentication token | `abc123...` |

#### For Artifactory:

| Secret | Description | Example |
|--------|-------------|---------|
| `ARTIFACTORY_PYPI_URL` | Artifactory PyPI repository URL | `https://artifactory.company.com/artifactory/api/pypi/pypi-local` |
| `ARTIFACTORY_TOKEN` | Artifactory API token | `abc123...` |

#### For AWS CodeArtifact:

| Secret | Description | Example |
|--------|-------------|---------|
| `CODEARTIFACT_DOMAIN` | AWS CodeArtifact domain | `my-domain` |
| `CODEARTIFACT_REPOSITORY` | AWS CodeArtifact repository name | `python-packages` |
| `AWS_CODEARTIFACT_TOKEN` | AWS CodeArtifact auth token | `abc123...` |

#### For GitLab:

| Secret | Description | Example |
|--------|-------------|---------|
| `GITLAB_PROJECT_ID` | GitLab project ID | `12345` |
| `GITLAB_TOKEN` | GitLab deploy token or personal access token | `abc123...` |

#### For Azure Artifacts:

| Secret | Description | Example |
|--------|-------------|---------|
| `AZURE_ORG` | Azure DevOps organization | `myorg` |
| `AZURE_PROJECT` | Azure DevOps project | `myproject` |
| `AZURE_FEED` | Azure Artifacts feed name | `python-packages` |
| `AZURE_ARTIFACTS_TOKEN` | Azure Artifacts personal access token | `abc123...` |

**How to add secrets:**
1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click the **Secrets** tab
4. Click **New repository secret**
5. Add each secret with its name and value

### Step 4: Grant Workflow Permissions

Ensure the workflow has permission to create releases:

1. Go to **Settings** → **Actions** → **General**
2. Scroll to **Workflow permissions**
3. Select **Read and write permissions**
4. Check **Allow GitHub Actions to create and approve pull requests**
5. Click **Save**

## Creating a Release

### Automated Release Process

1. **Update Version Number**

   Edit `src/databricks_tools/__init__.py`:
   ```python
   __version__ = "0.3.0"  # Update to new version
   ```

2. **Update CHANGELOG.md**

   Add release notes for the new version:
   ```markdown
   ## [0.3.0] - 2024-10-18

   ### Added
   - New feature X
   - Enhancement Y

   ### Fixed
   - Bug Z
   ```

3. **Commit Changes**
   ```bash
   git add src/databricks_tools/__init__.py CHANGELOG.md
   git commit -m "chore: bump version to 0.3.0"
   git push origin main
   ```

4. **Create and Push Tag**
   ```bash
   git tag v0.3.0
   git push origin v0.3.0
   ```

5. **Monitor Workflow**
   - Go to **Actions** tab in GitHub
   - Watch the "Publish to Private PyPI" workflow run
   - Verify successful completion

6. **Verify Release**
   - Check **Releases** section in GitHub
   - Confirm distribution files (.whl, .tar.gz) are attached
   - Verify installation instructions in release body

### Manual Release Trigger

If needed, you can manually trigger the publish workflow:

1. Go to **Actions** tab
2. Select **Publish to Private PyPI** workflow
3. Click **Run workflow**
4. Select branch/tag
5. Click **Run workflow** button

## Workflow Execution Details

### Build Process

The `scripts/build.py` script performs the following:

1. **Clean** - Removes old distributions from `dist/`
2. **Validate** - Checks required files exist (pyproject.toml, README.md, LICENSE, __init__.py)
3. **Build** - Creates source distribution (.tar.gz) and wheel (.whl) using `python -m build`
4. **Verify** - Validates distributions with `twine check`

### Publish Process

The `scripts/publish.py` script performs the following:

1. **Detect Backend** - Reads `PYPI_BACKEND` environment variable
2. **Get Credentials** - Retrieves backend-specific URL and token from environment
3. **Configure Authentication** - Creates temporary `.pypirc` with secure permissions (0600)
4. **Upload** - Uses `twine upload` to publish distributions
5. **Cleanup** - Removes `.pypirc` and restores backup if existed

### Security Features

- **No Token Logging** - Tokens are never printed to stdout/stderr
- **Secure File Permissions** - `.pypirc` created with 0600 permissions (owner-only read/write)
- **Automatic Cleanup** - `.pypirc` removed after upload (success or failure)
- **Backup Restoration** - Original `.pypirc` backed up and restored
- **GitHub Secrets** - Sensitive data stored as encrypted secrets

## Troubleshooting

### Workflow Fails at Build Step

**Error:** "Required file X not found"

**Solution:**
- Ensure all required files exist: `pyproject.toml`, `README.md`, `LICENSE`, `src/databricks_tools/__init__.py`
- Verify file paths are correct

### Workflow Fails at Publish Step

**Error:** "Authentication token not found"

**Solution:**
- Verify `PYPI_BACKEND` variable is set correctly
- Ensure backend-specific secrets are configured (e.g., `DEVPI_TOKEN` for devpi backend)
- Check secret names match expected format: `{BACKEND}_TOKEN`

**Error:** "Upload failed: 401 Unauthorized"

**Solution:**
- Verify token has write permissions for the PyPI repository
- Regenerate token and update GitHub secret
- Check repository URL is correct

### Release Not Created

**Error:** No release appears after workflow completes

**Solution:**
- Verify tag follows `v*` pattern (e.g., `v0.2.0` not `0.2.0`)
- Check workflow permissions allow creating releases
- Look for errors in "Create GitHub Release" step logs

### Token Exposed in Logs

**Issue:** Token appears in workflow logs

**Solution:**
- Tokens should never appear in logs - this is a security issue
- Verify `scripts/publish.py` doesn't print token values
- GitHub automatically masks secrets in logs, but custom scripts must not expose them
- If exposed, immediately revoke token and generate new one

### Installation Fails After Publishing

**Error:** `pip install databricks-tools` fails with 404

**Solution:**
- Verify package published successfully by checking PyPI server
- Ensure users are using correct index URL:
  ```bash
  pip install databricks-tools --index-url https://your-pypi-url
  ```
- Check package name matches exactly (case-sensitive)
- Allow a few minutes for package to propagate

### Version Already Exists

**Error:** "File already exists" during upload

**Solution:**
- Most PyPI servers don't allow overwriting existing versions
- Bump version number in `src/databricks_tools/__init__.py`
- Create new tag with new version number
- Delete old tag if needed: `git tag -d v0.2.0 && git push origin :refs/tags/v0.2.0`

## Local Testing

Before pushing tags, test the build and publish scripts locally:

### Test Build

```bash
# Clean old builds
rm -rf dist/

# Run build script
python scripts/build.py

# Verify outputs
ls -lh dist/
# Should see: databricks-tools-X.Y.Z.tar.gz and databricks_tools-X.Y.Z-py3-none-any.whl
```

### Test Publish (Dry Run)

```bash
# Set environment variables
export PYPI_BACKEND=devpi
export DEVPI_INDEX_URL=https://pypi.company.com/root/prod/+simple/
export DEVPI_TOKEN=your-token-here

# Run publish script (will actually publish!)
python scripts/publish.py

# Note: There's no dry-run mode, so test on dev environment first
```

## Best Practices

1. **Version Numbering**
   - Follow semantic versioning: MAJOR.MINOR.PATCH
   - Increment MAJOR for breaking changes
   - Increment MINOR for new features
   - Increment PATCH for bug fixes

2. **Release Timing**
   - Create releases during business hours for quick issue resolution
   - Avoid Friday releases (less time to fix issues)
   - Test in development environment before production release

3. **Documentation**
   - Always update CHANGELOG.md before releasing
   - Include migration guides for breaking changes
   - Document new features with examples

4. **Testing**
   - Ensure all tests pass before creating release tag
   - Test installation from private PyPI before announcing
   - Verify examples still work with new version

5. **Communication**
   - Announce releases to users via email/Slack
   - Include installation and upgrade instructions
   - Highlight breaking changes and migration steps

## Advanced Configuration

### Multi-Environment Publishing

To publish to multiple environments (dev/staging/prod):

1. Create separate workflows for each environment:
   - `publish-dev.yml` - Publishes to dev index
   - `publish-prod.yml` - Publishes to prod index

2. Use different tag patterns:
   - Dev: `dev-*` (e.g., `dev-0.2.0`)
   - Prod: `v*` (e.g., `v0.2.0`)

3. Configure environment-specific secrets:
   - `DEV_DEVPI_INDEX_URL`, `DEV_DEVPI_TOKEN`
   - `PROD_DEVPI_INDEX_URL`, `PROD_DEVPI_TOKEN`

### Pre-Release Versions

For beta/alpha releases:

1. Use pre-release version numbers:
   ```python
   __version__ = "0.3.0a1"  # Alpha
   __version__ = "0.3.0b1"  # Beta
   __version__ = "0.3.0rc1"  # Release candidate
   ```

2. Create tags with pre-release suffix:
   ```bash
   git tag v0.3.0a1
   git push origin v0.3.0a1
   ```

3. Mark GitHub release as pre-release:
   - Edit `.github/workflows/publish.yml`
   - Add `prerelease: true` to release step for pre-release tags

## Support

For issues with CI/CD:
- Check workflow logs in GitHub Actions tab
- Review CHANGELOG.md for recent changes
- Consult your DevOps team for private PyPI access issues
- Open an issue in the repository for workflow bugs

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python Packaging Guide](https://packaging.python.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)
