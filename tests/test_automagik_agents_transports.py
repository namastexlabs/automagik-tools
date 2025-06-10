"""
Test automagik tool with different transports
"""

import asyncio
import json
import pytest
import sys
import os
import httpx
from tests.conftest import SAMPLE_MCP_INITIALIZE


class TestAutomagikAgentsTransports:
    """Test automagik tool with different transports"""

    @pytest.mark.asyncio
    async def test_stdio_transport(self):
        """Test automagik with stdio transport"""
        # Create environment with dummy config
        env = os.environ.copy()
        env.update(
            {
                "AUTOMAGIK_AGENTS_BASE_URL": "http://test-api.example.com",
                "AUTOMAGIK_AGENTS_API_KEY": "test_key",
                "AUTOMAGIK_AGENTS_TIMEOUT": "30",
                "FASTMCP_LOG_LEVEL": "ERROR",
            }
        )

        command = [
            sys.executable,
            "-m",
            "automagik_tools.cli",
            "serve",
            "--tool",
            "automagik",
            "--transport",
            "stdio",
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        try:
            # Send initialization message
            init_msg = json.dumps(SAMPLE_MCP_INITIALIZE) + "\n"
            process.stdin.write(init_msg.encode())
            await process.stdin.drain()

            # Read response
            response_line = await asyncio.wait_for(
                process.stdout.readline(), timeout=5.0
            )
            response = json.loads(response_line.decode().strip())

            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 1
            assert "result" in response
            assert response["result"]["serverInfo"]["name"] == "Automagik Agents"

        finally:
            process.terminate()
            await process.wait()

    @pytest.mark.asyncio
    async def test_sse_transport(self):
        """Test automagik with SSE transport"""
        env = os.environ.copy()
        env.update(
            {
                "AUTOMAGIK_AGENTS_BASE_URL": "http://test-api.example.com",
                "AUTOMAGIK_AGENTS_API_KEY": "test_key",
                "AUTOMAGIK_AGENTS_TIMEOUT": "30",
                "HOST": "127.0.0.1",
                "PORT": "0",  # Use random port
            }
        )

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "automagik_tools.cli",
            "serve",
            "--tool",
            "automagik",
            "--transport",
            "sse",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        try:
            # Wait for server to start and capture port
            started = False
            port = None

            async def read_output():
                nonlocal started, port
                while True:
                    line = await process.stderr.readline()  # FastMCP logs to stderr
                    if not line:
                        break
                    line_str = line.decode().strip()
                    print(f"SSE stderr: {line_str}")
                    # Look for uvicorn startup message
                    if "Uvicorn running on" in line_str:
                        # Extract port from "Uvicorn running on http://127.0.0.1:8000"
                        import re

                        match = re.search(r":(\d+)", line_str)
                        if match:
                            port = int(match.group(1))
                            started = True
                            break

            # Start reading output with timeout
            try:
                await asyncio.wait_for(read_output(), timeout=5.0)
            except asyncio.TimeoutError:
                # Check stderr for errors
                stderr = await process.stderr.read()
                print(f"SSE stderr: {stderr.decode()}")

            assert started, "SSE server did not start"
            assert port is not None, "Could not determine SSE server port"

            # Test SSE endpoint
            async with httpx.AsyncClient() as client:
                # Test that server is responding
                response = await client.get(f"http://127.0.0.1:{port}/sse")
                assert response.status_code in [200, 405]  # 405 if GET not allowed

        finally:
            process.terminate()
            await process.wait()

    @pytest.mark.asyncio
    async def test_serve_all_command(self):
        """Test serve-all command with multiple tools"""
        env = os.environ.copy()
        env.update(
            {
                "EVOLUTION_API_BASE_URL": "http://test-api.example.com",
                "EVOLUTION_API_KEY": "test_key",
                "AUTOMAGIK_AGENTS_BASE_URL": "http://test-api.example.com",
                "AUTOMAGIK_AGENTS_API_KEY": "test_key",
                "HOST": "127.0.0.1",
                "PORT": "0",  # Use random port
            }
        )

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "automagik_tools.cli",
            "serve-all",
            "--tools",
            "evolution-api,automagik",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        try:
            # Wait for server to start
            started = False
            port = None

            async def read_output():
                nonlocal started, port
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    line_str = line.decode().strip()
                    print(f"serve-all stdout: {line_str}")
                    if "Starting multi-tool server on" in line_str and ":" in line_str:
                        # Extract port
                        port = int(line_str.split(":")[-1])
                        started = True
                        break

            try:
                await asyncio.wait_for(read_output(), timeout=5.0)
            except asyncio.TimeoutError:
                # Check stderr
                stderr = await process.stderr.read()
                print(f"serve-all stderr: {stderr.decode()}")

            assert started, "Multi-tool server did not start"
            assert port is not None, "Could not determine server port"

            # Test endpoints
            async with httpx.AsyncClient() as client:
                # Test root endpoint
                response = await client.get(f"http://127.0.0.1:{port}/")
                assert response.status_code == 200
                data = response.json()
                assert "available_tools" in data
                assert "evolution-api" in data["available_tools"]
                assert "automagik" in data["available_tools"]

        finally:
            process.terminate()
            await process.wait()
