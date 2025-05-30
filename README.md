# automagik-tools

A monorepo Python package for building, running, and extending Model Context Protocol (MCP) tools and servers. It provides a plugin-based framework for integrating real-world services (like WhatsApp, Discord, Notion, GitHub, etc.) with AI agents and LLMs, using the FastMCP protocol.

---

## 🚀 Features
- **Multi-tool server:** Serve multiple tools on a single FastAPI/Uvicorn server with path-based routing
- **Plugin architecture:** Easily add new tools via entry points
- **Ready-to-use integrations:** WhatsApp (Evolution API), with more planned (Discord, Notion, GitHub)
- **CLI interface:** List, run, and manage tools from the command line
- **Dynamic loading:** Tools are discovered and loaded at runtime

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

For development (editable) installs:

```bash
git clone https://github.com/namastexlabs/automagik-tools.git
cd automagik-tools
pip install -e ".[dev]"
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
uvx automagik-tools serve --tool evolution-api

# Or using pip-installed version
automagik-tools serve --tool evolution-api
```

- By default, serves on `0.0.0.0:8000` (configurable with `--host` and `--port`)
- The tool will be available at `/mcp` (e.g., `http://localhost:8000/mcp`)

### 3. Run a Multi-Tool Server

```bash
# Using uvx
uvx automagik-tools serve-all --tools evolution-api

# Or using pip-installed version  
automagik-tools serve-all --tools evolution-api,discord,notion
```

- Each tool is mounted at its own path, e.g., `/evolution-api/mcp`, `/discord/mcp`
- You can specify which tools to serve with `--tools`, or omit to serve all discovered tools

### 🤖 Connecting to MCP-Compatible Clients

You can connect your automagik-tools server to any MCP-compatible client in several ways:

#### Option 1: Using uvx with stdio transport (Recommended)

Most MCP clients support running tools via stdio transport using uvx:

```json
{
  "mcpServers": {
    "automagik-tools": {
      "transport": "stdio",
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://your-api-server.com",
        "EVOLUTION_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

For multiple tools:

```json
{
  "mcpServers": {
    "automagik-tools-multi": {
      "transport": "stdio",
      "command": "uvx", 
      "args": ["automagik-tools", "serve-all", "--tools", "evolution-api", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://your-api-server.com",
        "EVOLUTION_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

#### Option 2: Using uvx with development version

If you're developing or want to use a local version:

```json
{
  "mcpServers": {
    "automagik-tools-dev": {
      "transport": "stdio",
      "command": "uvx",
      "args": ["--from", "/path/to/automagik-tools", "automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
      "env": {
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
    "automagik-tools": {
      "command": "uvx",
      "args": ["automagik-tools", "serve", "--tool", "evolution-api", "--transport", "stdio"],
      "env": {
        "EVOLUTION_API_BASE_URL": "https://your-api-server.com",
        "EVOLUTION_API_KEY": "your_api_key_here"
      }
    }
  }
}
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

Some tools require configuration (e.g., API keys, base URLs). You can set these via environment variables or a `.env` file in your project root. Example for Evolution API:

```env
EVOLUTION_API_BASE_URL=https://your-evolution-api-server.com
EVOLUTION_API_KEY=your_api_key_here
EVOLUTION_API_TIMEOUT=30
```

---

## 🛠️ Developing New Tools

You can add new tools by creating a Python module and registering it as an entry point in your `pyproject.toml`:

1. **Create your tool:**

```python
# my_tools/my_cool_tool.py
from fastmcp import FastMCP

def create_tool(config):
    mcp = FastMCP("My Cool Tool")

    @mcp.tool()
    def say_hello(name: str) -> str:
        return f"Hello, {name}!"

    return mcp
```

2. **Register the tool in your `pyproject.toml`:**

```toml
[project.entry-points."automagik_tools.plugins"]
my-cool-tool = "my_tools.my_cool_tool:create_tool"
```

3. **Install your package (editable mode recommended for development):**

```bash
pip install -e .
```

4. **Your tool will now appear in `automagik-tools list` and can be served!**

---

## 🧩 Extending/Contributing
- Add new tools as plugins using the entry point system
- Follow the FastMCP documentation for advanced tool/resource/prompt patterns
- PRs and issues welcome!

---

## 📚 Documentation
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

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