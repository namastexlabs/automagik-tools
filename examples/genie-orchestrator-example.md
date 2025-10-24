# Genie Orchestrator Example

This example demonstrates how to use Genie as a universal MCP orchestrator that connects multiple MCP servers with persistent memory for intelligent multi-tool workflows.

## Use Case Description

Genie is your AI conductor that orchestrates any MCP servers with persistent memory. Use it to:
- Coordinate multiple MCP tools for complex workflows
- Maintain conversation context across all sessions
- Learn from every interaction to provide personalized assistance
- Manage file systems, Git repositories, databases, and APIs simultaneously
- Remember your preferences and project details across sessions
- Automate multi-step tasks that require multiple tools

Perfect for developers who need an intelligent assistant that can work with multiple tools while remembering your workflow patterns and preferences.

## Setup

### Prerequisites

1. **OpenAI API Key**: For Genie's intelligence (required)
2. **MCP Servers**: Any MCP-compatible servers you want to connect
3. **Python 3.12+**: For running automagik-tools

### Environment Configuration

Create a `.env` file or set environment variables:

```bash
# Required
OPENAI_API_KEY=sk-your-openai-key-here

# Optional - Genie Configuration
GENIE_MODEL=gpt-4o                    # AI model to use (default: gpt-4o)
GENIE_MEMORY_DB_FILE=./genie_memory.db  # Memory database location
GENIE_STORAGE_DB_FILE=./genie_storage.db  # Chat history location
GENIE_SHARED_SESSION_ID=default-user   # Default session ID
GENIE_NUM_HISTORY_RUNS=5              # Number of previous conversations to include
GENIE_SHOW_TOOL_CALLS=true            # Show tool execution details

# MCP Server Configurations (JSON format)
GENIE_MCP_CONFIGS='{
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
    "env": {}
  },
  "github": {
    "command": "uvx",
    "args": ["mcp-server-git"],
    "env": {
      "GITHUB_TOKEN": "your-github-token"
    }
  }
}'
```

## CLI Commands

### Direct Command Line Usage

```bash
# Run with stdio transport (for Claude/Cursor)
uvx automagik-tools tool genie --transport stdio

# Run with SSE transport (for team sharing)
uvx automagik-tools tool genie --transport sse --port 8000

# Run with HTTP transport
uvx automagik-tools tool genie --transport http --port 8001
```

### Check Genie Status

```bash
# List available tools
uvx automagik-tools list

# Get Genie metadata
uvx automagik-tools tool genie --help
```

## MCP Configuration

### For Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "genie": {
      "command": "uvx",
      "args": [
        "automagik-tools",
        "tool",
        "genie",
        "--transport",
        "stdio"
      ],
      "env": {
        "OPENAI_API_KEY": "sk-your-openai-key-here",
        "GENIE_MODEL": "gpt-4o",
        "GENIE_MCP_CONFIGS": "{\"filesystem\":{\"command\":\"npx\",\"args\":[\"-y\",\"@modelcontextprotocol/server-filesystem\",\"/Users/yourname/projects\"],\"env\":{}},\"git\":{\"command\":\"uvx\",\"args\":[\"mcp-server-git\"],\"env\":{\"GITHUB_TOKEN\":\"your-token\"}}}"
      }
    }
  }
}
```

### For Cursor

Add this to your Cursor MCP configuration (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "genie": {
      "command": "uvx",
      "args": [
        "automagik-tools",
        "tool",
        "genie",
        "--transport",
        "stdio"
      ],
      "env": {
        "OPENAI_API_KEY": "sk-your-openai-key-here",
        "GENIE_MODEL": "gpt-4o",
        "GENIE_MCP_CONFIGS": "{\"filesystem\":{\"command\":\"npx\",\"args\":[\"-y\",\"@modelcontextprotocol/server-filesystem\",\"C:\\\\Users\\\\yourname\\\\projects\"],\"env\":{}},\"database\":{\"command\":\"uvx\",\"args\":[\"mcp-server-sqlite\"],\"env\":{}}}"
      }
    }
  }
}
```

## Expected Output

### 1. Simple Query with Tool Orchestration

**Command:**
```python
ask_genie(
    query="List all Python files in my project and check their Git status",
    user_id="developer-123"
)
```

**Expected Response:**
```markdown
I'll help you find all Python files and check their Git status.

**Python Files Found:**
1. `src/main.py` - Modified (uncommitted changes)
2. `src/utils/helper.py` - Staged for commit
3. `tests/test_main.py` - Untracked
4. `config/settings.py` - Clean (committed)

**Summary:**
- Total Python files: 4
- Modified: 1
- Staged: 1
- Untracked: 1
- Clean: 1

Would you like me to help you commit these changes or review the modifications?
```

### 2. Multi-Tool Workflow

**Command:**
```python
ask_genie(
    query="Create a new feature branch, add a README file explaining the project, and commit it",
    user_id="developer-123"
)
```

**Expected Response:**
```markdown
I've completed the workflow for you:

**Step 1: Created Feature Branch**
✅ Created and switched to branch: `feature/add-readme`

**Step 2: Created README.md**
✅ Created `README.md` with:
- Project overview
- Installation instructions
- Usage examples
- Contributing guidelines

**Step 3: Committed Changes**
✅ Committed with message: "docs: Add comprehensive README"
- Commit hash: `a1b2c3d`
- Files changed: 1
- Insertions: 45 lines

**Next Steps:**
Would you like me to push this branch to the remote repository?
```

### 3. Memory-Based Personalization

**Command:**
```python
ask_genie(
    query="Set up my usual project structure",
    user_id="developer-123"
)
```

**Expected Response:**
```markdown
I remember your preferred project structure! Setting it up now...

**Created Structure:**
```
project/
├── src/
│   ├── __init__.py
│   ├── main.py
│   └── utils/
│       └── __init__.py
├── tests/
│   └── __init__.py
├── docs/
├── .gitignore (Python template)
├── requirements.txt
├── README.md
└── pyproject.toml
```

**Initialized:**
- ✅ Git repository
- ✅ Python virtual environment
- ✅ Pre-commit hooks (as you prefer)

This matches your usual setup from previous projects. Anything else you'd like me to add?
```

### 4. Check Memory Stats

**Command:**
```python
genie_memory_stats(user_id="developer-123")
```

**Expected Response:**
```markdown
🧞 **Genie Memory Stats**

**Session ID:** developer-123
**Total Memories:** 12

**Recent Memories:**
1. User prefers Python over JavaScript for backend projects (Topics: preferences, programming)
2. Project structure: src/, tests/, docs/ with pyproject.toml (Topics: project_setup, structure)
3. Uses pytest for testing with coverage reports (Topics: testing, tools)
4. Prefers feature branch workflow with descriptive commit messages (Topics: git, workflow)
5. Works on AI/ML projects using PyTorch and FastAPI (Topics: tech_stack, frameworks)
```

## Real-World Usage Scenarios

### Scenario 1: Full-Stack Development Workflow

```python
# Genie coordinates filesystem, Git, and database tools
ask_genie(
    query="""I'm starting a new FastAPI project. Please:
    1. Create the project structure
    2. Initialize Git with a good .gitignore
    3. Create a SQLite database with users table
    4. Generate a basic FastAPI app with user endpoints
    5. Create initial migration files""",
    user_id="fullstack-dev"
)
```

**What Genie Does:**
- Uses filesystem MCP to create directories and files
- Uses Git MCP to initialize repo and create .gitignore
- Uses database MCP to create SQLite database and schema
- Generates FastAPI boilerplate code
- Creates Alembic migration files
- Remembers your FastAPI preferences for future projects

### Scenario 2: Code Review and Documentation

```python
# Genie analyzes code and updates documentation
ask_genie(
    query="""Review the changes in my current branch and:
    1. Check for potential bugs or improvements
    2. Update the CHANGELOG.md
    3. Generate API documentation
    4. Suggest test cases for new features""",
    user_id="code-reviewer",
    context="Working on authentication feature"
)
```

**What Genie Does:**
- Uses Git MCP to get diff and changed files
- Uses filesystem MCP to read code files
- Analyzes code for issues
- Updates CHANGELOG.md with new entries
- Generates API docs from code
- Suggests comprehensive test cases
- Remembers your code review preferences

### Scenario 3: Database Migration Workflow

```python
# Genie handles complex database operations
ask_genie(
    query="""I need to add a 'last_login' timestamp to users table:
    1. Create a migration file
    2. Add the column with default value
    3. Update the SQLAlchemy model
    4. Generate a test to verify the migration""",
    user_id="backend-dev"
)
```

**What Genie Does:**
- Uses database MCP to inspect current schema
- Creates migration file with proper up/down methods
- Uses filesystem MCP to update model files
- Generates appropriate test cases
- Remembers your database naming conventions

### Scenario 4: Multi-Repository Management

```python
# Genie coordinates across multiple repositories
ask_genie(
    query="""Check all my active projects:
    1. List repos with uncommitted changes
    2. Show repos that are ahead of origin
    3. Identify repos with pending pull requests
    4. Create a summary report""",
    user_id="tech-lead",
    mcp_servers={
        "git-work": {
            "command": "uvx",
            "args": ["mcp-server-git"],
            "env": {"GIT_DIR": "/work/projects"}
        },
        "git-personal": {
            "command": "uvx",
            "args": ["mcp-server-git"],
            "env": {"GIT_DIR": "/personal/projects"}
        }
    }
)
```

**What Genie Does:**
- Connects to multiple Git MCP servers
- Scans all repositories
- Identifies uncommitted changes
- Checks remote sync status
- Queries GitHub API for PRs
- Generates comprehensive report
- Remembers which repos you work on most

## Features Demonstrated

1. **Multi-Tool Orchestration**: Seamlessly coordinates multiple MCP servers
2. **Persistent Memory**: Remembers preferences, patterns, and project details
3. **Natural Language**: Just describe what you want in plain English
4. **Context Awareness**: Uses conversation history for better responses
5. **Learning**: Improves responses based on your feedback and patterns
6. **Flexible Configuration**: Connect any MCP-compatible servers
7. **Session Management**: Separate sessions for different users/projects

## Advanced Configuration

### Connecting Multiple MCP Servers

```bash
export GENIE_MCP_CONFIGS='{
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
    "env": {}
  },
  "git": {
    "command": "uvx",
    "args": ["mcp-server-git"],
    "env": {"GITHUB_TOKEN": "ghp_xxx"}
  },
  "database": {
    "command": "uvx",
    "args": ["mcp-server-sqlite"],
    "env": {"DB_PATH": "./data.db"}
  },
  "slack": {
    "command": "uvx",
    "args": ["mcp-server-slack"],
    "env": {"SLACK_TOKEN": "xoxb-xxx"}
  },
  "memory": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-memory"],
    "env": {}
  }
}'
```

### Runtime MCP Server Configuration

You can also provide MCP servers at runtime:

```python
ask_genie(
    query="List all my GitHub repositories",
    mcp_servers={
        "github": {
            "command": "uvx",
            "args": ["mcp-server-github"],
            "env": {"GITHUB_TOKEN": "ghp_your_token"}
        }
    },
    user_id="developer-123"
)
```

## Best Practices

1. **Start Simple**: Begin with one or two MCP servers, add more as needed
2. **Use Sessions**: Different `user_id` for different projects or contexts
3. **Provide Context**: Use the `context` parameter for complex queries
4. **Check Memory**: Periodically review what Genie remembers with `genie_memory_stats()`
5. **Clear When Needed**: Use `genie_clear_memories()` to reset if needed
6. **Descriptive Queries**: Be specific about what you want Genie to do
7. **Iterative Refinement**: Follow up with additional questions to refine results

## Troubleshooting

### Common Issues

1. **"No MCP server configurations provided"**
   - Set `GENIE_MCP_CONFIGS` environment variable
   - Or provide `mcp_servers` parameter in the query

2. **"OpenAI API key not configured"**
   - Set `OPENAI_API_KEY` environment variable
   - Verify the key is valid and has credits

3. **MCP server connection failed**
   - Check MCP server command is correct
   - Verify required environment variables are set
   - Ensure MCP server package is installed

4. **Empty or no response**
   - Check OpenAI API status
   - Verify MCP servers are responding
   - Review logs for errors (stderr)

5. **Memory not persisting**
   - Check write permissions for database files
   - Verify `GENIE_MEMORY_DB_FILE` path is accessible
   - Ensure same `user_id` is used across sessions

## Performance Tips

1. **Model Selection**: Use `gpt-4o` for complex tasks, `gpt-4o-mini` for simple queries
2. **History Limit**: Adjust `GENIE_NUM_HISTORY_RUNS` based on context needs
3. **Session IDs**: Use meaningful session IDs for better memory organization
4. **Cleanup**: Periodically clear old memories to improve performance
5. **Server Selection**: Only connect MCP servers you actually need

## Security Considerations

- **API Keys**: Store in environment variables, never in code
- **File Access**: Limit filesystem MCP to specific directories
- **Database Access**: Use read-only connections when possible
- **Token Scope**: Minimize GitHub/API token permissions
- **Memory Privacy**: Different users should have different session IDs

## Next Steps

1. **Add More MCP Servers**: Connect to Slack, Linear, Notion, etc.
2. **Create Workflows**: Build reusable task sequences
3. **Team Sharing**: Use SSE transport for team-wide Genie access
4. **Custom Instructions**: Add domain-specific instructions
5. **Integration**: Embed Genie in your development tools

## Additional Resources

- [MCP Server Directory](https://github.com/modelcontextprotocol/servers)
- [Agno Framework Documentation](https://docs.agno.com)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Automagik Tools GitHub](https://github.com/namastexlabs/automagik-tools)
