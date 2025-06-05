"""
Pytest configuration and shared fixtures for automagik-tools tests
"""

import asyncio
import json
import os
import sys
import tempfile
import subprocess
import pytest
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import patch, AsyncMock

# Test data
TEST_EVOLUTION_CONFIG = {
    "base_url": "http://test-api.example.com",
    "api_key": "test_api_key",
    "timeout": 30,
}

SAMPLE_MCP_INITIALIZE = {
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1.0.0"},
    },
    "id": 1,
}

SAMPLE_MCP_LIST_TOOLS = {"jsonrpc": "2.0", "method": "tools/list", "id": 2}


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_evolution_config():
    """Mock evolution API configuration"""
    with patch.dict(
        os.environ,
        {
            "EVOLUTION_API_BASE_URL": TEST_EVOLUTION_CONFIG["base_url"],
            "EVOLUTION_API_KEY": TEST_EVOLUTION_CONFIG["api_key"],
            "EVOLUTION_API_TIMEOUT": str(TEST_EVOLUTION_CONFIG["timeout"]),
        },
    ):
        # Return string-based config for environment variables
        yield {
            "EVOLUTION_API_BASE_URL": TEST_EVOLUTION_CONFIG["base_url"],
            "EVOLUTION_API_KEY": TEST_EVOLUTION_CONFIG["api_key"],
            "EVOLUTION_API_TIMEOUT": str(TEST_EVOLUTION_CONFIG["timeout"]),
        }


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for API calls"""
    with patch("httpx.AsyncClient") as mock:
        mock_client = AsyncMock()
        mock.return_value.__aenter__.return_value = mock_client
        yield mock_client


@pytest.fixture
def project_root():
    """Get the project root directory"""
    return Path(__file__).parent.parent


@pytest.fixture
async def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


class MCPTestClient:
    """Helper class for testing MCP protocol interactions"""

    def __init__(self, command: list):
        self.command = command
        self.process = None

    async def start(self):
        """Start the MCP server process"""
        # Convert test config to proper environment variables
        env = os.environ.copy()
        env.update({
            "EVOLUTION_API_BASE_URL": TEST_EVOLUTION_CONFIG["base_url"],
            "EVOLUTION_API_KEY": TEST_EVOLUTION_CONFIG["api_key"],
            "EVOLUTION_API_TIMEOUT": str(TEST_EVOLUTION_CONFIG["timeout"]),
            # Suppress FastMCP logging to stderr
            "FASTMCP_LOG_LEVEL": "ERROR",
        })
        
        self.process = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        return self

    async def send_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a JSON-RPC message and get response"""
        if not self.process:
            raise RuntimeError("Process not started")
            
        # Check if process is still alive
        if self.process.returncode is not None:
            raise RuntimeError(f"Process exited with code {self.process.returncode}")

        # Check for any stderr output (non-blocking)
        try:
            stderr_data = await asyncio.wait_for(self.process.stderr.read(1024), timeout=0.1)
            if stderr_data:
                print(f"STDERR: {stderr_data.decode()}")
        except asyncio.TimeoutError:
            pass

        message_json = json.dumps(message) + "\n"
        self.process.stdin.write(message_json.encode())
        await self.process.stdin.drain()

        # Read response with timeout
        try:
            response_line = await asyncio.wait_for(self.process.stdout.readline(), timeout=2.0)
            if response_line:
                try:
                    return json.loads(response_line.decode().strip())
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}, line: {response_line}")
                    return None
        except asyncio.TimeoutError:
            print("Timeout waiting for response")
            # Check stderr for errors
            try:
                stderr_data = await asyncio.wait_for(self.process.stderr.read(1024), timeout=0.1)
                if stderr_data:
                    print(f"STDERR after timeout: {stderr_data.decode()}")
            except asyncio.TimeoutError:
                pass
        return None

    async def close(self):
        """Close the MCP server process"""
        if self.process:
            # Try graceful shutdown first
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                # Force kill if graceful shutdown fails
                self.process.kill()
                await self.process.wait()


@pytest.fixture(scope="function")  # Create new client for each test
async def mcp_test_client():
    """Create an MCP test client for stdio testing"""
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
    yield client
    await client.close()


def run_cli_command(
    args: list, env: Optional[Dict[str, str]] = None
) -> subprocess.CompletedProcess:
    """Helper function to run CLI commands"""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    return subprocess.run(
        ["python", "-m", "automagik_tools.cli"] + args,
        capture_output=True,
        text=True,
        env=full_env,
    )


@pytest.fixture
def cli_runner():
    """Fixture that provides the CLI runner helper"""
    return run_cli_command
