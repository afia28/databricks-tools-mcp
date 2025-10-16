"""
Basic Usage Examples for Databricks Tools MCP Server

This module demonstrates simple, common usage patterns for querying
Databricks Unity Catalog using the databricks-tools MCP server.

Examples include:
- Listing catalogs and schemas
- Executing basic SQL queries
- Getting table details
- Basic error handling
"""

from databricks_tools.core.container import ApplicationContainer
from databricks_tools.security.role_manager import Role


def example_list_catalogs() -> None:
    """
    List all available catalogs in the default workspace.

    This is the simplest operation - no parameters required.
    """
    # Create application container in ANALYST mode (default workspace only)
    container = ApplicationContainer(role=Role.ANALYST)

    # Use the catalog service to list all catalogs
    catalogs_response = container.catalog_service.list_catalogs()

    print("Available Catalogs:")
    print("-" * 50)
    for catalog in catalogs_response["catalogs"]:
        print(f"  - {catalog}")
    print()


def example_list_schemas(catalog_name: str = "main") -> None:
    """
    List all schemas in a specific catalog.

    Args:
        catalog_name: Name of the catalog to explore (default: "main")
    """
    container = ApplicationContainer(role=Role.ANALYST)

    # List schemas in the specified catalog
    schemas_response = container.catalog_service.list_schemas(catalog_name)

    print(f"Schemas in catalog '{catalog_name}':")
    print("-" * 50)
    for schema in schemas_response["schemas"]:
        print(f"  - {schema}")
    print()


def example_list_tables(catalog: str = "main", schema: str = "default") -> None:
    """
    List all tables in a specific schema.

    Args:
        catalog: Catalog name
        schema: Schema name
    """
    container = ApplicationContainer(role=Role.ANALYST)

    # List tables in the specified schema
    tables_response = container.table_service.list_tables(catalog, schema)

    print(f"Tables in {catalog}.{schema}:")
    print("-" * 50)
    for table in tables_response["tables"]:
        print(f"  - {table}")
    print()


def example_get_table_details(
    catalog: str = "main", schema: str = "default", table: str = "sample_table"
) -> None:
    """
    Get detailed information about a table including schema and sample data.

    Args:
        catalog: Catalog name
        schema: Schema name
        table: Table name
    """
    container = ApplicationContainer(role=Role.ANALYST)

    # Get table details (schema + sample rows)
    details_response = container.table_service.get_table_details(
        catalog=catalog,
        schema=schema,
        table=table,
        limit=5,  # Return first 5 rows
    )

    print(f"Table Details: {catalog}.{schema}.{table}")
    print("=" * 70)

    # Display schema
    print("\nSchema:")
    print("-" * 70)
    for column in details_response["schema"]:
        print(f"  {column['name']:30} {column['type']}")

    # Display sample data
    print("\nSample Data (first 5 rows):")
    print("-" * 70)
    if details_response["data"]:
        # Print column headers
        headers = [col["name"] for col in details_response["schema"]]
        print("  " + " | ".join(headers))
        print("  " + "-" * 60)

        # Print rows
        for row in details_response["data"]:
            values = [str(row.get(h, "NULL")) for h in headers]
            print("  " + " | ".join(values))
    else:
        print("  (No data)")
    print()


def example_get_row_count(
    catalog: str = "main", schema: str = "default", table: str = "sample_table"
) -> None:
    """
    Get the total row count for a table.

    Args:
        catalog: Catalog name
        schema: Schema name
        table: Table name
    """
    container = ApplicationContainer(role=Role.ANALYST)

    # Get row count
    count_response = container.table_service.get_table_row_count(
        catalog=catalog, schema=schema, table=table
    )

    print(f"Row count for {catalog}.{schema}.{table}:")
    print(f"  Total rows: {count_response['row_count']:,}")
    print()


def example_simple_query(sql: str = "SELECT CURRENT_DATE() as today") -> None:
    """
    Execute a simple SQL query and display results.

    Args:
        sql: SQL query to execute
    """
    container = ApplicationContainer(role=Role.ANALYST)

    # Execute query using the query executor
    result_df = container.query_executor.execute_query(sql)

    print(f"Query: {sql}")
    print("-" * 70)
    print(result_df.to_string(index=False))
    print()


def example_query_with_catalog(
    catalog: str = "main", sql: str = "SELECT * FROM sample_table LIMIT 3"
) -> None:
    """
    Execute a query with a specific catalog context.

    This sets the default catalog for the query, so you don't need
    to fully qualify table names.

    Args:
        catalog: Default catalog to use
        sql: SQL query (can use unqualified table names)
    """
    container = ApplicationContainer(role=Role.ANALYST)

    # Execute query with catalog context
    result_df = container.query_executor.execute_query_with_catalog(sql=sql, catalog=catalog)

    print(f"Query with catalog '{catalog}':")
    print(f"  {sql}")
    print("-" * 70)
    print(result_df.to_string(index=False))
    print()


def example_error_handling() -> None:
    """
    Demonstrate proper error handling for common scenarios.
    """
    container = ApplicationContainer(role=Role.ANALYST)

    print("Error Handling Examples:")
    print("=" * 70)

    # Example 1: Invalid catalog
    try:
        container.catalog_service.list_schemas("nonexistent_catalog")
    except Exception as e:
        print(f"✗ Invalid catalog error: {type(e).__name__}")
        print(f"  Message: {str(e)[:100]}...")

    # Example 2: Invalid SQL query
    try:
        container.query_executor.execute_query("SELECT * FROM invalid.table.name")
    except Exception as e:
        print(f"✗ Invalid query error: {type(e).__name__}")
        print(f"  Message: {str(e)[:100]}...")

    # Example 3: Invalid workspace (developer mode)
    try:
        dev_container = ApplicationContainer(role=Role.DEVELOPER)
        dev_container.query_executor.execute_query("SELECT 1", workspace="nonexistent_workspace")
    except ValueError as e:
        print(f"✗ Invalid workspace error: {type(e).__name__}")
        print(f"  Message: {str(e)}")

    print()


def example_workspace_configuration() -> None:
    """
    Demonstrate how to work with workspace configurations.
    """
    container = ApplicationContainer(role=Role.ANALYST)

    print("Workspace Configuration:")
    print("=" * 70)

    # List all available workspaces
    workspaces = container.workspace_manager.get_available_workspaces()
    print(f"Available workspaces: {list(workspaces.keys())}")

    # Get default workspace config
    default_config = container.workspace_manager.get_workspace_config("default")
    print("\nDefault workspace:")
    print(f"  Server: {default_config.server_hostname}")
    print(f"  HTTP Path: {default_config.http_path}")
    print(f"  Token: {'*' * 20} (hidden)")
    print()


def example_developer_mode() -> None:
    """
    Demonstrate developer mode with access to multiple workspaces.

    Note: This requires DEVELOPER role and multiple workspace configurations
    in environment variables (e.g., PRODUCTION_DATABRICKS_*, STAGING_DATABRICKS_*).
    """
    # Create container in DEVELOPER mode
    dev_container = ApplicationContainer(role=Role.DEVELOPER)

    print("Developer Mode - Multiple Workspaces:")
    print("=" * 70)

    # List all available workspaces
    workspaces = dev_container.workspace_manager.get_available_workspaces()
    print(f"Available workspaces: {list(workspaces.keys())}")

    # Query different workspaces
    for workspace_name in workspaces.keys():
        try:
            result_df = dev_container.query_executor.execute_query(
                sql="SELECT CURRENT_USER() as user, CURRENT_CATALOG() as catalog",
                workspace=workspace_name,
            )
            print(f"\n{workspace_name.upper()} workspace:")
            print(result_df.to_string(index=False))
        except Exception as e:
            print(f"\n{workspace_name.upper()} workspace:")
            print(f"  Error: {str(e)[:100]}...")

    print()


if __name__ == "__main__":
    """
    Run all basic examples.

    Note: You must have valid Databricks credentials in your .env file
    for these examples to work.
    """
    print("\n" + "=" * 70)
    print("DATABRICKS TOOLS MCP SERVER - BASIC USAGE EXAMPLES")
    print("=" * 70 + "\n")

    # Run examples
    example_list_catalogs()
    example_list_schemas("main")
    example_list_tables("main", "default")
    example_simple_query()
    example_workspace_configuration()
    example_error_handling()

    # Optional: Uncomment to test specific examples
    # example_get_table_details("main", "default", "my_table")
    # example_get_row_count("main", "default", "my_table")
    # example_query_with_catalog("main", "SELECT * FROM my_table LIMIT 5")
    # example_developer_mode()  # Requires DEVELOPER role and multiple workspaces

    print("=" * 70)
    print("Examples completed!")
    print("=" * 70 + "\n")
