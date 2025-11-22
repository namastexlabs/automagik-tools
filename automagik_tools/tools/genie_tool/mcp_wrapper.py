"""
MCP Server wrapper that filters out repetitive stdout messages.
This prevents servers like Linear from corrupting SSE streams.
"""

import sys
import asyncio
import os
import signal
from typing import Optional, List


class FilteredMCPServer:
    """Wraps an MCP server command and filters its output"""

    def __init__(
        self,
        command: List[str],
        env: Optional[dict] = None,
        filter_patterns: Optional[List[str]] = None,
    ):
        self.command = command
        self.env = env
        self.filter_patterns = filter_patterns or [
            "MCP Linear is running",
            "Starting MCP Linear...",
            "MCP Linear version:",
            "Linear MCP server started",
        ]
        self.process = None
        self.stdout_task = None
        self.stderr_task = None
        self.transport_mode = os.environ.get("AUTOMAGIK_TRANSPORT", "stdio")

    async def start(self):
        """Start the MCP server with filtered output"""
        # For SSE transport, be more aggressive about subprocess management
        if self.transport_mode == "sse":
            # Create new process group to isolate subprocess
            create_new_process_group = True if os.name != "nt" else False
        else:
            create_new_process_group = False

        # Start the subprocess with pipes
        kwargs = {
            "stdin": asyncio.subprocess.PIPE,
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.PIPE,
            "env": self.env,
        }

        # On Unix systems, create new process group for better cleanup
        if create_new_process_group and hasattr(
            asyncio.subprocess, "CREATE_NEW_PROCESS_GROUP"
        ):
            kwargs["creationflags"] = asyncio.subprocess.CREATE_NEW_PROCESS_GROUP
        elif create_new_process_group:
            kwargs["preexec_fn"] = os.setsid

        self.process = await asyncio.create_subprocess_exec(*self.command, **kwargs)

        # Start tasks to handle stdout and stderr
        self.stdout_task = asyncio.create_task(self._filter_stdout())
        self.stderr_task = asyncio.create_task(self._forward_stderr())

        return self.process

    async def _filter_stdout(self):
        """Filter stdout, removing unwanted patterns"""
        line_count = 0
        max_filtered_lines = 100  # Prevent infinite filtering

        while self.process and self.process.stdout:
            try:
                line = await asyncio.wait_for(
                    self.process.stdout.readline(), timeout=1.0
                )
                if not line:
                    break

                line_str = line.decode("utf-8", errors="ignore").rstrip()

                # Skip lines that match filter patterns
                should_skip = any(
                    pattern in line_str for pattern in self.filter_patterns
                )

                if should_skip:
                    line_count += 1
                    # In SSE mode, be more aggressive about filtering
                    if self.transport_mode == "sse" and line_count > max_filtered_lines:
                        # Too many filtered lines, might be flooding
                        print(
                            f"Warning: Filtered {line_count} lines from MCP server",
                            file=sys.stderr,
                            flush=True,
                        )
                        break
                elif line_str:
                    # Forward non-filtered lines to stdout
                    print(line_str, flush=True)

            except asyncio.TimeoutError:
                # Timeout reading stdout - check if process is still alive
                if self.process.returncode is not None:
                    break
                continue
            except Exception as e:
                print(f"Error filtering stdout: {e}", file=sys.stderr, flush=True)
                break

    async def _forward_stderr(self):
        """Forward stderr without filtering"""
        while self.process and self.process.stderr:
            try:
                line = await asyncio.wait_for(
                    self.process.stderr.readline(), timeout=1.0
                )
                if not line:
                    break

                # Forward to stderr
                sys.stderr.write(line.decode("utf-8", errors="ignore"))
                sys.stderr.flush()

            except asyncio.TimeoutError:
                # Timeout reading stderr - check if process is still alive
                if self.process.returncode is not None:
                    break
                continue
            except Exception as e:
                print(f"Error forwarding stderr: {e}", file=sys.stderr, flush=True)
                break

    async def stop(self):
        """Stop the MCP server with aggressive cleanup for SSE"""
        if self.process:
            try:
                # Cancel stdout/stderr tasks first
                if self.stdout_task and not self.stdout_task.done():
                    self.stdout_task.cancel()
                if self.stderr_task and not self.stderr_task.done():
                    self.stderr_task.cancel()

                # For SSE transport, be more aggressive about termination
                if self.transport_mode == "sse":
                    # Try graceful termination first
                    self.process.terminate()

                    try:
                        # Wait up to 1 second for graceful shutdown
                        await asyncio.wait_for(self.process.wait(), timeout=1.0)
                    except asyncio.TimeoutError:
                        # Force kill if graceful termination fails
                        self.process.kill()
                        await self.process.wait()

                    # On Unix systems, also try to kill the process group
                    if hasattr(os, "killpg") and hasattr(os, "SIGTERM"):
                        try:
                            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                        except (OSError, ProcessLookupError):
                            pass  # Process already dead or not in a process group
                else:
                    # Stdio mode - gentler cleanup
                    self.process.terminate()
                    await self.process.wait()

            except Exception as e:
                print(f"Error stopping MCP server: {e}", file=sys.stderr, flush=True)


async def main():
    """Main entry point when used as a wrapper script"""
    if len(sys.argv) < 2:
        print("Usage: python -m mcp_wrapper <command> [args...]", file=sys.stderr)
        sys.exit(1)

    # Get command from arguments
    command = sys.argv[1:]

    # Create and start filtered server
    server = FilteredMCPServer(command)
    process = await server.start()

    # Create task to forward stdin to the subprocess
    stdin_task = asyncio.create_task(forward_stdin_to_process(process))

    # Wait for process to complete
    await process.wait()

    # Cancel stdin forwarding
    stdin_task.cancel()


async def forward_stdin_to_process(process):
    """Forward stdin from parent to subprocess"""
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
            process.stdin.write(data)
            await process.stdin.drain()
    except asyncio.CancelledError:
        pass
    finally:
        if process.stdin:
            process.stdin.close()


if __name__ == "__main__":
    asyncio.run(main())
