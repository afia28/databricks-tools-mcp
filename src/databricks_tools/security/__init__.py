"""Security and access control for Databricks Tools MCP Server.

This package provides role-based access control (RBAC) functionality for managing
workspace permissions. It implements the Strategy pattern to support different
access control policies based on user roles.

The package exports:
- Role: Enum defining available user roles (ANALYST, DEVELOPER)
- RoleManager: Main interface for role-based access control
"""

from databricks_tools.security.role_manager import Role, RoleManager

__all__ = ["Role", "RoleManager"]
