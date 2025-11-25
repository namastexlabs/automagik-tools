"""Genie agent discovery and filesystem integration."""

from .frontmatter_utils import FrontmatterManager
from .project_scanner import ProjectScanner
from .agent_parser import AgentParser
from .cache import AgentCache
from .file_watcher import GenieAgentWatcher, AgentDiscoveryService, get_discovery_service

__all__ = [
    "FrontmatterManager",
    "ProjectScanner",
    "AgentParser",
    "AgentCache",
    "GenieAgentWatcher",
    "AgentDiscoveryService",
    "get_discovery_service",
]
