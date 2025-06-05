<p align="center">
  <img src=".github/images/automagik_logo.png" alt="AutoMagik Tools Logo" width="600"/>
</p>

# 🪄 AutoMagik Tools

## Turn Any API into an AI-Ready Tool in Seconds™

Drop any OpenAPI URL → Get a live, auto-updating MCP server. When the API updates, your tool updates automagikally. No code, no maintenance.

Born from our daily work at [Namastex Labs](https://www.linkedin.com/company/namastexlabs), AutoMagik Tools makes **every API on the internet instantly accessible to AI agents**.

## 🚀 Dynamic OpenAPI → MCP

Turn any API into an MCP tool instantly:

```bash
# Just point to any OpenAPI URL - here's Discord as an example
uvx automagik-tools serve \
  --openapi-url https://raw.githubusercontent.com/discord/discord-api-spec/main/specs/openapi.json \
  --transport sse --port 8001
```

**Works with ANY OpenAPI spec:**
- 🔄 Auto-updates when the API changes
- 🚀 Zero code, just paste the URL
- 🌐 Discord, Stripe, GitHub, Slack, or your internal APIs

## 🌟 Featured Tool: AutoMagik

> **AI orchestration that speaks human** - Production-ready platform for complex AI workflows

```bash
uvx automagik-tools serve --tool automagik-agents --transport sse --port 8000
```

💬 Natural Language • ✨ Spark (spawn agent hives) • 🔄 Task Scheduling • 🏗️ Framework Agnostic (PydanticAI, LangGraph, CrewAI) • 🤝 Dev Friendly

## 🚀 Quick Start

### Copy this into Claude/Cursor to get Discord AI powers:

```json
{
  "mcpServers": {
    "discord": {
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
        "DISCORD_TOKEN": "YOUR_BOT_TOKEN"
      }
    }
  }
}
```

**Where to paste:**
- **Claude Desktop**: Settings → Developer → Edit Config
- **Cursor**: `~/.cursor/mcp.json`

### Or test instantly via command line:

```bash
# Discord API
uvx automagik-tools serve \
  --openapi-url https://raw.githubusercontent.com/discord/discord-api-spec/main/specs/openapi.json \
  --transport sse --port 8001

# AutoMagik AI orchestration
uvx automagik-tools serve --tool automagik-agents --transport sse --port 8000
```

## 📋 Real-World Examples

### AutoMagik Configuration (for Claude/Cursor)
```json
{
  "mcpServers": {
    "automagik": {
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

Now in Claude/Cursor you can say:
- "Use AutoMagik to analyze these 10 CSV files and find patterns"
- "Set up a workflow that monitors my GitHub repos and creates weekly summaries"
- "Process these customer feedback emails and categorize them by sentiment"


### More OpenAPI Examples
```bash
# Stripe Payments
uvx automagik-tools serve \
  --openapi-url https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json \
  --api-key $STRIPE_API_KEY

# GitHub API  
uvx automagik-tools serve \
  --openapi-url https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json \
  --api-key $GITHUB_TOKEN

# Your Internal API
uvx automagik-tools serve \
  --openapi-url https://api.yourcompany.com/openapi.json \
  --api-key $YOUR_API_KEY
```

## 🛠️ Built-in Tools

### AutoMagik 🤖
AI orchestration that speaks human:

```bash
# Quick test with SSE
uvx automagik-tools serve --tool automagik-agents --transport sse --port 8000
```

**What you can do:**
- ✨ Use Spark to spawn hives of agents in seconds
- 🔄 Schedule recurring AI tasks and automations
- 💬 Natural language task descriptions
- 🏗️ Works with any AI framework

### Evolution API (WhatsApp) 📱
Complete WhatsApp automation:
- Send/receive messages
- Media support (images, documents)
- Group management
- Status updates

## 🎯 Why This Changes Everything

**Before AutoMagik Tools:**
1. Find an API you want to use
2. Read documentation for hours
3. Write tool definitions manually
4. Test and debug
5. Maintain when API changes
6. Repeat for every API 😭

**With AutoMagik Tools:**
1. Find the OpenAPI URL
2. Run one command
3. Done! 🎉

**The best part**: When the API provider updates their OpenAPI spec, your tool automagikally gets the new endpoints. No code changes, no maintenance.

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