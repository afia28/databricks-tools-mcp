"""
Custom Service Implementation Example

This module demonstrates how to create custom services that extend
the databricks-tools framework. It shows:
- Creating a new service class
- Using dependency injection
- Following the service layer pattern
- Writing testable code
- Best practices for extending the framework
"""

from typing import Any

import pandas as pd

from databricks_tools.core.container import ApplicationContainer
from databricks_tools.core.query_executor import QueryExecutor
from databricks_tools.core.token_counter import TokenCounter
from databricks_tools.security.role_manager import Role


class MetricsService:
    """
    Custom service for calculating and reporting table metrics.

    This service demonstrates how to create a new business logic service
    that integrates with the existing framework.

    Attributes:
        token_counter: Token counting utility for response estimation
        query_executor: Query executor for database operations
    """

    def __init__(
        self,
        token_counter: TokenCounter,
        query_executor: QueryExecutor,
    ):
        """
        Initialize the MetricsService.

        Args:
            token_counter: Token counting utility
            query_executor: Query executor for database access
        """
        self.token_counter = token_counter
        self.query_executor = query_executor

    def get_table_statistics(
        self, catalog: str, schema: str, table: str, workspace: str = "default"
    ) -> dict[str, Any]:
        """
        Get comprehensive statistics for a table.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            workspace: Workspace name (default: "default")

        Returns:
            Dictionary containing table statistics including:
            - row_count: Total number of rows
            - column_count: Total number of columns
            - size_bytes: Approximate size in bytes
            - last_modified: Last modification timestamp
            - columns: List of column names and types

        Example:
            >>> service = MetricsService(token_counter, query_executor)
            >>> stats = service.get_table_statistics("main", "default", "orders")
            >>> print(f"Table has {stats['row_count']} rows")
        """
        full_table_name = f"{catalog}.{schema}.{table}"

        # Get row count
        row_count_sql = f"SELECT COUNT(*) as count FROM {full_table_name}"
        row_count_df = self.query_executor.execute_query(row_count_sql, workspace)
        row_count = int(row_count_df.iloc[0]["count"])

        # Get column information
        columns_sql = f"DESCRIBE TABLE {full_table_name}"
        columns_df = self.query_executor.execute_query(columns_sql, workspace)

        # Get table details from information schema
        details_sql = f"""
        SELECT
            table_catalog,
            table_schema,
            table_name,
            table_type,
            created
        FROM information_schema.tables
        WHERE table_catalog = '{catalog}'
            AND table_schema = '{schema}'
            AND table_name = '{table}'
        """
        details_df = self.query_executor.execute_query(details_sql, workspace)

        # Build response
        return {
            "catalog": catalog,
            "schema": schema,
            "table": table,
            "row_count": row_count,
            "column_count": len(columns_df),
            "columns": columns_df.to_dict("records"),
            "table_type": details_df.iloc[0]["table_type"] if not details_df.empty else "UNKNOWN",
            "created": str(details_df.iloc[0]["created"]) if not details_df.empty else None,
        }

    def get_column_statistics(
        self, catalog: str, schema: str, table: str, column: str, workspace: str = "default"
    ) -> dict[str, Any]:
        """
        Get statistics for a specific column.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            column: Column name
            workspace: Workspace name

        Returns:
            Dictionary containing column statistics:
            - distinct_count: Number of distinct values
            - null_count: Number of null values
            - min_value: Minimum value (for numeric/date columns)
            - max_value: Maximum value (for numeric/date columns)
            - avg_value: Average value (for numeric columns)
        """
        full_table_name = f"{catalog}.{schema}.{table}"

        sql = f"""
        SELECT
            COUNT(DISTINCT {column}) as distinct_count,
            SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END) as null_count,
            MIN({column}) as min_value,
            MAX({column}) as max_value,
            AVG({column}) as avg_value
        FROM {full_table_name}
        """

        result_df = self.query_executor.execute_query(sql, workspace)
        row = result_df.iloc[0]

        return {
            "catalog": catalog,
            "schema": schema,
            "table": table,
            "column": column,
            "distinct_count": int(row["distinct_count"]) if pd.notna(row["distinct_count"]) else 0,
            "null_count": int(row["null_count"]) if pd.notna(row["null_count"]) else 0,
            "min_value": row["min_value"] if pd.notna(row["min_value"]) else None,
            "max_value": row["max_value"] if pd.notna(row["max_value"]) else None,
            "avg_value": float(row["avg_value"]) if pd.notna(row["avg_value"]) else None,
        }

    def compare_tables(
        self, table1: tuple[str, str, str], table2: tuple[str, str, str], workspace: str = "default"
    ) -> dict[str, Any]:
        """
        Compare two tables and return differences.

        Args:
            table1: Tuple of (catalog, schema, table) for first table
            table2: Tuple of (catalog, schema, table) for second table
            workspace: Workspace name

        Returns:
            Dictionary containing comparison results:
            - row_count_diff: Difference in row counts
            - column_diff: Columns present in one but not the other
            - schema_diff: Schema differences
        """
        cat1, schema1, table1_name = table1
        cat2, schema2, table2_name = table2

        # Get stats for both tables
        stats1 = self.get_table_statistics(cat1, schema1, table1_name, workspace)
        stats2 = self.get_table_statistics(cat2, schema2, table2_name, workspace)

        # Compare row counts
        row_count_diff = stats1["row_count"] - stats2["row_count"]

        # Compare columns
        cols1 = {col["col_name"] for col in stats1["columns"]}
        cols2 = {col["col_name"] for col in stats2["columns"]}

        cols_only_in_1 = list(cols1 - cols2)
        cols_only_in_2 = list(cols2 - cols1)
        common_cols = list(cols1 & cols2)

        return {
            "table1": f"{cat1}.{schema1}.{table1_name}",
            "table2": f"{cat2}.{schema2}.{table2_name}",
            "row_count_diff": row_count_diff,
            "table1_rows": stats1["row_count"],
            "table2_rows": stats2["row_count"],
            "columns_only_in_table1": cols_only_in_1,
            "columns_only_in_table2": cols_only_in_2,
            "common_columns": common_cols,
            "column_count_diff": len(cols1) - len(cols2),
        }


class DataQualityService:
    """
    Custom service for data quality checks.

    This demonstrates another pattern for custom services with
    more complex business logic.
    """

    def __init__(
        self,
        token_counter: TokenCounter,
        query_executor: QueryExecutor,
    ):
        """Initialize the DataQualityService."""
        self.token_counter = token_counter
        self.query_executor = query_executor

    def check_data_freshness(
        self,
        catalog: str,
        schema: str,
        table: str,
        date_column: str,
        max_age_hours: int = 24,
        workspace: str = "default",
    ) -> dict[str, Any]:
        """
        Check if data is fresh (recently updated).

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            date_column: Column containing timestamp/date
            max_age_hours: Maximum acceptable age in hours
            workspace: Workspace name

        Returns:
            Dictionary containing freshness check results
        """
        full_table_name = f"{catalog}.{schema}.{table}"

        sql = f"""
        SELECT
            MAX({date_column}) as latest_timestamp,
            TIMESTAMPDIFF(HOUR, MAX({date_column}), CURRENT_TIMESTAMP) as hours_old
        FROM {full_table_name}
        """

        result_df = self.query_executor.execute_query(sql, workspace)
        row = result_df.iloc[0]

        hours_old = float(row["hours_old"]) if pd.notna(row["hours_old"]) else None
        is_fresh = hours_old is not None and hours_old <= max_age_hours

        return {
            "table": full_table_name,
            "latest_timestamp": (
                str(row["latest_timestamp"]) if pd.notna(row["latest_timestamp"]) else None
            ),
            "hours_old": hours_old,
            "max_age_hours": max_age_hours,
            "is_fresh": is_fresh,
            "status": "PASS" if is_fresh else "FAIL",
        }

    def check_null_percentage(
        self,
        catalog: str,
        schema: str,
        table: str,
        columns: list[str],
        max_null_percentage: float = 5.0,
        workspace: str = "default",
    ) -> dict[str, Any]:
        """
        Check null percentage for specified columns.

        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            columns: List of column names to check
            max_null_percentage: Maximum acceptable null percentage
            workspace: Workspace name

        Returns:
            Dictionary containing null check results for each column
        """
        full_table_name = f"{catalog}.{schema}.{table}"

        # Build SQL to check nulls for all columns
        null_checks = [
            f"SUM(CASE WHEN {col} IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as {col}_null_pct"
            for col in columns
        ]

        sql = f"""
        SELECT {", ".join(null_checks)}
        FROM {full_table_name}
        """

        result_df = self.query_executor.execute_query(sql, workspace)
        row = result_df.iloc[0]

        results = {}
        all_passed = True

        for col in columns:
            null_pct = float(row[f"{col}_null_pct"]) if pd.notna(row[f"{col}_null_pct"]) else 0.0
            passed = null_pct <= max_null_percentage

            results[col] = {
                "null_percentage": round(null_pct, 2),
                "max_allowed": max_null_percentage,
                "status": "PASS" if passed else "FAIL",
            }

            if not passed:
                all_passed = False

        return {
            "table": full_table_name,
            "columns_checked": columns,
            "results": results,
            "overall_status": "PASS" if all_passed else "FAIL",
        }


def example_custom_service_usage() -> None:
    """Demonstrate using custom services."""
    # Create container
    container = ApplicationContainer(role=Role.ANALYST)

    # Create custom service with dependency injection
    _metrics_service = MetricsService(
        token_counter=container.token_counter,
        query_executor=container.query_executor,
    )

    print("Custom Service Example - Table Metrics:")
    print("=" * 80)

    # Use the custom service
    # stats = metrics_service.get_table_statistics("main", "default", "orders")
    # print(f"Table: {stats['catalog']}.{stats['schema']}.{stats['table']}")
    # print(f"Rows: {stats['row_count']:,}")
    # print(f"Columns: {stats['column_count']}")
    # print()


def example_extending_container() -> None:
    """
    Demonstrate how to extend ApplicationContainer with custom services.
    """

    class ExtendedContainer(ApplicationContainer):
        """Extended container with custom services."""

        def __init__(self, role: Role = Role.ANALYST, max_tokens: int = 9000):
            # Initialize base container
            super().__init__(role, max_tokens)

            # Add custom services
            self.metrics_service = MetricsService(
                self.token_counter,
                self.query_executor,
            )

            self.data_quality_service = DataQualityService(
                self.token_counter,
                self.query_executor,
            )

    print("Extended Container Example:")
    print("=" * 80)

    # Create extended container
    extended_container = ExtendedContainer(role=Role.ANALYST)

    # Use custom services
    print("Available services:")
    print(f"  • metrics_service: {extended_container.metrics_service.__class__.__name__}")
    print(f"  • data_quality_service: {extended_container.data_quality_service.__class__.__name__}")
    print()

    # Example usage
    # stats = extended_container.metrics_service.get_table_statistics(
    #     "main", "default", "orders"
    # )
    # quality = extended_container.data_quality_service.check_data_freshness(
    #     "main", "default", "orders", "order_date"
    # )


if __name__ == "__main__":
    """
    Run custom service examples.
    """
    print("\n" + "=" * 80)
    print("DATABRICKS TOOLS MCP SERVER - CUSTOM SERVICE EXAMPLES")
    print("=" * 80 + "\n")

    example_custom_service_usage()
    example_extending_container()

    print("=" * 80)
    print("Custom service examples completed!")
    print("=" * 80 + "\n")
