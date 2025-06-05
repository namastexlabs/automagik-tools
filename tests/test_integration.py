"""
Integration tests for automagik-tools
Tests the complete workflow from CLI to tool execution
"""

import pytest
import asyncio
import json
import subprocess
import signal
import time
import sys
from tests.conftest import SAMPLE_MCP_INITIALIZE, SAMPLE_MCP_LIST_TOOLS


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""

    @pytest.mark.asyncio
    async def test_complete_mcp_workflow(self, mock_evolution_config):
        """Test complete MCP workflow from CLI startup to tool execution"""
        # Start the server
        import os

        env = os.environ.copy()
        env.update(mock_evolution_config)
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "automagik_tools.cli",
            "serve",
            "--tool",
            "evolution-api",
            "--transport",
            "stdio",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        try:
            # 1. Initialize MCP connection
            init_message = json.dumps(SAMPLE_MCP_INITIALIZE) + "\n"
            process.stdin.write(init_message.encode())
            await process.stdin.drain()

            # Read initialization response
            response_line = await asyncio.wait_for(
                process.stdout.readline(), timeout=5.0
            )
            init_response = json.loads(response_line.decode().strip())

            assert init_response["jsonrpc"] == "2.0"
            assert init_response["id"] == 1
            assert "result" in init_response

            # 2. List available tools
            list_message = json.dumps(SAMPLE_MCP_LIST_TOOLS) + "\n"
            process.stdin.write(list_message.encode())
            await process.stdin.drain()

            response_line = await asyncio.wait_for(
                process.stdout.readline(), timeout=5.0
            )
            list_response = json.loads(response_line.decode().strip())

            assert list_response["jsonrpc"] == "2.0"
            assert list_response["id"] == 2
            assert "result" in list_response
            assert "tools" in list_response["result"]
            assert len(list_response["result"]["tools"]) > 0

            # 3. Execute a tool (this may fail due to no real API, but should be properly formatted)
            tool_call = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "send_text_message",
                    "arguments": {
                        "instance": "test_instance",
                        "number": "1234567890",
                        "text": "Test message",
                    },
                },
                "id": 3,
            }

            call_message = json.dumps(tool_call) + "\n"
            process.stdin.write(call_message.encode())
            await process.stdin.drain()

            response_line = await asyncio.wait_for(
                process.stdout.readline(), timeout=5.0
            )
            call_response = json.loads(response_line.decode().strip())

            assert call_response["jsonrpc"] == "2.0"
            assert call_response["id"] == 3
            # Should get either a result or an error (error is OK for testing)
            assert "result" in call_response or "error" in call_response

        finally:
            # Clean up
            process.terminate()
            await process.wait()

    def test_cli_to_sse_server_startup(self, mock_evolution_config):
        """Test that CLI can start SSE server successfully"""
        # Use port 0 to avoid conflicts
        env = {**mock_evolution_config, "PORT": "0"}

        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "automagik_tools.cli",
                "serve",
                "--tool",
                "evolution-api",
                "--transport",
                "sse",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        try:
            # Give it time to start
            stdout, stderr = process.communicate(timeout=3)
            # If it times out, that means it's running (good)
        except subprocess.TimeoutExpired:
            process.terminate()
            stdout, stderr = process.communicate()

        output = stdout.decode() + stderr.decode()

        # Should show server startup messages
        assert "Tool 'evolution-api' loaded successfully" in output
        assert "Starting" in output

    def test_multi_tool_server_startup(self, mock_evolution_config):
        """Test that multi-tool server starts successfully"""
        import os

        env = os.environ.copy()
        env.update(mock_evolution_config)
        env["PORT"] = "0"

        process = subprocess.Popen(
            ["python", "-m", "automagik_tools.cli", "serve-all"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        try:
            stdout, stderr = process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            process.terminate()
            stdout, stderr = process.communicate()

        output = stdout.decode() + stderr.decode()

        # Should show multi-tool server startup
        assert "evolution-api" in output
        assert "Multi-tool server" in output or "Starting" in output


class TestPackageBuildAndInstall:
    """Test package building and installation workflows"""

    def test_package_builds_successfully(self, project_root):
        """Test that the package builds without errors"""
        result = subprocess.run(
            ["python", "-m", "build", "--no-isolation"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        # Build should succeed
        assert result.returncode == 0

        # Should create distribution files
        dist_dir = project_root / "dist"
        assert dist_dir.exists()

        # Should have both sdist and wheel
        files = list(dist_dir.glob("*"))
        tar_gz_files = [f for f in files if f.suffix == ".gz"]
        whl_files = [f for f in files if f.suffix == ".whl"]

        assert len(tar_gz_files) >= 1
        assert len(whl_files) >= 1

    def test_entry_points_work_after_install(self, project_root):
        """Test that entry points work after package installation"""
        # Install in development mode using uv
        result = subprocess.run(
            ["uv", "pip", "install", "-e", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        # Installation should succeed
        assert result.returncode == 0

        # Entry point should be available
        result = subprocess.run(
            ["automagik-tools", "--help"], capture_output=True, text=True
        )

        assert result.returncode == 0
        assert "automagik-tools" in result.stdout

    def test_uvx_installation_works(self, project_root):
        """Test that uvx can install and run the package"""
        # Test uvx with local installation
        result = subprocess.run(
            ["uvx", "--from", str(project_root), "automagik-tools", "--help"],
            capture_output=True,
            text=True,
        )

        # Should work or provide meaningful error
        assert result.returncode == 0 or "automagik-tools" in result.stderr


class TestConfigurationIntegration:
    """Test configuration handling in integrated scenarios"""

    def test_environment_variable_precedence(self, temp_config_dir):
        """Test that environment variables take precedence"""
        env = {
            "EVOLUTION_API_BASE_URL": "http://test-env.example.com",
            "EVOLUTION_API_KEY": "env_test_key",
        }

        result = subprocess.run(
            ["python", "-m", "automagik_tools.cli", "list"],
            env=env,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # The tool should load with environment config
        assert "evolution-api" in result.stdout

    def test_missing_config_graceful_handling(self):
        """Test that missing configuration is handled gracefully"""
        # Remove all Evolution API environment variables
        env = {
            k: v
            for k, v in __import__("os").environ.items()
            if not k.startswith("EVOLUTION_API")
        }

        result = subprocess.run(
            ["python", "-m", "automagik_tools.cli", "list"],
            env=env,
            capture_output=True,
            text=True,
        )

        # Should still work with default config
        assert result.returncode == 0
        assert "evolution-api" in result.stdout


class TestErrorRecoveryAndResilience:
    """Test error recovery and system resilience"""

    @pytest.mark.asyncio
    async def test_server_recovers_from_malformed_input(self, mock_evolution_config):
        """Test that server recovers from malformed JSON input"""
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "automagik_tools.cli",
            "serve",
            "--tool",
            "evolution-api",
            "--transport",
            "stdio",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**mock_evolution_config},
        )

        try:
            # Send malformed JSON
            malformed = '{"invalid": json,}\n'
            process.stdin.write(malformed.encode())
            await process.stdin.drain()

            # Wait a bit
            await asyncio.sleep(0.5)

            # Send valid initialization - should still work
            init_message = json.dumps(SAMPLE_MCP_INITIALIZE) + "\n"
            process.stdin.write(init_message.encode())
            await process.stdin.drain()

            # Should get a response to the valid message
            response_line = await asyncio.wait_for(
                process.stdout.readline(), timeout=3.0
            )

            response = json.loads(response_line.decode().strip())
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == 1

        finally:
            process.terminate()
            await process.wait()

    def test_graceful_shutdown_on_interrupt(self, mock_evolution_config):
        """Test that server shuts down gracefully on interrupt"""
        env = {**mock_evolution_config, "PORT": "0"}

        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "automagik_tools.cli",
                "serve",
                "--tool",
                "evolution-api",
                "--transport",
                "sse",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        # Give it time to start
        time.sleep(1)

        # Send interrupt signal
        process.send_signal(signal.SIGINT)

        # Should terminate gracefully within reasonable time
        try:
            stdout, stderr = process.communicate(timeout=5)
            # If it completes within timeout, it handled the interrupt
            assert process.returncode is not None
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't respond to interrupt
            process.kill()
            stdout, stderr = process.communicate()
            # This is a failure case
            pytest.fail("Server did not respond to interrupt signal")


class TestPerformanceAndScaling:
    """Test performance characteristics and scaling"""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self, mock_evolution_config):
        """Test handling multiple concurrent MCP requests"""
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "automagik_tools.cli",
            "serve",
            "--tool",
            "evolution-api",
            "--transport",
            "stdio",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**mock_evolution_config},
        )

        try:
            # Initialize
            init_message = json.dumps(SAMPLE_MCP_INITIALIZE) + "\n"
            process.stdin.write(init_message.encode())
            await process.stdin.drain()

            # Read init response
            await process.stdout.readline()

            # Send multiple requests quickly
            messages = []
            for i in range(5):
                message = {"jsonrpc": "2.0", "method": "tools/list", "id": i + 2}
                messages.append(json.dumps(message) + "\n")

            # Send all messages
            for msg in messages:
                process.stdin.write(msg.encode())
            await process.stdin.drain()

            # Read all responses
            responses = []
            for _ in range(5):
                response_line = await asyncio.wait_for(
                    process.stdout.readline(), timeout=3.0
                )
                response = json.loads(response_line.decode().strip())
                responses.append(response)

            # All should be successful
            assert len(responses) == 5
            for i, response in enumerate(responses):
                assert response["jsonrpc"] == "2.0"
                assert response["id"] == i + 2
                assert "result" in response

        finally:
            process.terminate()
            await process.wait()

    def test_memory_usage_reasonable(self, mock_evolution_config):
        """Test that memory usage is reasonable during operation"""
        try:
            import psutil
        except ImportError:
            pytest.skip("psutil not installed, skipping memory test")

        env = {**mock_evolution_config, "PORT": "0"}

        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "automagik_tools.cli",
                "serve",
                "--tool",
                "evolution-api",
                "--transport",
                "sse",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        try:
            # Give it time to start
            time.sleep(2)

            # Check memory usage
            ps_process = psutil.Process(process.pid)
            memory_info = ps_process.memory_info()

            # Memory usage should be reasonable (less than 200MB for basic operation)
            assert memory_info.rss < 200 * 1024 * 1024  # 200MB in bytes

        finally:
            process.terminate()
            process.wait()


class TestDocumentationAndExamples:
    """Test that documentation examples work"""

    def test_readme_examples_work(self, project_root):
        """Test that examples from README actually work"""
        # Test basic list command mentioned in README
        result = subprocess.run(
            ["python", "-m", "automagik_tools.cli", "list"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "evolution-api" in result.stdout
        assert "Available Tools" in result.stdout

    def test_help_output_comprehensive(self, project_root):
        """Test that help output is comprehensive and useful"""
        # Main help
        result = subprocess.run(
            ["python", "-m", "automagik_tools.cli", "--help"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "serve" in result.stdout
        assert "serve-all" in result.stdout
        assert "list" in result.stdout
        assert "version" in result.stdout

        # Serve command help
        result = subprocess.run(
            ["python", "-m", "automagik_tools.cli", "serve", "--help"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "--tool" in result.stdout
        assert "--transport" in result.stdout
