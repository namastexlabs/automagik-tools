# automagik-tools

🚀 **The Premier Repository for Model Context Protocol (MCP) Tools**

A **self-discovering**, **zero-configuration** monorepo for MCP tools. Just drop your tool in the `tools/` directory and it's automatically available - no registration needed!

**✨ Key Features:**
- 🔍 **Auto-Discovery** - Tools are found automatically, no manual registration
- 📦 **Self-Contained** - Each tool is completely independent
- 🚀 **Zero Config** - Just add your tool folder and it works
- 🛠️ **FastMCP Powered** - Built on the robust FastMCP framework
- 🎯 **5-Minute Setup** - Add a new tool in minutes, not hours

**Our Vision**: To become the largest and most comprehensive collection of MCP tools, making it trivially easy for developers to add new integrations and for users to discover and use them.

---

## 🚀 Features

### 🎯 For Tool Developers
- **Zero Registration** - Just create a folder in `tools/` and it's discovered
- **Self-Contained Tools** - Each tool is independent with its own config
- **Auto-Discovery** - The hub automatically finds and mounts all tools
- **FastMCP Compliant** - Built on FastMCP with proper patterns
- **5-Minute Setup** - Add a new tool faster than making coffee

### 🛠️ For Tool Users
- **One Command** - `make fastmcp-hub` runs everything
- **Multi-tool Server** - All tools available on one server
- **Dynamic Loading** - Tools are discovered and loaded at runtime
- **CLI Interface** - List, run, and manage tools easily
- **Type-Safe Config** - Pydantic-based settings with environment variables

---

## 📦 Installation

### Option 1: Using uvx (Recommended)

The easiest way to use automagik-tools is with [uvx](https://docs.astral.sh/uv/guides/tools/), which runs the tool in an isolated environment without affecting your system Python:

```bash
# Run directly without installation
uvx automagik-tools --help

# List available tools
uvx automagik-tools list

# Run a server
uvx automagik-tools serve-all --tools evolution-api
```

### Option 2: Using pip

You can also install automagik-tools as a standard Python package:

```bash
# Install globally or in a virtual environment
pip install automagik-tools

# Or install the latest development version
pip install git+https://github.com/namastexlabs/automagik-tools.git
```

### Option 3: Development Installation

For development, we use [uv](https://docs.astral.sh/uv/) for dependency management:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/namastexlabs/automagik-tools.git
cd automagik-tools
uv sync --all-extras

# Run commands with uv
uv run automagik-tools list
uv run pytest
```

---

## 🏁 Quick Start

### 1. List Available Tools

```bash
# Using uvx (recommended)
uvx automagik-tools list

# Or using pip-installed version
automagik-tools list
```

### 2. Run a Tool Server (Single Tool)

```bash
# Using uvx
uvx automagik-tools serve --tool automagik-agents

# Or using pip-installed version
automagik-tools serve --tool automagik-agents
```

- By default, serves on `0.0.0.0:8000` (configurable with `--host` and `--port`)
- The tool will be available at `/mcp` (e.g., `http://localhost:8000/mcp`)

### 3. Run a Multi-Tool Server

```bash
# Using uvx
uvx automagik-tools serve-all --tools automagik-agents

# Or using pip-installed version  
automagik-tools serve-all --tools automagik-agents,evolution-api,example-hello
```

- Each tool is mounted at its own path, e.g., `/automagik-agents/mcp`, `/evolution-api/mcp`
- You can specify which tools to serve with `--tools`, or omit to serve all discovered tools

### 🤖 Connecting to MCP-Compatible Clients

You can connect your automagik-tools server to any MCP-compatible client using various transport methods:

#### Method 1: stdio Transport (Recommended for Desktop Clients)

##### Using uvx (no installation required)

```json
{
  "mcpServers": {
    "automagik-agents": {
      "transport": "stdio",
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "automagik-agents", "--transport", "stdio"],
      "env": {
        "AUTOMAGIK_AGENTS_API_KEY": "your_api_key_here",
        "AUTOMAGIK_AGENTS_BASE_URL": "http://your-server:8881",
        "AUTOMAGIK_AGENTS_OPENAPI_URL": "http://your-server:8881/api/v1/openapi.json",
        "AUTOMAGIK_AGENTS_TIMEOUT": "1000"
      }
    }
  }
}
```

##### Using pip-installed version

```json
{
  "mcpServers": {
    "automagik-agents": {
      "transport": "stdio",
      "command": "automagik-tools",
      "args": ["serve", "--tool", "automagik-agents", "--transport", "stdio"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

##### Using Python directly

```json
{
  "mcpServers": {
    "automagik-agents": {
      "transport": "stdio",
      "command": "python",
      "args": ["-m", "automagik_tools.tools.automagik_agents"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

#### Method 2: SSE (Server-Sent Events) Transport

##### Start the server

```bash
# Single tool
uvx automagik-tools serve --tool automagik-agents --transport sse --port 8080

# Multiple tools
uvx automagik-tools serve-all --tools automagik-agents,evolution-api --transport sse --port 8080
```

##### Client configuration

```json
{
  "mcpServers": {
    "automagik-agents": {
      "transport": "sse",
      "url": "http://localhost:8080/mcp/sse"
    }
  }
}
```

#### Method 3: HTTP Transport (REST API)

##### Start the server

```bash
# Single tool (default is HTTP transport)
uvx automagik-tools serve --tool automagik-agents --host 0.0.0.0 --port 8000

# Multiple tools
uvx automagik-tools serve-all --tools automagik-agents,evolution-api --host 0.0.0.0 --port 8000
```

##### Access endpoints

- Single tool: `http://localhost:8000/mcp`
- Multiple tools: `http://localhost:8000/automagik-agents/mcp`

#### Method 4: Development Mode

##### Local development with uvx

```json
{
  "mcpServers": {
    "automagik-agents-dev": {
      "transport": "stdio",
      "command": "uvx",
      "args": ["--from", "/path/to/automagik-tools", "automagik-tools", "serve", "--tool", "automagik-agents", "--transport", "stdio"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

##### Direct Python execution

```json
{
  "mcpServers": {
    "automagik-agents-dev": {
      "transport": "stdio",
      "command": "/path/to/automagik-tools/.venv/bin/python",
      "args": ["-m", "automagik_tools", "serve", "--tool", "automagik-agents", "--transport", "stdio"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

#### Method 5: Multiple Tools Configuration

##### All tools with stdio

```json
{
  "mcpServers": {
    "automagik-all": {
      "transport": "stdio",
      "command": "uvx", 
      "args": ["automagik-tools", "serve-all", "--tools", "automagik-agents,evolution-api,example-hello", "--transport", "stdio"],
      "env": {
        "AUTOMAGIK_AGENTS_API_KEY": "your_api_key_here",
        "AUTOMAGIK_AGENTS_BASE_URL": "http://your-server:8881",
        "AUTOMAGIK_AGENTS_OPENAPI_URL": "http://your-server:8881/api/v1/openapi.json",
        "AUTOMAGIK_AGENTS_TIMEOUT": "1000",
        "EVOLUTION_API_BASE_URL": "https://your-api-server.com",
        "EVOLUTION_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

#### Claude Desktop Example

For Claude Desktop, add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "automagik-agents": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "automagik-agents", "--transport", "stdio"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

#### Environment Variables

Each tool requires specific environment variables. For automagik-agents:

```bash
# Required
AUTOMAGIK_AGENTS_API_KEY=your_api_key_here
AUTOMAGIK_AGENTS_BASE_URL=http://your-server:8881

# Optional
AUTOMAGIK_AGENTS_OPENAPI_URL=http://your-server:8881/api/v1/openapi.json
AUTOMAGIK_AGENTS_TIMEOUT=1000    # Request timeout in milliseconds
```

This allows your LLM agent or automation platform to call tools, access resources, and use prompts exposed by automagik-tools as part of its workflow.

### 💡 Why uvx?

- **No installation required**: Run automagik-tools without installing it globally
- **Isolated environment**: Each run uses a fresh, isolated Python environment
- **Always latest**: Automatically pulls the latest version from PyPI
- **No conflicts**: Doesn't interfere with your system Python or other tools
- **Zero setup**: Works immediately if you have uv installed

---

## ⚙️ Configuration

Tools use environment variables for configuration. Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

Each tool has its own configuration prefix:

```env
# Automagik Agents
AUTOMAGIK_AGENTS_API_KEY=your_api_key_here
AUTOMAGIK_AGENTS_BASE_URL=http://your-server:8881
AUTOMAGIK_AGENTS_OPENAPI_URL=http://your-server:8881/api/v1/openapi.json
AUTOMAGIK_AGENTS_TIMEOUT=1000

# Evolution API (WhatsApp)
EVOLUTION_API_BASE_URL=https://your-evolution-api-server.com
EVOLUTION_API_KEY=your_api_key_here
EVOLUTION_API_TIMEOUT=30

# Future tools follow the same pattern
# GITHUB_API_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
# DISCORD_BOT_TOKEN=your-bot-token
# NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxx
```

See `.env.example` for all available configuration options.

---

## 🚀 Running Tools: Complete Examples

Here are all the ways you can run a tool, using `automagik-agents` as an example:

### Command Line Interface

```bash
# 1. Using uvx (no installation required)
uvx automagik-tools serve --tool automagik-agents

# 2. Using pip-installed version
pip install automagik-tools
automagik-tools serve --tool automagik-agents

# 3. Direct Python module execution
python -m automagik_tools.tools.automagik_agents

# 4. Development mode
cd /path/to/automagik-tools
uv run automagik-tools serve --tool automagik-agents
```

### Transport Options

```bash
# stdio transport (for MCP clients)
uvx automagik-tools serve --tool automagik-agents --transport stdio

# SSE transport (Server-Sent Events)
uvx automagik-tools serve --tool automagik-agents --transport sse --port 8080

# HTTP transport (default)
uvx automagik-tools serve --tool automagik-agents --host 0.0.0.0 --port 8000
```

### Multiple Tools

```bash
# Serve specific tools
uvx automagik-tools serve-all --tools automagik-agents,evolution-api

# Serve all discovered tools
uvx automagik-tools serve-all
```

### Environment Configuration

```bash
# Option 1: Export environment variables
export AUTOMAGIK_AGENTS_API_KEY=your_api_key_here
export AUTOMAGIK_AGENTS_BASE_URL=http://your-server:8881
uvx automagik-tools serve --tool automagik-agents

# Option 2: Use .env file
cat > .env << EOF
AUTOMAGIK_AGENTS_API_KEY=your_api_key_here
AUTOMAGIK_AGENTS_BASE_URL=http://your-server:8881
AUTOMAGIK_AGENTS_OPENAPI_URL=http://your-server:8881/api/v1/openapi.json
AUTOMAGIK_AGENTS_TIMEOUT=1000
EOF
uvx automagik-tools serve --tool automagik-agents

# Option 3: Inline environment variables
AUTOMAGIK_AGENTS_API_KEY=your_key AUTOMAGIK_AGENTS_BASE_URL=http://your-server:8881 uvx automagik-tools serve --tool automagik-agents
```

### MCP Client Configurations

```json
// For Claude Desktop, Cline, Continue, etc.
{
  "mcpServers": {
    "automagik-agents": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "automagik-agents", "--transport", "stdio"],
      "env": {
        "AUTOMAGIK_AGENTS_API_KEY": "your_api_key_here",
        "AUTOMAGIK_AGENTS_BASE_URL": "http://your-server:8881",
        "AUTOMAGIK_AGENTS_OPENAPI_URL": "http://your-server:8881/api/v1/openapi.json",
        "AUTOMAGIK_AGENTS_TIMEOUT": "1000"
      }
    }
  }
}
```

---

## 🪄 Adding a New Tool (5 Minutes!)

**No registration needed!** Just create your tool and it's automatically discovered.

### Super Quick Start

1. **Create your tool folder:**
```bash
mkdir -p automagik_tools/tools/my_tool
```

2. **Add required files** (see [Tool Development Guide](docs/TOOL_DEVELOPMENT_GUIDE.md)):
   - `__init__.py` - Your tool implementation with 3 required functions
   - `config.py` - Pydantic configuration class
   - `__main__.py` - Standalone runner (optional)
   - `README.md` - Documentation (optional)

3. **That's it!** Your tool is now:
   - ✅ Auto-discovered by the hub
   - ✅ Available in all commands
   - ✅ Ready to use

### Example Tool Structure
```python
# automagik_tools/tools/my_tool/__init__.py
def get_metadata():
    return {"name": "my-tool", "version": "1.0.0", "description": "My awesome tool"}

def get_config_class():
    return MyToolConfig

def create_server(config=None):
    # Create your FastMCP server here
    pass
```

**Try it:** Run `make fastmcp-hub` and your tool is automatically mounted!

---

## 🛠️ Developing New Tools

### Quick Start: Create a New Tool

The easiest way to create a new tool is using our interactive tool generator:

```bash
# Interactive mode (recommended)
python scripts/create_tool.py

# Or with parameters
python scripts/create_tool.py --name "GitHub API" --description "GitHub integration for MCP"
```

This will:
1. Create the tool directory structure
2. Generate boilerplate code from templates
3. Set up tests
4. Update configuration files
5. Register the tool in pyproject.toml

### Manual Tool Creation

For more control, see our comprehensive [Tool Creation Guide](docs/TOOL_CREATION_GUIDE.md) which includes:
- Step-by-step instructions
- Common patterns (REST APIs, WebSockets, databases)
- Testing strategies
- Best practices
- Example implementations

### Available Tool Templates

- **Basic Tool**: Minimal MCP tool structure
- **REST API Tool**: HTTP client with authentication
- **WebSocket Tool**: Real-time communication
- **Database Tool**: SQL/NoSQL integrations
- **File System Tool**: Local file operations

### Example: Hello World Tool

See `automagik_tools/tools/example_hello/` for a minimal working example that demonstrates:
- Basic tool structure
- Multiple tool methods
- Resources and prompts
- Proper testing patterns

---

## 🧩 Contributing

### Adding a New Tool

1. **Use the tool generator**: `python scripts/create_tool.py`
2. **Implement your tool logic**: Follow the patterns in existing tools
3. **Add tests**: Use the generated test template
4. **Update documentation**: Add your tool to this README
5. **Submit a PR**: We welcome all contributions!

### Tool Ideas We'd Love to See

- **Communication**: Discord, Slack, Telegram, Email
- **Productivity**: Notion, Google Workspace, Microsoft 365, Todoist
- **Development**: GitHub, GitLab, Jira, Docker, Kubernetes
- **AI/ML**: OpenAI, Anthropic, Hugging Face, Replicate
- **Data**: PostgreSQL, Redis, Elasticsearch, S3
- **Monitoring**: Datadog, Sentry, Prometheus
- **Finance**: Stripe, PayPal, Crypto APIs
- **IoT**: Home Assistant, MQTT, Arduino

See [docs/TOOL_CREATION_GUIDE.md](docs/TOOL_CREATION_GUIDE.md) for detailed contribution guidelines.

---

## 📚 Documentation

- [Tool Creation Guide](docs/TOOL_CREATION_GUIDE.md) - Comprehensive guide for building new tools
- [FastMCP Documentation](https://github.com/jlowin/fastmcp) - MCP framework documentation
- [MCP Specification](https://modelcontextprotocol.io) - Model Context Protocol specification
- [API Reference](docs/API.md) - Detailed API documentation (coming soon)

### Available Tools

| Tool | Description | Status |
|------|-------------|--------|
| automagik-agents | OpenAPI-based agent system for task automation | ✅ Ready |
| evolution-api | WhatsApp integration via Evolution API | ✅ Ready |
| example-hello | Simple example tool for learning | ✅ Ready |
| discord | Discord bot integration | 🚧 Planned |
| notion | Notion workspace integration | 🚧 Planned |
| github | GitHub API integration | 🚧 Planned |

Want to add a tool? Check our [contribution guide](docs/TOOL_CREATION_GUIDE.md)!

---

## 📝 License
MIT 

---

## 🧪 Testing

The project includes a comprehensive test suite using **pytest**. After installation, you can run tests directly:

### Quick Test Commands

```bash
# Install development dependencies first
uv pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run specific test categories
pytest tests/test_cli.py              # CLI tests
pytest tests/test_mcp_protocol.py     # MCP protocol tests  
pytest tests/test_integration.py      # Integration tests
pytest tests/tools/                   # Tool-specific tests

# Run tests with coverage
pytest tests/ --cov=automagik_tools --cov-report=html

# Run specific test
pytest tests/test_cli.py::TestCLIBasics::test_list_command -v

# Run tests matching a pattern
pytest -k "test_list" -v

# Skip slow tests
pytest tests/ -m "not slow" -v
```

### Using Make (Alternative)

We also provide a Makefile for convenience:

```bash
make help           # Show all available commands
make test           # Run all tests  
make test-unit      # Run unit tests
make test-mcp       # Run MCP protocol tests
make test-coverage  # Run with coverage report
make lint           # Check code quality
make format         # Format code
```

### Test Categories

The test suite is organized into several categories:

- **Unit Tests** (`test_cli.py`, `test_evolution_api.py`): Test individual components
- **MCP Protocol Tests** (`test_mcp_protocol.py`): Test MCP compliance and stdio transport
- **Integration Tests** (`test_integration.py`): Test complete workflows end-to-end

### Environment Variables for Testing

Set these environment variables for Evolution API tests:

```bash
export EVOLUTION_API_BASE_URL="http://your-api-server:8080"
export EVOLUTION_API_KEY="your_api_key"
```

### Test Configuration

Tests are configured via `pytest.ini`. Key features:

- **Automatic async support** for MCP protocol testing
- **Coverage reporting** with HTML output in `htmlcov/`
- **Test markers** for categorizing tests (`unit`, `integration`, `mcp`, etc.)
- **Timeout protection** for long-running tests

--- 