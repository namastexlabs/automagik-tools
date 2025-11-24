"""Tool instance lifecycle management.

Manages running tool instances per user:
- Start tool with user-specific configuration
- Stop running tool instances
- Refresh/reload tool configuration
- Track tool runtime status
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ToolStatus(str, Enum):
    """Tool instance status."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class ToolInstance:
    """Represents a running tool instance for a specific user."""

    def __init__(self, tool_name: str, user_id: str, config: Dict[str, Any]):
        self.tool_name = tool_name
        self.user_id = user_id
        self.config = config
        self.status = ToolStatus.STOPPED
        self.started_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.process: Optional[asyncio.subprocess.Process] = None

    async def start(self) -> None:
        """Start the tool instance."""
        if self.status == ToolStatus.RUNNING:
            logger.warning(f"Tool {self.tool_name} already running for user {self.user_id}")
            return

        self.status = ToolStatus.STARTING
        try:
            # TODO: Implement actual tool process spawning
            # For now, just mark as running
            # In production, this would:
            # 1. Create isolated process/container
            # 2. Inject user configuration
            # 3. Start MCP server
            # 4. Monitor health

            await asyncio.sleep(0.1)  # Simulate startup
            self.status = ToolStatus.RUNNING
            self.started_at = datetime.utcnow()
            self.error_message = None
            logger.info(f"Started tool {self.tool_name} for user {self.user_id}")

        except Exception as e:
            self.status = ToolStatus.ERROR
            self.error_message = str(e)
            logger.error(f"Failed to start tool {self.tool_name} for user {self.user_id}: {e}")
            raise

    async def stop(self) -> None:
        """Stop the tool instance."""
        if self.status == ToolStatus.STOPPED:
            logger.warning(f"Tool {self.tool_name} already stopped for user {self.user_id}")
            return

        self.status = ToolStatus.STOPPING
        try:
            # TODO: Implement actual process termination
            # For now, just mark as stopped

            if self.process:
                self.process.terminate()
                await self.process.wait()

            self.status = ToolStatus.STOPPED
            self.started_at = None
            logger.info(f"Stopped tool {self.tool_name} for user {self.user_id}")

        except Exception as e:
            self.status = ToolStatus.ERROR
            self.error_message = str(e)
            logger.error(f"Failed to stop tool {self.tool_name} for user {self.user_id}: {e}")
            raise

    async def refresh(self, new_config: Dict[str, Any]) -> None:
        """Refresh tool configuration (restart with new config)."""
        logger.info(f"Refreshing tool {self.tool_name} for user {self.user_id}")

        was_running = self.status == ToolStatus.RUNNING

        if was_running:
            await self.stop()

        self.config = new_config

        if was_running:
            await self.start()

    def get_status(self) -> Dict[str, Any]:
        """Get current tool status."""
        return {
            "tool_name": self.tool_name,
            "user_id": self.user_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "error_message": self.error_message,
            "uptime_seconds": (datetime.utcnow() - self.started_at).total_seconds() if self.started_at else 0
        }


class ToolInstanceManager:
    """Manages all tool instances across users."""

    def __init__(self):
        # Key: (user_id, tool_name) -> ToolInstance
        self._instances: Dict[tuple, ToolInstance] = {}
        self._lock = asyncio.Lock()

    def _get_key(self, user_id: str, tool_name: str) -> tuple:
        """Generate instance key."""
        return (user_id, tool_name)

    async def start_tool(self, user_id: str, tool_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Start a tool instance for a user."""
        async with self._lock:
            key = self._get_key(user_id, tool_name)

            if key in self._instances:
                instance = self._instances[key]
                if instance.status == ToolStatus.RUNNING:
                    return {
                        "status": "already_running",
                        "message": f"Tool {tool_name} is already running",
                        "instance": instance.get_status()
                    }
            else:
                instance = ToolInstance(tool_name, user_id, config)
                self._instances[key] = instance

            await instance.start()

            return {
                "status": "started",
                "message": f"Tool {tool_name} started successfully",
                "instance": instance.get_status()
            }

    async def stop_tool(self, user_id: str, tool_name: str) -> Dict[str, Any]:
        """Stop a tool instance for a user."""
        async with self._lock:
            key = self._get_key(user_id, tool_name)

            if key not in self._instances:
                return {
                    "status": "not_found",
                    "message": f"Tool {tool_name} is not running",
                    "tool_name": tool_name
                }

            instance = self._instances[key]
            await instance.stop()

            # Remove stopped instance
            del self._instances[key]

            return {
                "status": "stopped",
                "message": f"Tool {tool_name} stopped successfully",
                "instance": instance.get_status()
            }

    async def refresh_tool(self, user_id: str, tool_name: str, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Refresh tool configuration."""
        async with self._lock:
            key = self._get_key(user_id, tool_name)

            if key not in self._instances:
                # Start new instance with config
                instance = ToolInstance(tool_name, user_id, new_config)
                self._instances[key] = instance
                await instance.start()
                action = "started"
            else:
                instance = self._instances[key]
                await instance.refresh(new_config)
                action = "refreshed"

            return {
                "status": "success",
                "message": f"Tool {tool_name} {action} successfully",
                "instance": instance.get_status()
            }

    async def get_tool_status(self, user_id: str, tool_name: str) -> Dict[str, Any]:
        """Get status of a tool instance."""
        key = self._get_key(user_id, tool_name)

        if key not in self._instances:
            return {
                "tool_name": tool_name,
                "user_id": user_id,
                "status": ToolStatus.STOPPED.value,
                "message": "Tool instance not running"
            }

        instance = self._instances[key]
        return instance.get_status()

    async def list_user_tools(self, user_id: str) -> list[Dict[str, Any]]:
        """List all running tools for a user."""
        return [
            instance.get_status()
            for (uid, _), instance in self._instances.items()
            if uid == user_id
        ]

    async def stop_all_user_tools(self, user_id: str) -> Dict[str, Any]:
        """Stop all tools for a user."""
        async with self._lock:
            stopped = []
            keys_to_remove = []

            for (uid, tool_name), instance in self._instances.items():
                if uid == user_id:
                    try:
                        await instance.stop()
                        stopped.append(tool_name)
                        keys_to_remove.append((uid, tool_name))
                    except Exception as e:
                        logger.error(f"Error stopping {tool_name} for {user_id}: {e}")

            for key in keys_to_remove:
                del self._instances[key]

            return {
                "status": "success",
                "message": f"Stopped {len(stopped)} tools",
                "stopped_tools": stopped
            }


# Global instance manager
_instance_manager: Optional[ToolInstanceManager] = None


def get_instance_manager() -> ToolInstanceManager:
    """Get the global tool instance manager."""
    global _instance_manager
    if _instance_manager is None:
        _instance_manager = ToolInstanceManager()
    return _instance_manager
