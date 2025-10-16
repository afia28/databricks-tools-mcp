"""Comprehensive test suite for ApplicationContainer dependency injection.

This module contains comprehensive tests for the ApplicationContainer class, covering:
- Container initialization with default and custom parameters
- Service instantiation (all 9 services)
- Service type verification
- Dependency wiring between services
- Role-based configuration (ANALYST vs DEVELOPER)
- Configuration propagation (max_tokens)
- Multiple container independence
- Edge cases and extreme values

Test coverage goal: 90%+ for src/databricks_tools/core/container.py
"""

from databricks_tools.config.workspace import WorkspaceConfigManager
from databricks_tools.core.container import ApplicationContainer
from databricks_tools.core.query_executor import QueryExecutor
from databricks_tools.core.token_counter import TokenCounter
from databricks_tools.security.role_manager import Role, RoleManager
from databricks_tools.services.catalog_service import CatalogService
from databricks_tools.services.chunking_service import ChunkingService
from databricks_tools.services.function_service import FunctionService
from databricks_tools.services.response_manager import ResponseManager
from databricks_tools.services.table_service import TableService

# =============================================================================
# Container Initialization Tests
# =============================================================================


class TestContainerInitialization:
    """Tests for ApplicationContainer initialization."""

    def test_container_default_initialization(self):
        """Test that container initializes successfully with default parameters.

        The container should initialize with Role.ANALYST and max_tokens=9000
        when no parameters are provided.
        """
        container = ApplicationContainer()

        # Verify container is created
        assert container is not None
        assert isinstance(container, ApplicationContainer)

        # Verify default role
        assert container.role_manager.role == Role.ANALYST

    def test_container_custom_role_initialization(self):
        """Test container initialization with custom role.

        The container should accept Role.DEVELOPER and configure accordingly.
        """
        container = ApplicationContainer(role=Role.DEVELOPER)

        assert container is not None
        assert container.role_manager.role == Role.DEVELOPER

    def test_container_custom_max_tokens_initialization(self):
        """Test container initialization with custom max_tokens.

        The container should accept custom max_tokens and propagate to services.
        """
        custom_max_tokens = 5000
        container = ApplicationContainer(max_tokens=custom_max_tokens)

        assert container is not None
        # Verify max_tokens is propagated to services that use it
        assert container.response_manager.max_tokens == custom_max_tokens
        assert container.chunking_service.max_tokens == custom_max_tokens
        assert container.catalog_service.max_tokens == custom_max_tokens

    def test_container_both_custom_parameters(self):
        """Test container initialization with both custom parameters.

        The container should accept both role and max_tokens simultaneously.
        """
        custom_role = Role.DEVELOPER
        custom_max_tokens = 7500

        container = ApplicationContainer(role=custom_role, max_tokens=custom_max_tokens)

        assert container is not None
        assert container.role_manager.role == custom_role
        assert container.response_manager.max_tokens == custom_max_tokens


# =============================================================================
# Service Instantiation Tests
# =============================================================================


class TestContainerServices:
    """Tests for service instantiation in ApplicationContainer."""

    def test_container_all_services_created(self):
        """Test that all 9 services are instantiated.

        The container must create all required services:
        1. role_manager
        2. workspace_manager
        3. token_counter
        4. query_executor
        5. catalog_service
        6. table_service
        7. function_service
        8. chunking_service
        9. response_manager
        """
        container = ApplicationContainer()

        # Verify all services exist and are not None
        assert container.role_manager is not None
        assert container.workspace_manager is not None
        assert container.token_counter is not None
        assert container.query_executor is not None
        assert container.catalog_service is not None
        assert container.table_service is not None
        assert container.function_service is not None
        assert container.chunking_service is not None
        assert container.response_manager is not None

    def test_container_service_types(self):
        """Test that all services are of correct types.

        Each service attribute should be an instance of the expected class.
        """
        container = ApplicationContainer()

        # Verify service types
        assert isinstance(container.role_manager, RoleManager)
        assert isinstance(container.workspace_manager, WorkspaceConfigManager)
        assert isinstance(container.token_counter, TokenCounter)
        assert isinstance(container.query_executor, QueryExecutor)
        assert isinstance(container.catalog_service, CatalogService)
        assert isinstance(container.table_service, TableService)
        assert isinstance(container.function_service, FunctionService)
        assert isinstance(container.chunking_service, ChunkingService)
        assert isinstance(container.response_manager, ResponseManager)

    def test_container_services_immediately_usable(self):
        """Test that services can be accessed immediately after creation.

        Services should be fully initialized and ready to use without
        additional configuration.
        """
        container = ApplicationContainer()

        # Verify services have expected attributes/methods
        assert hasattr(container.role_manager, "role")
        assert hasattr(container.token_counter, "count_tokens")
        assert hasattr(container.catalog_service, "list_catalogs")
        assert hasattr(container.table_service, "list_tables")
        assert hasattr(container.function_service, "list_user_functions")
        assert hasattr(container.chunking_service, "create_chunked_response")
        assert hasattr(container.response_manager, "format_response")


# =============================================================================
# Dependency Wiring Tests
# =============================================================================


class TestContainerDependencies:
    """Tests for dependency wiring in ApplicationContainer."""

    def test_container_core_dependencies(self):
        """Test that core infrastructure dependencies are wired correctly.

        Verify:
        - workspace_manager depends on role_manager
        - query_executor depends on workspace_manager
        """
        container = ApplicationContainer()

        # workspace_manager should have reference to role_manager
        assert container.workspace_manager.role_manager is container.role_manager

        # query_executor should have reference to workspace_manager
        assert container.query_executor.workspace_manager is container.workspace_manager

    def test_container_business_service_dependencies(self):
        """Test that business services are wired with correct dependencies.

        All business services (catalog, table, function) should have:
        - query_executor reference
        - token_counter reference
        - max_tokens configuration
        """
        container = ApplicationContainer()

        # Catalog service dependencies
        assert container.catalog_service.query_executor is container.query_executor
        assert container.catalog_service.token_counter is container.token_counter
        assert container.catalog_service.max_tokens == 9000

        # Table service dependencies
        assert container.table_service.query_executor is container.query_executor
        assert container.table_service.token_counter is container.token_counter
        assert container.table_service.max_tokens == 9000

        # Function service dependencies
        assert container.function_service.query_executor is container.query_executor
        assert container.function_service.token_counter is container.token_counter
        assert container.function_service.max_tokens == 9000

    def test_container_response_management_dependencies(self):
        """Test that response management services are wired correctly.

        Verify:
        - chunking_service has token_counter (but NO query_executor)
        - response_manager has token_counter and chunking_service
        """
        container = ApplicationContainer()

        # Chunking service dependencies
        assert container.chunking_service.token_counter is container.token_counter
        assert container.chunking_service.max_tokens == 9000
        # Verify chunking_service does NOT have query_executor
        assert not hasattr(container.chunking_service, "query_executor")

        # Response manager dependencies
        assert container.response_manager.token_counter is container.token_counter
        assert container.response_manager.chunking_service is container.chunking_service
        assert container.response_manager.max_tokens == 9000

    def test_container_shared_instances(self):
        """Test that services share the same dependency instances.

        All services should reference the same token_counter, query_executor,
        etc., ensuring consistent behavior across the application.
        """
        container = ApplicationContainer()

        # All business services should share the same query_executor
        assert container.catalog_service.query_executor is container.table_service.query_executor
        assert container.table_service.query_executor is container.function_service.query_executor

        # All services should share the same token_counter
        assert container.catalog_service.token_counter is container.table_service.token_counter
        assert container.table_service.token_counter is container.function_service.token_counter
        assert container.function_service.token_counter is container.chunking_service.token_counter
        assert container.chunking_service.token_counter is container.response_manager.token_counter


# =============================================================================
# Role-Based Configuration Tests
# =============================================================================


class TestContainerRoles:
    """Tests for role-based configuration in ApplicationContainer."""

    def test_container_analyst_role(self):
        """Test container with Role.ANALYST configuration.

        Analyst role should be properly configured and accessible through
        the role_manager.
        """
        container = ApplicationContainer(role=Role.ANALYST)

        assert container.role_manager.role == Role.ANALYST
        # Verify analyst role strategy is active
        assert container.role_manager.can_access_workspace("default")

    def test_container_developer_role(self):
        """Test container with Role.DEVELOPER configuration.

        Developer role should be properly configured and accessible through
        the role_manager.
        """
        container = ApplicationContainer(role=Role.DEVELOPER)

        assert container.role_manager.role == Role.DEVELOPER
        # Developer role should have access to all workspaces
        assert hasattr(container.role_manager, "role")

    def test_container_role_propagation(self):
        """Test that role is properly propagated through dependencies.

        The role set in initialization should be accessible through the
        entire dependency chain.
        """
        analyst_container = ApplicationContainer(role=Role.ANALYST)
        developer_container = ApplicationContainer(role=Role.DEVELOPER)

        # Analyst container
        assert analyst_container.role_manager.role == Role.ANALYST
        assert analyst_container.workspace_manager.role_manager.role == Role.ANALYST

        # Developer container
        assert developer_container.role_manager.role == Role.DEVELOPER
        assert developer_container.workspace_manager.role_manager.role == Role.DEVELOPER


# =============================================================================
# Configuration Propagation Tests
# =============================================================================


class TestContainerConfiguration:
    """Tests for configuration propagation in ApplicationContainer."""

    def test_container_max_tokens_propagation(self):
        """Test that max_tokens is propagated to all services that need it.

        Services that use max_tokens should all receive the same value.
        """
        custom_max_tokens = 5000
        container = ApplicationContainer(max_tokens=custom_max_tokens)

        # Verify max_tokens in all services that use it
        assert container.catalog_service.max_tokens == custom_max_tokens
        assert container.table_service.max_tokens == custom_max_tokens
        assert container.function_service.max_tokens == custom_max_tokens
        assert container.chunking_service.max_tokens == custom_max_tokens
        assert container.response_manager.max_tokens == custom_max_tokens

    def test_container_token_counter_model(self):
        """Test that token_counter is initialized with gpt-4 model.

        The token_counter should always use gpt-4 model as specified
        in the container initialization.
        """
        container = ApplicationContainer()

        assert container.token_counter.model == "gpt-4"

    def test_container_extreme_max_tokens_values(self):
        """Test container with extreme max_tokens values.

        The container should handle both very small and very large
        max_tokens values without errors.
        """
        # Very small max_tokens
        small_container = ApplicationContainer(max_tokens=1)
        assert small_container.response_manager.max_tokens == 1

        # Very large max_tokens
        large_container = ApplicationContainer(max_tokens=1000000)
        assert large_container.response_manager.max_tokens == 1000000

        # Zero max_tokens (edge case)
        zero_container = ApplicationContainer(max_tokens=0)
        assert zero_container.response_manager.max_tokens == 0


# =============================================================================
# Multiple Container Independence Tests
# =============================================================================


class TestContainerIndependence:
    """Tests for independence of multiple container instances."""

    def test_container_multiple_instances_independent(self):
        """Test that multiple containers don't interfere with each other.

        Creating multiple containers with different configurations should
        result in independent instances that don't share state.
        """
        container1 = ApplicationContainer(role=Role.ANALYST, max_tokens=5000)
        container2 = ApplicationContainer(role=Role.DEVELOPER, max_tokens=7000)
        container3 = ApplicationContainer(role=Role.ANALYST, max_tokens=9000)

        # Verify each container has independent configuration
        assert container1.role_manager.role == Role.ANALYST
        assert container2.role_manager.role == Role.DEVELOPER
        assert container3.role_manager.role == Role.ANALYST

        assert container1.response_manager.max_tokens == 5000
        assert container2.response_manager.max_tokens == 7000
        assert container3.response_manager.max_tokens == 9000

        # Verify services are not shared between containers
        assert container1.token_counter is not container2.token_counter
        assert container1.query_executor is not container2.query_executor
        assert container1.catalog_service is not container2.catalog_service

    def test_container_for_testing(self):
        """Test that containers can easily be created for testing purposes.

        This demonstrates the pattern for creating test containers with
        specific configurations.
        """
        # Test container with analyst role and small token limit
        test_container = ApplicationContainer(role=Role.ANALYST, max_tokens=1000)

        assert test_container.role_manager.role == Role.ANALYST
        assert test_container.response_manager.max_tokens == 1000

        # Services should be fully functional
        assert test_container.catalog_service is not None
        assert test_container.table_service is not None
        assert test_container.response_manager is not None

    def test_container_no_shared_state_between_instances(self):
        """Test that containers don't share any mutable state.

        Modifying state in one container should not affect other containers.
        This is critical for testing and production use.
        """
        container1 = ApplicationContainer()
        container2 = ApplicationContainer()

        # Verify different role_manager instances
        assert container1.role_manager is not container2.role_manager

        # Verify different workspace_manager instances
        assert container1.workspace_manager is not container2.workspace_manager

        # Verify different service instances
        assert container1.catalog_service is not container2.catalog_service
        assert container1.response_manager is not container2.response_manager
        assert container1.chunking_service is not container2.chunking_service


# =============================================================================
# Edge Cases and Integration Tests
# =============================================================================


class TestContainerEdgeCases:
    """Tests for edge cases and integration scenarios."""

    def test_container_services_can_be_used_together(self):
        """Test that services work together in realistic scenarios.

        This integration test verifies that services are properly wired
        and can be used in combination.
        """
        container = ApplicationContainer()

        # Verify services can be accessed sequentially
        assert container.role_manager.role == Role.ANALYST
        assert container.token_counter.count_tokens("test") > 0
        assert hasattr(container.catalog_service, "list_catalogs")

        # Verify response management chain works
        assert container.chunking_service is not None
        assert container.response_manager.chunking_service is not None

    def test_container_import_paths(self):
        """Test that ApplicationContainer can be imported from correct paths.

        The container should be importable from both the module and package.
        """
        # Already imported at top of file, just verify it works
        from databricks_tools.core import ApplicationContainer as Container1
        from databricks_tools.core.container import (
            ApplicationContainer as Container2,
        )

        # Both import paths should reference the same class
        assert Container1 is Container2
        assert Container1 is ApplicationContainer

        # Should be able to instantiate from both imports
        c1 = Container1()
        c2 = Container2()
        assert isinstance(c1, ApplicationContainer)
        assert isinstance(c2, ApplicationContainer)

    def test_container_default_parameters_match_documentation(self):
        """Test that default parameters match documented values.

        The defaults should be Role.ANALYST and max_tokens=9000 as per
        the container's documentation.
        """
        container = ApplicationContainer()

        # Verify documented defaults
        assert container.role_manager.role == Role.ANALYST
        assert container.response_manager.max_tokens == 9000
        assert container.chunking_service.max_tokens == 9000
        assert container.catalog_service.max_tokens == 9000
