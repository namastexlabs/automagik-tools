"""
Evolution API CLI runner
"""

from .config import EvolutionAPIConfig
from . import create_server

config = EvolutionAPIConfig()
mcp = create_server(config)