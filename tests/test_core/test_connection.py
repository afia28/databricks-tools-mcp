"""Tests for ConnectionManager class.

This module contains comprehensive tests for the ConnectionManager class,
covering context manager protocol, connection lifecycle, and error handling.

Test coverage goal: 95%+ for src/databricks_tools/core/connection.py

Test cases included:
1. test_connection_manager_context_manager - Basic context manager usage
2. test_connection_manager_auto_close - Connection auto-closed on exit
3. test_connection_manager_get_connection - Get/create connection
4. test_connection_manager_explicit_close - Explicit close() method
5. test_connection_manager_invalid_credentials - Invalid credentials handling
6. test_connection_manager_connection_error - Connection error handling
7. test_connection_manager_reuse_connection - Connection reuse
8. test_connection_manager_multiple_contexts - Multiple context usage
9. test_connection_manager_exception_handling - Exception cleanup
10. test_connection_manager_from_workspace_config - WorkspaceConfig integration
11. test_connection_manager_connection_properties - Connection parameters
12. test_connection_manager_is_connected - is_connected property
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from databricks.sql import Error as DatabricksError
from pydantic import SecretStr

from databricks_tools.config.models import WorkspaceConfig
from databricks_tools.core.connection import ConnectionManager

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_config() -> WorkspaceConfig:
    """Create a mock WorkspaceConfig for testing.

    Returns:
        A WorkspaceConfig instance with valid test credentials.
    """
    return WorkspaceConfig(
        server_hostname="https://test.cloud.databricks.com",
        http_path="/sql/1.0/warehouses/test123",
        access_token=SecretStr("dapi_test_token_12345678901234567890"),
        workspace_name="test",
    )


@pytest.fixture
def mock_connection():
    """Create a mock databricks.sql.Connection.

    Returns:
        A MagicMock configured to behave like a Databricks SQL connection.
    """
    mock_conn = MagicMock()
    mock_conn.close = Mock()
    mock_conn.cursor = Mock(return_value=MagicMock())
    return mock_conn


# =============================================================================
# Context Manager Protocol Tests
# =============================================================================


class TestConnectionManagerContextProtocol:
    """Tests for context manager protocol (__enter__/__exit__)."""

    @patch("databricks_tools.core.connection.sql.connect")
    def test_connection_manager_context_manager(
        self,
        mock_connect: Mock,
        mock_config: WorkspaceConfig,
        mock_connection: MagicMock,
    ):
        """Test basic context manager usage (with statement).

        The ConnectionManager should:
        1. Create a connection on __enter__
        2. Return the connection object
        3. Be usable within a with statement

        This is test case 1 from the requirements.
        """
        mock_connect.return_value = mock_connection

        manager = ConnectionManager(mock_config)

        # Use context manager
        with manager as conn:
            # Connection should be returned and available
            assert conn is mock_connection
            assert manager.is_connected is True

        # Verify sql.connect was called
        mock_connect.assert_called_once()

    @patch("databricks_tools.core.connection.sql.connect")
    def test_connection_manager_auto_close(
        self,
        mock_connect: Mock,
        mock_config: WorkspaceConfig,
        mock_connection: MagicMock,
    ):
        """Test connection is automatically closed on context exit.

        The ConnectionManager should:
        1. Close the connection when exiting the context
        2. Set _connection to None after closing
        3. Call connection.close() exactly once

        This is test case 2 from the requirements.
        """
        mock_connect.return_value = mock_connection

        manager = ConnectionManager(mock_config)

        # Use context manager
        with manager:
            assert manager.is_connected is True
            assert manager._connection is mock_connection

        # After exiting context
        mock_connection.close.assert_called_once()
        assert manager._connection is None
        assert manager.is_connected is False

    @patch("databricks_tools.core.connection.sql.connect")
    def test_connection_manager_multiple_contexts(
        self, mock_connect: Mock, mock_config: WorkspaceConfig
    ):
        """Test using ConnectionManager in multiple sequential contexts.

        The ConnectionManager should:
        1. Allow multiple sequential with statements
        2. Close connection after first context exits
        3. Create new connection for second context

        This is test case 8 from the requirements.
        """
        # Create separate mock connections for each context
        mock_conn1 = MagicMock()
        mock_conn2 = MagicMock()
        mock_connect.side_effect = [mock_conn1, mock_conn2]

        manager = ConnectionManager(mock_config)

        # First context
        with manager as conn1:
            assert conn1 is mock_conn1
            assert manager.is_connected is True

        # Connection should be closed after first context
        mock_conn1.close.assert_called_once()
        assert manager.is_connected is False

        # Second context should create new connection
        with manager as conn2:
            assert conn2 is mock_conn2
            assert manager.is_connected is True

        # Second connection should also be closed
        mock_conn2.close.assert_called_once()
        assert manager.is_connected is False

        # Verify sql.connect was called twice
        assert mock_connect.call_count == 2

    @patch("databricks_tools.core.connection.sql.connect")
    def test_connection_manager_exception_handling(
        self,
        mock_connect: Mock,
        mock_config: WorkspaceConfig,
        mock_connection: MagicMock,
    ):
        """Test connection is closed even if exception occurs in context.

        The ConnectionManager should:
        1. Close connection even if exception is raised
        2. Propagate the exception
        3. Ensure cleanup happens regardless of exception type

        This is test case 9 from the requirements.
        """
        mock_connect.return_value = mock_connection

        manager = ConnectionManager(mock_config)

        # Test with ValueError
        with pytest.raises(ValueError, match="Test error"):
            with manager:
                assert manager.is_connected is True
                raise ValueError("Test error")

        # Connection should still be closed
        mock_connection.close.assert_called_once()
        assert manager.is_connected is False

        # Reset mock for second test
        mock_connection.close.reset_mock()
        mock_connect.reset_mock()
        mock_connect.return_value = mock_connection

        # Test with different exception type (RuntimeError)
        with pytest.raises(RuntimeError, match="Another error"):
            with manager:
                assert manager.is_connected is True
                raise RuntimeError("Another error")

        # Connection should still be closed
        mock_connection.close.assert_called_once()
        assert manager.is_connected is False


# =============================================================================
# Connection Lifecycle Tests
# =============================================================================


class TestConnectionManagerLifecycle:
    """Tests for connection lifecycle (get_connection, close, is_connected)."""

    @patch("databricks_tools.core.connection.sql.connect")
    def test_connection_manager_get_connection(
        self,
        mock_connect: Mock,
        mock_config: WorkspaceConfig,
        mock_connection: MagicMock,
    ):
        """Test get_connection() creates and reuses connections.

        The get_connection() method should:
        1. Create a new connection if none exists
        2. Return the same connection on subsequent calls
        3. Not create multiple connections unnecessarily

        This is test case 3 from the requirements.
        """
        mock_connect.return_value = mock_connection

        manager = ConnectionManager(mock_config)

        # Initially not connected
        assert manager.is_connected is False

        # First call creates connection
        conn1 = manager.get_connection()
        assert conn1 is mock_connection
        assert manager.is_connected is True
        mock_connect.assert_called_once()

        # Second call reuses connection
        conn2 = manager.get_connection()
        assert conn2 is mock_connection
        assert conn2 is conn1  # Same object
        assert manager.is_connected is True
        # sql.connect should still only be called once
        mock_connect.assert_called_once()

    @patch("databricks_tools.core.connection.sql.connect")
    def test_connection_manager_explicit_close(
        self,
        mock_connect: Mock,
        mock_config: WorkspaceConfig,
        mock_connection: MagicMock,
    ):
        """Test explicit close() method.

        The close() method should:
        1. Close the connection if one exists
        2. Set _connection to None
        3. Be safe to call multiple times (idempotent)

        This is test case 4 from the requirements.
        """
        mock_connect.return_value = mock_connection

        manager = ConnectionManager(mock_config)

        # Create connection
        manager.get_connection()
        assert manager.is_connected is True

        # Close it
        manager.close()
        mock_connection.close.assert_called_once()
        assert manager._connection is None
        assert manager.is_connected is False

        # Calling close again should be safe (no error)
        manager.close()
        # close() should still only be called once (no second call since _connection is None)
        mock_connection.close.assert_called_once()
        assert manager.is_connected is False

    @patch("databricks_tools.core.connection.sql.connect")
    def test_connection_manager_reuse_connection(
        self,
        mock_connect: Mock,
        mock_config: WorkspaceConfig,
        mock_connection: MagicMock,
    ):
        """Test get_connection() doesn't create new connection if one exists.

        This test verifies:
        1. sql.connect is called only once when get_connection is called multiple times
        2. The same connection object is returned each time
        3. Connection reuse works correctly

        This is test case 7 from the requirements.
        """
        mock_connect.return_value = mock_connection

        manager = ConnectionManager(mock_config)

        # Call get_connection multiple times
        conn1 = manager.get_connection()
        conn2 = manager.get_connection()
        conn3 = manager.get_connection()

        # All should be the same connection
        assert conn1 is conn2
        assert conn2 is conn3
        assert conn1 is mock_connection

        # sql.connect should only be called once
        mock_connect.assert_called_once()

    @patch("databricks_tools.core.connection.sql.connect")
    def test_connection_manager_is_connected(
        self,
        mock_connect: Mock,
        mock_config: WorkspaceConfig,
        mock_connection: MagicMock,
    ):
        """Test is_connected property lifecycle.

        The is_connected property should:
        1. Return False initially (no connection)
        2. Return True after get_connection()
        3. Return False after close()

        This is test case 12 from the requirements.
        """
        mock_connect.return_value = mock_connection

        manager = ConnectionManager(mock_config)

        # Initially not connected
        assert manager.is_connected is False

        # After getting connection
        manager.get_connection()
        assert manager.is_connected is True

        # After closing
        manager.close()
        assert manager.is_connected is False


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestConnectionManagerErrorHandling:
    """Tests for error handling and edge cases."""

    @patch("databricks_tools.core.connection.sql.connect")
    def test_connection_manager_invalid_credentials(
        self, mock_connect: Mock, mock_config: WorkspaceConfig
    ):
        """Test behavior with invalid credentials.

        When sql.connect raises an exception:
        1. The exception should propagate to the caller
        2. The ConnectionManager should not suppress the error
        3. databricks.sql exceptions should be raised

        This is test case 5 from the requirements.
        """
        # Mock sql.connect to raise authentication error
        mock_connect.side_effect = DatabricksError("Invalid access token")

        manager = ConnectionManager(mock_config)

        # Attempting to connect should raise the error
        with pytest.raises(DatabricksError, match="Invalid access token"):
            with manager:
                pass

        # Verify connection was not established
        assert manager.is_connected is False

    @patch("databricks_tools.core.connection.sql.connect")
    def test_connection_manager_connection_error(
        self, mock_connect: Mock, mock_config: WorkspaceConfig
    ):
        """Test network/connection errors are propagated.

        When sql.connect raises a connection error:
        1. The error should propagate
        2. Different error types should all be propagated
        3. No connection should be established

        This is test case 6 from the requirements.
        """
        # Test with generic connection error
        mock_connect.side_effect = ConnectionError("Network unreachable")

        manager = ConnectionManager(mock_config)

        with pytest.raises(ConnectionError, match="Network unreachable"):
            manager.get_connection()

        assert manager.is_connected is False

        # Test with DatabricksError for server error
        mock_connect.reset_mock()
        mock_connect.side_effect = DatabricksError("Server error: 503")

        manager2 = ConnectionManager(mock_config)

        with pytest.raises(DatabricksError, match="Server error: 503"):
            manager2.get_connection()

        assert manager2.is_connected is False


# =============================================================================
# Integration Tests
# =============================================================================


class TestConnectionManagerIntegration:
    """Tests for integration with WorkspaceConfig."""

    @patch("databricks_tools.core.connection.sql.connect")
    def test_connection_manager_from_workspace_config(
        self, mock_connect: Mock, mock_connection: MagicMock
    ):
        """Test ConnectionManager accepts WorkspaceConfig correctly.

        The ConnectionManager should:
        1. Accept a WorkspaceConfig instance
        2. Store the config as an attribute
        3. Be able to access config properties

        This is test case 10 from the requirements.
        """
        mock_connect.return_value = mock_connection

        # Create config with specific values
        config = WorkspaceConfig(
            server_hostname="https://prod.cloud.databricks.com",
            http_path="/sql/1.0/warehouses/prod456",
            access_token=SecretStr("dapi_prod_token_12345678901234567890"),
            workspace_name="production",
        )

        manager = ConnectionManager(config)

        # Config should be stored
        assert manager.config is config
        assert manager.config.server_hostname == "https://prod.cloud.databricks.com"
        assert manager.config.http_path == "/sql/1.0/warehouses/prod456"
        assert manager.config.workspace_name == "production"

        # Should be able to use the connection
        with manager as conn:
            assert conn is mock_connection

    @patch("databricks_tools.core.connection.sql.connect")
    def test_connection_manager_connection_properties(
        self,
        mock_connect: Mock,
        mock_config: WorkspaceConfig,
        mock_connection: MagicMock,
    ):
        """Test connection is created with correct parameters.

        The sql.connect call should:
        1. Use server_hostname from config
        2. Use http_path from config
        3. Use access_token.get_secret_value() from config
        4. Pass all parameters correctly

        This is test case 11 from the requirements.
        """
        mock_connect.return_value = mock_connection

        manager = ConnectionManager(mock_config)

        # Create connection
        manager.get_connection()

        # Verify sql.connect was called with correct arguments
        mock_connect.assert_called_once_with(
            server_hostname=mock_config.server_hostname,
            http_path=mock_config.http_path,
            access_token=mock_config.access_token.get_secret_value(),
        )

        # Verify the token was unwrapped correctly
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs["access_token"] == "dapi_test_token_12345678901234567890"
        assert isinstance(call_kwargs["access_token"], str)  # Not SecretStr

    @patch("databricks_tools.core.connection.sql.connect")
    def test_connection_manager_context_uses_correct_parameters(
        self,
        mock_connect: Mock,
        mock_config: WorkspaceConfig,
        mock_connection: MagicMock,
    ):
        """Test context manager also passes correct parameters.

        Both __enter__ and get_connection should use the same parameters
        when calling sql.connect.
        """
        mock_connect.return_value = mock_connection

        manager = ConnectionManager(mock_config)

        # Use context manager
        with manager:
            pass

        # Verify parameters
        mock_connect.assert_called_once_with(
            server_hostname=mock_config.server_hostname,
            http_path=mock_config.http_path,
            access_token=mock_config.access_token.get_secret_value(),
        )


# =============================================================================
# Edge Cases and Additional Tests
# =============================================================================


class TestConnectionManagerEdgeCases:
    """Tests for edge cases and additional scenarios."""

    @patch("databricks_tools.core.connection.sql.connect")
    def test_connection_manager_close_without_connection(
        self, mock_connect: Mock, mock_config: WorkspaceConfig
    ):
        """Test calling close() when no connection exists.

        Calling close() without a connection should be safe and not error.
        """
        manager = ConnectionManager(mock_config)

        # Close without ever creating a connection
        assert manager.is_connected is False
        manager.close()  # Should not raise
        assert manager.is_connected is False

        # Verify sql.connect was never called
        mock_connect.assert_not_called()

    @patch("databricks_tools.core.connection.sql.connect")
    def test_connection_manager_exit_without_connection(
        self, mock_connect: Mock, mock_config: WorkspaceConfig
    ):
        """Test __exit__ is safe when no connection was created.

        If __enter__ wasn't called, __exit__ should handle None gracefully.
        """
        manager = ConnectionManager(mock_config)

        # Call __exit__ directly without __enter__
        manager.__exit__(None, None, None)

        # Should not raise and should be safe
        assert manager.is_connected is False
        mock_connect.assert_not_called()

    @patch("databricks_tools.core.connection.sql.connect")
    def test_connection_manager_new_connection_after_close(
        self, mock_connect: Mock, mock_config: WorkspaceConfig
    ):
        """Test creating new connection after closing previous one.

        After close(), get_connection() should create a fresh connection.
        """
        mock_conn1 = MagicMock()
        mock_conn2 = MagicMock()
        mock_connect.side_effect = [mock_conn1, mock_conn2]

        manager = ConnectionManager(mock_config)

        # Create first connection
        conn1 = manager.get_connection()
        assert conn1 is mock_conn1
        assert manager.is_connected is True

        # Close it
        manager.close()
        assert manager.is_connected is False

        # Create second connection
        conn2 = manager.get_connection()
        assert conn2 is mock_conn2
        assert conn2 is not conn1  # Different connection
        assert manager.is_connected is True

        # Verify sql.connect was called twice
        assert mock_connect.call_count == 2
