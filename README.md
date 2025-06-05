<p align="center">
  <img src=".github/images/automagik_logo.png" alt="AutoMagik Tools Logo" width="600"/>
</p>

# 🪄 AutoMagik Tools

## Turn Any API into an AI-Ready Tool in Seconds™

**The most comprehensive collection of Model Context Protocol (MCP) tools**. Drop an OpenAPI spec, get an MCP tool. It's that simple.

Born from our daily work at [Namastex Labs](https://www.linkedin.com/company/namastexlabs), AutoMagik Tools transforms the way AI agents interact with the real world. We're building the infrastructure that makes **every API on the internet instantly accessible to AI**.

## 🚀 Quick Start

### Using uvx (Recommended - No Installation)

```bash
# List available tools
uvx automagik-tools list

# Instant MCP server from any OpenAPI spec
uvx automagik-tools serve \
  --openapi-url https://raw.githubusercontent.com/discord/discord-api-spec/main/specs/openapi.json \
  --transport stdio

# Serve a built-in tool
uvx automagik-tools serve --tool automagik-agents --transport stdio

# Generate MCP config for Claude/Cursor
uvx automagik-tools mcp-config discord-api
uvx automagik-tools mcp-config automagik-agents
```

### Local Installation

```bash
# Install with uv
uv pip install automagik-tools

# Or clone and install from source
git clone https://github.com/namastexlabs/automagik-tools
cd automagik-tools
make install  # Uses uv internally

# Then use commands without uvx
automagik-tools serve --tool evolution-api
```

## 🎯 For Claude/Cursor Users

### 1. Generate your MCP configuration:

```bash
# For Discord API (dynamic OpenAPI)
uvx automagik-tools mcp-config discord-api

# For built-in tools
uvx automagik-tools mcp-config automagik-agents
```

### 2. Add to your MCP config file:
- **Cursor**: `~/.cursor/mcp.json`
- **Claude Desktop**: Settings → Developer → Edit Config

### 3. Example configuration:

```json
{
  "mcpServers": {
    "discord-api": {
      "command": "uvx",
      "args": [
        "automagik-tools@latest",
        "serve",
        "--openapi-url",
        "https://raw.githubusercontent.com/discord/discord-api-spec/main/specs/openapi.json",
        "--transport",
        "stdio"
      ],
      "env": {
        "DISCORD_TOKEN": "YOUR_DISCORD_TOKEN"
      }
    },
    "automagik-agents": {
      "command": "uvx",
      "args": [
        "automagik-tools@latest",
        "serve",
        "--tool",
        "automagik-agents",
        "--transport",
        "stdio"
      ],
      "env": {
        "AUTOMAGIK_AGENTS_API_KEY": "YOUR_API_KEY",
        "AUTOMAGIK_AGENTS_BASE_URL": "http://localhost:8881",
        "AUTOMAGIK_AGENTS_OPENAPI_URL": "http://localhost:8881/api/v1/openapi.json"
      }
    }
  }
}
```

## 🌟 Key Features

### 1. **Instant OpenAPI → MCP** ✨
```bash
# Any OpenAPI URL becomes an MCP server instantly
uvx automagik-tools serve --openapi-url <url> --transport stdio

# With authentication
uvx automagik-tools serve --openapi-url <url> --api-key YOUR_KEY

# Custom base URL
uvx automagik-tools serve --openapi-url <url> --base-url https://api.custom.com
```

### 2. **Auto-Discovery Engine** 🔍
- Drop tools in the `tools/` folder
- They're instantly available - no registration, no config
- Dynamic loading at runtime

### 3. **Production-Ready** 🏭
- FastMCP framework for reliability
- Built-in auth, rate limiting, error handling
- Battle-tested at Namastex Labs

## 📦 Built-in Tools

| Tool | Description |
|------|-------------|
| **evolution-api** | WhatsApp automation via Evolution API |
| **evolution-api-v2** | Enhanced WhatsApp with media support |
| **automagik-agents** | AI agent orchestration platform |

## 🎯 Why AutoMagik Tools?

**The Problem**: AI agents need to interact with thousands of APIs, but creating MCP tools is time-consuming and repetitive.

**Our Solution**: 
- 🚀 **Instant API → MCP Tool**: Drop any OpenAPI.json, get a fully functional MCP tool
- 🤖 **Coming Soon: Smart Tools™**: Natural language API calls - just describe what you want
- 🔌 **Zero Configuration**: Auto-discovery means tools just work
- 🌐 **Universal Compatibility**: Works with Claude, Cursor, and any MCP-compatible AI

<details>
<summary><b>🛠️ Developer Documentation</b></summary>

## Development Setup

```bash
# Clone the repo
git clone https://github.com/namastexlabs/automagik-tools
cd automagik-tools

# Install with all dev dependencies
make install

# Run tests
make test

# Create a new tool
make new-tool
```

## Creating Tools from OpenAPI

```bash
# Method 1: Dynamic (no files created)
uvx automagik-tools serve --openapi-url https://api.example.com/openapi.json

# Method 2: Generate persistent tool
uvx automagik-tools tool --url https://api.example.com/openapi.json --name my-api
uvx automagik-tools serve --tool my-api
```

## Adding Your Own Tools

1. Create a folder in `automagik_tools/tools/your_tool/`
2. Add `__init__.py` with FastMCP server
3. That's it - auto-discovered!

See our [Tool Creation Guide](docs/TOOL_CREATION_GUIDE.md) for details.

## Available Commands

```bash
# Core commands
automagik-tools list                    # List all available tools
automagik-tools serve                   # Serve a tool or OpenAPI spec
automagik-tools serve-all               # Serve all tools on one server
automagik-tools mcp-config <tool>       # Generate MCP config
automagik-tools info <tool>             # Show tool details
automagik-tools version                 # Show version

# Development commands  
make install                            # Install dev environment
make test                               # Run all tests
make lint                               # Check code style
make format                             # Auto-format code
make build                              # Build package
make docker-build                       # Build Docker images
```

</details>

## 🚀 The Future: Smart Tools™ (Coming Q2 2025)

Imagine describing what you want in plain English and having AI automatically:
- Find the right API
- Understand its documentation
- Make the correct calls
- Handle authentication
- Process responses

**"Hey, get me all unread messages from Slack and create tasks in Notion"** → Done. No configuration needed.

## 🤝 Contributing

We love contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🙏 Credits

Built with ❤️ by [Namastex Labs](https://www.linkedin.com/company/namastexlabs)

Special thanks to:
- [Anthropic](https://anthropic.com) for MCP
- [FastMCP](https://github.com/jlowin/fastmcp) for the awesome framework
- Our amazing community of contributors

---

<p align="center">
  <b>Transform any API into an AI-ready tool in seconds.</b><br>
  <a href="https://github.com/namastexlabs/automagik-tools">Star us on GitHub</a> • 
  <a href="https://discord.gg/automagik">Join our Discord</a> • 
  <a href="https://twitter.com/namastexlabs">Follow on Twitter</a>
</p>