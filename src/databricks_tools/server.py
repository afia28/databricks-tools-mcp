import argparse
import json
import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from databricks_tools.core.container import ApplicationContainer
from databricks_tools.security.role_manager import Role

# Initialize FastMCP server
load_dotenv()
mcp = FastMCP("databricks_sql")

# AIDEV-NOTE: ApplicationContainer provides dependency injection for all services
# Default role is ANALYST (default workspace only). Use --developer flag for all workspaces.
_container = ApplicationContainer(role=Role.ANALYST, max_tokens=9000)


@mcp.tool()
async def list_workspaces() -> str:
    """
    Lists all configured Databricks workspaces.

    Role-based behavior:
    - ANALYST mode: Returns only ['default'] if configured.
    - DEVELOPER mode: Returns all configured workspaces.

    Returns:
    -------
    str
        A JSON-formatted list of available workspace names.
    """
    workspaces = _container.workspace_manager.get_available_workspaces()
    return _container.response_manager.format_response(workspaces)


@mcp.tool()
async def get_chunk(session_id: str, chunk_number: int) -> str:
    """
    Retrieves a specific chunk from a chunked response session.

    Parameters:
    ----------
    session_id : str
        The session ID from the chunked response.
    chunk_number : int
        The chunk number to retrieve (1-indexed).

    Returns:
    -------
    str
        JSON-formatted chunk data with metadata.
    """
    try:
        # Use ChunkingService to get chunk
        chunk = _container.chunking_service.get_chunk(session_id, chunk_number)
        return _container.response_manager.format_response(chunk, auto_chunk=False)
    except ValueError as e:
        # Handle session not found or invalid chunk number
        error_message = str(e)
        if "Session not found" in error_message:
            return _container.response_manager.format_error(
                "Session not found",
                "The specified session ID does not exist or has expired.",
                session_id=session_id,
            )
        else:
            # Invalid chunk number
            return _container.response_manager.format_error(
                "Invalid chunk number",
                error_message,
                session_id=session_id,
                chunk_number=chunk_number,
            )


@mcp.tool()
async def get_chunking_session_info(session_id: str) -> str:
    """
    Get information about a chunking session.

    Parameters:
    ----------
    session_id : str
        The session ID to get information about.

    Returns:
    -------
    str
        JSON-formatted session information.
    """
    try:
        # Use ChunkingService to get session info
        session_info = _container.chunking_service.get_session_info(session_id)
        return _container.response_manager.format_response(session_info, auto_chunk=False)
    except ValueError:
        # Handle session not found
        return _container.response_manager.format_error(
            "Session not found",
            "The specified session ID does not exist or has expired.",
            session_id=session_id,
        )


@mcp.tool()
async def get_table_row_count(
    catalog: str, schema: str, table_name: str, workspace: str | None = None
) -> str:
    """
    Gets the total row count for a table without fetching all data.

    Parameters:
    ----------
    catalog : str
        The catalog name where the table is stored.
    schema : str
        The schema name where the table is stored.
    table_name : str
        The name of the table to count rows from.
    workspace : str, optional
        The workspace name to connect to.
        - In ANALYST mode: This parameter is ignored, always uses default workspace.
        - In DEVELOPER mode: If None or not found, falls back to default workspace.

    Returns:
    -------
    str
        A JSON-formatted string containing the row count and estimated pages for different page sizes.
    """
    # Use TableService to get row count
    result = _container.table_service.get_table_row_count(catalog, schema, table_name, workspace)

    return _container.response_manager.format_response(result)


@mcp.tool()
async def get_table_details(
    catalog: str,
    schema: str,
    table_name: str,
    limit: int | None = 1000,
    workspace: str | None = None,
) -> str:
    """
    Fetches the schema and data from a specified table in Databricks with automatic chunking for large responses.

    Parameters:
    ----------
    catalog : str
        The catalog name where the table is stored.
    schema : str
        The schema name where the table is stored.
    table_name : str
        The name of the table to retrieve details from.
    limit : int, optional
        Total number of rows to fetch from the table. If None, fetches all rows (use with caution).
    workspace : str, optional
        The workspace name to connect to.
        - In ANALYST mode: This parameter is ignored, always uses default workspace.
        - In DEVELOPER mode: If None or not found, falls back to default workspace.

    Returns:
    -------
    str
        A JSON-formatted string containing the table name, schema, and data.
        If response exceeds token limits, returns chunked response information.
    """
    # Use TableService to get table details
    result = _container.table_service.get_table_details(
        catalog, schema, table_name, limit, workspace
    )

    # AIDEV-NOTE: ResponseManager automatically handles token checking and chunking
    return _container.response_manager.format_response(result)


@mcp.tool()
async def run_query(query: str, workspace: str | None = None) -> str:
    """
    Executes an arbitrary SQL query and returns the result formatted as JSON with automatic chunking for large responses.

    Parameters:
    ----------
    query : str
        The SQL query string to execute.
    workspace : str, optional
        The workspace name to connect to.
        - In ANALYST mode: This parameter is ignored, always uses default workspace.
        - In DEVELOPER mode: If None or not found, falls back to default workspace.

    Returns:
    -------
    str
        A JSON-formatted string containing the result data.
        If response exceeds token limits, returns chunked response information.
    """
    # Execute query directly using container's query executor
    df = _container.query_executor.execute_query(query, workspace, None)

    # Convert DataFrame to result format
    df_json = json.loads(df.to_json(orient="table", index=False))
    result = {"data": df_json["data"], "schema": df_json["schema"], "query": query}

    # AIDEV-NOTE: ResponseManager automatically handles token checking and chunking
    return _container.response_manager.format_response(result)


# Tools for listing catalogs, schemas, and tables
@mcp.tool()
async def list_catalogs(workspace: str | None = None) -> str:
    """
    Lists all catalogs available in the specified Databricks workspace.

    Role-based behavior:
    - ANALYST mode: Only accesses default workspace.
    - DEVELOPER mode: Can access any configured workspace.

    Parameters:
    ----------
    workspace : str, optional
        The workspace name to connect to.
        - In ANALYST mode: This parameter is ignored, always uses default workspace.
        - In DEVELOPER mode: If None or not found, falls back to default workspace.

    Returns:
    -------
    str
        A JSON-formatted list of catalog names.

    Example:
        >>> result = await list_catalogs()
        >>> print(result)
        ["main", "analytics", "prod"]
    """
    try:
        # Use CatalogService to get catalogs
        catalogs = _container.catalog_service.list_catalogs(workspace)

        # Return as JSON
        return _container.response_manager.format_response(catalogs)

    except Exception as e:
        error_msg = f"Error listing catalogs: {str(e)}"
        return _container.response_manager.format_error("Error", error_msg)


@mcp.tool()
async def list_schemas(
    catalogs: str | list[str] | None = None, workspace: str | None = None
) -> str:
    """
    Lists schemas for specified catalogs.

    Parameters:
    ----------
    catalogs : str | list[str] | None
        Catalog name(s) to query. Can be:
        - Single catalog name (str)
        - List of catalog names
        - None (queries all catalogs)
    workspace : str, optional
        The workspace name to connect to.
        - In ANALYST mode: This parameter is ignored, always uses default workspace.
        - In DEVELOPER mode: If None or not found, falls back to default workspace.

    Returns:
    -------
    str
        A JSON-formatted dictionary with catalog names as keys and lists of schema names as values.

    Example:
        >>> result = await list_schemas(catalogs=["main"])
        >>> print(result)
        {"main": ["default", "staging"]}
    """
    try:
        # Handle catalogs parameter
        if catalogs is None:
            # Get all catalogs first
            catalog_list = _container.catalog_service.list_catalogs(workspace)
        elif isinstance(catalogs, str):
            catalog_list = [catalogs]
        else:
            catalog_list = catalogs

        # Use CatalogService to get schemas
        result = _container.catalog_service.list_schemas(catalog_list, workspace)

        # Return as JSON
        return _container.response_manager.format_response(result)

    except Exception as e:
        error_msg = f"Error listing schemas: {str(e)}"
        return _container.response_manager.format_error("Error", error_msg)


@mcp.tool()
async def list_tables(catalog: str, schemas: list[str], workspace: str | None = None) -> str:
    """
    Lists tables for a given catalog and one or more schemas.

    Parameters:
    ----------
    catalog : str
        The catalog name.
    schemas : list
        A list of schema names under the given catalog.
    workspace : str, optional
        The workspace name to connect to.
        - In ANALYST mode: This parameter is ignored, always uses default workspace.
        - In DEVELOPER mode: If None or not found, falls back to default workspace.

    Returns:
    -------
    str
        A JSON-formatted dictionary with schema names as keys and lists of table names as values.
    """
    # Use TableService to list tables
    result = _container.table_service.list_tables(catalog, schemas, workspace)

    # Check token count before formatting
    temp_response = json.dumps(result, separators=(",", ":"))
    token_count = _container.token_counter.count_tokens(temp_response)

    # AIDEV-NOTE: list_tables doesn't support chunking (no 'data' key), so return error for large responses
    if token_count > 9000:
        # Return error with guidance
        error_response = _container.response_manager.format_error(
            "Response too large",
            f"Response would be {token_count} tokens (limit: 9000)",
            catalog=catalog,
            schemas_requested=len(schemas),
            suggestions=[
                "Request fewer schemas at once",
                f"Split the {len(schemas)} schemas into smaller batches",
            ],
        )
        return "\n---\n".join([error_response])

    formatted_result = _container.response_manager.format_response(result, auto_chunk=False)
    return "\n---\n".join([formatted_result])


@mcp.tool()
async def list_columns(
    catalog: str, schema: str, tables: list[str], workspace: str | None = None
) -> str:
    """
    Lists column names, data types, and descriptions for the given table(s).

    Parameters:
    ----------
    catalog : str
        The catalog name.
    schema : str
        The schema name.
    tables : list
        A list of table names to inspect.
    workspace : str, optional
        The workspace name to connect to.
        - In ANALYST mode: This parameter is ignored, always uses default workspace.
        - In DEVELOPER mode: If None or not found, falls back to default workspace.

    Returns:
    -------
    str
        A JSON-formatted dictionary where each key is a table name and the value is a list of dictionaries
        with column metadata (name, type, and description).
    """
    # Use TableService to list columns
    result = _container.table_service.list_columns(catalog, schema, tables, workspace)

    # Check token count before formatting
    temp_response = json.dumps(result, separators=(",", ":"))
    token_count = _container.token_counter.count_tokens(temp_response)

    # AIDEV-NOTE: list_columns doesn't support chunking (no 'data' key), so return error for large responses
    if token_count > 9000:
        # Return error with guidance for large responses
        error_response = _container.response_manager.format_error(
            "Response too large",
            f"Response would be {token_count} tokens (limit: 9000)",
            catalog=catalog,
            schema=schema,
            tables_requested=len(tables),
            suggestions=[
                "Request fewer tables at once",
                "Use individual table queries instead of batch",
                f"Split the {len(tables)} tables into smaller batches",
            ],
        )
        return "\n---\n".join([error_response])

    formatted_result = _container.response_manager.format_response(result, auto_chunk=False)
    return "\n---\n".join([formatted_result])


@mcp.tool()
async def list_user_functions(
    catalog: str | None = None, schema: str | None = None, workspace: str | None = None
) -> str:
    """
    Lists all user-defined functions in a specific catalog and schema.

    Parameters:
    ----------
    catalog : str, optional
        The catalog name where the functions are stored.
        If not provided, uses DATABRICKS_DEFAULT_CATALOG environment variable.
    schema : str, optional
        The schema name where the functions are stored.
        If not provided, uses DATABRICKS_DEFAULT_SCHEMA environment variable.
    workspace : str, optional
        The workspace name to connect to.
        - In ANALYST mode: This parameter is ignored, always uses default workspace.
        - In DEVELOPER mode: If None or not found, falls back to default workspace.

    Returns:
    -------
    str
        A JSON-formatted string containing the list of user function names.
    """
    # Get defaults from environment variables if not provided
    if catalog is None:
        catalog = os.getenv("DATABRICKS_DEFAULT_CATALOG")
        if not catalog:
            return _container.response_manager.format_error(
                "No catalog specified",
                "Please provide a catalog parameter or set DATABRICKS_DEFAULT_CATALOG environment variable",
            )

    if schema is None:
        schema = os.getenv("DATABRICKS_DEFAULT_SCHEMA")
        if not schema:
            return _container.response_manager.format_error(
                "No schema specified",
                "Please provide a schema parameter or set DATABRICKS_DEFAULT_SCHEMA environment variable",
            )

    # Use FunctionService to list user functions
    result = _container.function_service.list_user_functions(catalog, schema, workspace)

    # Check token count before formatting
    temp_response = json.dumps(result, separators=(",", ":"))
    token_count = _container.token_counter.count_tokens(temp_response)

    # AIDEV-NOTE: list_user_functions doesn't support chunking, so return error for large responses
    if token_count > 9000:
        # Return error with guidance
        error_response = _container.response_manager.format_error(
            "Response too large",
            f"Response would be {token_count} tokens (limit: 9000)",
            catalog=catalog,
            schema=schema,
            function_count=result.get("function_count", 0),
            suggestions=[
                "Too many functions to display at once",
                "Consider using specific function queries",
            ],
        )
        return "\n---\n".join([error_response])

    formatted_result = _container.response_manager.format_response(result, auto_chunk=False)
    return "\n---\n".join([formatted_result])


@mcp.tool()
async def describe_function(
    function_name: str,
    catalog: str | None = None,
    schema: str | None = None,
    workspace: str | None = None,
) -> str:
    """
    Describes a specific user-defined function using the DESCRIBE FUNCTION SQL command.

    Parameters:
    ----------
    function_name : str
        The name of the function to describe.
    catalog : str, optional
        The catalog name where the function is stored.
        If not provided, uses DATABRICKS_DEFAULT_CATALOG environment variable.
    schema : str, optional
        The schema name where the function is stored.
        If not provided, uses DATABRICKS_DEFAULT_SCHEMA environment variable.
    workspace : str, optional
        The workspace name to connect to.
        - In ANALYST mode: This parameter is ignored, always uses default workspace.
        - In DEVELOPER mode: If None or not found, falls back to default workspace.

    Returns:
    -------
    str
        A JSON-formatted string containing the function details including parameters,
        return type, description, and other metadata.
    """
    # Get defaults from environment variables if not provided
    if catalog is None:
        catalog = os.getenv("DATABRICKS_DEFAULT_CATALOG")
        if not catalog:
            return _container.response_manager.format_error(
                "No catalog specified",
                "Please provide a catalog parameter or set DATABRICKS_DEFAULT_CATALOG environment variable",
            )

    if schema is None:
        schema = os.getenv("DATABRICKS_DEFAULT_SCHEMA")
        if not schema:
            return _container.response_manager.format_error(
                "No schema specified",
                "Please provide a schema parameter or set DATABRICKS_DEFAULT_SCHEMA environment variable",
            )

    try:
        # Use FunctionService to describe function
        function_info = _container.function_service.describe_function(
            function_name, catalog, schema, workspace
        )

        # AIDEV-NOTE: ResponseManager automatically handles token checking and chunking
        formatted_result = _container.response_manager.format_response(function_info)
        return "\n---\n".join([formatted_result])

    except Exception as e:
        error_response = _container.response_manager.format_error(
            "Function not found or error describing function",
            str(e),
            catalog=catalog,
            schema=schema,
            function_name=function_name,
        )
        return "\n---\n".join([error_response])


@mcp.tool()
async def list_and_describe_all_functions(
    catalog: str | None = None, schema: str | None = None, workspace: str | None = None
) -> str:
    """
    Lists all user-defined functions in a catalog.schema and provides descriptions for each.

    This tool combines the functionality of list_user_functions and describe_function to
    provide comprehensive information about all functions in a single call. For large
    numbers of functions, the response will be automatically chunked.

    Parameters:
    ----------
    catalog : str, optional
        The catalog name where the functions are stored.
        If not provided, uses DATABRICKS_DEFAULT_CATALOG environment variable.
    schema : str, optional
        The schema name where the functions are stored.
        If not provided, uses DATABRICKS_DEFAULT_SCHEMA environment variable.
    workspace : str, optional
        The workspace name to connect to.
        - In ANALYST mode: This parameter is ignored, always uses default workspace.
        - In DEVELOPER mode: If None or not found, falls back to default workspace.

    Returns:
    -------
    str
        A JSON-formatted string containing a dictionary with function names as keys
        and their descriptions as values. If response exceeds token limits, returns
        chunked response information.
    """
    # Get defaults from environment variables if not provided
    if catalog is None:
        catalog = os.getenv("DATABRICKS_DEFAULT_CATALOG")
        if not catalog:
            return _container.response_manager.format_error(
                "No catalog specified",
                "Please provide a catalog parameter or set DATABRICKS_DEFAULT_CATALOG environment variable",
            )

    if schema is None:
        schema = os.getenv("DATABRICKS_DEFAULT_SCHEMA")
        if not schema:
            return _container.response_manager.format_error(
                "No schema specified",
                "Please provide a schema parameter or set DATABRICKS_DEFAULT_SCHEMA environment variable",
            )

    # Use FunctionService to list and describe all functions
    result = _container.function_service.list_and_describe_all_functions(catalog, schema, workspace)

    # AIDEV-NOTE: ResponseManager automatically handles token checking and chunking
    formatted_result = _container.response_manager.format_response(result)
    return "\n---\n".join([formatted_result])


def main() -> None:
    """Main entry point for the databricks-tools MCP server."""
    global _container

    # Parse command-line arguments for role-based access control
    parser = argparse.ArgumentParser(description="Databricks MCP Server")
    parser.add_argument(
        "--developer",
        action="store_true",
        help="Enable developer mode to access all configured workspaces (default is analyst mode with access to default workspace only)",
    )

    args = parser.parse_args()

    # AIDEV-NOTE: Recreate ApplicationContainer with DEVELOPER role if --developer flag is set
    if args.developer:
        _container = ApplicationContainer(role=Role.DEVELOPER, max_tokens=9000)

    # Initialize and run the server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
