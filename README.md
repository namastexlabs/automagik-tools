<p align="center">
  <img src=".github/images/automagik_logo.png" alt="AutoMagik Tools Logo" width="600"/>
</p>

# 🪄 AutoMagik Tools

## Turn Any API into an AI-Ready Tool in Seconds™

**The killer MCP feature**: Drop any OpenAPI URL → Get a live, auto-updating MCP server. When the API updates, your tool updates automatically. No code, no maintenance, just magic. ✨

Born from our daily work at [Namastex Labs](https://www.linkedin.com/company/namastexlabs), AutoMagik Tools makes **every API on the internet instantly accessible to AI agents**.

## 🌟 The Killer Feature: Dynamic OpenAPI → MCP

```bash
# Example: Discord Bot in ONE command
uvx automagik-tools serve \
  --openapi-url https://raw.githubusercontent.com/discord/discord-api-spec/main/specs/openapi.json \
  --transport stdio
```

**That's it!** Your AI can now:
- Send Discord messages
- Manage channels and servers  
- React to messages
- Handle voice channels
- Everything in Discord's API

**The Magic**: 
- 🔄 **Always Up-to-Date**: Fetches the OpenAPI spec on every start - if Discord updates their API, your tool automatically has the new endpoints!
- 🚀 **Zero Code**: No writing tool definitions, no maintenance
- 🔐 **Secure**: API keys stay in your environment
- 🌐 **Universal**: Works with ANY OpenAPI spec (Stripe, Slack, GitHub, your internal APIs...)

## 🚀 Quick Start (30 seconds to your first AI tool)

### 1️⃣ Test it instantly (no install needed):

```bash
# Try with Discord API
uvx automagik-tools serve \
  --openapi-url https://raw.githubusercontent.com/discord/discord-api-spec/main/specs/openapi.json \
  --transport stdio

# Or try AutoMagik Agents (our AI orchestration tool)
uvx automagik-tools serve --tool automagik-agents --transport stdio
```

### 2️⃣ Add to Claude/Cursor:

```bash
# Generate config automatically
uvx automagik-tools mcp-config discord-api

# Copy the output to:
# - Cursor: ~/.cursor/mcp.json
# - Claude Desktop: Settings → Developer → Edit Config
```

### 3️⃣ That's it! Your AI now has superpowers 🚀

## 📋 Real-World Examples

### Discord Bot (using official Discord OpenAPI)
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
        "DISCORD_TOKEN": "YOUR_BOT_TOKEN"  // Get from https://discord.com/developers
      }
    }
  }
}
```

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

### AutoMagik Agents 🤖
Our flagship AI orchestration platform - perfect for complex workflows:

```bash
# Quick test
uvx automagik-tools serve --tool automagik-agents --transport stdio
```

**Features:**
- Multi-agent orchestration
- Tool composition & chaining
- Memory management
- Async execution
- Built-in safety rails

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

**The killer part**: When the API provider updates their OpenAPI spec, your tool automatically gets the new endpoints. No code changes, no maintenance.

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