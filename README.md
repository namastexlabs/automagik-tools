<p align="center">
  <img src=".github/images/automagik_logo.png" alt="AutoMagik Tools Logo" width="600"/>
</p>

# 🪄 AutoMagik Tools

## MCP Agents That Learn Your APIs Automagikally

Drop any OpenAPI spec → Get an intelligent MCP agent that learns how you work and gets better with every interaction. Export to code when you're ready to customize.

Born from our daily work at [Namastex Labs](https://www.linkedin.com/company/namastexlabs), AutoMagik Tools creates **self-evolving agents** that turn any API into a natural language interface.

## 🧠 Self-Learning MCP Agents

Unlike static tools, AutoMagik agents **remember and adapt**:

```bash
# First time: "How much did I sell last month?"
# Agent learns your sales endpoints, date formats, and preferences

# By the 10th interaction:
# Agent already knows exactly which data you want and how you like it formatted
uvx automagik-tools tool automagik -t sse --port 8000
```

**Three Intelligence Modes:**
- 🔧 **Standard**: Full schema access for precise control
- 📋 **Markdown**: Agent processes noisy JSON into clean, readable output (powered by GPT-4.1-nano)
- 💬 **Genie**: Natural language interface - just describe what you need

*Powered by GPT-4.1 family models for cost-effective agentic behavior and reliable API reasoning.*

## 🚀 From Any API to Smart Agent

Turn any OpenAPI spec into an intelligent agent:

```bash
# Discord API becomes a smart agent
uvx automagik-tools openapi \
  https://raw.githubusercontent.com/discord/discord-api-spec/main/specs/openapi.json \
  -t sse --port 8001

# Share this agent with your entire team via SSE
# Team members can access the same learning agent at http://localhost:8001
```

**Now you can say:**
- "Show me unread messages from the design team"
- "Schedule a voice call for 3pm in the dev channel"
- "Find all threads where someone mentioned the new feature"

Agent learns your patterns, server preferences, and communication style.

## 🧞 Genie: Universal MCP Orchestrator

**Genie connects any MCP servers and orchestrates them with persistent memory**:

```bash
# Run Genie with memory-based agents
uvx automagik-tools tool genie -t sse --port 8000
```

### Configure Genie with Multiple MCP Servers

Genie can orchestrate any combination of MCP servers. Configure via environment variables:

```bash
# Method 1: JSON configuration for multiple servers
export GENIE_MCP_CONFIGS='{
  "agent-memory": {
    "url": "http://192.168.112.149:8000/sse",
    "transport": "sse"
  },
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"],
    "env": {}
  },
  "github": {
    "command": "uvx",
    "args": ["mcp-server-git"],
    "env": {"GITHUB_TOKEN": "your-token"}
  }
}'

# Method 2: AutoMagik-specific shorthand
export GENIE_AUTOMAGIK_API_KEY="your-api-key"
export GENIE_AUTOMAGIK_BASE_URL="http://localhost:8881"
export GENIE_AUTOMAGIK_TIMEOUT="600"
```

### Add Genie to Claude/Cursor (Universal Orchestrator)

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=discord&config=eyJjb21tYW5kIjoidXZ4IGF1dG9tYWdpay10b29sc0BsYXRlc3Qgc2VydmUgLS1vcGVuYXBpLXVybCBodHRwczovL3Jhdy5naXRodWJ1c2VyY29udGVudC5jb20vZGlzY29yZC9kaXNjb3JkLWFwaS1zcGVjL21haW4vc3BlY3Mvb3BlbmFwaS5qc29uIC0tdHJhbnNwb3J0IHN0ZGlvIiwiZW52Ijp7IkRJU0NPUkRfVE9LRU4iOiJZT1VSX0JPVF9UT0tFTiJ9fQ%3D%3D)

```json
{
  "mcpServers": {
    "genie": {
      "command": "uvx",
      "args": [
        "automagik-tools@latest",
        "serve",
        "--tool",
        "genie",
        "--transport",
        "stdio"
      ],
      "env": {
        "OPENAI_API_KEY": "your-openai-key",
        "GENIE_MCP_CONFIGS": "{\"agent-memory\":{\"url\":\"http://192.168.112.149:8000/sse\",\"transport\":\"sse\"},\"filesystem\":{\"command\":\"npx\",\"args\":[\"-y\",\"@modelcontextprotocol/server-filesystem\",\"/allowed/path\"],\"env\":{}}}"
      }
    }
  }
}
```

**Now in Claude/Cursor, Genie can:**
- "Use the memory agent to remember this conversation"
- "Check the filesystem for project files and analyze them with the memory agent"
- "Coordinate between multiple tools to complete complex tasks"

## 🌟 Featured: AutoMagik Orchestration

Enterprise-grade agent orchestration that speaks human:

```bash
uvx automagik-tools tool automagik --transport sse --port 8000
```

**Real examples from our users:**
- "Monitor inventory across all warehouses and alert me when Corona drops below 10k units"
- "Generate weekly performance reports and send to regional managers"  
- "Set up automated quality checks for next month's production runs"
- "Track competitor pricing and notify me of changes above 5%"

💬 Natural Language • 🧠 Memory & Learning • 🔄 Task Orchestration • 🏗️ Framework Agnostic • 👩‍💻 Export to Code

## 🚀 Quick Start

### Environment Setup

Create a `.env` file with your API keys:

```bash
# .env
OPENAI_API_KEY=sk-your-openai-key-here
AUTOMAGIK_API_KEY=your-automagik-api-key
AUTOMAGIK_BASE_URL=http://localhost:8881

# Enable JSON to Markdown processing (optional)
ENABLE_JSON_PROCESSING=true
JSON_PROCESSOR_MODEL=gpt-4.1-nano
```

### Copy this into Claude/Cursor for instant API orchestration:


[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/install-mcp?name=automagik&config=eyJjb21tYW5kIjoidXZ4IGF1dG9tYWdpay10b29sc0BsYXRlc3Qgc2VydmUgLS10b29sIGF1dG9tYWdpayAtLXRyYW5zcG9ydCBzdGRpbyIsImVudiI6eyJBVVRPTUFHSUtfQUdFTlRTX0FQSV9LRVkiOiJZT1VSX0FQSV9LRVkiLCJBVVRPTUFHSUtfQUdFTlRTX0JBU0VfVVJMIjoiaHR0cDovL2xvY2FsaG9zdDo4ODgxIiwiQVVUT01BR0lLX0FHRU5UU19PUEVOQVBJX1VSTCI6Imh0dHA6Ly9sb2NhbGhvc3Q6ODg4MS9hcGkvdjEvb3BlbmFwaS5qc29uIn19)
```json
{
  "mcpServers": {
    "automagik": {
      "command": "uvx",
      "args": [
        "automagik-tools@latest",
        "serve",
        "--tool",
        "automagik",
        "--transport",
        "stdio"
      ],
      "env": {
        "AUTOMAGIK_API_KEY": "YOUR_API_KEY",
        "AUTOMAGIK_BASE_URL": "http://localhost:8881",
        "OPENAI_API_KEY": "YOUR_OPENAI_API_KEY"
      }
    }
  }
}
```

**Where to add:**
- **Claude Desktop**: Settings → Developer → Edit Config
- **Cursor**: `~/.cursor/mcp.json`

### Test any API instantly:

```bash
# Jira becomes conversational project management
OPENAI_API_KEY=your_key JIRA_API_TOKEN=your_token uvx automagik-tools serve \
  --openapi-url https://dac-static.atlassian.com/cloud/jira/platform/swagger-v3.v3.json \
  --transport sse --port 8002

# Shopify for e-commerce automation  
OPENAI_API_KEY=your_key SHOPIFY_ACCESS_TOKEN=your_token uvx automagik-tools serve \
  --openapi-url https://shopify.dev/docs/api/admin-rest/2023-04/openapi.json \
  --transport sse --port 8003

# SSE mode allows your team to share the same learning agent
```

## 📋 Real-World Agent Examples

### Genie Orchestrating Multiple Tools

**Personal Automation:**
- "Use memory agent to remember my GitHub preferences, then check my repos and create a weekly summary"
- "Process these expense receipts with the filesystem tool and store insights in memory"
- "Monitor my crypto portfolio with the trading API and remember my risk preferences"

**Team Coordination:**
- "Coordinate between Slack and Linear to set up daily standups for the design team"
- "Use the file system to track project deadlines and notify stakeholders via Discord"  
- "Analyze customer feedback from multiple sources and create sentiment reports"

**Business Intelligence:**
- "Compare Q4 sales across all regions using the database and memory tools"
- "Generate inventory reports by coordinating warehouse APIs and document storage"
- "Monitor competitor pricing across platforms and update my preference memory"

The agent **learns your patterns** - after a few interactions, it knows exactly how you like your data formatted, which metrics matter most, and when to proactively alert you.

## 🛠️ Advanced Usage

### Multiple Server Configurations

Configure Genie with different MCP server combinations:

```bash
# Development setup with local tools
export GENIE_MCP_CONFIGS='{
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"],
    "env": {}
  },
  "git": {
    "command": "uvx", 
    "args": ["mcp-server-git"],
    "env": {"GIT_AUTHOR_NAME": "Your Name"}
  }
}'

# Production setup with external services
export GENIE_MCP_CONFIGS='{
  "automagik": {
    "command": "uvx",
    "args": ["automagik-tools", "tool", "automagik", "--transport", "stdio"],
    "env": {
      "AUTOMAGIK_API_KEY": "prod-key",
      "AUTOMAGIK_BASE_URL": "https://api.yourcompany.com"
    }
  },
  "slack": {
    "command": "docker",
    "args": ["run", "-i", "--rm", "-e", "SLACK_BOT_TOKEN", "mcp/slack"],
    "env": {"SLACK_BOT_TOKEN": "xoxb-your-token"}
  }
}'
```

### Dynamic MCP Server Connection

You can also pass MCP server configurations directly to Genie via the `ask_genie` tool:

```json
{
  "tool": "ask_genie",
  "arguments": {
    "query": "List all my GitHub repositories and remember my coding preferences",
    "mcp_servers": {
      "github": {
        "command": "uvx",
        "args": ["mcp-server-git"],
        "env": {"GITHUB_TOKEN": "your-token"}
      },
      "memory": {
        "url": "http://localhost:8000/sse",
        "transport": "sse"
      }
    }
  }
}
```

## 🎯 Why Intelligent Agents Matter

**The old way:** Hours writing API integrations, maintaining complex schemas, fighting with documentation. When APIs change, everything breaks.

**The AutoMagik way:**
1. **Point** to any OpenAPI spec
2. **Ask** in natural language what you need  
3. **Learn** as the agent adapts to your workflow
4. **Export** to code when you need customization

When your needs evolve, your agent **learns and remembers**.

## 🛠️ Built-in Tools

### AutoMagik 🤖
AI orchestration that speaks human:

```bash
# Quick test with SSE
uvx automagik-tools tool automagik --transport sse --port 8000
```

**What you can do:**
- ✨ Use Spark to spawn hives of agents in seconds
- 🔄 Schedule recurring AI tasks and automations
- 💬 Natural language task descriptions
- 🏗️ Works with any AI framework

### Genie 🧞
Universal MCP orchestrator with persistent memory:

```bash
# Run as SSE server for team sharing
uvx automagik-tools tool genie --transport sse --port 8000
```

**Capabilities:**
- 🧠 Persistent memory across all sessions
- 🔗 Connect to unlimited MCP servers
- 💬 Natural language task coordination
- 👥 Shared learning across team members

### AutoMagik Workflows 🚀
Smart Claude workflow orchestration with real-time progress tracking:

```bash
# Execute Claude Code workflows with progress monitoring
uvx automagik-tools tool automagik-workflows --transport stdio
```

**Features:**
- 🚀 **Run Claude Code Workflows**: Execute workflows with progress reporting
- 📊 **Real-time Status**: Track workflow completion with visual progress
- 📋 **List Workflows**: Discover available workflows and recent runs  
- 🔄 **Status Monitoring**: Get detailed workflow execution status

### Evolution API (WhatsApp) 📱
Complete WhatsApp automation:
- Send/receive messages
- Media support (images, documents)
- Group management
- Status updates

## 🚀 The Future: Self-Maintaining Tools

Our roadmap includes agents that:
- **Auto-discover** API endpoints without OpenAPI specs
- **Auto-evolution**: Tools that update and adapt when APIs change
- **Self-debug** and report issues back to maintainers
- **Collaborate** with other agents for complex workflows
- **Generate** their own tools from natural language descriptions

**Production Deployments (Coming Soon):**
- 🐳 **Docker**: One-click deployment scripts for containerized agents
- ☁️ **Cloud Ready**: Deploy to AWS, Google Cloud, Azure with pre-built templates
- 🌐 **Team Sharing**: VPS and network deployments for organization-wide agent access
- 📈 **Scalable**: Load balancing and auto-scaling for high-demand agents

*Coming 2025: A hive of AI agents maintaining this entire codebase - reporting bugs, implementing features, and keeping users happy. All open source.*

## 📋 Real-World Examples

### Genie with Memory Agent
```json
{
  "mcpServers": {
    "genie_with_memory": {
      "command": "uvx",
      "args": [
        "automagik-tools@latest",
        "serve",
        "--tool",
        "genie",
        "--transport",
        "stdio"
      ],
      "env": {
        "OPENAI_API_KEY": "your-openai-key",
        "GENIE_MCP_CONFIGS": "{\"agent-memory\":{\"url\":\"http://192.168.112.149:8000/sse\",\"transport\":\"sse\"}}"
      }
    }
  }
}
```

### AutoMagik with Multiple APIs
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
uvx automagik-tools openapi https://api.example.com/openapi.json

# Method 2: Generate persistent tool
uvx automagik-tools create-tool --url https://api.example.com/openapi.json --name my-api
uvx automagik-tools tool my-api
```

## Adding Your Own Tools

1. Create a folder in `automagik_tools/tools/your_tool/`
2. Add `__init__.py` with FastMCP server
3. That's it - auto-discovered!

See our [Tool Creation Guide](docs/TOOL_CREATION_GUIDE.md) for details.

## Available Commands

```bash
# Core commands
automagik-tools list              # List all available tools
automagik-tools hub               # Serve all tools together
automagik-tools tool <name>       # Serve a specific tool
automagik-tools openapi <url>     # Serve from OpenAPI spec
automagik-tools mcp-config <tool> # Generate MCP config
automagik-tools info <tool>       # Show tool details
automagik-tools version           # Show version

# Development commands  
make install                            # Install dev environment
make test                               # Run all tests
make lint                               # Check code style
make format                             # Auto-format code
make build                              # Build package
make docker-build                       # Build Docker images
```

</details>

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
  <b>Every API becomes a smart agent that learns how you work.</b><br>
  <a href="https://github.com/namastexlabs/automagik-tools">Star us on GitHub</a> • 
  <a href="https://discord.gg/automagik">Join our Discord</a> • 
  <a href="https://twitter.com/namastexlabs">Follow on Twitter</a>
</p>
