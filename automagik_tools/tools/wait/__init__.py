"""
Wait Utility - Smart Timing Functions for Agent Workflows

This tool provides intelligent waiting capabilities for agents, particularly useful for
workflow polling delays, rate limiting, and scheduled operations.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastmcp import FastMCP, Context
from .config import WaitConfig

# Global config instance
config: Optional[WaitConfig] = None

# Create FastMCP instance
mcp = FastMCP(
    "Wait Utility",
    instructions="""
Wait Utility - Smart timing functions for agent workflows

⏱️ Intelligent delay functions for workflow timing
🚦 Rate limiting and polling delay management  
📊 Progress reporting for long waits
⏰ Timestamp-based waiting capabilities

Perfect for workflow polling, rate limiting, and scheduled operations in automated systems.
""",
)


@mcp.tool()
async def wait_seconds(
    duration: float, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Wait for specified number of seconds

    Args:
        duration: Number of seconds to wait (must be positive)
        ctx: MCP context for logging

    Returns:
        Dict containing wait details and completion status
    """
    global config
    if not config:
        raise ValueError("Tool not configured")

    # Validate duration
    if duration <= 0:
        raise ValueError("Duration must be positive")

    if duration > config.max_duration:
        raise ValueError(
            f"Duration {duration}s exceeds maximum allowed {config.max_duration}s"
        )

    start_time = time.time()

    if ctx:
        ctx.info(f"⏱️ Starting wait for {duration} seconds")

    try:
        await asyncio.sleep(duration)

        actual_duration = time.time() - start_time

        if ctx:
            ctx.info(f"✅ Wait completed after {actual_duration:.2f} seconds")

        return {
            "status": "completed",
            "requested_duration": duration,
            "actual_duration": round(actual_duration, 3),
            "start_time": start_time,
            "end_time": time.time(),
            "message": f"Successfully waited {duration} seconds",
        }

    except asyncio.CancelledError:
        actual_duration = time.time() - start_time
        if ctx:
            ctx.info(f"⚠️ Wait cancelled after {actual_duration:.2f} seconds")

        return {
            "status": "cancelled",
            "requested_duration": duration,
            "actual_duration": round(actual_duration, 3),
            "start_time": start_time,
            "end_time": time.time(),
            "message": f"Wait cancelled after {actual_duration:.2f} seconds",
        }


@mcp.tool()
async def wait_minutes(
    duration: float, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Wait for specified number of minutes

    Args:
        duration: Number of minutes to wait (must be positive)
        ctx: MCP context for logging

    Returns:
        Dict containing wait details and completion status
    """
    # Convert minutes to seconds
    duration_seconds = duration * 60

    if ctx:
        ctx.info(f"⏱️ Converting {duration} minutes to {duration_seconds} seconds")

    # Use wait_seconds for the actual implementation
    result = await wait_seconds(duration_seconds, ctx)

    # Update the result to include minute information
    result["requested_duration_minutes"] = duration
    result["message"] = (
        f"Successfully waited {duration} minutes ({duration_seconds} seconds)"
    )

    return result


@mcp.tool()
async def wait_until_timestamp(
    timestamp: str, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Wait until specific ISO 8601 timestamp

    Args:
        timestamp: Target timestamp in ISO 8601 format (e.g., "2024-01-01T12:00:00Z")
        ctx: MCP context for logging

    Returns:
        Dict containing wait details and completion status
    """
    global config
    if not config:
        raise ValueError("Tool not configured")

    try:
        # Parse the timestamp
        target_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        current_time = datetime.now(timezone.utc)

        # Calculate wait duration
        wait_duration = (target_time - current_time).total_seconds()

        if wait_duration < 0:
            if ctx:
                ctx.info(f"⚠️ Target timestamp {timestamp} is in the past")

            return {
                "status": "already_passed",
                "target_timestamp": timestamp,
                "current_time": current_time.isoformat(),
                "time_difference": wait_duration,
                "message": f"Target timestamp {timestamp} is {abs(wait_duration):.1f} seconds in the past",
            }

        if wait_duration > config.max_duration:
            raise ValueError(
                f"Wait duration {wait_duration:.1f}s exceeds maximum allowed {config.max_duration}s"
            )

        if ctx:
            ctx.info(
                f"⏰ Waiting until {timestamp} ({wait_duration:.1f} seconds from now)"
            )

        # Use wait_seconds for the actual waiting
        result = await wait_seconds(wait_duration, ctx)

        # Update result with timestamp information
        result["target_timestamp"] = timestamp
        result["start_timestamp"] = current_time.isoformat()
        result["message"] = f"Successfully waited until {timestamp}"

        return result

    except ValueError as e:
        if "exceeds maximum" in str(e):
            raise e

        if ctx:
            ctx.error(f"❌ Invalid timestamp format: {timestamp}")

        return {
            "status": "error",
            "target_timestamp": timestamp,
            "error": f"Invalid timestamp format: {timestamp}",
            "message": "Timestamp must be in ISO 8601 format (e.g., '2024-01-01T12:00:00Z')",
        }


@mcp.tool()
async def wait_with_progress(
    duration: float, interval: float = 1.0, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Wait with progress updates at specified intervals

    Args:
        duration: Total duration to wait in seconds (must be positive)
        interval: Progress reporting interval in seconds (default: 1.0)
        ctx: MCP context for progress reporting

    Returns:
        Dict containing wait details and completion status
    """
    global config
    if not config:
        raise ValueError("Tool not configured")

    # Validate inputs
    if duration <= 0:
        raise ValueError("Duration must be positive")

    if interval <= 0:
        raise ValueError("Interval must be positive")

    if duration > config.max_duration:
        raise ValueError(
            f"Duration {duration}s exceeds maximum allowed {config.max_duration}s"
        )

    # Use default interval from config if not specified
    if interval == 1.0 and config.default_progress_interval != 1.0:
        interval = config.default_progress_interval

    start_time = time.time()
    elapsed = 0.0
    progress_reports = 0

    if ctx:
        ctx.info(f"⏳ Starting {duration}s wait with {interval}s progress intervals")

    try:
        while elapsed < duration:
            # Calculate remaining time and next sleep duration
            remaining = duration - elapsed
            sleep_duration = min(interval, remaining)

            # Sleep for the interval or remaining time
            await asyncio.sleep(sleep_duration)

            elapsed = time.time() - start_time
            progress_reports += 1

            # Report progress if context is available
            if ctx:
                progress_percentage = (elapsed / duration) * 100
                try:
                    await ctx.report_progress(
                        progress=int(elapsed), total=int(duration)
                    )
                except Exception:
                    # Context reporting might not be available, continue without it
                    pass
                ctx.info(
                    f"📊 Progress: {elapsed:.1f}/{duration}s ({progress_percentage:.1f}%)"
                )

        actual_duration = time.time() - start_time

        if ctx:
            ctx.info(
                f"✅ Wait with progress completed after {actual_duration:.2f} seconds"
            )

        return {
            "status": "completed",
            "requested_duration": duration,
            "actual_duration": round(actual_duration, 3),
            "progress_interval": interval,
            "progress_reports": progress_reports,
            "start_time": start_time,
            "end_time": time.time(),
            "message": f"Successfully waited {duration} seconds with {progress_reports} progress updates",
        }

    except asyncio.CancelledError:
        actual_duration = time.time() - start_time

        if ctx:
            ctx.info(
                f"⚠️ Wait with progress cancelled after {actual_duration:.2f} seconds"
            )

        return {
            "status": "cancelled",
            "requested_duration": duration,
            "actual_duration": round(actual_duration, 3),
            "progress_interval": interval,
            "progress_reports": progress_reports,
            "start_time": start_time,
            "end_time": time.time(),
            "message": f"Wait cancelled after {actual_duration:.2f} seconds with {progress_reports} progress updates",
        }


def get_metadata() -> Dict[str, Any]:
    """Return tool metadata for discovery"""
    return {
        "name": "wait",
        "version": "1.0.0",
        "description": "Smart timing functions for agent workflows including delays, progress reporting, and timestamp waiting",
        "author": "Namastex Labs",
        "category": "utility",
        "tags": ["timing", "delay", "workflow", "progress", "scheduling"],
    }


def get_config_class():
    """Return the config class for this tool"""
    return WaitConfig


def create_server(tool_config: Optional[WaitConfig] = None):
    """Create FastMCP server instance"""
    global config
    config = tool_config or WaitConfig()
    return mcp
