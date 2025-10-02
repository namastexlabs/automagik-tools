"""Edge case tests for Spark MCP tool"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
import httpx

from automagik_tools.tools.spark import create_server
from automagik_tools.tools.spark.config import SparkConfig
from automagik_tools.tools.spark.client import SparkClient


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


class TestSparkEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_workflow_list(self, tool_instance):
        """Test handling of empty workflow list"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = []
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            tools = await tool_instance.get_tools()
            result = await tools["list_workflows"]()

            workflows = json.loads(result)
            assert workflows == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_input_text(self, tool_instance):
        """Test handling of empty input text for workflow execution"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "id": "task-123",
                "status": "completed",
                "input_data": {"value": ""},
                "output_data": {"result": "Empty input processed"},
            }
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            tools = await tool_instance.get_tools()
            result = await tools["run_workflow"](
                workflow_id="workflow-1", input_text=""
            )

            task = json.loads(result)
            assert task["input_data"]["value"] == ""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_large_workflow_input(self, tool_instance):
        """Test handling of large input payloads"""
        large_input = "x" * 10000  # 10KB of text

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "id": "task-123",
                "status": "completed",
                "input_data": {"value": large_input},
                "output_data": {"result": "Processed large input"},
            }
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            tools = await tool_instance.get_tools()
            result = await tools["run_workflow"](
                workflow_id="workflow-1", input_text=large_input
            )

            task = json.loads(result)
            assert task["status"] == "completed"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_schedule_expression(self, tool_instance):
        """Test handling of invalid schedule expressions"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 422
            mock_response.text = "Invalid schedule expression"
            mock_response.json.return_value = {
                "detail": [
                    {
                        "loc": ["schedule_expr"],
                        "msg": "Invalid cron expression",
                        "type": "value_error",
                    }
                ]
            }

            error = httpx.HTTPStatusError(
                "Validation error", request=Mock(), response=mock_response
            )
            mock_response.raise_for_status.side_effect = error

            mock_client.request.return_value = mock_response

            tools = await tool_instance.get_tools()

            with pytest.raises(ValueError, match="HTTP 422"):
                await tools["create_schedule"](
                    workflow_id="workflow-1",
                    schedule_type="cron",
                    schedule_expr="invalid-cron",
                )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_special_characters_in_input(self, tool_instance):
        """Test handling of special characters in input"""
        special_input = "Test with \"quotes\" and 'apostrophes' and \n newlines"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "id": "task-123",
                "status": "completed",
                "input_data": {"value": special_input},
                "output_data": {"result": "Processed special characters"},
            }
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            tools = await tool_instance.get_tools()
            result = await tools["run_workflow"](
                workflow_id="workflow-1", input_text=special_input
            )

            task = json.loads(result)
            assert task["input_data"]["value"] == special_input

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, tool_instance):
        """Test handling of concurrent workflow executions"""
        import asyncio

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Simulate different responses for concurrent calls
            responses = []
            for i in range(3):
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {"content-type": "application/json"}
                mock_response.json.return_value = {
                    "id": f"task-{i}",
                    "status": "completed",
                    "output_data": {"result": f"Result {i}"},
                }
                mock_response.raise_for_status = Mock()
                responses.append(mock_response)

            mock_client.request.side_effect = responses

            tools = await tool_instance.get_tools()

            # Execute workflows concurrently
            tasks = [
                tools["run_workflow"](
                    workflow_id=f"workflow-{i}", input_text=f"Input {i}"
                )
                for i in range(3)
            ]

            results = await asyncio.gather(*tasks)

            # Verify all completed
            for i, result in enumerate(results):
                task_data = json.loads(result)
                assert task_data["id"] == f"task-{i}"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_null_response_fields(self, tool_instance):
        """Test handling of null fields in API responses"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "id": "task-123",
                "workflow_id": "workflow-1",
                "status": "pending",
                "input_data": None,
                "output_data": None,
                "error": None,
                "started_at": None,
                "finished_at": None,
            }
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            tools = await tool_instance.get_tools()
            result = await tools["get_task"](task_id="task-123")

            task = json.loads(result)
            assert task["status"] == "pending"
            assert task["output_data"] is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_malformed_json_response(self, tool_instance):
        """Test handling of malformed JSON responses"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/plain"}
            mock_response.text = "Not JSON"
            mock_response.json.side_effect = json.JSONDecodeError("msg", "doc", 0)
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            tools = await tool_instance.get_tools()
            result = await tools["get_health"]()

            # Should handle non-JSON response gracefully
            result_data = json.loads(result)
            assert result_data["result"] == "Not JSON"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, tool_instance):
        """Test handling of rate limit responses"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit exceeded"
            mock_response.headers = {"Retry-After": "60"}
            mock_response.json.return_value = {"detail": "Too many requests"}

            error = httpx.HTTPStatusError(
                "Rate limited", request=Mock(), response=mock_response
            )
            mock_response.raise_for_status.side_effect = error

            mock_client.request.return_value = mock_response

            tools = await tool_instance.get_tools()

            with pytest.raises(ValueError, match="HTTP 429"):
                await tools["list_workflows"]()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_partial_api_failure(self, tool_instance):
        """Test handling when API returns partial success"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {
                "status": "degraded",
                "timestamp": "2025-08-23 15:00:00",
                "services": {
                    "api": {"status": "healthy"},
                    "worker": {"status": "error", "error": "Connection failed"},
                    "redis": {"status": "unhealthy"},
                },
            }
            mock_response.raise_for_status = Mock()

            mock_client.request.return_value = mock_response

            tools = await tool_instance.get_tools()
            result = await tools["get_health"]()

            health = json.loads(result)
            assert health["status"] == "degraded"
            assert health["services"]["worker"]["status"] == "error"
