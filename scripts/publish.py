#!/usr/bin/env python3
"""Publish databricks-tools to private PyPI server.

This script handles publishing built packages to various private PyPI backends
including devpi, Artifactory, AWS CodeArtifact, GitLab, and Azure Artifacts.
It manages authentication, .pypirc configuration, and secure token handling.

Example:
    $ PYPI_BACKEND=devpi DEVPI_TOKEN=xxx python scripts/publish.py
    Publishing to devpi...
    ✓ Successfully published to private PyPI!

    Installation command for users:
      pip install databricks-tools --index-url https://pypi.company.com/root/prod/+simple/
"""

import os
import subprocess
import sys
from enum import Enum
from pathlib import Path


class PyPIBackend(Enum):
    """Supported private PyPI backends using Strategy pattern.

    Each backend has specific URL patterns and authentication requirements.
    The enum value matches the environment variable prefix for backend-specific
    configuration.

    Attributes:
        DEVPI: Lightweight PyPI server for small teams
        ARTIFACTORY: JFrog Artifactory enterprise repository
        AWS_CODEARTIFACT: AWS managed artifact repository
        GITLAB: GitLab package registry
        AZURE_ARTIFACTS: Azure DevOps artifact feeds
    """

    DEVPI = "devpi"
    ARTIFACTORY = "artifactory"
    AWS_CODEARTIFACT = "aws_codeartifact"
    GITLAB = "gitlab"
    AZURE_ARTIFACTS = "azure_artifacts"


class PackagePublisher:
    """Handles package publishing to private PyPI using Template Method pattern.

    This class manages the publishing workflow including authentication setup,
    .pypirc configuration, package upload, and cleanup. It supports multiple
    PyPI backends through the PyPIBackend enum.

    Attributes:
        backend: The PyPI backend to publish to
        root_dir: Project root directory
        dist_dir: Directory containing built distributions
    """

    def __init__(self, backend: PyPIBackend) -> None:
        """Initialize PackagePublisher with specified backend.

        Args:
            backend: PyPI backend to use for publishing
        """
        self.backend = backend
        self.root_dir = Path(__file__).parent.parent
        self.dist_dir = self.root_dir / "dist"

    def get_repository_url(self) -> str:
        """Get repository URL based on backend configuration.

        Reads backend-specific environment variables to construct the
        appropriate PyPI repository URL. Falls back to sensible defaults
        if environment variables are not set.

        Returns:
            Repository URL for the configured backend

        Raises:
            ValueError: If backend is not supported

        Environment Variables:
            DEVPI_INDEX_URL: devpi index URL
            ARTIFACTORY_PYPI_URL: Artifactory PyPI repository URL
            CODEARTIFACT_DOMAIN: AWS CodeArtifact domain
            CODEARTIFACT_REPOSITORY: AWS CodeArtifact repository name
            GITLAB_PROJECT_ID: GitLab project ID
            AZURE_ORG: Azure DevOps organization
            AZURE_PROJECT: Azure DevOps project
            AZURE_FEED: Azure Artifacts feed name
        """
        if self.backend == PyPIBackend.DEVPI:
            return os.getenv("DEVPI_INDEX_URL", "https://pypi.company.com/root/prod/+simple/")
        elif self.backend == PyPIBackend.ARTIFACTORY:
            return os.getenv(
                "ARTIFACTORY_PYPI_URL",
                "https://artifactory.company.com/artifactory/api/pypi/pypi-local",
            )
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
        """Get authentication token for PyPI backend from environment.

        Reads the backend-specific token from environment variables.
        Token variable name is constructed as {BACKEND}_TOKEN.

        Returns:
            Authentication token for the backend

        Raises:
            ValueError: If authentication token is not found

        Environment Variables:
            DEVPI_TOKEN: devpi authentication token
            ARTIFACTORY_TOKEN: Artifactory API token
            AWS_CODEARTIFACT_TOKEN: AWS CodeArtifact auth token
            GITLAB_TOKEN: GitLab deploy token or personal access token
            AZURE_ARTIFACTS_TOKEN: Azure Artifacts personal access token

        Security:
            Tokens are never logged or printed to stdout/stderr
        """
        token_env_var = f"{self.backend.value.upper()}_TOKEN"
        token = os.getenv(token_env_var)
        if not token:
            raise ValueError(
                f"Authentication token not found. Set {token_env_var} environment variable."
            )
        return token

    def configure_pypirc(self) -> Path | None:
        """Create temporary .pypirc for authentication with secure permissions.

        Generates a .pypirc file in the user's home directory for twine
        authentication. If an existing .pypirc exists, it is backed up
        before being replaced.

        Returns:
            Path to backup file if existing .pypirc was backed up, None otherwise

        Raises:
            OSError: If file operations fail

        Security:
            - .pypirc is created with 0600 permissions (owner read/write only)
            - Existing .pypirc is backed up to .pypirc.backup
            - Token is written to file but never logged
            - File is cleaned up after upload in publish_packages()
        """
        pypirc_path = Path.home() / ".pypirc"

        # Backup existing .pypirc if it exists
        backup_path = None
        if pypirc_path.exists():
            backup_path = pypirc_path.with_suffix(".backup")
            print(f"Backing up existing .pypirc to {backup_path}")
            pypirc_path.rename(backup_path)

        # Get configuration
        repository_url = self.get_repository_url()
        token = self.get_auth_token()

        # Write new .pypirc with token authentication
        pypirc_content = f"""[distutils]
index-servers = private

[private]
repository = {repository_url}
username = __token__
password = {token}
"""
        pypirc_path.write_text(pypirc_content)
        pypirc_path.chmod(0o600)  # Secure permissions: owner read/write only

        print("✓ Created .pypirc with secure permissions")

        return backup_path

    def publish_packages(self) -> bool:
        """Upload packages to private PyPI using twine.

        Finds all distributions in dist/ directory, configures authentication,
        and uploads packages using twine. Automatically cleans up .pypirc
        and restores backup after upload (success or failure).

        Returns:
            True if publishing succeeds, False otherwise

        Raises:
            FileNotFoundError: If no distributions found in dist/

        Security:
            - .pypirc is cleaned up in finally block to prevent token leakage
            - Original .pypirc is restored if it existed
            - Upload errors are printed without exposing tokens
        """
        # Find distributions
        distributions = list(self.dist_dir.glob("*.tar.gz")) + list(self.dist_dir.glob("*.whl"))
        if not distributions:
            print("✗ No distributions found in dist/. Run scripts/build.py first.")
            return False

        print(f"\nPublishing to {self.backend.value}...")
        print(f"Found {len(distributions)} distribution(s) to upload")

        # Configure authentication
        backup_path = self.configure_pypirc()

        try:
            # Upload with twine using .pypirc configuration
            cmd = ["twine", "upload", "-r", "private"] + [str(d) for d in distributions]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"✗ Upload failed: {result.stderr}")
                return False

            print("\n" + "=" * 60)
            print("✓ Successfully published to private PyPI!")
            print("=" * 60)
            print("\nInstallation command for users:")
            print(f"  pip install databricks-tools --index-url {self.get_repository_url()}")
            print("\nUpgrade command:")
            print(
                f"  pip install --upgrade databricks-tools --index-url {self.get_repository_url()}"
            )

            return True

        finally:
            # Always restore original .pypirc (cleanup)
            pypirc_path = Path.home() / ".pypirc"
            pypirc_path.unlink(missing_ok=True)

            if backup_path and backup_path.exists():
                print("Restoring original .pypirc from backup")
                backup_path.rename(pypirc_path)


def main() -> None:
    """Main publishing process.

    Detects PyPI backend from PYPI_BACKEND environment variable and
    orchestrates the publishing workflow. Exits with code 1 on failure.

    Environment Variables:
        PYPI_BACKEND: PyPI backend name (devpi, artifactory, aws_codeartifact,
                      gitlab, azure_artifacts). Defaults to 'devpi'.

    Raises:
        SystemExit: If publishing fails or backend is invalid
    """
    # Detect backend from environment or use default
    backend_name = os.getenv("PYPI_BACKEND", "devpi").lower()

    try:
        backend = PyPIBackend[backend_name.upper()]
    except KeyError:
        print(f"✗ Unknown PyPI backend: {backend_name}")
        print("\nSupported backends:")
        for b in PyPIBackend:
            print(f"  - {b.value}")
        print("\nSet PYPI_BACKEND environment variable to one of the above values.")
        sys.exit(1)

    print("=" * 60)
    print(f"Publishing databricks-tools to {backend.value}")
    print("=" * 60)

    publisher = PackagePublisher(backend)

    if not publisher.publish_packages():
        sys.exit(1)


if __name__ == "__main__":
    main()
