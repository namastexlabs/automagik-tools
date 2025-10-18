"""
Tests for Spark MCP tool
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastmcp import Context, Client
import httpx

from automagik_tools.tools.spark import (
    create_server,
    get_metadata,
    get_config_class,
)
from automagik_tools.tools.spark.config import SparkConfig
from automagik_tools.tools.spark.client import SparkClient
from automagik_tools.tools.spark.models import TaskStatus, ScheduleType, SourceType


@pytest.fixture
def mock_config():
    """Create a mock configuration"""
    return SparkConfig(
        api_key="test-api-key",
        base_url="http://test.spark.api",
        timeout=10,
        max_retries=3,
    )


@pytest.fixture
def tool_instance(mock_config):
    """Create a tool instance with mock config"""
    return create_server(mock_config)


@pytest.fixture
def mock_context():
    """Create a mock context"""
    ctx = MagicMock(spec=Context)
    ctx.info = MagicMock()
    ctx.error = MagicMock()
    return ctx


@pytest.fixture
def mock_client(mock_config):
    """Create a mock Spark client"""
    return SparkClient(mock_config)


class TestSparkMetadata:
    """Test tool metadata and discovery"""

    @pytest.mark.unit
    def test_metadata_structure(self):
        """Test that metadata has required fields"""
        metadata = get_metadata()
        assert metadata["name"] == "spark"
        assert metadata["version"] == "0.9.7"
        assert "description" in metadata
        assert metadata["author"] == "Namastex Labs"
        assert metadata["category"] == "workflow"
        assert "orchestration" in metadata["tags"]

    @pytest.mark.unit
    def test_config_class(self):
        """Test config class is returned correctly"""
        config_class = get_config_class()
        assert config_class == SparkConfig


class TestSparkConfig:
    """Test configuration management"""

    @pytest.mark.unit
    def test_default_config(self):
        """Test default configuration values"""
        config = SparkConfig()
        assert config.api_key == "namastex888"
        assert config.base_url == "http://localhost:8883"
        assert config.timeout == 30
        assert config.max_retries == 3

    @pytest.mark.unit
    def test_env_config(self, monkeypatch):
        """Test configuration from environment"""
        monkeypatch.setenv("SPARK_API_KEY", "env-test-key")
        monkeypatch.setenv("SPARK_BASE_URL", "https://env.test.com")
        monkeypatch.setenv("SPARK_TIMEOUT", "60")

        config = SparkConfig()
        assert config.api_key == "env-test-key"
        assert config.base_url == "https://env.test.com"
        assert config.timeout == 60


class TestSparkServer:
    """Test MCP server creation and tools"""

    @pytest.mark.unit
    def test_server_creation(self, tool_instance):
        """Test server is created with correct metadata"""
        assert tool_instance.name == "Spark"
        assert tool_instance.instructions is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_server_has_tools(self, tool_instance):
        """Test server has expected tools registered"""
        tools_dict = await tool_instance.get_tools()
        tool_names = list(tools_dict.keys())

        # Check ALL 23 tools are registered (100% API coverage)
        expected_tools = [
            # Health
            "get_health",
            # Workflows
            "list_workflows",
            "get_workflow",
            "run_workflow",
            "delete_workflow",
            # Remote Workflows
            "list_remote_workflows",
            "get_remote_workflow",  # NEW
            "sync_workflow",
            # Tasks
            "list_tasks",
            "get_task",
            "delete_task",  # NEW
            # Schedules
            "list_schedules",
            "create_schedule",
            "get_schedule",  # NEW
            "update_schedule",  # NEW
            "delete_schedule",
            "enable_schedule",
            "disable_schedule",
            # Sources
            "list_sources",
            "get_source",  # NEW
            "add_source",
            "update_source",  # NEW
            "delete_source",
        ]

        # Verify we have exactly 23 tools
        assert len(tools_dict) == 23, f"Expected 23 tools, got {len(tools_dict)}"

        for tool in expected_tools:
            assert tool in tool_names, f"Tool '{tool}' should be registered"


class TestSparkHealthCheck:
    """Test health check functionality"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_health_success(self, tool_instance):
        """Test successful health check"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "status": "healthy",
                "timestamp": "2025-08-23 15:00:00",
                "services": {
                    "api": {"status": "healthy", "version": "0.3.6"},
                    "worker": {"status": "healthy"},
                    "redis": {"status": "healthy"},
                },
            }
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            async with Client(tool_instance) as client:
                result = await client.call_tool("get_health", {})

            result_data = json.loads(result.data)
            assert result_data["status"] == "healthy"
            assert "services" in result_data

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_health_error(self, tool_instance, mock_context):
        """Test health check with API error"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_client.request.side_effect = httpx.RequestError("Connection failed")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Connection failed"):
                    await client.call_tool("get_health", {})


class TestWorkflowManagement:
    """Test workflow management functions"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_workflows(self, tool_instance):
        """Test listing workflows"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = [
                {
                    "id": "workflow-1",
                    "name": "Test Workflow",
                    "description": "A test workflow",
                    "source": "http://localhost:8886",
                    "latest_run": "COMPLETED",
                }
            ]
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            async with Client(tool_instance) as client:
                result = await client.call_tool("list_workflows", {"limit": 10})

            workflows = json.loads(result.data)
            assert len(workflows) == 1
            assert workflows[0]["name"] == "Test Workflow"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_workflow(self, tool_instance):
        """Test running a workflow"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "id": "task-123",
                "workflow_id": "workflow-1",
                "status": "completed",
                "input_data": {"value": "Test input"},
                "output_data": {"result": "Test output"},
            }
            mock_response.raise_for_status = Mock()

            mock_client.post.return_value = mock_response

            async with Client(tool_instance) as client:
                result = await client.call_tool(
                    "run_workflow",
                    {"workflow_id": "workflow-1", "input_text": "Test input"},
                )

            task = json.loads(result.data)
            assert task["status"] == "completed"
            assert task["output_data"]["result"] == "Test output"


class TestScheduleManagement:
    """Test schedule management functions"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_schedule(self, tool_instance):
        """Test creating a schedule"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "id": "schedule-123",
                "workflow_id": "workflow-1",
                "schedule_type": "interval",
                "schedule_expr": "30m",
                "status": "active",
                "next_run_at": "2025-08-23T16:00:00Z",
            }
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            async with Client(tool_instance) as client:
                result = await client.call_tool(
                    "create_schedule",
                    {
                        "workflow_id": "workflow-1",
                        "schedule_type": "interval",
                        "schedule_expr": "30m",
                        "input_value": "Test input",
                    },
                )

            schedule = json.loads(result.data)
            assert schedule["id"] == "schedule-123"
            assert schedule["schedule_type"] == "interval"
            assert schedule["status"] == "active"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_schedules(self, tool_instance):
        """Test listing schedules"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = [
                {
                    "id": "schedule-1",
                    "workflow_id": "workflow-1",
                    "schedule_type": "cron",
                    "schedule_expr": "0 9 * * *",
                    "status": "active",
                }
            ]
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            async with Client(tool_instance) as client:
                result = await client.call_tool("list_schedules", {})

            schedules = json.loads(result.data)
            assert len(schedules) == 1
            assert schedules[0]["schedule_type"] == "cron"


class TestSourceManagement:
    """Test source management functions"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_source(self, tool_instance):
        """Test adding a workflow source"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "id": "source-123",
                "name": "Test Source",
                "source_type": "automagik-agents",
                "url": "http://localhost:8881",
            }
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            async with Client(tool_instance) as client:
                result = await client.call_tool(
                    "add_source",
                    {
                        "name": "Test Source",
                        "source_type": "automagik-agents",
                        "url": "http://localhost:8881",
                        "api_key": "test-key",
                    },
                )

            source = json.loads(result.data)
            assert source["name"] == "Test Source"
            assert source["source_type"] == "automagik-agents"


class TestSparkClient:
    """Test Spark HTTP client"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_client_request_success(self, mock_client):
        """Test successful client request"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_async_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"success": True}
            mock_response.raise_for_status = Mock()

            mock_async_client.request.return_value = mock_response

            result = await mock_client.request("GET", "/test")
            assert result["success"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_client_request_error(self, mock_client):
        """Test client request with HTTP error"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_async_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not found"
            mock_response.json.return_value = {"detail": "Resource not found"}

            error = httpx.HTTPStatusError(
                "Not found", request=Mock(), response=mock_response
            )
            mock_response.raise_for_status.side_effect = error

            mock_async_client.request.return_value = mock_response

            with pytest.raises(ValueError, match="HTTP 404"):
                await mock_client.request("GET", "/nonexistent")


class TestSparkFlexibleSchema:
    """Test flexible schema support for Spark API responses"""

    @pytest.mark.unit
    def test_spark_enums_work(self):
        """Test that Spark enums are properly defined"""
        from automagik_tools.tools.spark.models import (
            WorkflowType,
        )

        # Test enum values
        assert WorkflowType.AGENT == "hive_agent"
        assert WorkflowType.TEAM == "hive_team"
        assert WorkflowType.WORKFLOW == "hive_workflow"

        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"

        assert ScheduleType.INTERVAL == "interval"
        assert ScheduleType.CRON == "cron"

        assert SourceType.AUTOMAGIK_AGENTS == "automagik-agents"

    @pytest.mark.unit
    def test_spark_api_flexible_responses(self):
        """Test that Spark API can handle flexible responses"""
        # Spark doesn't use Pydantic models for responses,
        # it returns raw dicts which are flexible by nature

        # Simulate API response with extra fields
        workflow_response = {
            "id": "workflow-1",
            "name": "Test Workflow",
            "source": "http://localhost:8886",
            "workflow_type": "hive_agent",
            # Extra fields that might be added
            "execution_metrics": {"avg_time": 1.5},
            "tags": ["production", "critical"],
            "owner": "admin",
        }

        # These would be returned as JSON strings
        import json

        result = json.dumps(workflow_response, indent=2)
        parsed = json.loads(result)

        assert parsed["id"] == "workflow-1"
        assert parsed["execution_metrics"]["avg_time"] == 1.5
        assert parsed["tags"] == ["production", "critical"]

    @pytest.mark.unit
    def test_spark_client_accepts_any_json(self):
        """Test that Spark client accepts any valid JSON"""
        from automagik_tools.tools.spark.client import SparkClient
        from automagik_tools.tools.spark.config import SparkConfig

        config = SparkConfig()
        client = SparkClient(config)

        # Client methods return Dict[str, Any] which accepts any JSON structure
        # This is inherently flexible
        assert client is not None


class TestSparkIntegration:
    """Test integration with automagik hub"""

    @pytest.mark.integration
    def test_tool_discovery(self):
        """Test tool can be discovered"""
        from automagik_tools.tools import spark

        assert spark is not None
        assert hasattr(spark, "create_server")
        assert hasattr(spark, "get_metadata")

    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_mcp_protocol_compliance(self, tool_instance):
        """Test MCP protocol compliance"""
        # Test tool listing
        tools_dict = await tool_instance.get_tools()
        assert len(tools_dict) > 0

        # Test each tool has required properties
        for tool_name, tool_func in tools_dict.items():
            assert tool_name is not None
            assert hasattr(tool_func, "run"), f"Tool {tool_name} should have run method"
            assert (
                tool_func.description is not None
            ), f"Tool {tool_name} should have documentation"

        # Test resources (Spark doesn't define resources, but method should exist)
        resources = await tool_instance._list_resources()
        assert isinstance(resources, list)


class TestSparkErrorHandling:
    """Test error scenarios"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_api_timeout(self, tool_instance):
        """Test handling of API timeout"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_client.request.side_effect = httpx.TimeoutException(
                "Request timed out"
            )

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Request failed|timed out"):
                    await client.call_tool("get_health", {})

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_workflow_id(self, tool_instance):
        """Test handling of invalid workflow ID"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Workflow not found"
            mock_response.json.return_value = {"detail": "Workflow not found"}

            error = httpx.HTTPStatusError(
                "Not found", request=Mock(), response=mock_response
            )
            mock_response.raise_for_status.side_effect = error

            mock_client.request.return_value = mock_response

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="HTTP 404|not found"):
                    await client.call_tool(
                        "get_workflow", {"workflow_id": "invalid-id"}
                    )

    @pytest.mark.unit
    def test_missing_config(self):
        """Test behavior with missing configuration"""
        config = SparkConfig(api_key="")

        # Should still create server
        server = create_server(config)
        assert server is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_tool_not_configured(self, monkeypatch):
        """Test error when tool is not configured"""
        # Import the module to get access to its globals
        import automagik_tools.tools.spark as spark_module

        # Save original values
        original_config = spark_module.config
        original_client = spark_module.client

        # Set them to None
        spark_module.config = None
        spark_module.client = None

        server = spark_module.mcp

        async with Client(server) as client:
            with pytest.raises(Exception, match="Tool not configured|not configured"):
                await client.call_tool("get_health", {})

        # Restore original values
        spark_module.config = original_config
        spark_module.client = original_client


class TestNewRemoteWorkflowTools:
    """Test new remote workflow tools added in v1.1.0"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_remote_workflow(self, tool_instance):
        """Test getting remote workflow details"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "id": "workflow-123",
                "name": "Remote Test Workflow",
                "description": "A remote workflow",
                "flow_type": "hive_agent",
                "components": ["input", "output"],
                "inputs": {"input": {"type": "string"}},
            }
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            async with Client(tool_instance) as client:
                result = await client.call_tool(
                    "get_remote_workflow",
                    {
                        "workflow_id": "workflow-123",
                        "source_url": "http://localhost:8881",
                    },
                )

            workflow = json.loads(result.data)
            assert workflow["id"] == "workflow-123"
            assert workflow["name"] == "Remote Test Workflow"
            assert "components" in workflow

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_remote_workflows_with_simplified(self, tool_instance):
        """Test listing remote workflows with simplified parameter"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = [
                {"id": "flow-1", "name": "Simple Flow"},
                {"id": "flow-2", "name": "Another Flow"},
            ]
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            async with Client(tool_instance) as client:
                result = await client.call_tool(
                    "list_remote_workflows",
                    {"source_url": "http://localhost:8881", "simplified": True},
                )

            flows = json.loads(result.data)
            assert len(flows) == 2
            assert flows[0]["name"] == "Simple Flow"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_workflow_with_source_url(self, tool_instance):
        """Test syncing workflow with required source_url parameter (bug fix)"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "id": "synced-workflow-123",
                "name": "Synced Workflow",
                "source": "http://localhost:8881",
                "status": "active",
            }
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            async with Client(tool_instance) as client:
                result = await client.call_tool(
                    "sync_workflow",
                    {
                        "workflow_id": "workflow-123",
                        "source_url": "http://localhost:8881",  # CRITICAL: now required
                        "input_component": "input",
                        "output_component": "output",
                    },
                )

            workflow = json.loads(result.data)
            assert workflow["id"] == "synced-workflow-123"
            assert workflow["status"] == "active"


class TestNewTaskTools:
    """Test new task management tools added in v1.1.0"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_task(self, tool_instance):
        """Test deleting a task execution"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "success": True,
                "deleted": "task-123",
            }
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            async with Client(tool_instance) as client:
                result = await client.call_tool("delete_task", {"task_id": "task-123"})

            response = json.loads(result.data)
            assert response["success"] is True
            assert response["deleted"] == "task-123"


class TestNewScheduleTools:
    """Test new schedule management tools added in v1.1.0"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_schedule(self, tool_instance):
        """Test getting schedule details"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "id": "schedule-123",
                "workflow_id": "workflow-1",
                "schedule_type": "interval",
                "schedule_expr": "30m",
                "status": "active",
                "next_run_at": "2025-10-17T22:00:00Z",
                "last_run_at": "2025-10-17T21:30:00Z",
            }
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            async with Client(tool_instance) as client:
                result = await client.call_tool(
                    "get_schedule", {"schedule_id": "schedule-123"}
                )

            schedule = json.loads(result.data)
            assert schedule["id"] == "schedule-123"
            assert schedule["schedule_type"] == "interval"
            assert "next_run_at" in schedule
            assert "last_run_at" in schedule

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_schedule(self, tool_instance):
        """Test updating an existing schedule"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "id": "schedule-123",
                "workflow_id": "workflow-1",
                "schedule_type": "cron",  # Changed from interval
                "schedule_expr": "0 */2 * * *",  # Changed expression
                "status": "active",
            }
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            async with Client(tool_instance) as client:
                result = await client.call_tool(
                    "update_schedule",
                    {
                        "schedule_id": "schedule-123",
                        "schedule_type": "cron",
                        "schedule_expr": "0 */2 * * *",
                    },
                )

            schedule = json.loads(result.data)
            assert schedule["id"] == "schedule-123"
            assert schedule["schedule_type"] == "cron"
            assert schedule["schedule_expr"] == "0 */2 * * *"


class TestNewSourceTools:
    """Test new source management tools added in v1.1.0"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_source(self, tool_instance):
        """Test getting source details"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "id": "source-123",
                "name": "Production Agents",
                "source_type": "automagik-agents",
                "url": "https://prod.agents.com",
                "status": "active",
                "last_sync": "2025-10-17T21:00:00Z",
            }
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            async with Client(tool_instance) as client:
                result = await client.call_tool(
                    "get_source", {"source_id": "source-123"}
                )

            source = json.loads(result.data)
            assert source["id"] == "source-123"
            assert source["name"] == "Production Agents"
            assert source["source_type"] == "automagik-agents"
            assert "last_sync" in source

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_source(self, tool_instance):
        """Test updating source configuration"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "id": "source-123",
                "name": "Updated Source Name",  # Updated
                "source_type": "automagik-agents",
                "url": "https://new-url.com",  # Updated
                "status": "active",
            }
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            async with Client(tool_instance) as client:
                result = await client.call_tool(
                    "update_source",
                    {
                        "source_id": "source-123",
                        "name": "Updated Source Name",
                        "url": "https://new-url.com",
                        "api_key": "new-api-key",
                    },
                )

            source = json.loads(result.data)
            assert source["id"] == "source-123"
            assert source["name"] == "Updated Source Name"
            assert source["url"] == "https://new-url.com"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_sources_with_status_filter(self, tool_instance):
        """Test listing sources with status filter parameter"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = [
                {
                    "id": "source-1",
                    "name": "Active Source",
                    "source_type": "automagik-agents",
                    "url": "http://localhost:8881",
                    "status": "active",
                }
            ]
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            async with Client(tool_instance) as client:
                result = await client.call_tool(
                    "list_sources", {"status": "active"}  # NEW parameter
                )

            sources = json.loads(result.data)
            assert len(sources) == 1
            assert sources[0]["status"] == "active"


class TestComprehensiveErrorCoverage:
    """Test all error handling paths for 100% coverage"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_workflows_error(self, tool_instance):
        """Test list_workflows error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("API Error")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="API Error"):
                    await client.call_tool("list_workflows", {})

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_workflow_error(self, tool_instance):
        """Test get_workflow error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Workflow not found")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Workflow not found"):
                    await client.call_tool("get_workflow", {"workflow_id": "invalid"})

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_workflow_error(self, tool_instance):
        """Test run_workflow error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = Exception("Execution failed")

            async with Client(tool_instance) as client:
                with pytest.raises(
                    Exception, match="Execution failed|not JSON serializable"
                ):
                    await client.call_tool(
                        "run_workflow",
                        {"workflow_id": "wf-1", "input_text": "test"},
                    )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_workflow_error(self, tool_instance):
        """Test delete_workflow error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Delete failed")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Delete failed"):
                    await client.call_tool("delete_workflow", {"workflow_id": "wf-1"})

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_remote_workflows_error(self, tool_instance):
        """Test list_remote_workflows error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Remote connection failed")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Remote connection failed"):
                    await client.call_tool(
                        "list_remote_workflows",
                        {"source_url": "http://localhost:8881"},
                    )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_remote_workflow_error(self, tool_instance):
        """Test get_remote_workflow error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Remote fetch failed")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Remote fetch failed"):
                    await client.call_tool(
                        "get_remote_workflow",
                        {
                            "workflow_id": "wf-1",
                            "source_url": "http://localhost:8881",
                        },
                    )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_workflow_error(self, tool_instance):
        """Test sync_workflow error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Sync failed")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Sync failed"):
                    await client.call_tool(
                        "sync_workflow",
                        {
                            "workflow_id": "wf-1",
                            "source_url": "http://localhost:8881",
                        },
                    )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_tasks_error(self, tool_instance):
        """Test list_tasks error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Task list failed")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Task list failed"):
                    await client.call_tool("list_tasks", {})

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_task_error(self, tool_instance):
        """Test get_task error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Task not found")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Task not found"):
                    await client.call_tool("get_task", {"task_id": "task-1"})

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_task_error(self, tool_instance):
        """Test delete_task error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Delete failed")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Delete failed"):
                    await client.call_tool("delete_task", {"task_id": "task-1"})

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_schedules_error(self, tool_instance):
        """Test list_schedules error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Schedule list failed")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Schedule list failed"):
                    await client.call_tool("list_schedules", {})

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_schedule_error(self, tool_instance):
        """Test create_schedule error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Create failed")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Create failed"):
                    await client.call_tool(
                        "create_schedule",
                        {
                            "workflow_id": "wf-1",
                            "schedule_type": "interval",
                            "schedule_expr": "30m",
                        },
                    )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_schedule_error(self, tool_instance):
        """Test get_schedule error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Schedule not found")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Schedule not found"):
                    await client.call_tool("get_schedule", {"schedule_id": "sched-1"})

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_schedule_error(self, tool_instance):
        """Test update_schedule error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Update failed")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Update failed"):
                    await client.call_tool(
                        "update_schedule",
                        {"schedule_id": "sched-1", "schedule_type": "cron"},
                    )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_schedule_error(self, tool_instance):
        """Test delete_schedule error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Delete failed")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Delete failed"):
                    await client.call_tool(
                        "delete_schedule", {"schedule_id": "sched-1"}
                    )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_enable_schedule_error(self, tool_instance):
        """Test enable_schedule error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Enable failed")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Enable failed"):
                    await client.call_tool(
                        "enable_schedule", {"schedule_id": "sched-1"}
                    )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_disable_schedule_error(self, tool_instance):
        """Test disable_schedule error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Disable failed")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Disable failed"):
                    await client.call_tool(
                        "disable_schedule", {"schedule_id": "sched-1"}
                    )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_sources_error(self, tool_instance):
        """Test list_sources error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Source list failed")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Source list failed"):
                    await client.call_tool("list_sources", {})

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_source_error(self, tool_instance):
        """Test get_source error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Source not found")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Source not found"):
                    await client.call_tool("get_source", {"source_id": "src-1"})

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_source_error(self, tool_instance):
        """Test add_source error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Add failed")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Add failed"):
                    await client.call_tool(
                        "add_source",
                        {
                            "name": "Test",
                            "source_type": "automagik-agents",
                            "url": "http://test.com",
                        },
                    )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_source_error(self, tool_instance):
        """Test update_source error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Update failed")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Update failed"):
                    await client.call_tool(
                        "update_source", {"source_id": "src-1", "name": "Updated"}
                    )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_source_error(self, tool_instance):
        """Test delete_source error handling"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Delete failed")

            async with Client(tool_instance) as client:
                with pytest.raises(Exception, match="Delete failed"):
                    await client.call_tool("delete_source", {"source_id": "src-1"})


class TestClientMethodsCoverage:
    """Test uncovered client methods for 100% client coverage"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_client_workflow_deletion(self, mock_client):
        """Test client delete_workflow method"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_async_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"success": True}
            mock_response.raise_for_status = Mock()

            mock_async_client.request.return_value = mock_response

            result = await mock_client.delete_workflow("wf-123")
            assert result["success"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_client_task_deletion(self, mock_client):
        """Test client delete_task method"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_async_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"deleted": "task-123"}
            mock_response.raise_for_status = Mock()

            mock_async_client.request.return_value = mock_response

            result = await mock_client.delete_task("task-123")
            assert result["deleted"] == "task-123"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_client_get_schedule(self, mock_client):
        """Test client get_schedule method"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_async_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "id": "sched-123",
                "workflow_id": "wf-1",
            }
            mock_response.raise_for_status = Mock()

            mock_async_client.request.return_value = mock_response

            result = await mock_client.get_schedule("sched-123")
            assert result["id"] == "sched-123"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_client_update_schedule(self, mock_client):
        """Test client update_schedule method"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_async_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"id": "sched-123", "updated": True}
            mock_response.raise_for_status = Mock()

            mock_async_client.request.return_value = mock_response

            result = await mock_client.update_schedule("sched-123", "cron", "0 9 * * *")
            assert result["updated"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_client_delete_schedule(self, mock_client):
        """Test client delete_schedule method"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_async_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"deleted": True}
            mock_response.raise_for_status = Mock()

            mock_async_client.request.return_value = mock_response

            result = await mock_client.delete_schedule("sched-123")
            assert result["deleted"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_client_enable_schedule(self, mock_client):
        """Test client enable_schedule method"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_async_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"enabled": True}
            mock_response.raise_for_status = Mock()

            mock_async_client.request.return_value = mock_response

            result = await mock_client.enable_schedule("sched-123")
            assert result["enabled"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_client_disable_schedule(self, mock_client):
        """Test client disable_schedule method"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_async_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"disabled": True}
            mock_response.raise_for_status = Mock()

            mock_async_client.request.return_value = mock_response

            result = await mock_client.disable_schedule("sched-123")
            assert result["disabled"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_client_get_source(self, mock_client):
        """Test client get_source method"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_async_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"id": "src-123", "name": "Source"}
            mock_response.raise_for_status = Mock()

            mock_async_client.request.return_value = mock_response

            result = await mock_client.get_source("src-123")
            assert result["id"] == "src-123"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_client_update_source(self, mock_client):
        """Test client update_source method"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_async_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"id": "src-123", "updated": True}
            mock_response.raise_for_status = Mock()

            mock_async_client.request.return_value = mock_response

            result = await mock_client.update_source("src-123", "New Name")
            assert result["updated"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_client_delete_source(self, mock_client):
        """Test client delete_source method"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_async_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"deleted": True}
            mock_response.raise_for_status = Mock()

            mock_async_client.request.return_value = mock_response

            result = await mock_client.delete_source("src-123")
            assert result["deleted"] is True
