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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastMCP server setup
mcp = FastMCP("Genie")

# Initialize config at module level to check for MCP servers
_module_config = get_config()
if _module_config.mcp_server_configs:
    logger.info(
        f"📡 Genie configured with MCP servers: {list(_module_config.mcp_server_configs.keys())}"
    )
else:
    logger.warning("⚠️ No MCP servers configured in environment variables")


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
    config = get_config()
    session_id = user_id or config.shared_session_id

    logger.info(f"🧞 Genie processing query: {query[:100]}...")

    try:
        # Import Agno components
        from agno.agent import Agent
        from agno.models.openai import OpenAIChat
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from agno.memory.v2.memory import Memory
        from agno.storage.sqlite import SqliteStorage
        from agno.tools.mcp import MCPTools

        # Use provided MCP servers or fall back to config
        if mcp_servers:
            mcp_configs_to_use = mcp_servers
        else:
            mcp_configs_to_use = config.mcp_server_configs

        if not mcp_configs_to_use:
            return "❌ No MCP server configurations provided. Please provide MCP servers or configure them in environment variables."

        # Prepare all MCP tools
        mcp_tools_list = []
        mcp_contexts = []

        # Connect to each configured MCP server
        for server_name, server_config in mcp_configs_to_use.items():
            try:
                logger.info(f"📡 Setting up MCP server: {server_name}")

                # Parse the server config if it's a string (JSON)
                if isinstance(server_config, str):
                    server_config = json.loads(server_config)

                # Create MCP tools configuration for this server
                if "command" in server_config and "args" in server_config:
                    # Build command string from config
                    cmd_parts = [server_config["command"]] + server_config["args"]
                    command_str = " ".join(cmd_parts)

                    # Get environment variables if provided
                    env_vars = server_config.get("env", {})

                    logger.info(f"🔧 Command: {command_str}")
                    if env_vars:
                        logger.info(f"📦 With env vars: {list(env_vars.keys())}")

                    # Create MCPTools instance
                    mcp_tool = MCPTools(command_str, env=env_vars)
                    mcp_tools_list.append((server_name, mcp_tool))

                elif "url" in server_config:
                    # URL-based configuration
                    mcp_tool = MCPTools(
                        url=server_config["url"],
                        transport=server_config.get("transport", "sse"),
                    )
                    mcp_tools_list.append((server_name, mcp_tool))
                else:
                    logger.warning(
                        f"⚠️ Invalid config for {server_name}: missing command/args or url"
                    )

            except Exception as e:
                logger.error(f"❌ Failed to configure {server_name}: {e}")
                continue

        if not mcp_tools_list:
            return "❌ Failed to configure any MCP servers. Please check your configuration."

        # Initialize all MCP tools as context managers
        async def run_with_mcp_tools():
            # Enter all contexts
            entered_tools = []
            for server_name, mcp_tool in mcp_tools_list:
                try:
                    logger.info(f"🔌 Initializing MCPTools for {server_name}")
                    await mcp_tool.__aenter__()
                    entered_tools.append((server_name, mcp_tool))
                    mcp_contexts.append(mcp_tool)

                    # Log discovered functions after initialization
                    if hasattr(mcp_tool, "functions"):
                        logger.info(
                            f"🛠️ Discovered {len(mcp_tool.functions)} tools from {server_name}"
                        )
                except Exception as e:
                    logger.error(f"❌ Failed to initialize {server_name}: {e}")

            if not entered_tools:
                return "❌ Failed to initialize any MCP tools. Please check server configurations."

            try:
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

                # Extract just the MCPTools objects for the agent
                tools_for_agent = [tool for _, tool in entered_tools]

                # Initialize the agent inside the MCP context
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
                    # Tool access
                    tools=tools_for_agent,
                    # Output configuration
                    markdown=True,
                    show_tool_calls=True,
                    debug_mode=True,
                    # Verbose logging configuration
                    monitoring=True,
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
                    f"🧞 Genie initialized with {len(tools_for_agent)} MCP servers"
                )

                # Prepare the full query with context
                full_query = query
                if context:
                    full_query = f"Context: {context}\n\nQuery: {query}"

                # Get response from agent
                logger.info(f"🎯 Starting agent execution for session: {session_id}")

                response = await agent.arun(
                    full_query,
                    user_id=session_id,
                    stream=False,  # Use non-streaming for simplicity
                )

                logger.info("🧞 Genie response completed")
                return (
                    response.content if hasattr(response, "content") else str(response)
                )

            finally:
                # Exit all MCP tool contexts
                for mcp_tool in mcp_contexts:
                    try:
                        await mcp_tool.__aexit__(None, None, None)
                        logger.info("🔓 Closed MCPTools context")
                    except Exception as e:
                        logger.error(f"Error closing MCPTools: {e}")

        # Run with all MCP tools
        return await run_with_mcp_tools()

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
    config = get_config()
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

    config = get_config()
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
