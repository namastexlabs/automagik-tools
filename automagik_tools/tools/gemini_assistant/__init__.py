"""Gemini Assistant MCP Tool for Automagik Tools"""

from .config import GeminiAssistantConfig
from .server import create_server


def get_config_class():
    """Return the configuration class for this tool"""
    return GeminiAssistantConfig


def get_metadata():
    """Return metadata about this tool"""
    return {
        "name": "gemini_assistant",
        "description": "Advanced Gemini consultation tool with session management and file attachments",
        "version": "3.0.0",
        "author": "Peter Krueck (adapted for automagik-tools)",
        "tools": [
            "consult_gemini",
            "list_sessions", 
            "end_session",
            "get_gemini_requests"
        ]
    }


__all__ = ["create_server", "get_config_class", "get_metadata"]