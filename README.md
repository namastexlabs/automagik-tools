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

You can install automagik-tools as a standard Python package:

```bash
pip install automagik-tools
```

Or, for development (editable) installs:

```bash
git clone https://github.com/namastexlabs/automagik-tools.git
cd automagik-tools
pip install -e .
```

---

## 🏁 Quick Start

### 1. List Available Tools

```bash
automagik-tools list
```

### 2. Run a Tool Server (Single Tool)

```bash
automagik-tools serve --tool evolution-api
```

- By default, serves on `0.0.0.0:8000` (configurable with `--host` and `--port`)
- The tool will be available at `/mcp` (e.g., `http://localhost:8000/mcp`)

### 3. Run a Multi-Tool Server

```bash
automagik-tools serve-all --tools evolution-api,discord,notion
```

- Each tool is mounted at its own path, e.g., `/evolution-api/mcp`, `/discord/mcp`
- You can specify which tools to serve with `--tools`, or omit to serve all discovered tools

### 🤖 Connecting to MCP-Compatible Clients

You can connect your automagik-tools server to any MCP-compatible client (such as an LLM agent, orchestrator, or workflow tool) by specifying the server endpoint in a JSON configuration. For example:

```json
{
    "mcpServers": {
        {
        "whatsapp-evolution-api": {
            "transport": "sse",
            "url": "http://localhost:8000/mcp"
        }
    }
}
```

- For multi-tool servers, use the full path (e.g., `/evolution-api/mcp`):

```json
{
    "mcpServers": {
        {
        "whatsapp-evolution-api": {
            "transport": "sse",
           "url": "http://localhost:8000/evolution-api/mcp"
        }
    }
}
```

- Adjust the `url` to match your server's address and port.
- The `transport` can be `sse`, `stdio`, or another supported protocol depending on your client and deployment.

This allows your LLM agent or automation platform to call tools, access resources, and use prompts exposed by automagik-tools as part of its workflow.

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
- [Automagik Tools Docs](https://automagik-tools.readthedocs.io/) *(if available)*

---

## 📝 License
MIT 