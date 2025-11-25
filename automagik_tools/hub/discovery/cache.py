"""In-memory cache for agents and projects.

Provides fast lookups without database queries.
Synced with database via file watcher.
"""
from typing import Dict, Optional, List
from datetime import datetime
import asyncio


class AgentCache:
    """Thread-safe in-memory cache for agents."""

    def __init__(self):
        """Initialize agent cache."""
        self._agents: Dict[str, dict] = {}  # agent_id -> agent_dict
        self._by_file_path: Dict[str, str] = {}  # file_path -> agent_id
        self._by_project: Dict[str, List[str]] = {}  # project_id -> [agent_ids]
        self._lock = asyncio.Lock()

    async def set(self, agent_id: str, agent_data: dict):
        """Add or update agent in cache.

        Args:
            agent_id: Agent ID
            agent_data: Agent dictionary
        """
        async with self._lock:
            self._agents[agent_id] = agent_data

            # Index by file path
            file_path = agent_data.get("file_path")
            if file_path:
                self._by_file_path[file_path] = agent_id

            # Index by project
            project_id = agent_data.get("project_id")
            if project_id:
                if project_id not in self._by_project:
                    self._by_project[project_id] = []
                if agent_id not in self._by_project[project_id]:
                    self._by_project[project_id].append(agent_id)

    async def get(self, agent_id: str) -> Optional[dict]:
        """Get agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Agent dict or None
        """
        async with self._lock:
            return self._agents.get(agent_id)

    async def get_by_file_path(self, file_path: str) -> Optional[dict]:
        """Get agent by file path.

        Args:
            file_path: Absolute file path

        Returns:
            Agent dict or None
        """
        async with self._lock:
            agent_id = self._by_file_path.get(file_path)
            if agent_id:
                return self._agents.get(agent_id)
            return None

    async def get_by_project(self, project_id: str) -> List[dict]:
        """Get all agents for a project.

        Args:
            project_id: Project ID

        Returns:
            List of agent dicts
        """
        async with self._lock:
            agent_ids = self._by_project.get(project_id, [])
            return [
                self._agents[aid]
                for aid in agent_ids
                if aid in self._agents
            ]

    async def remove(self, agent_id: str):
        """Remove agent from cache.

        Args:
            agent_id: Agent ID
        """
        async with self._lock:
            agent_data = self._agents.pop(agent_id, None)
            if not agent_data:
                return

            # Remove from file path index
            file_path = agent_data.get("file_path")
            if file_path:
                self._by_file_path.pop(file_path, None)

            # Remove from project index
            project_id = agent_data.get("project_id")
            if project_id and project_id in self._by_project:
                try:
                    self._by_project[project_id].remove(agent_id)
                except ValueError:
                    pass

    async def clear(self):
        """Clear all cache."""
        async with self._lock:
            self._agents.clear()
            self._by_file_path.clear()
            self._by_project.clear()

    async def reload_agent(self, file_path: str):
        """Reload agent from file path (called by file watcher).

        Args:
            file_path: Absolute file path

        Note:
            This is a placeholder - actual reload is done by AgentParser
        """
        # File watcher will call this, but actual parsing
        # is delegated to AgentParser
        print(f"🔄 Cache reload requested for: {file_path}")


# Global cache instance
_agent_cache: Optional[AgentCache] = None


def get_agent_cache() -> AgentCache:
    """Get global agent cache instance.

    Returns:
        AgentCache singleton
    """
    global _agent_cache
    if _agent_cache is None:
        _agent_cache = AgentCache()
    return _agent_cache
