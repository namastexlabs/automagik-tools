<p align="center">
  <img src=".github/images/automagik_logo.png" alt="AutoMagik Tools Logo" width="600"/>
</p>

# 🪄 AutoMagik Tools

## Turn Any API into an AI-Ready Tool in Seconds™

**The most comprehensive collection of Model Context Protocol (MCP) tools**. Drop an OpenAPI spec, get an MCP tool. It's that simple.

Born from our daily work at [Namastex Labs](https://www.linkedin.com/company/namastexlabs), AutoMagik Tools transforms the way AI agents interact with the real world. We're building the infrastructure that makes **every API on the internet instantly accessible to AI**.

### 🎯 Why AutoMagik Tools?

**The Problem**: AI agents need to interact with thousands of APIs, but creating MCP tools is time-consuming and repetitive.

**Our Solution**: 
- 🚀 **Instant API → MCP Tool**: Drop any OpenAPI.json, get a fully functional MCP tool
- 🤖 **Coming Soon: Smart Tools™**: Natural language API calls - just describe what you want
- 🔌 **Zero Configuration**: Auto-discovery means tools just work
- 🌐 **Universal Compatibility**: Works with Claude, Cursor, and any MCP-compatible AI

### 🌟 Game-Changing Features

1. **OpenAPI Magic** ✨
   ```bash
   # Turn any API into an MCP tool in one command
   uvx automagik-tools tool --url https://api.example.com/openapi.json
   
   # Or if you're in the repo:
   make tool URL=https://api.example.com/openapi.json
   ```

2. **Auto-Discovery Engine** 🔍
   - Drop tools in the `tools/` folder
   - They're instantly available - no registration, no config
   - Dynamic loading at runtime

3. **Production-Ready** 🏭
   - FastMCP framework for reliability
   - Built-in auth, rate limiting, error handling
   - Battle-tested at Namastex Labs

### 🚀 The Future: Smart Tools™ (Coming Q1 2025)

Imagine describing what you want in plain English and having AI automatically:
- Find the right API
- Understand its documentation
- Make the correct calls
- Handle authentication
- Process responses

**"Hey, get me all unread messages from Slack and create tasks in Notion"** → Done. No configuration needed.

---

## 💡 Quick Demo

```bash
# No installation needed - just run with uvx!
uvx automagik-tools list

# Method 1: Pre-generate a tool from OpenAPI (persistent)
uvx automagik-tools tool --url https://api.stripe.com/v1/openapi.json
uvx automagik-tools serve --tool stripe

# Method 2: Direct OpenAPI deployment (no pre-generation needed!) 🚀
uvx automagik-tools serve --openapi-url https://api.stripe.com/v1/openapi.json --api-key sk_test_...
```

That's it. You now have a fully functional MCP tool for Stripe that any AI can use.

### Alternative: Traditional Installation

```bash
# If you prefer pip installation
pip install automagik-tools

# Then use the same commands without uvx
automagik-tools serve --tool stripe
```

---

## 🎯 Perfect For

### AI Engineers & Developers 👩‍💻
- **Build once, use everywhere**: Your tools work with any MCP-compatible AI
- **OpenAPI → MCP in seconds**: Stop writing boilerplate integration code
- **Focus on business logic**: We handle the MCP protocol complexity

### Companies & Startups 🏢
- **Instant AI integration**: Connect your APIs to AI agents immediately
- **Future-proof**: Works with Claude, GPT-4, and upcoming AI models
- **Enterprise-ready**: Built for scale with proper auth and rate limiting

### AI Power Users 🚀
- **1000+ tools coming**: Access the world's APIs through one interface
- **Mix and match**: Combine tools for complex workflows
- **No coding required**: Just configuration and natural language

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
automagik-tools serve-all --tools automagik-agents,evolution-api,evolution-api-v2
```

- Each tool is mounted at its own path, e.g., `/automagik-agents/mcp`, `/evolution-api/mcp`
- You can specify which tools to serve with `--tools`, or omit to serve all discovered tools

### 🤖 Connecting to MCP-Compatible Clients

You can connect your automagik-tools server to any MCP-compatible client using various transport methods:

#### Method 1: stdio Transport (Recommended for Desktop Clients)

##### Using uvx (requires local path until next release)

```json
{
  "mcpServers": {
    "automagik-agents": {
      "transport": "stdio",
      "command": "uvx",
      "args": ["--from", "/path/to/automagik-tools", "automagik-tools", "serve", "--tool", "automagik-agents", "--transport", "stdio"],
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

> **Note**: The automagik-agents tool is not yet available in the PyPI release. Use the local path method above or wait for version 0.1.2.

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

## 🚀 Dynamic OpenAPI Tools (NEW!)

Run any OpenAPI-based API as an MCP tool **without pre-generating files**:

```bash
# Direct deployment - no tool generation needed!
uvx automagik-tools serve --openapi-url https://api.stripe.com/v1/openapi.json --api-key sk_test_...

# With custom base URL (if different from OpenAPI spec)
uvx automagik-tools serve --openapi-url https://example.com/openapi.json --base-url https://api.example.com --api-key your-key

# For stdio transport (Claude Desktop, Cursor, etc.)
uvx automagik-tools serve --openapi-url https://api.stripe.com/v1/openapi.json --api-key sk_test_... --transport stdio
```

### MCP Client Configuration for Dynamic OpenAPI Tools

```json
{
  "mcpServers": {
    "stripe-api": {
      "command": "uvx",
      "args": [
        "automagik-tools", 
        "serve", 
        "--openapi-url", "https://api.stripe.com/v1/openapi.json",
        "--api-key", "sk_test_...",
        "--transport", "stdio"
      ]
    }
  }
}
```

This feature uses FastMCP's native OpenAPI support to create MCP tools on-the-fly from any OpenAPI specification.

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

**Try it:** Run `make serve-all` and your tool is automatically mounted!

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

## 🔥 Current Tools & Integrations

### ⭐ Featured: AutoMagik Agents Integration

**[AutoMagik Agents](https://github.com/namastexlabs/automagik-agents)** - Our flagship integration showcases the power of OpenAPI → MCP transformation:

```json
{
  "mcpServers": {
    "automagik-agents": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "automagik-agents"],
      "env": {
        "AUTOMAGIK_AGENTS_API_KEY": "your-key",
        "AUTOMAGIK_AGENTS_BASE_URL": "http://your-server:8881"
      }
    }
  }
}
```

This single tool gives you access to an entire AI agent ecosystem with:
- 🤖 Template-based agent creation
- 💾 Persistent memory with variable injection
- 🔧 Production-ready FastAPI endpoints
- 🧠 Knowledge graph integration

### 📦 Available Tools

| Tool | Description | Type | Status |
|------|-------------|------|--------|
| **automagik-agents** | Full AI agent system with memory & tools | 🌟 OpenAPI | ✅ Live |
| **evolution-api** | WhatsApp Business integration (legacy) | 📱 Messaging | ✅ Live |
| **evolution-api-v2** | WhatsApp Business integration v2 | 🌟 OpenAPI | ✅ Live |
| **stripe** | Payment processing | 💳 OpenAPI | 🚀 1-click setup |
| **github** | Repository management | 🐙 OpenAPI | 🚀 1-click setup |
| **slack** | Team communication | 💬 OpenAPI | 🚀 1-click setup |
| **notion** | Workspace & docs | 📝 OpenAPI | 🚀 1-click setup |

*🚀 1-click setup = Just run: `uvx automagik-tools tool --url [api-url]` or `make tool URL=[api-url]`*

---

## 🗺️ Roadmap: The Future of AI-API Integration

### Phase 1: Foundation (Completed ✅)
- ✅ Auto-discovery framework
- ✅ OpenAPI → MCP tool generation
- ✅ Multi-tool server with dynamic loading
- ✅ Production-ready deployment

### Phase 2: Scale (Q4 2024 - In Progress 🏗️)
- 🏗️ Tool marketplace with 100+ integrations
- 🏗️ One-click tool installation from registry
- 🏗️ Advanced authentication handling (OAuth2, JWT, API keys)
- 🏗️ Tool composition and chaining

### Phase 3: Intelligence (Q1 2025 - The Game Changer 🚀)

#### **Smart Tools™** - Natural Language API Orchestration

Imagine this conversation:
```
User: "Monitor my Stripe transactions and create Notion tasks for failed payments"
AI: "I'll set that up for you. Connecting to Stripe and Notion..."
[AI automatically discovers APIs, handles auth, sets up monitoring]
AI: "Done! I'm now monitoring your Stripe account and will create Notion tasks for any failed payments."
```

**How Smart Tools Will Work:**
1. **Natural Language Understanding**: Describe what you want in plain English
2. **Automatic API Discovery**: AI finds the right APIs and endpoints
3. **Intelligent Mapping**: Understands API docs and creates optimal integrations
4. **Self-Healing**: Adapts to API changes automatically
5. **Context Awareness**: Remembers your preferences and patterns

### Phase 4: Ecosystem (Q2 2025 🌍)
- **Tool Studio**: Visual tool builder for non-developers
- **Community Hub**: Share and monetize your tools
- **Enterprise Gateway**: Managed tool hosting with SLAs
- **AI Tool Mesh**: Tools that discover and integrate with each other

---

## 📚 Documentation

### For End Users
- 🚀 [Quick Start Guide](docs/end-users/quick-start.md) - Get up and running in 2 minutes
- 🤖 [Claude Desktop Integration](docs/end-users/claude-integration.md) - Step-by-step Claude setup
- 💻 [Cursor Integration](docs/end-users/cursor-integration.md) - AI-powered coding with MCP tools
- 📝 [Configuration Examples](docs/end-users/configuration-examples.md) - Ready-to-use configs
- 🔧 [Troubleshooting](docs/end-users/troubleshooting.md) - Common issues and solutions

### For Developers
- 🏁 [Getting Started](docs/developers/getting-started.md) - Development environment setup
- 🛠️ [Creating Tools](docs/developers/creating-tools.md) - Build your own MCP tools
- 🧪 [Testing Guide](docs/developers/testing-guide.md) - Testing best practices
- 📖 [API Reference](docs/developers/api-reference.md) - Complete API documentation

### Technical Guides
- 📖 [Tool Creation Guide](docs/TOOL_CREATION_GUIDE.md) - Build MCP tools from scratch
- 🚀 [OpenAPI Integration](docs/OPENAPI_GUIDE.md) - Convert any API to MCP
- 🛠️ [Tool Development Guide](docs/TOOL_DEVELOPMENT_GUIDE.md) - Advanced development
- ✅ [FastMCP Compliance](docs/FASTMCP_COMPLIANCE.md) - Framework compliance guide

### Deployment
- 🐳 [Docker Deployment Guide](deploy/README.md) - Deploy to AWS, Google Cloud, Railway, and more

### External Resources
- [FastMCP Documentation](https://github.com/jlowin/fastmcp) - Framework reference
- [MCP Specification](https://modelcontextprotocol.io) - Protocol details

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

## 🌟 Join the AI Revolution

**AutoMagik Tools is reshaping how AI interacts with the digital world.** We're not just building tools; we're creating the infrastructure that will power the next generation of AI applications.

### Why This Matters

Every API on the internet is a capability waiting to be unlocked. With AutoMagik Tools:
- **Today**: Convert any OpenAPI spec to an MCP tool in seconds
- **Tomorrow**: AI that understands and uses any API through natural language
- **The Future**: A world where AI agents seamlessly orchestrate thousands of services

### Get Started Now

```bash
# No installation needed - just run!
uvx automagik-tools list

# You're 30 seconds away from your first AI-powered API integration
```

---

<p align="center">
  <b>🪄 Part of the AutoMagik Ecosystem</b><br>
  <a href="https://github.com/namastexlabs/automagik">AutoMagik</a> |
  <a href="https://github.com/namastexlabs/automagik-agents">AutoMagik Agents</a> |
  <a href="https://github.com/namastexlabs/automagik-tools">AutoMagik Tools</a> |
  <a href="https://github.com/namastexlabs/automagik-ui">AutoMagik UI</a>
</p>

<p align="center">
  <b>Built with ❤️ by <a href="https://namastex.com">Namastex Labs</a></b><br>
  <i>Because we believe AI should talk to everything, everywhere, all at once.</i>
</p>

**AutoMagik Tools is open source and always will be.** We use it daily at Namastex Labs to build production AI systems. Join us in making every API on the internet AI-ready.

🚀 **The future of AI is connected. The future is AutoMagik.** 