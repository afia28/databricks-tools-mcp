"""Database connection manager for Databricks SQL connections.

This module provides a ConnectionManager class that implements the context manager
protocol for safe and efficient management of Databricks SQL connections.
"""

from databricks import sql
from databricks.sql.client import Connection

from databricks_tools.config.models import WorkspaceConfig


class ConnectionManager:
    """Manages Databricks SQL connections with context manager support.

    This class provides safe resource management for Databricks SQL connections
    using the context manager protocol. Connections are automatically closed
    when exiting the context or when explicitly requested.

    Attributes:
        config: The WorkspaceConfig containing connection parameters.
        _connection: The active Databricks SQL connection (if any).

    Example:
        >>> from databricks_tools.config.models import WorkspaceConfig
        >>> from pydantic import SecretStr
        >>> config = WorkspaceConfig(
        ...     server_hostname="https://example.cloud.databricks.com",
        ...     http_path="/sql/1.0/warehouses/abc123",
        ...     access_token=SecretStr("dapi_token_here")
        ... )
        >>>
        >>> # Context manager usage (recommended)
        >>> with ConnectionManager(config) as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT 1")
        ...     result = cursor.fetchone()

        >>> # Manual usage
        >>> manager = ConnectionManager(config)
        >>> conn = manager.get_connection()
        >>> try:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT 1")
        ... finally:
        ...     manager.close()
    """

    def __init__(self, config: WorkspaceConfig) -> None:
        """Initialize ConnectionManager with workspace configuration.

        Args:
            config: WorkspaceConfig containing connection parameters
                   (server_hostname, http_path, access_token).

        Example:
            >>> from databricks_tools.config.models import WorkspaceConfig
            >>> from pydantic import SecretStr
            >>> config = WorkspaceConfig(
            ...     server_hostname="https://example.cloud.databricks.com",
            ...     http_path="/sql/1.0/warehouses/abc123",
            ...     access_token=SecretStr("dapi_token_here")
            ... )
            >>> manager = ConnectionManager(config)
        """
        self.config = config
        self._connection: Connection | None = None

    def __enter__(self) -> Connection:
        """Enter context manager - create and return database connection.

        Creates a new Databricks SQL connection using the configured
        workspace parameters.

        Returns:
            An active databricks.sql.Connection object.

        Raises:
            databricks.sql.exc.Error: If connection fails due to invalid
                credentials, network issues, or server errors.

        Example:
            >>> with ConnectionManager(config) as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT 1")
        """
        self._connection = sql.connect(
            server_hostname=self.config.server_hostname,
            http_path=self.config.http_path,
            access_token=self.config.access_token.get_secret_value(),
        )
        return self._connection

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager - close database connection.

        Automatically closes the connection when exiting the context,
        regardless of whether an exception occurred.

        Args:
            exc_type: Exception type (if any).
            exc_val: Exception value (if any).
            exc_tb: Exception traceback (if any).

        Example:
            >>> with ConnectionManager(config) as conn:
            ...     # Connection automatically closed on exit
            ...     pass
        """
        if self._connection:
            self._connection.close()
            self._connection = None

    def get_connection(self) -> Connection:
        """Get or create a database connection.

        Returns an existing connection if available, otherwise creates
        a new one. For manual connection management (non-context manager usage).

        Returns:
            An active databricks.sql.Connection object.

        Raises:
            databricks.sql.exc.Error: If connection fails due to invalid
                credentials, network issues, or server errors.

        Example:
            >>> manager = ConnectionManager(config)
            >>> conn = manager.get_connection()
            >>> try:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT 1")
            ... finally:
            ...     manager.close()
        """
        if not self._connection:
            self._connection = sql.connect(
                server_hostname=self.config.server_hostname,
                http_path=self.config.http_path,
                access_token=self.config.access_token.get_secret_value(),
            )
        return self._connection

    def close(self) -> None:
        """Explicitly close the database connection.

        Closes the active connection if one exists. Safe to call multiple times.

        Example:
            >>> manager = ConnectionManager(config)
            >>> conn = manager.get_connection()
            >>> # ... use connection ...
            >>> manager.close()
        """
        if self._connection:
            self._connection.close()
            self._connection = None

    @property
    def is_connected(self) -> bool:
        """Check if a connection is currently active.

        Returns:
            True if a connection exists and is active, False otherwise.

        Example:
            >>> manager = ConnectionManager(config)
            >>> manager.is_connected
            False
            >>> conn = manager.get_connection()
            >>> manager.is_connected
            True
            >>> manager.close()
            >>> manager.is_connected
            False
        """
        return self._connection is not None
