"""
Wait Utility - Smart Timing Functions for Agent Workflows

This tool provides intelligent waiting capabilities for agents, particularly useful for
workflow polling delays, rate limiting, and scheduled operations.
"""

import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

from fastmcp import FastMCP, Context
from .config import WaitConfig

# Global config instance
config: Optional[WaitConfig] = None

# Timer registry for non-blocking operations
active_timers: Dict[str, 'TimerHandle'] = {}

class TimerStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"

@dataclass
class TimerHandle:
    timer_id: str
    status: TimerStatus
    start_time: float
    start_iso: str
    duration: float
    end_time: Optional[float] = None
    end_iso: Optional[str] = None
    progress: float = 0.0
    task: Optional[asyncio.Task] = None
    error: Optional[str] = None

# Create FastMCP instance
mcp = FastMCP(
    "Wait Utility",
    instructions="Smart timing functions: blocking waits, non-blocking timers, progress tracking, cancellation support.",
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
                # Real-time progress streaming - removed try/catch that was silencing errors
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


# Non-blocking timer functions

async def _timer_task(timer_id: str, duration: float, interval: Optional[float] = None) -> None:
    """Background task for non-blocking timers"""
    handle = active_timers.get(timer_id)
    if not handle:
        return
    
    try:
        elapsed = 0.0
        while elapsed < duration and handle.status == TimerStatus.RUNNING:
            if interval and interval > 0:
                sleep_duration = min(interval, duration - elapsed)
            else:
                sleep_duration = min(0.1, duration - elapsed)  # Small default interval
            
            await asyncio.sleep(sleep_duration)
            elapsed = time.time() - handle.start_time
            handle.progress = min(elapsed / duration, 1.0)
            
            if handle.status != TimerStatus.RUNNING:
                break
        
        if handle.status == TimerStatus.RUNNING:
            handle.status = TimerStatus.COMPLETED
            handle.end_time = time.time()
            handle.end_iso = _get_iso_timestamp(handle.end_time)
            handle.progress = 1.0
            
    except asyncio.CancelledError:
        handle.status = TimerStatus.CANCELLED
        handle.end_time = time.time()
        handle.end_iso = _get_iso_timestamp(handle.end_time)
    except Exception as e:
        handle.status = TimerStatus.ERROR
        handle.end_time = time.time()
        handle.end_iso = _get_iso_timestamp(handle.end_time)
        handle.error = str(e)


@mcp.tool()
async def start_timer(duration: float, interval: Optional[float] = None, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """Start non-blocking timer, returns immediately with timer ID"""
    global config
    if not config:
        raise ValueError("Tool not configured")
    
    _validate_duration(duration, config)
    
    timer_id = str(uuid.uuid4())
    start_time = time.time()
    start_iso = _get_iso_timestamp(start_time)
    
    handle = TimerHandle(
        timer_id=timer_id,
        status=TimerStatus.RUNNING,
        start_time=start_time,
        start_iso=start_iso,
        duration=duration,
        progress=0.0
    )
    
    active_timers[timer_id] = handle
    handle.task = asyncio.create_task(_timer_task(timer_id, duration, interval))
    
    return {
        "timer_id": timer_id,
        "status": "running",
        "duration": duration,
        "start_time": start_time,
        "start_iso": start_iso
    }


@mcp.tool()
async def get_timer_status(timer_id: str, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """Get status of timer by ID"""
    handle = active_timers.get(timer_id)
    if not handle:
        return {"error": "Timer not found"}
    
    result = {
        "timer_id": timer_id,
        "status": handle.status.value,
        "progress": round(handle.progress, 3),
        "duration": handle.duration,
        "start_time": handle.start_time,
        "start_iso": handle.start_iso
    }
    
    if handle.end_time:
        result["end_time"] = handle.end_time
        result["end_iso"] = handle.end_iso
        result["elapsed"] = round(handle.end_time - handle.start_time, 3)
    else:
        result["elapsed"] = round(time.time() - handle.start_time, 3)
    
    if handle.error:
        result["error"] = handle.error
        
    return result


@mcp.tool()
async def cancel_timer(timer_id: str, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """Cancel running timer by ID"""
    handle = active_timers.get(timer_id)
    if not handle:
        return {"error": "Timer not found"}
    
    if handle.status != TimerStatus.RUNNING:
        return {"error": f"Timer already {handle.status.value}"}
    
    handle.status = TimerStatus.CANCELLED
    if handle.task and not handle.task.done():
        handle.task.cancel()
    
    return {
        "timer_id": timer_id,
        "status": "cancelled",
        "elapsed": round(time.time() - handle.start_time, 3)
    }


@mcp.tool()
async def list_active_timers(ctx: Optional[Context] = None) -> Dict[str, Any]:
    """List all active timers"""
    timers = []
    current_time = time.time()
    
    for timer_id, handle in active_timers.items():
        elapsed = current_time - handle.start_time
        timers.append({
            "timer_id": timer_id,
            "status": handle.status.value,
            "progress": round(handle.progress, 3),
            "elapsed": round(elapsed, 3),
            "duration": handle.duration
        })
    
    return {
        "active_timers": len([t for t in timers if t["status"] == "running"]),
        "total_timers": len(timers),
        "timers": timers
    }


@mcp.tool()
async def cleanup_timers(ctx: Optional[Context] = None) -> Dict[str, Any]:
    """Remove completed/cancelled timers from memory"""
    global active_timers
    
    before_count = len(active_timers)
    active_timers = {
        timer_id: handle for timer_id, handle in active_timers.items()
        if handle.status == TimerStatus.RUNNING
    }
    
    cleaned = before_count - len(active_timers)
    return {
        "cleaned": cleaned,
        "remaining": len(active_timers)
    }


def get_metadata() -> Dict[str, Any]:
    """Return tool metadata for discovery"""
    return {
        "name": "wait",
        "version": "2.0.0",
        "description": "Timing functions: blocking waits, non-blocking timers, progress tracking, cancellation support",
        "author": "Namastex Labs",
        "category": "utility",
        "tags": ["timing", "delay", "workflow", "progress", "async", "cancellation"],
    }


def get_config_class():
    """Return the config class for this tool"""
    return WaitConfig


def create_server(tool_config: Optional[WaitConfig] = None):
    """Create FastMCP server instance"""
    global config
    config = tool_config or WaitConfig()
    return mcp
