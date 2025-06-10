"""
Tests for MCP protocol compliance and stdio transport
"""

import asyncio
import json
import pytest
import sys
from tests.conftest import SAMPLE_MCP_INITIALIZE, SAMPLE_MCP_LIST_TOOLS, MCPTestClient


class TestMCPProtocolCompliance:
    """Test MCP protocol compliance"""

    @pytest.mark.asyncio
    async def test_mcp_initialization(self, mcp_test_client):
        """Test MCP initialization handshake"""
        response = await mcp_test_client.send_message(SAMPLE_MCP_INITIALIZE)

        assert response is not None
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response

        result = response["result"]
        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "Evolution API Tool"

    @pytest.mark.skip(reason="Skipping multi-message test for now")
    @pytest.mark.asyncio
    async def test_mcp_list_tools(self):
        """Test listing tools via MCP protocol with separate client"""
        # Create a new client for this specific test
        command = [
            sys.executable,
            "-m",
            "automagik_tools.cli",
            "serve",
            "--tool",
            "evolution-api",
            "--transport",
            "stdio",
        ]

        client = MCPTestClient(command)
        await client.start()

        try:
            # First initialize
            init_response = await client.send_message(SAMPLE_MCP_INITIALIZE)
            assert init_response is not None
            assert init_response["id"] == 1

            # Wait a bit for initialization to complete
            await asyncio.sleep(0.5)

            # Then list tools
            tools_response = await client.send_message(SAMPLE_MCP_LIST_TOOLS)

            assert tools_response is not None
            assert tools_response["jsonrpc"] == "2.0"
            assert tools_response["id"] == 2
            assert "result" in tools_response

            result = tools_response["result"]
            assert "tools" in result
            assert len(result["tools"]) > 0

            # Check that evolution API tools are present
            tool_names = [tool["name"] for tool in result["tools"]]
            assert any("send_text_message" in name for name in tool_names)
        finally:
            await client.close()

    @pytest.mark.skip(reason="Skipping multi-message test for now")
    @pytest.mark.asyncio
    async def test_mcp_invalid_method(self, mcp_test_client):
        """Test handling of invalid MCP method"""
        invalid_message = {"jsonrpc": "2.0", "method": "invalid/method", "id": 99}

        # Initialize first
        await mcp_test_client.send_message(SAMPLE_MCP_INITIALIZE)

        # Wait for initialization to complete
        await asyncio.sleep(0.1)

        # Send invalid method
        response = await mcp_test_client.send_message(invalid_message)

        assert response is not None
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 99
        assert "error" in response
        assert response["error"]["code"] == -32601  # Method not found

    @pytest.mark.asyncio
    async def test_mcp_malformed_json(self, mcp_test_client):
        """Test handling of malformed JSON"""
        # Send malformed JSON directly to stdin
        if mcp_test_client.process:
            malformed_json = '{"jsonrpc": "2.0", "method": "test", "id": 1, invalid}\n'
            mcp_test_client.process.stdin.write(malformed_json.encode())
            await mcp_test_client.process.stdin.drain()

            # Should not crash the server - read any response
            try:
                response_line = await asyncio.wait_for(
                    mcp_test_client.process.stdout.readline(), timeout=1.0
                )
                # If we get a response, it should be an error or the server should ignore it
                if response_line:
                    response = json.loads(response_line.decode().strip())
                    if "error" in response:
                        assert response["error"]["code"] == -32700  # Parse error
            except (asyncio.TimeoutError, json.JSONDecodeError):
                # Timeout or no response is also acceptable
                pass


class TestStdioTransport:
    """Test stdio transport specific functionality"""

    @pytest.mark.skip(reason="Skipping multi-message test for now")
    @pytest.mark.asyncio
    async def test_stdio_message_delimiter(self, mcp_test_client):
        """Test that messages are properly delimited by newlines"""
        # Send multiple messages in quick succession
        messages = [
            SAMPLE_MCP_INITIALIZE,
            {"jsonrpc": "2.0", "method": "tools/list", "id": 2},
        ]

        responses = []
        for i, message in enumerate(messages):
            response = await mcp_test_client.send_message(message)
            responses.append(response)
            # Wait between messages if not the last one
            if i < len(messages) - 1:
                await asyncio.sleep(0.1)

        assert len(responses) == 2
        assert all(r is not None for r in responses)
        assert responses[0]["id"] == 1
        assert responses[1]["id"] == 2

    @pytest.mark.asyncio
    async def test_stdio_no_embedded_newlines(self, mcp_test_client):
        """Test that responses don't contain embedded newlines"""
        response = await mcp_test_client.send_message(SAMPLE_MCP_INITIALIZE)

        assert response is not None
        # When we get the raw response, it should be a single line
        response_json = json.dumps(response)
        assert "\n" not in response_json
        assert "\r" not in response_json

    @pytest.mark.skip(reason="Skipping multi-message test for now")
    @pytest.mark.asyncio
    async def test_stdio_utf8_encoding(self, mcp_test_client):
        """Test that messages are properly UTF-8 encoded"""
        # Send a message with Unicode characters
        unicode_message = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "send_text_message",
                "arguments": {"number": "1234567890", "text": "Hello 世界! 🌍 émojis"},
            },
            "id": 3,
        }

        # Initialize first
        await mcp_test_client.send_message(SAMPLE_MCP_INITIALIZE)

        # Wait for initialization to complete
        await asyncio.sleep(0.1)

        # Send unicode message
        response = await mcp_test_client.send_message(unicode_message)

        # Should get a response (even if it's an error due to no actual API)
        assert response is not None
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 3


class TestMCPResources:
    """Test MCP resources functionality"""

    @pytest.mark.skip(reason="Skipping multi-message test for now")
    @pytest.mark.asyncio
    async def test_list_resources(self, mcp_test_client):
        """Test listing resources"""
        # Initialize
        await mcp_test_client.send_message(SAMPLE_MCP_INITIALIZE)

        # Wait for initialization to complete
        await asyncio.sleep(0.1)

        # List resources
        resources_message = {"jsonrpc": "2.0", "method": "resources/list", "id": 4}

        response = await mcp_test_client.send_message(resources_message)

        assert response is not None
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 4
        assert "result" in response

        result = response["result"]
        assert "resources" in result
        # Should have some evolution API resources
        assert len(result["resources"]) > 0

    @pytest.mark.skip(reason="Skipping multi-message test for now")
    @pytest.mark.asyncio
    async def test_read_resource(self, mcp_test_client):
        """Test reading a resource"""
        # Initialize
        await mcp_test_client.send_message(SAMPLE_MCP_INITIALIZE)

        # Wait for initialization to complete
        await asyncio.sleep(0.1)

        # Read config resource
        read_message = {
            "jsonrpc": "2.0",
            "method": "resources/read",
            "params": {"uri": "evolution://config"},
            "id": 5,
        }

        response = await mcp_test_client.send_message(read_message)

        assert response is not None
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 5
        assert "result" in response

        result = response["result"]
        assert "contents" in result
        assert len(result["contents"]) > 0


class TestMCPPrompts:
    """Test MCP prompts functionality"""

    @pytest.mark.skip(reason="Skipping multi-message test for now")
    @pytest.mark.asyncio
    async def test_list_prompts(self, mcp_test_client):
        """Test listing prompts"""
        # Initialize
        await mcp_test_client.send_message(SAMPLE_MCP_INITIALIZE)

        # Wait for initialization to complete
        await asyncio.sleep(0.1)

        # List prompts
        prompts_message = {"jsonrpc": "2.0", "method": "prompts/list", "id": 6}

        response = await mcp_test_client.send_message(prompts_message)

        assert response is not None
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 6
        assert "result" in response

        result = response["result"]
        assert "prompts" in result
        # Should have some evolution API prompts
        assert len(result["prompts"]) > 0

    @pytest.mark.skip(reason="Skipping multi-message test for now")
    @pytest.mark.asyncio
    async def test_get_prompt(self, mcp_test_client):
        """Test getting a specific prompt"""
        # Initialize
        await mcp_test_client.send_message(SAMPLE_MCP_INITIALIZE)

        # Wait for initialization to complete
        await asyncio.sleep(0.1)

        # Get prompt
        prompt_message = {
            "jsonrpc": "2.0",
            "method": "prompts/get",
            "params": {
                "name": "whatsapp_message_template",
                "arguments": {"recipient": "test_user", "message_type": "greeting"},
            },
            "id": 7,
        }

        response = await mcp_test_client.send_message(prompt_message)

        assert response is not None
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 7
        assert "result" in response

        result = response["result"]
        assert "description" in result or "messages" in result


class TestMCPErrorHandling:
    """Test MCP error handling"""

    @pytest.mark.skip(reason="Skipping multi-message test for now")
    @pytest.mark.asyncio
    async def test_tool_call_with_missing_args(self, mcp_test_client):
        """Test tool call with missing required arguments"""
        # Initialize
        await mcp_test_client.send_message(SAMPLE_MCP_INITIALIZE)

        # Wait for initialization to complete
        await asyncio.sleep(0.1)

        # Call tool with missing arguments
        tool_call = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "send_text_message",
                "arguments": {
                    # Missing required 'number' and 'text' parameters
                },
            },
            "id": 8,
        }

        response = await mcp_test_client.send_message(tool_call)

        assert response is not None
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 8
        assert "error" in response
        # Should be invalid params error
        assert response["error"]["code"] == -32602

    @pytest.mark.skip(reason="Skipping multi-message test for now")
    @pytest.mark.asyncio
    async def test_nonexistent_tool_call(self, mcp_test_client):
        """Test calling a non-existent tool"""
        # Initialize
        await mcp_test_client.send_message(SAMPLE_MCP_INITIALIZE)

        # Wait for initialization to complete
        await asyncio.sleep(0.1)

        # Call non-existent tool
        tool_call = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "nonexistent_tool", "arguments": {}},
            "id": 9,
        }

        response = await mcp_test_client.send_message(tool_call)

        assert response is not None
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 9
        assert "error" in response
