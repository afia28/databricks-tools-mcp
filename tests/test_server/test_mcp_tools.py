"""Integration tests for MCP tools in server.py.

This module tests all 13 MCP tools to ensure they:
1. Properly use ApplicationContainer services
2. Handle errors correctly
3. Return properly formatted responses
4. Work in both ANALYST and DEVELOPER modes
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from databricks_tools.security.role_manager import Role


@pytest.fixture
def mock_container():
    """Create a mock ApplicationContainer with all services."""
    container = MagicMock()

    # Mock workspace_manager
    container.workspace_manager = MagicMock()
    container.workspace_manager.get_available_workspaces.return_value = ["default", "production"]
    container.workspace_manager.get_workspace_config.return_value = MagicMock(
        server_hostname="test.databricks.com",
        http_path="/sql/1.0/warehouses/test",
        access_token=MagicMock(get_secret_value=lambda: "test_token"),
    )

    # Mock token_counter
    container.token_counter = MagicMock()
    container.token_counter.count_tokens.return_value = 100
    container.token_counter.estimate_tokens.return_value = 100

    # Mock query_executor
    container.query_executor = MagicMock()
    container.query_executor.execute_query.return_value = pd.DataFrame(
        {"col1": [1, 2, 3], "col2": ["a", "b", "c"]}
    )

    # Mock catalog_service
    container.catalog_service = MagicMock()
    container.catalog_service.list_catalogs.return_value = ["main", "analytics"]
    container.catalog_service.list_schemas.return_value = {"main": ["default", "staging"]}

    # Mock table_service
    container.table_service = MagicMock()
    container.table_service.get_table_row_count.return_value = {
        "row_count": 1000,
        "estimated_pages": {"100": 10, "500": 2, "1000": 1},
    }
    container.table_service.get_table_details.return_value = {
        "table_name": "test_table",
        "schema": [{"name": "col1", "type": "int"}],
        "data": [{"col1": 1}],
    }
    container.table_service.list_tables.return_value = {"default": ["table1", "table2"]}
    container.table_service.list_columns.return_value = {
        "table1": [{"name": "col1", "type": "int", "description": "Test column"}]
    }

    # Mock function_service
    container.function_service = MagicMock()
    container.function_service.list_user_functions.return_value = {
        "functions": ["func1", "func2"],
        "function_count": 2,
    }
    container.function_service.describe_function.return_value = {
        "function_name": "func1",
        "parameters": [{"name": "param1", "type": "int"}],
        "return_type": "string",
    }
    container.function_service.list_and_describe_all_functions.return_value = {
        "func1": {"parameters": []},
        "func2": {"parameters": []},
    }

    # Mock chunking_service
    container.chunking_service = MagicMock()
    container.chunking_service.get_chunk.return_value = {
        "chunk_number": 1,
        "total_chunks": 5,
        "data": [{"col1": 1}],
    }
    container.chunking_service.get_session_info.return_value = {
        "session_id": "test-session-id",
        "total_chunks": 5,
        "chunks_delivered": 0,
    }

    # Mock response_manager
    container.response_manager = MagicMock()
    container.response_manager.format_response.return_value = '{"status": "success"}'
    container.response_manager.format_error.return_value = '{"error": "test error"}'

    return container


class TestListWorkspaces:
    """Test list_workspaces MCP tool."""

    @pytest.mark.asyncio
    async def test_list_workspaces_returns_formatted_response(self, mock_container):
        """Test that list_workspaces returns properly formatted response."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import list_workspaces

            result = await list_workspaces()

            # Verify container services were called
            mock_container.workspace_manager.get_available_workspaces.assert_called_once()
            mock_container.response_manager.format_response.assert_called_once()
            assert result == '{"status": "success"}'

    @pytest.mark.asyncio
    async def test_list_workspaces_passes_workspaces_to_formatter(self, mock_container):
        """Test that list_workspaces passes workspace list to formatter."""
        mock_container.workspace_manager.get_available_workspaces.return_value = [
            "default",
            "staging",
        ]

        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import list_workspaces

            await list_workspaces()

            # Verify the workspaces were passed to format_response
            call_args = mock_container.response_manager.format_response.call_args
            assert call_args[0][0] == ["default", "staging"]


class TestGetChunk:
    """Test get_chunk MCP tool."""

    @pytest.mark.asyncio
    async def test_get_chunk_success(self, mock_container):
        """Test successful chunk retrieval."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import get_chunk

            result = await get_chunk("session-id", 1)

            # Verify services were called correctly
            mock_container.chunking_service.get_chunk.assert_called_once_with("session-id", 1)
            mock_container.response_manager.format_response.assert_called_once()
            assert result == '{"status": "success"}'

    @pytest.mark.asyncio
    async def test_get_chunk_session_not_found(self, mock_container):
        """Test get_chunk with invalid session ID."""
        mock_container.chunking_service.get_chunk.side_effect = ValueError(
            "Session not found: invalid-id"
        )

        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import get_chunk

            await get_chunk("invalid-id", 1)

            # Verify error formatting was called
            mock_container.response_manager.format_error.assert_called_once()
            assert (
                "Session not found" in mock_container.response_manager.format_error.call_args[0][0]
            )

    @pytest.mark.asyncio
    async def test_get_chunk_invalid_chunk_number(self, mock_container):
        """Test get_chunk with invalid chunk number."""
        mock_container.chunking_service.get_chunk.side_effect = ValueError(
            "Invalid chunk number: 99"
        )

        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import get_chunk

            await get_chunk("session-id", 99)

            # Verify error formatting was called with correct error type
            mock_container.response_manager.format_error.assert_called_once()
            assert (
                "Invalid chunk number"
                in mock_container.response_manager.format_error.call_args[0][0]
            )


class TestGetChunkingSessionInfo:
    """Test get_chunking_session_info MCP tool."""

    @pytest.mark.asyncio
    async def test_get_session_info_success(self, mock_container):
        """Test successful session info retrieval."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import get_chunking_session_info

            result = await get_chunking_session_info("session-id")

            # Verify services were called
            mock_container.chunking_service.get_session_info.assert_called_once_with("session-id")
            mock_container.response_manager.format_response.assert_called_once()
            assert result == '{"status": "success"}'

    @pytest.mark.asyncio
    async def test_get_session_info_not_found(self, mock_container):
        """Test get_chunking_session_info with invalid session."""
        mock_container.chunking_service.get_session_info.side_effect = ValueError(
            "Session not found"
        )

        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import get_chunking_session_info

            await get_chunking_session_info("invalid-id")

            # Verify error formatting
            mock_container.response_manager.format_error.assert_called_once()
            assert (
                "Session not found" in mock_container.response_manager.format_error.call_args[0][0]
            )


class TestGetTableRowCount:
    """Test get_table_row_count MCP tool."""

    @pytest.mark.asyncio
    async def test_get_table_row_count_success(self, mock_container):
        """Test successful table row count retrieval."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import get_table_row_count

            result = await get_table_row_count("catalog", "schema", "table")

            # Verify table service was called
            mock_container.table_service.get_table_row_count.assert_called_once_with(
                "catalog", "schema", "table", None
            )
            mock_container.response_manager.format_response.assert_called_once()
            assert result == '{"status": "success"}'

    @pytest.mark.asyncio
    async def test_get_table_row_count_with_workspace(self, mock_container):
        """Test table row count with specific workspace."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import get_table_row_count

            await get_table_row_count("catalog", "schema", "table", "production")

            # Verify workspace parameter was passed
            mock_container.table_service.get_table_row_count.assert_called_once_with(
                "catalog", "schema", "table", "production"
            )


class TestGetTableDetails:
    """Test get_table_details MCP tool."""

    @pytest.mark.asyncio
    async def test_get_table_details_success(self, mock_container):
        """Test successful table details retrieval."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import get_table_details

            await get_table_details("catalog", "schema", "table")

            # Verify table service was called
            mock_container.table_service.get_table_details.assert_called_once_with(
                "catalog", "schema", "table", 1000, None
            )
            mock_container.response_manager.format_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_table_details_custom_limit(self, mock_container):
        """Test table details with custom limit."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import get_table_details

            await get_table_details("catalog", "schema", "table", limit=500)

            # Verify limit was passed correctly
            mock_container.table_service.get_table_details.assert_called_once_with(
                "catalog", "schema", "table", 500, None
            )

    @pytest.mark.asyncio
    async def test_get_table_details_with_workspace(self, mock_container):
        """Test table details with workspace parameter."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import get_table_details

            await get_table_details("catalog", "schema", "table", workspace="staging")

            # Verify workspace was passed
            call_args = mock_container.table_service.get_table_details.call_args[0]
            assert call_args[4] == "staging"


class TestRunQuery:
    """Test run_query MCP tool."""

    @pytest.mark.asyncio
    async def test_run_query_success(self, mock_container):
        """Test successful query execution."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import run_query

            await run_query("SELECT 1")

            # Verify query executor was called
            mock_container.query_executor.execute_query.assert_called_once()
            mock_container.response_manager.format_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_query_with_workspace(self, mock_container):
        """Test query execution with workspace parameter."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import run_query

            await run_query("SELECT 1", workspace="production")

            # Verify workspace was passed to query executor (as positional arg)
            call_args = mock_container.query_executor.execute_query.call_args
            # execute_query signature: execute_query(query, workspace, parse_dates)
            assert call_args[0][1] == "production"  # workspace is 2nd positional arg


class TestListCatalogs:
    """Test list_catalogs MCP tool."""

    @pytest.mark.asyncio
    async def test_list_catalogs_success(self, mock_container):
        """Test successful catalog listing."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import list_catalogs

            await list_catalogs()

            # Verify catalog service was called
            mock_container.catalog_service.list_catalogs.assert_called_once_with(None)
            mock_container.response_manager.format_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_catalogs_with_workspace(self, mock_container):
        """Test catalog listing with workspace parameter."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import list_catalogs

            await list_catalogs(workspace="production")

            # Verify workspace was passed
            mock_container.catalog_service.list_catalogs.assert_called_once_with("production")

    @pytest.mark.asyncio
    async def test_list_catalogs_error_handling(self, mock_container):
        """Test list_catalogs error handling."""
        mock_container.catalog_service.list_catalogs.side_effect = Exception("Connection failed")

        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import list_catalogs

            await list_catalogs()

            # Verify error formatting
            mock_container.response_manager.format_error.assert_called_once()
            assert "Error" in mock_container.response_manager.format_error.call_args[0][0]


class TestListSchemas:
    """Test list_schemas MCP tool."""

    @pytest.mark.asyncio
    async def test_list_schemas_all_catalogs(self, mock_container):
        """Test listing schemas for all catalogs."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import list_schemas

            await list_schemas()

            # Verify catalog service methods were called
            mock_container.catalog_service.list_catalogs.assert_called_once()
            mock_container.catalog_service.list_schemas.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_schemas_single_catalog(self, mock_container):
        """Test listing schemas for single catalog (string)."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import list_schemas

            await list_schemas(catalogs="main")

            # Verify list_schemas was called with converted list
            mock_container.catalog_service.list_schemas.assert_called_once_with(["main"], None)

    @pytest.mark.asyncio
    async def test_list_schemas_multiple_catalogs(self, mock_container):
        """Test listing schemas for multiple catalogs (list)."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import list_schemas

            await list_schemas(catalogs=["main", "analytics"])

            # Verify list was passed directly
            mock_container.catalog_service.list_schemas.assert_called_once_with(
                ["main", "analytics"], None
            )

    @pytest.mark.asyncio
    async def test_list_schemas_error_handling(self, mock_container):
        """Test list_schemas error handling."""
        mock_container.catalog_service.list_schemas.side_effect = Exception("Query failed")

        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import list_schemas

            await list_schemas(catalogs="main")

            # Verify error formatting
            mock_container.response_manager.format_error.assert_called_once()


class TestListTables:
    """Test list_tables MCP tool."""

    @pytest.mark.asyncio
    async def test_list_tables_success(self, mock_container):
        """Test successful table listing."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import list_tables

            await list_tables("catalog", ["schema1", "schema2"])

            # Verify table service was called
            mock_container.table_service.list_tables.assert_called_once_with(
                "catalog", ["schema1", "schema2"], None
            )
            mock_container.response_manager.format_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tables_response_too_large(self, mock_container):
        """Test list_tables when response exceeds token limit."""
        # Make token counter return large count (above hardcoded 9000 limit)
        mock_container.token_counter.count_tokens.return_value = 10000

        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import list_tables

            await list_tables("catalog", ["schema1", "schema2"])

            # Verify error formatting was called
            mock_container.response_manager.format_error.assert_called_once()
            assert (
                "Response too large" in mock_container.response_manager.format_error.call_args[0][0]
            )


class TestListColumns:
    """Test list_columns MCP tool."""

    @pytest.mark.asyncio
    async def test_list_columns_success(self, mock_container):
        """Test successful column listing."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import list_columns

            await list_columns("catalog", "schema", ["table1", "table2"])

            # Verify table service was called
            mock_container.table_service.list_columns.assert_called_once_with(
                "catalog", "schema", ["table1", "table2"], None
            )

    @pytest.mark.asyncio
    async def test_list_columns_response_too_large(self, mock_container):
        """Test list_columns when response exceeds token limit."""
        mock_container.token_counter.count_tokens.return_value = 10000

        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import list_columns

            await list_columns("catalog", "schema", ["table1"])

            # Verify error formatting
            mock_container.response_manager.format_error.assert_called_once()


class TestListUserFunctions:
    """Test list_user_functions MCP tool."""

    @pytest.mark.asyncio
    async def test_list_user_functions_with_parameters(self, mock_container):
        """Test listing user functions with catalog and schema."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import list_user_functions

            await list_user_functions("catalog", "schema")

            # Verify function service was called
            mock_container.function_service.list_user_functions.assert_called_once_with(
                "catalog", "schema", None
            )

    @pytest.mark.asyncio
    async def test_list_user_functions_no_catalog(self, mock_container):
        """Test list_user_functions without catalog parameter."""
        with patch("databricks_tools.server._container", mock_container):
            with patch.dict("os.environ", {}, clear=True):
                from databricks_tools.server import list_user_functions

                await list_user_functions()

                # Verify error was returned
                mock_container.response_manager.format_error.assert_called_once()
                assert (
                    "No catalog specified"
                    in mock_container.response_manager.format_error.call_args[0][0]
                )

    @pytest.mark.asyncio
    async def test_list_user_functions_from_environment(self, mock_container):
        """Test list_user_functions using environment variables."""
        with patch("databricks_tools.server._container", mock_container):
            with patch.dict(
                "os.environ",
                {"DATABRICKS_DEFAULT_CATALOG": "main", "DATABRICKS_DEFAULT_SCHEMA": "default"},
            ):
                from databricks_tools.server import list_user_functions

                await list_user_functions()

                # Verify function service was called with env values
                mock_container.function_service.list_user_functions.assert_called_once_with(
                    "main", "default", None
                )

    @pytest.mark.asyncio
    async def test_list_user_functions_response_too_large(self, mock_container):
        """Test list_user_functions when response exceeds limit."""
        mock_container.token_counter.count_tokens.return_value = 10000

        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import list_user_functions

            await list_user_functions("catalog", "schema")

            # Verify error formatting
            mock_container.response_manager.format_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_user_functions_no_schema(self, mock_container):
        """Test list_user_functions without schema parameter and no env var."""
        with patch("databricks_tools.server._container", mock_container):
            with patch.dict("os.environ", {"DATABRICKS_DEFAULT_CATALOG": "main"}, clear=True):
                from databricks_tools.server import list_user_functions

                await list_user_functions(catalog="main")

                # Verify error was returned for missing schema
                mock_container.response_manager.format_error.assert_called_once()
                assert (
                    "No schema specified"
                    in mock_container.response_manager.format_error.call_args[0][0]
                )


class TestDescribeFunction:
    """Test describe_function MCP tool."""

    @pytest.mark.asyncio
    async def test_describe_function_success(self, mock_container):
        """Test successful function description."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import describe_function

            await describe_function("func1", "catalog", "schema")

            # Verify function service was called
            mock_container.function_service.describe_function.assert_called_once_with(
                "func1", "catalog", "schema", None
            )

    @pytest.mark.asyncio
    async def test_describe_function_no_catalog(self, mock_container):
        """Test describe_function without catalog parameter."""
        with patch("databricks_tools.server._container", mock_container):
            with patch.dict("os.environ", {}, clear=True):
                from databricks_tools.server import describe_function

                await describe_function("func1")

                # Verify error formatting
                mock_container.response_manager.format_error.assert_called_once()
                assert (
                    "No catalog specified"
                    in mock_container.response_manager.format_error.call_args[0][0]
                )

    @pytest.mark.asyncio
    async def test_describe_function_error_handling(self, mock_container):
        """Test describe_function error handling."""
        mock_container.function_service.describe_function.side_effect = Exception("Not found")

        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import describe_function

            await describe_function("func1", "catalog", "schema")

            # Verify error formatting
            assert mock_container.response_manager.format_error.call_count == 1

    @pytest.mark.asyncio
    async def test_describe_function_no_schema(self, mock_container):
        """Test describe_function without schema parameter and no env var."""
        with patch("databricks_tools.server._container", mock_container):
            with patch.dict("os.environ", {"DATABRICKS_DEFAULT_CATALOG": "main"}, clear=True):
                from databricks_tools.server import describe_function

                await describe_function("func1", catalog="main")

                # Verify error was returned for missing schema
                mock_container.response_manager.format_error.assert_called_once()
                assert (
                    "No schema specified"
                    in mock_container.response_manager.format_error.call_args[0][0]
                )


class TestListAndDescribeAllFunctions:
    """Test list_and_describe_all_functions MCP tool."""

    @pytest.mark.asyncio
    async def test_list_and_describe_all_success(self, mock_container):
        """Test successful list and describe all functions."""
        with patch("databricks_tools.server._container", mock_container):
            from databricks_tools.server import list_and_describe_all_functions

            await list_and_describe_all_functions("catalog", "schema")

            # Verify function service was called
            mock_container.function_service.list_and_describe_all_functions.assert_called_once_with(
                "catalog", "schema", None
            )

    @pytest.mark.asyncio
    async def test_list_and_describe_all_no_catalog(self, mock_container):
        """Test list_and_describe_all_functions without catalog."""
        with patch("databricks_tools.server._container", mock_container):
            with patch.dict("os.environ", {}, clear=True):
                from databricks_tools.server import list_and_describe_all_functions

                await list_and_describe_all_functions()

                # Verify error formatting
                mock_container.response_manager.format_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_and_describe_all_from_environment(self, mock_container):
        """Test list_and_describe_all_functions using environment variables."""
        with patch("databricks_tools.server._container", mock_container):
            with patch.dict(
                "os.environ",
                {"DATABRICKS_DEFAULT_CATALOG": "main", "DATABRICKS_DEFAULT_SCHEMA": "default"},
            ):
                from databricks_tools.server import list_and_describe_all_functions

                await list_and_describe_all_functions()

                # Verify env values were used
                mock_container.function_service.list_and_describe_all_functions.assert_called_once_with(
                    "main", "default", None
                )

    @pytest.mark.asyncio
    async def test_list_and_describe_all_no_schema(self, mock_container):
        """Test list_and_describe_all_functions without schema parameter and no env var."""
        with patch("databricks_tools.server._container", mock_container):
            with patch.dict("os.environ", {"DATABRICKS_DEFAULT_CATALOG": "main"}, clear=True):
                from databricks_tools.server import list_and_describe_all_functions

                await list_and_describe_all_functions(catalog="main")

                # Verify error was returned for missing schema
                mock_container.response_manager.format_error.assert_called_once()
                assert (
                    "No schema specified"
                    in mock_container.response_manager.format_error.call_args[0][0]
                )


class TestMainFunction:
    """Test main() function and container recreation."""

    def test_main_analyst_mode_default(self, mock_container):
        """Test main() function in analyst mode (default)."""
        with patch("databricks_tools.server._container", mock_container):
            with patch("databricks_tools.server.mcp") as mock_mcp:
                with patch("sys.argv", ["server.py"]):
                    from databricks_tools.server import main

                    main()

                    # Verify MCP server was run
                    mock_mcp.run.assert_called_once_with(transport="stdio")

    def test_main_developer_mode(self, mock_container):
        """Test main() function with --developer flag."""
        with patch("databricks_tools.server.ApplicationContainer") as mock_app_container:
            with patch("databricks_tools.server.mcp"):
                with patch("sys.argv", ["server.py", "--developer"]):
                    from databricks_tools.server import main

                    main()

                    # Verify container was recreated with DEVELOPER role
                    mock_app_container.assert_called_once()
                    call_args = mock_app_container.call_args
                    assert call_args[1]["role"] == Role.DEVELOPER
