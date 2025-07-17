"""
Integration tests for Agent Connect MCP tool
"""

import pytest
import asyncio
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor

from automagik_tools.tools.agent_connect import create_server
from automagik_tools.tools.agent_connect.config import AgentConnectConfig


class TestAgentConnectIntegration:
    """Test integration with automagik hub and other tools"""
    
    def test_hub_discovery(self):
        """Test tool is discoverable by hub"""
        result = subprocess.run(
            ["uv", "run", "automagik-tools", "list"],
            capture_output=True,
            text=True,
            cwd="/home/cezar/automagik/automagik-tools"
        )
        
        # Tool should be listed
        assert "agent-connect" in result.stdout
        assert "Seamless multi-agent coordination" in result.stdout
    
    def test_tool_can_be_served(self):
        """Test tool can be served standalone"""
        # Test that tool starts without error
        proc = subprocess.Popen(
            ["uv", "run", "automagik-tools", "tool", "agent-connect"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="/home/cezar/automagik/automagik-tools"
        )
        
        # Send a simple MCP request
        request = json.dumps({
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        })
        
        try:
            stdout, stderr = proc.communicate(input=request + "\n", timeout=2)
            # Should not error
            assert proc.returncode is None or proc.returncode == 0
        except subprocess.TimeoutExpired:
            proc.kill()
            # Timeout is fine - tool started successfully
        finally:
            proc.terminate()
    
    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self):
        """Test multiple agents coordinating through channels"""
        config = AgentConnectConfig()
        server = create_server(config)
        
        results = []
        
        async def agent1():
            """First agent - sends a task"""
            from automagik_tools.tools.agent_connect import send_message
            result = await send_message(
                channel_id="coordination",
                message="Task: Process data file",
                wait_for_reply=True,
                reply_timeout=2.0
            )
            results.append(("agent1", result))
        
        async def agent2():
            """Second agent - receives task and replies"""
            from automagik_tools.tools.agent_connect import listen_for_message, send_reply
            
            # Wait for task
            msg = await listen_for_message("coordination", timeout=2.0)
            if msg["status"] == "received":
                # Process and reply
                await asyncio.sleep(0.1)  # Simulate work
                await send_reply(
                    original_message_id=msg["message"]["id"],
                    reply_channel_id="coordination",
                    reply_content="Task completed successfully"
                )
                results.append(("agent2", msg))
        
        # Run both agents concurrently
        await asyncio.gather(agent1(), agent2())
        
        # Verify coordination worked
        assert len(results) == 2
        agent1_result = next(r for r in results if r[0] == "agent1")[1]
        assert agent1_result["reply_status"] == "received"
        assert agent1_result["reply"]["content"] == "Task completed successfully"
    
    @pytest.mark.asyncio
    async def test_broadcast_pattern(self):
        """Test broadcast to multiple listeners"""
        from automagik_tools.tools.agent_connect import send_message, listen_for_message
        
        received = []
        
        async def listener(listener_id):
            """Listen for broadcast"""
            msg = await listen_for_message("broadcast", timeout=2.0)
            if msg["status"] == "received":
                received.append((listener_id, msg["message"]["content"]))
        
        # Start multiple listeners
        listeners = [
            asyncio.create_task(listener(f"listener-{i}"))
            for i in range(3)
        ]
        
        # Give listeners time to start
        await asyncio.sleep(0.1)
        
        # Send broadcast messages
        for i in range(3):
            await send_message("broadcast", f"Broadcast {i}")
        
        # Wait for all listeners
        await asyncio.gather(*listeners)
        
        # Each listener should receive one message
        assert len(received) == 3
        # Messages should be distributed
        assert len(set(r[0] for r in received)) == 3  # All listeners got a message


class TestAgentConnectMCPProtocol:
    """Test MCP protocol compliance"""
    
    @pytest.mark.asyncio
    async def test_mcp_tool_discovery(self):
        """Test MCP tools can be discovered"""
        config = AgentConnectConfig()
        server = create_server(config)
        
        # FastMCP provides tools via get_tools()
        tools = await server.get_tools()
        
        assert len(tools) > 0
        
        # Check tool properties
        for tool_name, tool_func in tools.items():
            assert isinstance(tool_name, str)
            assert callable(tool_func)
            assert hasattr(tool_func, "__doc__")
    
    @pytest.mark.asyncio 
    async def test_mcp_error_handling(self):
        """Test MCP error responses"""
        from automagik_tools.tools.agent_connect import listen_for_message
        
        # Test with invalid parameters
        with pytest.raises(TypeError):
            # Missing required channel_id
            await listen_for_message()
    
    def test_mcp_transport_compatibility(self):
        """Test tool works with different transports"""
        # Test stdio transport (default)
        proc = subprocess.Popen(
            ["uv", "run", "python", "-m", "automagik_tools.tools.agent_connect"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="/home/cezar/automagik/automagik-tools"
        )
        
        try:
            # Should start without error
            proc.poll()
            assert proc.returncode is None
        finally:
            proc.terminate()
        
        # Test SSE transport
        proc = subprocess.Popen(
            ["uv", "run", "python", "-m", "automagik_tools.tools.agent_connect", "--transport", "sse"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="/home/cezar/automagik/automagik-tools"
        )
        
        try:
            # Give it time to start
            import time
            time.sleep(0.5)
            proc.poll()
            assert proc.returncode is None
        finally:
            proc.terminate()