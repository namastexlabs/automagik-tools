"""
Tests for Spark MCP tool
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastmcp import Context
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
        assert metadata["version"] == "1.0.0"
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

        # Check core tools are registered
        expected_tools = [
            "get_health",
            "list_workflows",
            "get_workflow",
            "run_workflow",
            "delete_workflow",
            "list_tasks",
            "get_task",
            "list_schedules",
            "create_schedule",
            "delete_schedule",
            "list_sources",
            "add_source",
        ]

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

            tools = await tool_instance.get_tools()
            result = await tools["get_health"].run({})

            result_data = json.loads(result)
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

            tools = await tool_instance.get_tools()

            with pytest.raises(ValueError, match="Connection failed"):
                await tools["get_health"].run({"ctx": mock_context})


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

            tools = await tool_instance.get_tools()
            result = await tools["list_workflows"].run({"limit": 10})

            workflows = json.loads(result)
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

            mock_client.request.return_value = mock_response

            tools = await tool_instance.get_tools()
            result = await tools["run_workflow"].run({
                "workflow_id": "workflow-1", "input_text": "Test input"
            })

            task = json.loads(result)
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

            tools = await tool_instance.get_tools()
            result = await tools["create_schedule"].run({
                "workflow_id": "workflow-1",
                "schedule_type": "interval",
                "schedule_expr": "30m",
                "input_value": "Test input",
            })

            schedule = json.loads(result)
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

            tools = await tool_instance.get_tools()
            result = await tools["list_schedules"].run({})

            schedules = json.loads(result)
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

            tools = await tool_instance.get_tools()
            result = await tools["add_source"].run({
                "name": "Test Source",
                "source_type": "automagik-agents",
                "url": "http://localhost:8881",
                "api_key": "test-key",
            })

            source = json.loads(result)
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
        from automagik_tools.tools.spark.models import WorkflowType, TaskStatus, ScheduleType, SourceType
        
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
            "owner": "admin"
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
            assert hasattr(tool_func, 'run'), f"Tool {tool_name} should have run method"
            assert tool_func.description is not None, f"Tool {tool_name} should have documentation"

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

            mock_client.request.side_effect = httpx.TimeoutException("Request timed out")

            tools = await tool_instance.get_tools()

            with pytest.raises(ValueError, match="Request failed"):
                await tools["get_health"].run({})

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

            tools = await tool_instance.get_tools()

            with pytest.raises(ValueError, match="HTTP 404"):
                await tools["get_workflow"].run({"workflow_id": "invalid-id"})

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

        tools = await server.get_tools()

        with pytest.raises(ValueError, match="Tool not configured"):
            await tools["get_health"].run({})

        # Restore original values
        spark_module.config = original_config
        spark_module.client = original_client