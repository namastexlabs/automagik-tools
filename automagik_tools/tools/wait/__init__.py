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
    instructions="Smart timing functions: blocking waits with progress tracking.",
)


def _validate_duration(duration: float, config: WaitConfig) -> None:
    """Validate duration parameters"""
    if duration <= 0:
        raise ValueError("Duration must be positive")
    if duration > config.max_duration:
        raise ValueError(f"Duration {duration}s exceeds max {config.max_duration}s")


def _get_iso_timestamp(timestamp: Optional[float] = None) -> str:
    """Get ISO-8601 timestamp"""
    dt = datetime.fromtimestamp(timestamp or time.time(), timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


@mcp.tool()
async def wait_seconds(duration: float, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """Wait for specified seconds (blocking)"""
    global config
    if not config:
        raise ValueError("Tool not configured")
    
    _validate_duration(duration, config)
    start_time = time.time()
    start_iso = _get_iso_timestamp(start_time)

    try:
        await asyncio.sleep(duration)
        end_time = time.time()
        return {
            "status": "completed",
            "duration": round(end_time - start_time, 3),
            "start_time": start_time,
            "start_iso": start_iso,
            "end_time": end_time,
            "end_iso": _get_iso_timestamp(end_time)
        }
    except asyncio.CancelledError:
        end_time = time.time()
        return {
            "status": "cancelled",
            "duration": round(end_time - start_time, 3),
            "start_time": start_time,
            "start_iso": start_iso,
            "end_time": end_time,
            "end_iso": _get_iso_timestamp(end_time)
        }


@mcp.tool()
async def wait_minutes(duration: float, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """Wait for specified minutes (blocking)"""
    result = await wait_seconds(duration * 60, ctx)
    result["duration_minutes"] = round(result["duration"] / 60, 3)
    return result


@mcp.tool()
async def wait_until_timestamp(timestamp: str, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """Wait until ISO 8601 timestamp (blocking)"""
    global config
    if not config:
        raise ValueError("Tool not configured")

    try:
        target_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        current_time = datetime.now(timezone.utc)
        wait_duration = (target_time - current_time).total_seconds()

        if wait_duration < 0:
            return {
                "status": "already_passed",
                "target_iso": timestamp,
                "current_iso": _get_iso_timestamp(),
                "time_diff": wait_duration
            }

        _validate_duration(wait_duration, config)
        result = await wait_seconds(wait_duration, ctx)
        result["target_iso"] = timestamp
        return result

    except ValueError as e:
        if "exceeds max" in str(e):
            raise e
        return {
            "status": "error",
            "target_iso": timestamp,
            "error": "Invalid ISO 8601 format"
        }


@mcp.tool()
async def wait_with_progress(
    duration: float, interval: float = 1.0, ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """Wait with real-time progress updates (blocking)"""
    global config
    if not config:
        raise ValueError("Tool not configured")
    
    _validate_duration(duration, config)
    if interval <= 0:
        raise ValueError("Interval must be positive")
    
    if interval == 1.0 and config.default_progress_interval != 1.0:
        interval = config.default_progress_interval

    start_time = time.time()
    start_iso = _get_iso_timestamp(start_time)
    elapsed = 0.0
    reports = 0

    try:
        while elapsed < duration:
            remaining = duration - elapsed
            sleep_duration = min(interval, remaining)
            await asyncio.sleep(sleep_duration)
            
            elapsed = time.time() - start_time
            reports += 1

            if ctx:
                # Real-time progress streaming
                await ctx.report_progress(progress=elapsed, total=duration)

        end_time = time.time()
        return {
            "status": "completed",
            "duration": round(end_time - start_time, 3),
            "interval": interval,
            "reports": reports,
            "start_time": start_time,
            "start_iso": start_iso,
            "end_time": end_time,
            "end_iso": _get_iso_timestamp(end_time)
        }

    except asyncio.CancelledError:
        end_time = time.time()
        return {
            "status": "cancelled",
            "duration": round(end_time - start_time, 3),
            "interval": interval,
            "reports": reports,
            "start_time": start_time,
            "start_iso": start_iso,
            "end_time": end_time,
            "end_iso": _get_iso_timestamp(end_time)
        }


def get_metadata() -> Dict[str, Any]:
    """Return tool metadata for discovery"""
    return {
        "name": "wait",
        "version": "2.1.0",
        "description": "Timing functions: blocking waits with progress tracking",
        "author": "Namastex Labs",
        "category": "utility",
        "tags": ["timing", "delay", "workflow", "progress"],
    }


def get_config_class():
    """Return the config class for this tool"""
    return WaitConfig


def create_server(tool_config: Optional[WaitConfig] = None):
    """Create FastMCP server instance"""
    global config
    config = tool_config or WaitConfig()
    return mcp