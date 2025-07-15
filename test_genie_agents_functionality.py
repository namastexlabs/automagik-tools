#!/usr/bin/env python3
"""
Test script for genie_agents MCP tool functionality.
Tests the tool's capabilities against a mock or real API.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from automagik_tools.tools.genie_agents import create_server, GenieAgentsConfig
from automagik_tools.tools.genie_agents.server import GenieAgentsClient


class MockResponse:
    """Mock HTTP response for testing."""
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


async def test_client_connectivity():
    """Test basic client connectivity."""
    print("🔌 Testing client connectivity...")
    config = GenieAgentsConfig(
        api_base_url="http://localhost:9888",
        api_key="test-key",
        timeout=30
    )
    
    try:
        async with GenieAgentsClient(config) as client:
            print("✅ Client initialized successfully")
            print(f"   Base URL: {client.config.api_base_url}")
            print(f"   Timeout: {client.config.timeout}")
            return True
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return False


async def test_playground_status():
    """Test playground status endpoint."""
    print("\n🎮 Testing playground status...")
    config = GenieAgentsConfig()
    
    # Mock successful response
    mock_response = MockResponse({
        "status": "healthy",
        "version": "1.0.0",
        "uptime": "2h 30m"
    })
    
    with patch('automagik_tools.tools.genie_agents.server.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        server = create_server(config)
        tools = await server.get_tools()
        
        # Find the check_playground_status tool
        check_status_tool = tools.get("check_playground_status")
        
        if check_status_tool:
            try:
                result = await check_status_tool.run({})
                print("✅ Playground status check successful")
                print(f"   Result: {result}")
                return True
            except Exception as e:
                print(f"❌ Playground status check failed: {e}")
                return False
        else:
            print("❌ check_playground_status tool not found")
            return False


async def test_agent_operations():
    """Test agent-related operations."""
    print("\n🤖 Testing agent operations...")
    config = GenieAgentsConfig()
    
    # Mock responses
    agents_response = MockResponse([
        {"id": "agent-1", "name": "Test Agent 1", "type": "chatbot"},
        {"id": "agent-2", "name": "Test Agent 2", "type": "assistant"}
    ])
    
    conversation_response = MockResponse({
        "run_id": "run-123",
        "agent_id": "agent-1",
        "status": "completed",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there! How can I help you?"}
        ]
    })
    
    with patch('automagik_tools.tools.genie_agents.server.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        server = create_server(config)
        tools = await server.get_tools()
        
        # Test list_available_agents
        mock_client.request.return_value = agents_response
        try:
            result = await tools["list_available_agents"].run({})
            print("✅ List agents successful")
            print(f"   Found {len(result)} agents")
        except Exception as e:
            print(f"❌ List agents failed: {e}")
            return False
        
        # Test start_agent_conversation
        mock_client.request.return_value = conversation_response
        try:
            result = await tools["start_agent_conversation"].run({
                "agent_id": "agent-1",
                "message": "Hello, can you help me?"
            })
            print("✅ Start conversation successful")
            print(f"   Run ID: {result.get('run_id')}")
        except Exception as e:
            print(f"❌ Start conversation failed: {e}")
            return False
        
        return True


async def test_workflow_operations():
    """Test workflow-related operations."""
    print("\n🔄 Testing workflow operations...")
    config = GenieAgentsConfig()
    
    # Mock responses
    workflows_response = MockResponse([
        {"id": "workflow-1", "name": "Data Analysis", "description": "Analyze data"},
        {"id": "workflow-2", "name": "Report Generation", "description": "Generate reports"}
    ])
    
    execution_response = MockResponse({
        "session_id": "session-123",
        "workflow_id": "workflow-1",
        "status": "running",
        "progress": 0.5
    })
    
    with patch('automagik_tools.tools.genie_agents.server.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        server = create_server(config)
        tools = await server.get_tools()
        
        # Test list_available_workflows
        mock_client.request.return_value = workflows_response
        try:
            result = await tools["list_available_workflows"].run({})
            print("✅ List workflows successful")
            print(f"   Found {len(result)} workflows")
        except Exception as e:
            print(f"❌ List workflows failed: {e}")
            return False
        
        # Test execute_workflow
        mock_client.request.return_value = execution_response
        try:
            result = await tools["execute_workflow"].run({
                "workflow_id": "workflow-1",
                "input_data": {"data": "test"}
            })
            print("✅ Execute workflow successful")
            print(f"   Session ID: {result.get('session_id')}")
        except Exception as e:
            print(f"❌ Execute workflow failed: {e}")
            return False
        
        return True


async def test_team_operations():
    """Test team-related operations."""
    print("\n👥 Testing team operations...")
    config = GenieAgentsConfig()
    
    # Mock responses
    teams_response = MockResponse([
        {"id": "team-1", "name": "Marketing Team", "members": ["agent-1", "agent-2"]},
        {"id": "team-2", "name": "Dev Team", "members": ["agent-3", "agent-4"]}
    ])
    
    collaboration_response = MockResponse({
        "session_id": "collab-123",
        "team_id": "team-1",
        "status": "active",
        "participants": ["agent-1", "agent-2"]
    })
    
    with patch('automagik_tools.tools.genie_agents.server.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        server = create_server(config)
        tools = await server.get_tools()
        
        # Test list_available_teams
        mock_client.request.return_value = teams_response
        try:
            result = await tools["list_available_teams"].run({})
            print("✅ List teams successful")
            print(f"   Found {len(result)} teams")
        except Exception as e:
            print(f"❌ List teams failed: {e}")
            return False
        
        # Test start_team_collaboration
        mock_client.request.return_value = collaboration_response
        try:
            result = await tools["start_team_collaboration"].run({
                "team_id": "team-1",
                "task_description": "Create a marketing campaign"
            })
            print("✅ Start collaboration successful")
            print(f"   Session ID: {result.get('session_id')}")
        except Exception as e:
            print(f"❌ Start collaboration failed: {e}")
            return False
        
        return True


async def test_quick_actions():
    """Test quick actions functionality."""
    print("\n🚀 Testing quick actions...")
    config = GenieAgentsConfig()
    
    # Mock response
    quick_response = MockResponse({
        "task_id": "task-123",
        "status": "completed",
        "result": "Task completed successfully"
    })
    
    with patch('automagik_tools.tools.genie_agents.server.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.request.return_value = quick_response
        mock_client_class.return_value = mock_client
        
        server = create_server(config)
        tools = await server.get_tools()
        
        try:
            result = await tools["quick_run"].run({
                "task_description": "Summarize the latest sales data"
            })
            print("✅ Quick run successful")
            print(f"   Task ID: {result.get('task_id')}")
            return True
        except Exception as e:
            print(f"❌ Quick run failed: {e}")
            return False


async def test_error_handling():
    """Test error handling scenarios."""
    print("\n⚠️ Testing error handling...")
    config = GenieAgentsConfig()
    
    # Mock error response
    error_response = MockResponse({"error": "Not found"}, 404)
    
    with patch('automagik_tools.tools.genie_agents.server.httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.request.return_value = error_response
        mock_client_class.return_value = mock_client
        
        server = create_server(config)
        tools = await server.get_tools()
        
        try:
            await tools["list_available_agents"].run({})
            print("❌ Error handling failed - should have raised exception")
            return False
        except Exception as e:
            print("✅ Error handling successful")
            print(f"   Caught expected error: {e}")
            return True


async def test_tool_availability():
    """Test that all expected tools are available."""
    print("\n🔧 Testing tool availability...")
    
    server = create_server()
    tools = await server.get_tools()
    tool_names = list(tools.keys())
    
    expected_tools = [
        "check_playground_status",
        "list_available_agents",
        "start_agent_conversation",
        "continue_agent_conversation",
        "view_agent_conversation_history",
        "list_available_workflows",
        "execute_workflow",
        "list_available_teams",
        "start_team_collaboration",
        "quick_run"
    ]
    
    missing_tools = [tool for tool in expected_tools if tool not in tool_names]
    extra_tools = [tool for tool in tool_names if tool not in expected_tools]
    
    if missing_tools:
        print(f"❌ Missing tools: {missing_tools}")
        return False
    
    if extra_tools:
        print(f"ℹ️ Extra tools found: {extra_tools}")
    
    print(f"✅ All expected tools available ({len(expected_tools)} tools)")
    return True


async def main():
    """Run all tests."""
    print("🧪 Starting Genie Agents Tool Tests")
    print("="*50)
    
    test_results = []
    
    # Run all tests
    test_results.append(await test_client_connectivity())
    test_results.append(await test_tool_availability())
    test_results.append(await test_playground_status())
    test_results.append(await test_agent_operations())
    test_results.append(await test_workflow_operations())
    test_results.append(await test_team_operations())
    test_results.append(await test_quick_actions())
    test_results.append(await test_error_handling())
    
    # Summary
    print("\n" + "="*50)
    print("📊 Test Results Summary:")
    passed = sum(test_results)
    total = len(test_results)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️ Some tests failed!")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)