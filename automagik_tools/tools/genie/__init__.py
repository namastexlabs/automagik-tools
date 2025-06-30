"""
Genie - An intelligent MCP tool orchestrator with persistent memory

A single Agno agent that can access all available MCP tools and learns from interactions
using persistent memory. The agent builds user personas and preferences over time,
providing increasingly personalized responses.

Key Features:
- Agentic memory management with SQLite persistence
- Access to all available MCP tools via auto-discovery
- Single shared agent instance for all users
- Learns and evolves from every interaction
- Can manage its own memories (create, update, delete)
"""

from typing import Optional, Dict, Any
import logging
import json

from fastmcp import FastMCP

# Import configuration
from .config import GenieConfig, get_config

# Configure logging
# For stdio transport, we must log to stderr to avoid corrupting JSON-RPC messages
import sys
import os

# Explicitly disable any debug environment variables that might pollute stdout
os.environ.pop("DEBUG", None)
os.environ.pop("AGNO_DEBUG", None)
os.environ.pop("MCP_DEBUG", None)
os.environ.pop("PYTHONPATH_DEBUG", None)

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,  # Log to stderr to avoid stdio conflicts
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# FastMCP server setup
mcp = FastMCP("Genie")

# Lazy config initialization - defer until actually needed
_module_config = None

def _ensure_config():
    """Ensure config is loaded, initializing only when needed"""
    global _module_config
    if _module_config is None:
        _module_config = get_config()
        if _module_config.mcp_server_configs:
            logger.info(
                f"📡 Genie configured with MCP servers: {list(_module_config.mcp_server_configs.keys())}"
            )
        else:
            logger.warning("⚠️ No MCP servers configured in environment variables")
    return _module_config


@mcp.tool()
async def ask_genie(
    query: str,
    mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None,
    user_id: Optional[str] = None,
    context: Optional[str] = None,
) -> str:
    """
    Ask Genie anything - it automatically connects to MCP tools and remembers your conversations.

    Simply ask your question directly! No configuration needed.

    Genie is an intelligent agent that:
    - Automatically connects to pre-configured MCP servers - no setup required
    - Maintains persistent memory across all sessions
    - Learns from every interaction to personalize responses
    - Can orchestrate multiple tools to complete complex tasks

    Args:
        query: Your question or request - just ask naturally!
        mcp_servers: (Optional) Custom MCP servers - only if you need additional tools
        user_id: (Optional) User identifier for personalized sessions
        context: (Optional) Additional context for your request

    Returns:
        Intelligent response using available tools and learned knowledge

    Examples:
        ask_genie("list all available agents")
        ask_genie("help me analyze this codebase")
        ask_genie("remember that I prefer Python over JavaScript")
    """
    config = _ensure_config()
    # Validate configuration only when actually using the tool
    config.validate_for_use()
    session_id = user_id or config.shared_session_id

    logger.info(f"🧞 Genie processing query: {query[:100]}...")

    try:
        # Import Agno components
        from agno.agent import Agent
        from agno.models.openai import OpenAIChat
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from agno.memory.v2.memory import Memory
        from agno.storage.sqlite import SqliteStorage
        from agno.tools.mcp import MultiMCPTools
        from mcp import StdioServerParameters

        # Protect stdout during MCP operations to prevent stdio corruption
        import contextlib
        from io import StringIO
        import subprocess
        import asyncio

        # For SSE transport, we need to ensure subprocess termination happens before response
        # This prevents subprocess output from corrupting the SSE stream
        transport_type = os.environ.get("AUTOMAGIK_TRANSPORT", "stdio")
        logger.info(f"🚀 Running in {transport_type} transport mode")

        # Use provided MCP servers or fall back to config
        if mcp_servers:
            mcp_configs_to_use = mcp_servers
        else:
            mcp_configs_to_use = config.mcp_server_configs

        if not mcp_configs_to_use:
            return "❌ No MCP server configurations provided. Please provide MCP servers or configure them in environment variables."

        # Prepare MCP server commands for MultiMCPTools
        mcp_commands = []
        combined_env = dict(os.environ)

        # Build command list for MultiMCPTools
        for server_name, server_config in mcp_configs_to_use.items():
            try:
                logger.info(f"📡 Setting up MCP server: {server_name}")

                # Parse the server config if it's a string (JSON)
                if isinstance(server_config, str):
                    server_config = json.loads(server_config)

                # Create MCP server command for MultiMCPTools
                if "command" in server_config and "args" in server_config:
                    # Build command string from config
                    cmd_parts = [server_config["command"]] + server_config["args"]
                    command_str = " ".join(cmd_parts)

                    # Get environment variables if provided
                    env_vars = server_config.get("env", {})
                    if env_vars:
                        combined_env.update(env_vars)
                        logger.info(
                            f"📦 Added env vars for {server_name}: {list(env_vars.keys())}"
                        )

                    logger.info(f"🔧 Command: {command_str}")

                    # For stdio transport, wrap ALL commands to prevent stdout pollution
                    if transport_type == "stdio":
                        # Use our wrapper that redirects subprocess stdout
                        # The wrapper expects: python -m mcp_wrapper <cmd> <arg1> <arg2> ...
                        wrapped_parts = [
                            "uv",
                            "run",
                            "python",
                            "-m",
                            "automagik_tools.tools.genie.mcp_wrapper",
                        ] + cmd_parts
                        command_str = " ".join(wrapped_parts)
                        logger.info(f"🔇 Wrapped for stdio: {command_str}")

                    mcp_commands.append(command_str)

                elif "url" in server_config:
                    # URL-based configuration - MultiMCPTools handles this differently
                    logger.warning(
                        f"⚠️ URL-based MCP servers ({server_name}) not yet supported with MultiMCPTools"
                    )
                    logger.warning(
                        f"⚠️ Consider using command-based configuration for {server_name}"
                    )
                else:
                    logger.warning(
                        f"⚠️ Invalid config for {server_name}: missing command/args or url"
                    )

            except Exception as e:
                logger.error(f"❌ Failed to configure {server_name}: {e}")
                continue

        if not mcp_commands:
            return "❌ Failed to configure any MCP servers. Please check your configuration."

        logger.info(
            f"🔗 Connecting to {len(mcp_commands)} MCP servers using MultiMCPTools"
        )

        # Use MultiMCPTools to handle all servers properly
        async with MultiMCPTools(mcp_commands, env=combined_env) as mcp_tools:
            logger.info(
                f"🛠️ Connected to MCP servers, discovered {len(mcp_tools.functions)} total tools"
            )

            # Set up memory with SQLite persistence
            memory_db = SqliteMemoryDb(
                table_name="genie_memories", db_file=config.memory_db_file
            )

            memory = Memory(
                model=OpenAIChat(id=config.model, api_key=config.openai_api_key),
                db=memory_db,
            )

            # Set up storage for chat history
            storage = SqliteStorage(
                table_name="genie_sessions", db_file=config.storage_db_file
            )

            # Initialize the agent with MultiMCPTools
            agent = Agent(
                name="Genie",
                model=OpenAIChat(id=config.model, api_key=config.openai_api_key),
                description="""I am Genie, an intelligent agent with persistent memory and access to any MCP tools you provide.
                
I have persistent memory and learn from every interaction to provide increasingly personalized assistance.
I can help with various tasks including:
- Natural language processing and analysis
- Problem solving and reasoning
- Code analysis and suggestions
- Project planning and management
- Tool orchestration via any MCP-compatible tools
- Managing and coordinating multiple MCP servers
- And much more using my AI capabilities and tool integrations!

I remember our conversations and your preferences, building a detailed understanding of your needs over time.
I can also manage my own memories - creating, updating, or deleting them as needed.""",
                # Memory configuration
                memory=memory,
                enable_agentic_memory=True,
                enable_user_memories=True,
                # Storage configuration
                storage=storage,
                add_history_to_messages=True,
                num_history_runs=config.num_history_runs,
                # Tool access - MultiMCPTools handles all servers
                tools=[mcp_tools],
                # Output configuration
                markdown=True,
                show_tool_calls=config.show_tool_calls,
                debug_mode=False,  # MUST be False for stdio transport to avoid JSON errors
                # Verbose logging configuration
                monitoring=False,  # MUST be False for stdio transport to avoid DEBUG output
                # Instructions for memory management
                instructions=[
                    "Always use your memory to provide personalized responses based on past interactions",
                    "Proactively create memories about user preferences, project details, and recurring patterns",
                    "Update existing memories when you learn new information about users or their projects",
                    "Use agentic memory search to find relevant context before responding",
                    "When users ask about past conversations or preferences, search your memories first",
                    "Be transparent about what you remember and what you're learning about users",
                ],
            )

            logger.info(
                f"🧞 Genie initialized with MultiMCPTools managing {len(mcp_commands)} servers"
            )

            # Prepare the full query with context
            full_query = query
            if context:
                full_query = f"Context: {context}\n\nQuery: {query}"

            # Get response from agent
            logger.info(f"🎯 Starting agent execution for session: {session_id}")

            # Capture any stdout pollution during agent execution
            captured_stdout = StringIO()
            with contextlib.redirect_stdout(captured_stdout):
                response = await agent.arun(
                    full_query,
                    user_id=session_id,
                    stream=False,  # Use non-streaming for simplicity
                )

            # Log any captured stdout for debugging (to stderr)
            stdout_content = captured_stdout.getvalue()
            if stdout_content.strip():
                logger.warning(
                    f"⚠️ Captured stdout pollution: {stdout_content[:200]}..."
                )

            logger.info("🧞 Genie response completed")

            # Debug logging to understand response structure
            logger.debug(f"Response type: {type(response)}")
            logger.debug(
                f"Response attributes: {dir(response) if response else 'None'}"
            )

            # Process response
            final_response = None
            if response is None:
                final_response = "❌ No response from agent"
            elif hasattr(response, "content"):
                # Check if content is empty
                if not response.content:
                    logger.warning("⚠️ Agent returned empty content")
                    final_response = "❌ Agent returned empty response"
                else:
                    final_response = response.content
            else:
                # Fallback to string representation
                result_str = str(response)
                if not result_str or result_str == "None":
                    final_response = "❌ Agent returned empty response"
                else:
                    final_response = result_str

            # Log what we're returning
            logger.info(
                f"📤 Returning response (length: {len(final_response) if final_response else 0})"
            )
            logger.info(
                f"📄 Response preview: {final_response[:200] if final_response else 'None'}..."
            )

            # MultiMCPTools handles cleanup automatically when exiting the context
            logger.info("🧹 MultiMCPTools will handle cleanup automatically")

            # For SSE transport, add small delay to ensure cleanup completes
            if transport_type == "sse":
                sse_delay = config.sse_cleanup_delay
                await asyncio.sleep(sse_delay)
                logger.info(f"🔄 SSE cleanup delay ({sse_delay}s) completed")

            return final_response

    except Exception as e:
        error_msg = f"Genie error: {str(e)}"
        logger.error(error_msg)
        logger.exception("Full traceback:")
        return f"❌ {error_msg}"


@mcp.tool()
async def genie_memory_stats(
    user_id: Optional[str] = None,
    mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    """
    View Genie's memories and learning statistics.

    Check what Genie remembers about you and your interactions.

    Args:
        user_id: (Optional) View memories for specific user
        mcp_servers: (Optional) Not needed - included for compatibility

    Returns:
        Memory count and recent memories
    """
    config = _ensure_config()
    # Validate configuration only when actually using the tool
    config.validate_for_use()
    session_id = user_id or config.shared_session_id

    try:
        # Import Agno components
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from agno.memory.v2.memory import Memory
        from agno.models.openai import OpenAIChat

        # Set up memory with SQLite persistence
        memory_db = SqliteMemoryDb(
            table_name="genie_memories", db_file=config.memory_db_file
        )

        memory = Memory(
            model=OpenAIChat(id=config.model, api_key=config.openai_api_key),
            db=memory_db,
        )

        # Get user memories
        memories = memory.get_user_memories(user_id=session_id)

        # Format response
        response = "🧞 **Genie Memory Stats**\n\n"
        response += f"**Session ID:** {session_id}\n"
        response += f"**Total Memories:** {len(memories)}\n\n"

        if memories:
            response += "**Recent Memories:**\n"
            for i, memo in enumerate(memories[-5:], 1):  # Show last 5 memories
                topics = ", ".join(memo.topics) if memo.topics else "general"
                response += f"{i}. {memo.memory} (Topics: {topics})\n"
        else:
            response += "No memories found for this session.\n"

        return response

    except Exception as e:
        return f"❌ Error getting memory stats: {str(e)}"


@mcp.tool()
async def genie_clear_memories(
    user_id: Optional[str] = None,
    mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None,
    confirm: bool = False,
) -> str:
    """
    Clear Genie's memories - use with caution!

    This will permanently delete what Genie has learned about you.

    Args:
        user_id: (Optional) Clear memories for specific user
        mcp_servers: (Optional) Not needed - included for compatibility
        confirm: Must be True to actually clear memories (safety check)

    Returns:
        Confirmation message
    """
    if not confirm:
        return "❌ To clear memories, set confirm=True. This action cannot be undone!"

    config = _ensure_config()
    # Validate configuration only when actually using the tool
    config.validate_for_use()
    session_id = user_id or config.shared_session_id

    try:
        # Import Agno components
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from agno.memory.v2.memory import Memory
        from agno.models.openai import OpenAIChat

        # Set up memory with SQLite persistence
        memory_db = SqliteMemoryDb(
            table_name="genie_memories", db_file=config.memory_db_file
        )

        memory = Memory(
            model=OpenAIChat(id=config.model, api_key=config.openai_api_key),
            db=memory_db,
        )

        # Get and clear memories for the user
        memories = memory.get_user_memories(user_id=session_id)
        count = len(memories)

        for memo in memories:
            memory.delete_user_memory(user_id=session_id, memory_id=memo.id)

        return f"🧞 Cleared {count} memories for session {session_id}"

    except Exception as e:
        return f"❌ Error clearing memories: {str(e)}"


def get_metadata() -> Dict[str, Any]:
    """Get Genie metadata"""
    return {
        "name": "genie",
        "description": "Generic MCP tool orchestrator with persistent memory - connect any MCP servers",
        "version": "2.0.0",
        "author": "automagik-tools",
        "capabilities": [
            "agentic_memory",
            "dynamic_mcp_connections",
            "multi_server_orchestration",
            "persistent_learning",
            "natural_language_processing",
            "isolated_server_sessions",
        ],
    }


def get_config_class():
    """Get the configuration class for Genie"""
    return GenieConfig


def create_server(config=None):
    """Create and return the FastMCP server instance"""
    return mcp
