# Automagik Hive Tool

A comprehensive MCP tool for interacting with the Automagik Hive. This tool provides an intuitive interface to test and interact with agents, teams, and workflows in the Automagik ecosystem.

## Features

### 🤖 Agent Conversations
- **Start Conversations**: Begin new conversations with any available agent
- **Continue Chats**: Keep conversations going with follow-up messages
- **Session Management**: View, rename, and delete conversation sessions
- **Memory Access**: See what agents remember about your interactions

### 🔄 Workflow Execution
- **Execute Workflows**: Run complex multi-step workflows with your input
- **Track Results**: Monitor workflow execution and get detailed results
- **Session History**: View all your workflow executions and their outcomes
- **Custom Naming**: Give meaningful names to your workflow sessions

### 👥 Team Collaboration
- **Team Projects**: Collaborate with teams of agents on complex tasks
- **Multi-Agent Coordination**: Watch agents work together to solve problems
- **Team Memory**: Access shared team knowledge and experiences
- **Progress Tracking**: Monitor team collaboration sessions and results

### 🎮 Hive Features
- **Safe Testing**: Experiment with agents in a risk-free environment
- **Status Monitoring**: Check hive health and availability
- **Quick Actions**: Fast way to run tasks without complex setup

## Configuration

Set the following environment variables in your `.env` file:

```bash
# Automagik Hive Tool Configuration
HIVE_API_BASE_URL=http://localhost:8886
HIVE_API_KEY=hive_l_15Bhc_B_ObYltpQ09EtdlSeNs3rXwWoB_g6UBDZ3o  # Optional - only if API requires authentication
HIVE_TIMEOUT=30
```

## Usage

### Command Line
```bash
# Start the tool
uvx automagik-tools tool automagik-hive

# With specific transport
uvx automagik-tools tool automagik-hive --transport sse

# Generate Claude Desktop config
uvx automagik-tools mcp-config automagik-hive
```

### MCP Integration
Add to your Claude Desktop config:
```json
{
  "mcpServers": {
    "automagik-hive": {
      "command": "uvx",
      "args": ["automagik-tools", "tool", "automagik-hive", "--transport", "stdio"]
    }
  }
}
```

## Available Functions

### 🎮 Hive Status
- `check_playground_status()` - Check if the hive is running and healthy

### 🤖 Agent Operations
- `list_available_agents()` - See all agents you can talk to
- `start_agent_conversation()` - Begin a new conversation with an agent
- `continue_agent_conversation()` - Send follow-up messages to an agent
- `view_agent_conversation_history()` - See all your past conversations with an agent
- `get_specific_agent_conversation()` - Get details of a specific conversation
- `delete_agent_conversation()` - Remove a conversation (cannot be undone)
- `rename_agent_conversation()` - Give a custom name to a conversation
- `view_agent_memories()` - See what an agent remembers about you

### 🔄 Workflow Operations
- `list_available_workflows()` - See all workflows you can execute
- `get_workflow_details()` - Learn about a specific workflow's capabilities
- `execute_workflow()` - Run a workflow with your input data
- `view_workflow_execution_history()` - See all your workflow executions
- `get_workflow_execution_details()` - Get detailed results from a workflow run
- `delete_workflow_execution()` - Remove a workflow execution (cannot be undone)
- `rename_workflow_execution()` - Give a custom name to a workflow execution

### 👥 Team Operations
- `list_available_teams()` - See all agent teams you can collaborate with
- `get_team_details()` - Learn about a specific team's capabilities
- `start_team_collaboration()` - Begin working with a team of agents
- `view_team_collaboration_history()` - See all your team collaborations
- `get_team_collaboration_details()` - Get detailed results from a team session
- `delete_team_collaboration()` - Remove a team collaboration (cannot be undone)
- `rename_team_collaboration()` - Give a custom name to a team collaboration
- `view_team_memories()` - See what a team remembers about your collaborations

### 🚀 Quick Actions
- `quick_run()` - Fast way to run any task with automatic agent/team/workflow selection

## Examples

### Having a Conversation with an Agent
```python
# See what agents are available
agents = await list_available_agents()

# Start talking to an agent
conversation = await start_agent_conversation(
    agent_id="customer-service-agent",
    message="Hello, I need help with my account",
    user_id="user123"
)

# Continue the conversation
response = await continue_agent_conversation(
    agent_id="customer-service-agent",
    run_id=conversation["run_id"],
    message="Actually, I have a question about billing"
)
```

### Running a Workflow
```python
# See available workflows
workflows = await list_available_workflows()

# Get details about a specific workflow
workflow_info = await get_workflow_details("data-analysis-workflow")

# Execute the workflow
result = await execute_workflow(
    workflow_id="data-analysis-workflow",
    input_data={"dataset": "sales_data.csv", "analysis_type": "monthly_trends"},
    user_id="analyst123"
)
```

### Collaborating with a Team
```python
# See available teams
teams = await list_available_teams()

# Get team information
team_info = await get_team_details("marketing-team")

# Start a collaboration
collaboration = await start_team_collaboration(
    team_id="marketing-team",
    task_description="Create a social media campaign for our new product launch",
    user_id="marketing_manager"
)
```

### Quick Actions
```python
# Fast way to run any task
result = await quick_run(
    task_description="Analyze customer feedback from last month",
    # Optionally specify which agent, team, or workflow to use
    agent_id="data-analyst-agent"
)
```

## Error Handling

The tool includes comprehensive error handling:
- Connection errors to the hive
- Invalid agent, team, or workflow IDs
- Session not found errors
- Invalid parameters
- Server errors

All errors are properly formatted and returned as MCP error responses with helpful messages.

## Development

### Testing
```bash
# Run tests
uv run pytest tests/tools/test_automagik_hive.py -v

# Run with coverage
uv run pytest tests/tools/test_automagik_hive.py --cov=automagik_tools.tools.automagik_hive
```

### Local Development
```bash
# Install in development mode
uv pip install -e .

# Run directly
uv run python -m automagik_tools.tools.automagik_hive
```

## API Documentation

This tool provides access to the Automagik Hive API endpoints. All hive-related endpoints are included with user-friendly function names and descriptions.

## License

MIT License - see the main project LICENSE file for details.