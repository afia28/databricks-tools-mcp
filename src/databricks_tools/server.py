import argparse
import json
import os
import uuid
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from databricks_tools.config.workspace import WorkspaceConfigManager
from databricks_tools.core.query_executor import QueryExecutor
from databricks_tools.core.token_counter import TokenCounter
from databricks_tools.security.role_manager import Role, RoleManager
from databricks_tools.services.catalog_service import CatalogService

# Initialize FastMCP server
load_dotenv()
mcp = FastMCP("databricks_sql")

# AIDEV-NOTE: Role-based access control using RoleManager (default is analyst)
_role_manager = RoleManager(role=Role.ANALYST)

# Workspace configuration manager instance (initialized with role_manager)
_workspace_manager = WorkspaceConfigManager(role_manager=_role_manager)

# Query executor instance
_query_executor = QueryExecutor(_workspace_manager)

# Token counting utility instance
_token_counter = TokenCounter(model="gpt-4")

# Token limit constant
MAX_RESPONSE_TOKENS = 9000  # MCP server limit is 25,000, keep 1,000 token buffer

# Catalog service instance
_catalog_service = CatalogService(_query_executor, _token_counter, MAX_RESPONSE_TOKENS)

# Chunking session storage (in-memory for now)
CHUNK_SESSIONS: dict[str, dict] = {}


# Constants and Configuration
def get_workspace_config(workspace: str | None = None) -> dict[str, str]:
    """Get configuration for a specific workspace.

    Legacy wrapper around WorkspaceConfigManager for backward compatibility.
    This function maintains the original dict-based return type while using
    the new WorkspaceConfigManager internally.

    Parameters:
    ----------
    workspace : str, optional
        The workspace name (e.g., 'production', 'dev', 'staging').
        - In ANALYST mode: This parameter is ignored, always uses default workspace.
        - In DEVELOPER mode: If None or not found, falls back to default workspace.

    Returns:
    -------
    Dict[str, str]
        Dictionary containing server_hostname, http_path, and access_token.

    Raises:
    ------
    ValueError
        If no workspace configuration is found.
    """
    # Use WorkspaceConfigManager to get configuration
    config = _workspace_manager.get_workspace_config(workspace)

    # Convert WorkspaceConfig to dict for backward compatibility
    return {
        "server_hostname": config.server_hostname,
        "http_path": config.http_path,
        "access_token": config.access_token.get_secret_value(),  # Extract from SecretStr
    }


def get_available_workspaces() -> list[str]:
    """Get a list of configured workspaces based on environment variables.

    Legacy wrapper around WorkspaceConfigManager for backward compatibility.

    Returns:
    -------
    List[str]
        List of available workspace names.
    """
    # Use WorkspaceConfigManager to get available workspaces
    return _workspace_manager.get_available_workspaces()


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in text using TokenCounter utility.

    Legacy wrapper function for backward compatibility with existing code.

    Args:
        text: The text to count tokens in.
        model: The model to use for counting (default "gpt-4").

    Returns:
        The number of tokens in the text.

    Example:
        >>> count_tokens("Hello, world!")
        4
    """
    if model != "gpt-4":
        counter = TokenCounter(model=model)
        return counter.count_tokens(text)
    return _token_counter.count_tokens(text)


def estimate_response_tokens(data: dict) -> int:
    """Estimate tokens in a response dict using TokenCounter utility.

    Legacy wrapper function for backward compatibility with existing code.

    Args:
        data: The dictionary to estimate tokens for.

    Returns:
        The estimated number of tokens.

    Example:
        >>> estimate_response_tokens({"key": "value"})
        7
    """
    return _token_counter.estimate_tokens(data)


def create_chunked_response(data: dict, max_tokens: int = MAX_RESPONSE_TOKENS) -> dict:
    """
    Create a chunked response for data that exceeds token limits.

    Parameters:
    ----------
    data : Dict
        The full response data dictionary.
    max_tokens : int
        Maximum tokens allowed per chunk.

    Returns:
    -------
    Dict
        Chunked response with session information.
    """
    # Generate session ID for this chunked response
    session_id = str(uuid.uuid4())

    # Extract data rows and metadata
    rows = data.get("data", [])
    schema = data.get("schema", {})
    metadata = {k: v for k, v in data.items() if k not in ["data", "schema"]}

    # Create base response structure
    base_response = {"schema": schema, **metadata}

    # Calculate how many rows can fit in each chunk
    base_tokens = estimate_response_tokens(base_response)
    available_tokens = (
        max_tokens - base_tokens - 500
    )  # Reserve 500 tokens for chunk metadata

    # Estimate tokens per row (using first few rows as sample)
    if rows:
        sample_rows = rows[: min(3, len(rows))]
        sample_tokens = estimate_response_tokens({"data": sample_rows})
        tokens_per_row = max(1, sample_tokens // len(sample_rows))
        rows_per_chunk = max(1, available_tokens // tokens_per_row)
    else:
        rows_per_chunk = 1

    # Split data into chunks
    chunks = []
    total_chunks = (len(rows) + rows_per_chunk - 1) // rows_per_chunk

    for i in range(0, len(rows), rows_per_chunk):
        chunk_rows = rows[i : i + rows_per_chunk]
        chunk_number = (i // rows_per_chunk) + 1

        chunk_response = {
            **base_response,
            "data": chunk_rows,
            "chunking_info": {
                "session_id": session_id,
                "chunk_number": chunk_number,
                "total_chunks": total_chunks,
                "rows_in_chunk": len(chunk_rows),
                "total_rows": len(rows),
                "is_chunked": True,
                "reconstruction_instructions": (
                    "This response is chunked due to token limits. "
                    f"Collect all {total_chunks} chunks with session_id '{session_id}' "
                    "and combine the 'data' arrays to reconstruct the full dataset."
                ),
            },
        }
        chunks.append(chunk_response)

    # Calculate token counts for each chunk
    chunk_token_amounts = {}
    for i, chunk in enumerate(chunks):
        chunk_number = i + 1
        chunk_tokens = estimate_response_tokens(chunk)
        chunk_token_amounts[str(chunk_number)] = chunk_tokens

    # Store session info
    CHUNK_SESSIONS[session_id] = {
        "chunks": chunks,
        "created_at": datetime.now(),
        "total_chunks": total_chunks,
        "chunks_delivered": 0,
        "chunk_token_amounts": chunk_token_amounts,
    }

    return {
        "chunked_response": True,
        "session_id": session_id,
        "total_chunks": total_chunks,
        "chunk_token_amounts": chunk_token_amounts,
        "message": f"Response exceeds token limit. Data will be delivered in {total_chunks} chunks.",
        "instructions": f"Use get_chunk(session_id='{session_id}', chunk_number=N) to retrieve each chunk (1-{total_chunks})",
    }


def databricks_sql_query(
    query: str, parse_dates: list[str] | None = None, workspace: str | None = None
) -> pd.DataFrame:
    """Execute SQL query using QueryExecutor service.

    Legacy wrapper function for backward compatibility with existing code.

    Args:
        query: SQL query string to execute.
        parse_dates: Optional list of column names to parse as dates.
        workspace: Optional workspace name.

    Returns:
        pandas DataFrame with query results.

    Example:
        >>> df = databricks_sql_query("SELECT 1 as value")
    """
    return _query_executor.execute_query(query, workspace, parse_dates)


def databricks_sql_query_with_catalog(
    catalog: str, query: str, workspace: str | None = None
) -> pd.DataFrame:
    """Execute query with catalog context using QueryExecutor service.

    Legacy wrapper function for backward compatibility with existing code.

    Args:
        catalog: Catalog name to set as context.
        query: SQL query string to execute.
        workspace: Optional workspace name.

    Returns:
        pandas DataFrame with query results.

    Example:
        >>> df = databricks_sql_query_with_catalog("my_catalog", "SELECT * FROM my_table")
    """
    return _query_executor.execute_query_with_catalog(catalog, query, workspace)


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
    workspaces = get_available_workspaces()
    return json.dumps(workspaces, indent=2)


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
    if session_id not in CHUNK_SESSIONS:
        return json.dumps(
            {
                "error": "Session not found",
                "session_id": session_id,
                "message": "The specified session ID does not exist or has expired.",
            },
            indent=2,
        )

    session = CHUNK_SESSIONS[session_id]
    chunks = session["chunks"]

    if chunk_number < 1 or chunk_number > len(chunks):
        return json.dumps(
            {
                "error": "Invalid chunk number",
                "session_id": session_id,
                "chunk_number": chunk_number,
                "total_chunks": len(chunks),
                "message": f"Chunk number must be between 1 and {len(chunks)}.",
            },
            indent=2,
        )

    # Get the requested chunk (convert to 0-indexed)
    chunk = chunks[chunk_number - 1]

    # Update delivery tracking
    session["chunks_delivered"] += 1

    # Add completion status to chunk
    chunk["chunking_info"]["chunks_delivered"] = session["chunks_delivered"]
    chunk["chunking_info"]["all_chunks_delivered"] = (
        session["chunks_delivered"] >= session["total_chunks"]
    )

    return json.dumps(chunk, indent=2, separators=(",", ":"))


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
    if session_id not in CHUNK_SESSIONS:
        return json.dumps(
            {
                "error": "Session not found",
                "session_id": session_id,
                "message": "The specified session ID does not exist or has expired.",
            },
            indent=2,
        )

    session = CHUNK_SESSIONS[session_id]

    return json.dumps(
        {
            "session_id": session_id,
            "total_chunks": session["total_chunks"],
            "chunks_delivered": session["chunks_delivered"],
            "chunks_remaining": session["total_chunks"] - session["chunks_delivered"],
            "created_at": session["created_at"].isoformat(),
            "all_chunks_delivered": session["chunks_delivered"]
            >= session["total_chunks"],
            "next_chunk_to_request": (
                min(session["chunks_delivered"] + 1, session["total_chunks"])
                if session["chunks_delivered"] < session["total_chunks"]
                else None
            ),
            "chunk_token_amounts": session.get("chunk_token_amounts", {}),
            "reconstruction_instructions": (
                f"Use get_chunk(session_id='{session_id}', chunk_number=N) "
                f"to retrieve chunks 1 through {session['total_chunks']}. "
                "Combine all 'data' arrays to reconstruct the full dataset."
            ),
        },
        indent=2,
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
    query = f"SELECT COUNT(*) as row_count FROM {catalog}.{schema}.{table_name}"
    df = databricks_sql_query(query, workspace=workspace)

    row_count = int(df.iloc[0]["row_count"])

    # Calculate estimated pages for common page sizes
    page_sizes = [50, 100, 250, 500, 1000]
    pages_info = {}
    for size in page_sizes:
        pages_info[f"pages_with_{size}_rows"] = (row_count + size - 1) // size

    result = {
        "table_name": f"{catalog}.{schema}.{table_name}",
        "total_rows": row_count,
        "estimated_pages": pages_info,
    }

    return json.dumps(result, indent=2, separators=(",", ":"))


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
    # Build query with optional limit
    if limit is not None:
        query = f"SELECT * FROM {catalog}.{schema}.{table_name} LIMIT {limit}"
    else:
        query = f"SELECT * FROM {catalog}.{schema}.{table_name}"

    df = databricks_sql_query(query, workspace=workspace)

    # Convert DataFrame to result format and add table information
    df_json = json.loads(df.to_json(orient="table", index=False))
    result = {
        "data": df_json["data"],
        "schema": df_json["schema"],
        "table_name": f"{catalog}.{schema}.{table_name}",
    }

    # Check token count before formatting final response
    temp_response = json.dumps(result, separators=(",", ":"))
    token_count = count_tokens(temp_response)

    if token_count > MAX_RESPONSE_TOKENS:
        # Create chunked response instead of error
        chunked_response = create_chunked_response(result)
        return json.dumps(chunked_response, indent=2, separators=(",", ":"))

    # Format the response
    final_data = json.dumps(result, indent=2, separators=(",", ":"))
    return final_data


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
    df = databricks_sql_query(query, workspace=workspace)

    # Convert DataFrame to result format
    df_json = json.loads(df.to_json(orient="table", index=False))
    result = {"data": df_json["data"], "schema": df_json["schema"], "query": query}

    # Add query information

    # Check token count before formatting final response
    temp_response = json.dumps(result, separators=(",", ":"))
    token_count = count_tokens(temp_response)

    if token_count > MAX_RESPONSE_TOKENS:
        # Create chunked response instead of error
        chunked_response = create_chunked_response(result)
        return json.dumps(chunked_response, indent=2, separators=(",", ":"))

    # Format the response
    final_data = json.dumps(result, indent=2, separators=(",", ":"))
    return final_data


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
        catalogs = _catalog_service.list_catalogs(workspace)

        # Return as JSON
        return json.dumps(catalogs, indent=2)

    except Exception as e:
        error_msg = f"Error listing catalogs: {str(e)}"
        return json.dumps({"error": error_msg})


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
            catalog_list = _catalog_service.list_catalogs(workspace)
        elif isinstance(catalogs, str):
            catalog_list = [catalogs]
        else:
            catalog_list = catalogs

        # Use CatalogService to get schemas
        result = _catalog_service.list_schemas(catalog_list, workspace)

        # Return as JSON
        return json.dumps(result, indent=2)

    except Exception as e:
        error_msg = f"Error listing schemas: {str(e)}"
        return json.dumps({"error": error_msg})


@mcp.tool()
async def list_tables(catalog: str, schemas: list, workspace: str | None = None) -> str:
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
    result = {}
    for schema in schemas:
        query = f"SHOW TABLES IN {catalog}.{schema}"
        df = databricks_sql_query(query, workspace=workspace)
        result[schema] = df["tableName"].tolist()

    # Check token count before formatting
    temp_response = json.dumps(result, separators=(",", ":"))
    token_count = count_tokens(temp_response)

    if token_count > MAX_RESPONSE_TOKENS:
        # Return error with guidance
        error_response = json.dumps(
            {
                "error": "Response too large",
                "message": f"Response would be {token_count} tokens (limit: {MAX_RESPONSE_TOKENS})",
                "catalog": catalog,
                "schemas_requested": len(schemas),
                "suggestions": [
                    "Request fewer schemas at once",
                    f"Split the {len(schemas)} schemas into smaller batches",
                ],
            },
            indent=2,
        )
        return "\n---\n".join([error_response])

    result = json.dumps(result, indent=2)
    return "\n---\n".join([result])


@mcp.tool()
async def list_columns(
    catalog: str, schema: str, tables: list, workspace: str | None = None
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
    result = {}
    for table in tables:
        query = f"DESCRIBE TABLE EXTENDED {catalog}.{schema}.{table}"
        df = databricks_sql_query(query, workspace=workspace)
        # Filter to only the schema description section
        metadata = []
        for _, row in df.iterrows():
            if row["col_name"] and not row["col_name"].startswith("#"):
                metadata.append(
                    {
                        "name": row["col_name"],
                        "type": row["data_type"],
                        "description": row.get("comment", ""),
                    }
                )
        result[table] = metadata

    # Check token count before formatting
    temp_response = json.dumps(result, separators=(",", ":"))
    token_count = count_tokens(temp_response)

    if token_count > MAX_RESPONSE_TOKENS:
        # Return error with guidance for large responses
        error_response = json.dumps(
            {
                "error": "Response too large",
                "message": f"Response would be {token_count} tokens (limit: {MAX_RESPONSE_TOKENS})",
                "catalog": catalog,
                "schema": schema,
                "tables_requested": len(tables),
                "suggestions": [
                    "Request fewer tables at once",
                    "Use individual table queries instead of batch",
                    f"Split the {len(tables)} tables into smaller batches",
                ],
            },
            indent=2,
        )
        return "\n---\n".join([error_response])

    result = json.dumps(result, indent=2)
    return "\n---\n".join([result])


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
            return json.dumps(
                {
                    "error": "No catalog specified",
                    "message": "Please provide a catalog parameter or set DATABRICKS_DEFAULT_CATALOG environment variable",
                },
                indent=2,
            )

    if schema is None:
        schema = os.getenv("DATABRICKS_DEFAULT_SCHEMA")
        if not schema:
            return json.dumps(
                {
                    "error": "No schema specified",
                    "message": "Please provide a schema parameter or set DATABRICKS_DEFAULT_SCHEMA environment variable",
                },
                indent=2,
            )

    # Use the helper function that sets catalog context
    query = f"SHOW USER FUNCTIONS IN {catalog}.{schema}"
    df = databricks_sql_query_with_catalog(catalog, query, workspace=workspace)

    # Extract function names from the result
    functions = df["function"].tolist() if "function" in df.columns else []

    result = {
        "catalog": catalog,
        "schema": schema,
        "user_functions": functions,
        "function_count": len(functions),
    }

    # Check token count before formatting
    temp_response = json.dumps(result, separators=(",", ":"))
    token_count = count_tokens(temp_response)

    if token_count > MAX_RESPONSE_TOKENS:
        # Return error with guidance
        error_response = json.dumps(
            {
                "error": "Response too large",
                "message": f"Response would be {token_count} tokens (limit: {MAX_RESPONSE_TOKENS})",
                "catalog": catalog,
                "schema": schema,
                "function_count": len(functions),
                "suggestions": [
                    "Too many functions to display at once",
                    "Consider using specific function queries",
                ],
            },
            indent=2,
        )
        return "\n---\n".join([error_response])

    result = json.dumps(result, indent=2)
    return "\n---\n".join([result])


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
            return json.dumps(
                {
                    "error": "No catalog specified",
                    "message": "Please provide a catalog parameter or set DATABRICKS_DEFAULT_CATALOG environment variable",
                },
                indent=2,
            )

    if schema is None:
        schema = os.getenv("DATABRICKS_DEFAULT_SCHEMA")
        if not schema:
            return json.dumps(
                {
                    "error": "No schema specified",
                    "message": "Please provide a schema parameter or set DATABRICKS_DEFAULT_SCHEMA environment variable",
                },
                indent=2,
            )

    try:
        # Use the helper function that sets catalog context
        query = f"DESCRIBE FUNCTION EXTENDED {catalog}.{schema}.{function_name}"
        df = databricks_sql_query_with_catalog(catalog, query, workspace=workspace)

        # Parse the describe function extended output
        function_info = {
            "catalog": catalog,
            "schema": schema,
            "function_name": function_name,
            "details": [],
        }

        # Process the describe extended output - each row contains info in function_desc column
        # Filter to keep only desired fields
        skip_configs = False
        for _, row in df.iterrows():
            if pd.notna(row.get("function_desc", "")):
                desc_line = str(row["function_desc"])

                # Check if we should skip this line
                if desc_line.startswith("Configs:"):
                    skip_configs = True
                    continue
                elif desc_line.startswith("Owner:") or desc_line.startswith(
                    "Create Time:"
                ):
                    continue
                elif skip_configs and desc_line.startswith("               "):
                    # Skip config lines (they are indented with many spaces)
                    continue
                elif desc_line.startswith("Deterministic:") or desc_line.startswith(
                    "Data Access:"
                ):
                    skip_configs = False  # These come after configs, so stop skipping

                # Add lines we want to keep
                if (
                    desc_line.startswith("Function:")
                    or desc_line.startswith("Type:")
                    or desc_line.startswith("Input:")
                    or desc_line.startswith("Returns:")
                    or desc_line.startswith("Comment:")
                    or desc_line.startswith("Deterministic:")
                    or desc_line.startswith("Data Access:")
                    or desc_line.startswith("Body:")
                    or desc_line.startswith("               ")
                ):  # Keep indented Input/Returns lines
                    # For indented lines, only keep if we're not in config section
                    if desc_line.startswith("               ") and not skip_configs:
                        function_info["details"].append(desc_line)
                    elif not desc_line.startswith("               "):
                        function_info["details"].append(desc_line)

        # Check token count before formatting
        temp_response = json.dumps(function_info, separators=(",", ":"))
        token_count = count_tokens(temp_response)

        if token_count > MAX_RESPONSE_TOKENS:
            # Create chunked response
            chunked_response = create_chunked_response(function_info)
            return json.dumps(chunked_response, indent=2, separators=(",", ":"))

        result = json.dumps(function_info, indent=2)
        return "\n---\n".join([result])

    except Exception as e:
        error_response = json.dumps(
            {
                "error": "Function not found or error describing function",
                "catalog": catalog,
                "schema": schema,
                "function_name": function_name,
                "message": str(e),
            },
            indent=2,
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
            return json.dumps(
                {
                    "error": "No catalog specified",
                    "message": "Please provide a catalog parameter or set DATABRICKS_DEFAULT_CATALOG environment variable",
                },
                indent=2,
            )

    if schema is None:
        schema = os.getenv("DATABRICKS_DEFAULT_SCHEMA")
        if not schema:
            return json.dumps(
                {
                    "error": "No schema specified",
                    "message": "Please provide a schema parameter or set DATABRICKS_DEFAULT_SCHEMA environment variable",
                },
                indent=2,
            )

    # Use the helper function that sets catalog context
    query = f"SHOW USER FUNCTIONS IN {catalog}.{schema}"
    df = databricks_sql_query_with_catalog(catalog, query, workspace=workspace)

    # Extract function names
    functions = df["function"].tolist() if "function" in df.columns else []

    # Initialize result structure
    result = {
        "catalog": catalog,
        "schema": schema,
        "function_count": len(functions),
        "functions": {},
    }

    # Describe each function
    for func in functions:
        # Extract just the function name (remove catalog.schema prefix if present)
        func_name = func.split(".")[-1]

        try:
            describe_query = (
                f"DESCRIBE FUNCTION EXTENDED {catalog}.{schema}.{func_name}"
            )
            desc_df = databricks_sql_query_with_catalog(
                catalog, describe_query, workspace=workspace
            )

            # Parse the describe extended output with filtering
            function_details = []
            skip_configs = False
            for _, row in desc_df.iterrows():
                if pd.notna(row.get("function_desc", "")):
                    desc_line = str(row["function_desc"])

                    # Check if we should skip this line
                    if desc_line.startswith("Configs:"):
                        skip_configs = True
                        continue
                    elif desc_line.startswith("Owner:") or desc_line.startswith(
                        "Create Time:"
                    ):
                        continue
                    elif skip_configs and desc_line.startswith("               "):
                        # Skip config lines (they are indented with many spaces)
                        continue
                    elif desc_line.startswith("Deterministic:") or desc_line.startswith(
                        "Data Access:"
                    ):
                        skip_configs = (
                            False  # These come after configs, so stop skipping
                        )

                    # Add lines we want to keep
                    if (
                        desc_line.startswith("Function:")
                        or desc_line.startswith("Type:")
                        or desc_line.startswith("Input:")
                        or desc_line.startswith("Returns:")
                        or desc_line.startswith("Comment:")
                        or desc_line.startswith("Deterministic:")
                        or desc_line.startswith("Data Access:")
                        or desc_line.startswith("Body:")
                        or desc_line.startswith("               ")
                    ):  # Keep indented Input/Returns lines
                        # For indented lines, only keep if we're not in config section
                        if desc_line.startswith("               ") and not skip_configs:
                            function_details.append(desc_line)
                        elif not desc_line.startswith("               "):
                            function_details.append(desc_line)

            result["functions"][func_name] = function_details

        except Exception as e:
            # If we can't describe a function, include error info
            result["functions"][func_name] = {
                "error": "Could not describe function",
                "message": str(e),
            }

    # Check token count before formatting final response
    temp_response = json.dumps(result, separators=(",", ":"))
    token_count = count_tokens(temp_response)

    if token_count > MAX_RESPONSE_TOKENS:
        # Create chunked response for large function lists
        chunked_response = create_chunked_response(result)
        return json.dumps(chunked_response, indent=2, separators=(",", ":"))

    # Format the response
    final_data = json.dumps(result, indent=2, separators=(",", ":"))
    return "\n---\n".join([final_data])


def main():
    """Main entry point for the databricks-tools MCP server."""
    global _role_manager, _workspace_manager, _query_executor, _catalog_service

    # Parse command-line arguments for role-based access control
    parser = argparse.ArgumentParser(description="Databricks MCP Server")
    parser.add_argument(
        "--developer",
        action="store_true",
        help="Enable developer mode to access all configured workspaces (default is analyst mode with access to default workspace only)",
    )

    args = parser.parse_args()

    # AIDEV-NOTE: Update role manager, workspace manager, query executor, and catalog service if developer mode enabled
    if args.developer:
        _role_manager = RoleManager(role=Role.DEVELOPER)
        # Reinitialize workspace manager with developer role manager
        _workspace_manager = WorkspaceConfigManager(role_manager=_role_manager)
        # Reinitialize query executor with updated workspace manager
        _query_executor = QueryExecutor(_workspace_manager)
        # Reinitialize catalog service with updated query executor
        _catalog_service = CatalogService(
            _query_executor, _token_counter, MAX_RESPONSE_TOKENS
        )

    # Initialize and run the server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
