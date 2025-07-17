"""
Automagik Workflows V2 - Smart Streaming Workflow Orchestration

Revolutionary workflow orchestration tool with:
- Dynamic workflow discovery and enum-based selection
- Elicitation-powered parameter collection
- Real-time progress streaming via FastMCP Context
- Session management with ID-based continuation
- Self-healing connectivity with health monitoring
- Epic name storage for orchestration systems
"""

from .server import create_server
from .config import AutomagikWorkflowsV2Config

def get_metadata():
    """Return tool metadata for automagik-tools discovery."""
    return {
        "name": "automagik-workflows-v2",
        "description": "Smart streaming workflow orchestration with dynamic discovery and real-time coordination",
        "version": "2.0.0",
        "capabilities": [
            "dynamic_workflow_discovery",
            "real_time_progress_streaming", 
            "session_management",
            "elicitation_powered_interaction",
            "self_healing_connectivity",
            "epic_name_storage"
        ]
    }

def get_config_class():
    """Return configuration class for automagik-tools CLI integration."""
    return AutomagikWorkflowsV2Config

__all__ = ["create_server", "get_metadata", "get_config_class", "AutomagikWorkflowsV2Config"]