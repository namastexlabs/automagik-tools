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
    instructions="Simple wait functionality for agent workflows.",
)


def _validate_duration(duration_minutes: float, config: WaitConfig) -> None:
    """Validate duration parameters"""
    if duration_minutes <= 0:
        raise ValueError("Duration must be positive")
    duration_seconds = duration_minutes * 60
    if duration_seconds > config.max_duration:
        raise ValueError(f"Duration {duration_seconds}s exceeds max {config.max_duration}s")


def _get_iso_timestamp(timestamp: Optional[float] = None) -> str:
    """Get ISO-8601 timestamp"""
    dt = datetime.fromtimestamp(timestamp or time.time(), timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


@mcp.tool()
async def wait_minutes(duration: float, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """Wait for specified minutes"""
    global config
    if not config:
        raise ValueError("Tool not configured")
    
    _validate_duration(duration, config)
    
    duration_seconds = duration * 60
    start_time = time.time()
    start_iso = _get_iso_timestamp(start_time)

    try:
        await asyncio.sleep(duration_seconds)
        end_time = time.time()
        actual_duration = end_time - start_time
        return {
            "status": "completed",
            "duration_minutes": round(duration, 3),
            "duration_seconds": round(actual_duration, 3),
            "start_time": start_time,
            "start_iso": start_iso,
            "end_time": end_time,
            "end_iso": _get_iso_timestamp(end_time)
        }
    except asyncio.CancelledError:
        end_time = time.time()
        actual_duration = end_time - start_time
        return {
            "status": "cancelled",
            "duration_minutes": round(duration, 3),
            "duration_seconds": round(actual_duration, 3),
            "start_time": start_time,
            "start_iso": start_iso,
            "end_time": end_time,
            "end_iso": _get_iso_timestamp(end_time)
        }


def get_metadata() -> Dict[str, Any]:
    """Return tool metadata for discovery"""
    return {
        "name": "wait",
        "version": "2.2.0",
        "description": "Simple wait functionality for agent workflows",
        "author": "Namastex Labs",
        "category": "utility",
        "tags": ["timing", "delay", "workflow"],
    }


def get_config_class():
    """Return the config class for this tool"""
    return WaitConfig


def create_server(tool_config: Optional[WaitConfig] = None):
    """Create FastMCP server instance"""
    global config
    config = tool_config or WaitConfig()
    return mcp