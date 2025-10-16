"""
Advanced Query Examples for Databricks Tools MCP Server

This module demonstrates advanced usage patterns including:
- Complex SQL queries with JOINs and aggregations
- Multi-workspace querying (developer mode)
- Response chunking for large results
- Custom query patterns
- Performance optimization techniques
"""

from typing import Any

from databricks_tools.core.container import ApplicationContainer
from databricks_tools.security.role_manager import Role


def example_complex_join_query() -> None:
    """
    Execute a complex query with JOINs and aggregations.

    This example demonstrates how to run sophisticated SQL queries
    that combine multiple tables and perform calculations.
    """
    container = ApplicationContainer(role=Role.ANALYST)

    sql = """
    SELECT
        o.order_id,
        o.order_date,
        c.customer_name,
        c.customer_email,
        COUNT(oi.item_id) as total_items,
        SUM(oi.quantity * oi.unit_price) as total_amount
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_date >= CURRENT_DATE - INTERVAL 30 DAYS
    GROUP BY o.order_id, o.order_date, c.customer_name, c.customer_email
    HAVING SUM(oi.quantity * oi.unit_price) > 1000
    ORDER BY total_amount DESC
    LIMIT 10
    """

    print("Complex JOIN Query - Top 10 Orders (Last 30 Days):")
    print("=" * 80)

    result_df = container.query_executor.execute_query(sql)

    print(f"\nFound {len(result_df)} orders")
    print("-" * 80)
    print(result_df.to_string(index=False))
    print()


def example_window_functions() -> None:
    """
    Demonstrate window functions for advanced analytics.
    """
    container = ApplicationContainer(role=Role.ANALYST)

    sql = """
    SELECT
        product_name,
        category,
        sales_amount,
        sales_date,
        AVG(sales_amount) OVER (
            PARTITION BY category
            ORDER BY sales_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as moving_avg_7_day,
        RANK() OVER (
            PARTITION BY category
            ORDER BY sales_amount DESC
        ) as sales_rank,
        PERCENT_RANK() OVER (
            PARTITION BY category
            ORDER BY sales_amount
        ) as percentile
    FROM product_sales
    WHERE sales_date >= CURRENT_DATE - INTERVAL 90 DAYS
    ORDER BY category, sales_rank
    LIMIT 20
    """

    print("Window Functions - Sales Analytics:")
    print("=" * 80)

    result_df = container.query_executor.execute_query(sql)

    print(f"\nAnalyzing {len(result_df)} products")
    print("-" * 80)
    print(result_df.to_string(index=False))
    print()


def example_cte_query() -> None:
    """
    Use Common Table Expressions (CTEs) for complex logic.
    """
    container = ApplicationContainer(role=Role.ANALYST)

    sql = """
    WITH monthly_sales AS (
        SELECT
            DATE_TRUNC('month', order_date) as month,
            SUM(total_amount) as monthly_total
        FROM orders
        WHERE order_date >= CURRENT_DATE - INTERVAL 12 MONTHS
        GROUP BY DATE_TRUNC('month', order_date)
    ),
    sales_growth AS (
        SELECT
            month,
            monthly_total,
            LAG(monthly_total) OVER (ORDER BY month) as prev_month_total,
            (monthly_total - LAG(monthly_total) OVER (ORDER BY month)) /
                NULLIF(LAG(monthly_total) OVER (ORDER BY month), 0) * 100 as growth_rate
        FROM monthly_sales
    )
    SELECT
        month,
        monthly_total,
        prev_month_total,
        ROUND(growth_rate, 2) as growth_percentage
    FROM sales_growth
    ORDER BY month DESC
    """

    print("CTE Query - Monthly Sales Growth:")
    print("=" * 80)

    result_df = container.query_executor.execute_query(sql)

    print("\nMonthly trends (last 12 months):")
    print("-" * 80)
    print(result_df.to_string(index=False))
    print()


def example_multi_workspace_query() -> None:
    """
    Query multiple workspaces and compare results (Developer mode only).

    This requires DEVELOPER role and multiple workspace configurations.
    """
    # Create container in DEVELOPER mode
    dev_container = ApplicationContainer(role=Role.DEVELOPER)

    print("Multi-Workspace Query Comparison:")
    print("=" * 80)

    # Get available workspaces
    workspaces = dev_container.workspace_manager.get_available_workspaces()
    print(f"Querying {len(workspaces)} workspaces: {list(workspaces.keys())}\n")

    # Query to run on each workspace
    sql = """
    SELECT
        CURRENT_DATABASE() as current_db,
        COUNT(*) as table_count
    FROM information_schema.tables
    WHERE table_schema = 'main'
    """

    # Execute query on each workspace
    results: dict[str, Any] = {}
    for workspace_name in workspaces.keys():
        try:
            result_df = dev_container.query_executor.execute_query(
                sql=sql, workspace=workspace_name
            )
            results[workspace_name] = result_df.to_dict("records")[0]
            print(f"✓ {workspace_name}: {results[workspace_name]}")
        except Exception as e:
            results[workspace_name] = {"error": str(e)[:100]}
            print(f"✗ {workspace_name}: Error - {str(e)[:50]}...")

    print(f"\nComparison complete. Queried {len(results)} workspaces.")
    print()


def example_chunked_response() -> None:
    """
    Demonstrate handling of chunked responses for large result sets.

    When a query returns more than 9000 tokens, the response is automatically
    chunked. This example shows how to retrieve all chunks.
    """
    container = ApplicationContainer(role=Role.ANALYST)

    # Query that might return large results
    sql = """
    SELECT * FROM large_table LIMIT 10000
    """

    print("Chunked Response Handling:")
    print("=" * 80)

    # Execute query - response manager will automatically chunk if needed
    result_df = container.query_executor.execute_query(sql)

    # Convert to response format
    response_data = {
        "data": result_df.to_dict("records"),
        "row_count": len(result_df),
        "columns": list(result_df.columns),
    }

    # Use response manager to format (with automatic chunking)
    formatted_response = container.response_manager.format_response(response_data)

    # Check if response was chunked
    if "session_id" in formatted_response:
        print("Response was chunked due to size!")
        print(f"  Session ID: {formatted_response['session_id']}")
        print(f"  Total chunks: {formatted_response['total_chunks']}")
        print(f"  Current chunk: {formatted_response['chunk_number']}")
        print(f"  Rows in first chunk: {len(formatted_response['data'])}")

        # Retrieve additional chunks
        session_id = formatted_response["session_id"]
        total_chunks = formatted_response["total_chunks"]

        print(f"\nRetrieving remaining {total_chunks - 1} chunks...")

        all_data = formatted_response["data"]
        for chunk_num in range(2, total_chunks + 1):
            chunk = container.chunking_service.get_chunk(session_id, chunk_num)
            if "data" in chunk:
                all_data.extend(chunk["data"])
                print(f"  ✓ Retrieved chunk {chunk_num}/{total_chunks} ({len(chunk['data'])} rows)")

        print(f"\nTotal rows retrieved: {len(all_data)}")

    else:
        print("Response fit in single response (no chunking needed)")
        print(f"  Rows returned: {len(formatted_response.get('data', []))}")

    print()


def example_dynamic_sql_generation() -> None:
    """
    Generate SQL dynamically based on parameters.
    """
    # Container available for actual execution (commented out in example)
    # container = ApplicationContainer(role=Role.ANALYST)  # noqa: F841

    def build_filtered_query(
        table: str, filters: dict[str, Any], order_by: str | None = None, limit: int = 100
    ) -> str:
        """Build SQL query dynamically based on filters."""
        # Base query
        sql_parts = [f"SELECT * FROM {table}"]

        # Add WHERE clause if filters exist
        if filters:
            conditions = []
            for column, value in filters.items():
                if isinstance(value, str):
                    conditions.append(f"{column} = '{value}'")
                elif isinstance(value, list | tuple):  # noqa: UP038
                    values_str = ", ".join(
                        f"'{v}'" if isinstance(v, str) else str(v) for v in value
                    )
                    conditions.append(f"{column} IN ({values_str})")
                else:
                    conditions.append(f"{column} = {value}")

            sql_parts.append(f"WHERE {' AND '.join(conditions)}")

        # Add ORDER BY clause
        if order_by:
            sql_parts.append(f"ORDER BY {order_by}")

        # Add LIMIT clause
        sql_parts.append(f"LIMIT {limit}")

        return " ".join(sql_parts)

    # Example: Filter customers by region and status
    print("Dynamic SQL Generation:")
    print("=" * 80)

    filters = {"region": ["West", "East"], "status": "active", "account_value": 10000}

    sql = build_filtered_query(
        table="customers", filters=filters, order_by="account_value DESC", limit=50
    )

    print("Generated SQL:")
    print(f"  {sql}")
    print()

    # Note: In real usage, you would execute this query
    # result_df = container.query_executor.execute_query(sql)


def example_query_with_parameters() -> None:
    """
    Demonstrate parameterized queries for safety and reusability.
    """
    container = ApplicationContainer(role=Role.ANALYST)

    def execute_parameterized_query(start_date: str, end_date: str, min_amount: float) -> None:
        """Execute a parameterized query."""

        # Use f-strings for this example, but in production consider
        # using proper SQL parameter binding if available
        sql = f"""
        SELECT
            order_id,
            customer_id,
            order_date,
            total_amount
        FROM orders
        WHERE order_date BETWEEN '{start_date}' AND '{end_date}'
            AND total_amount >= {min_amount}
        ORDER BY total_amount DESC
        LIMIT 100
        """

        result_df = container.query_executor.execute_query(sql)

        print("Parameterized Query Results:")
        print(f"  Date range: {start_date} to {end_date}")
        print(f"  Min amount: ${min_amount:,.2f}")
        print(f"  Results: {len(result_df)} orders")
        print()

        if not result_df.empty:
            print(result_df.head(10).to_string(index=False))

    print("Parameterized Queries:")
    print("=" * 80)

    # Example usage
    # execute_parameterized_query(
    #     start_date="2024-01-01",
    #     end_date="2024-12-31",
    #     min_amount=5000.00
    # )


def example_performance_optimization() -> None:
    """
    Demonstrate query performance optimization techniques.
    """
    # Container available for actual execution (commented out in example)
    # container = ApplicationContainer(role=Role.ANALYST)  # noqa: F841

    print("Performance Optimization Examples:")
    print("=" * 80)

    # Example SQL patterns for optimization (not executed in this demo)
    # 1. Use column pruning - select only needed columns
    _optimized_sql = """
    SELECT id, name, created_at  -- Only select needed columns
    FROM large_table
    WHERE status = 'active'
    LIMIT 1000
    """

    # 2. Use predicate pushdown - filter early
    _pushdown_sql = """
    SELECT *
    FROM orders
    WHERE order_date >= CURRENT_DATE - INTERVAL 7 DAYS  -- Filter pushed down
        AND status = 'completed'
    LIMIT 1000
    """

    # 3. Use LIMIT to reduce data transfer
    _limited_sql = """
    SELECT *
    FROM large_table
    LIMIT 100  -- Limit rows returned
    """

    # 4. Use approximate aggregations for large datasets
    _approx_sql = """
    SELECT
        approx_count_distinct(customer_id) as unique_customers,
        approx_percentile(order_amount, 0.5) as median_amount
    FROM orders
    WHERE order_date >= CURRENT_DATE - INTERVAL 30 DAYS
    """

    print("Optimization Techniques:")
    print("  1. Column pruning - select only needed columns")
    print("  2. Predicate pushdown - filter early in the query")
    print("  3. Use LIMIT to reduce data transfer")
    print("  4. Use approximate aggregations for large datasets")
    print()

    # Note: In real usage, you would execute and compare these queries
    # result = container.query_executor.execute_query(optimized_sql)


if __name__ == "__main__":
    """
    Run all advanced examples.

    Note: You must have valid Databricks credentials and appropriate
    tables/data for these examples to work.
    """
    print("\n" + "=" * 80)
    print("DATABRICKS TOOLS MCP SERVER - ADVANCED QUERY EXAMPLES")
    print("=" * 80 + "\n")

    # Run examples (comment out as needed based on your data)
    # example_complex_join_query()
    # example_window_functions()
    # example_cte_query()
    # example_multi_workspace_query()  # Requires DEVELOPER role
    # example_chunked_response()
    example_dynamic_sql_generation()
    # example_query_with_parameters()
    example_performance_optimization()

    print("=" * 80)
    print("Advanced examples completed!")
    print("=" * 80 + "\n")
