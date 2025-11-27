# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

automagik-tools is a monorepo Python package for building MCP (Model Context Protocol) tools. It provides a plugin-based framework for integrating real-world services with AI agents using FastMCP.

**IMPORTANT: Each tool is self-contained in its own folder under `automagik_tools/tools/`. There is no separate servers folder - tools export their servers directly.**

## Vision: The Premier MCP Tools Repository

This repository aims to become the largest and most comprehensive collection of MCP tools, making it trivially easy for developers to:
1. Add new tools with minimal boilerplate
2. Discover and use existing tools
3. Compose tools for complex workflows
4. Deploy tools at scale

## 🤖 Automated Development Workflows

**IMPORTANT: All development tasks must use the specialized workflows in `.claude/commands/` for consistency and quality.**

### Available Workflows

The repository contains specialized workflows for automated tool development:

- **ORCHESTRATOR** (`orchestrator.md`) - Project management and workflow coordination
- **ANALYZER** (`analyzer.md`) - Requirements analysis and implementation planning  
- **BUILDER** (`builder.md`) - Tool implementation and coding
- **TESTER** (`tester.md`) - Comprehensive testing and validation
- **VALIDATOR** (`validator.md`) - Quality assurance and compliance checks
- **DEPLOYER** (`deployer.md`) - Package and deployment management

### Workflow Usage

**For New Tool Development:**
```bash
# Use ORCHESTRATOR to coordinate the full development process
@ORCHESTRATOR Create MCP tool for [API Name] with [functionality]. 
API docs: [URL]. Authentication: [method]. Priority: [high/medium/low]
```

**For Tool Enhancement:**
```bash
# Use ORCHESTRATOR to coordinate enhancement work
@ORCHESTRATOR Enhance [tool_name] with [new_features]. 
Current issues: [description]. OpenAPI: [URL if applicable]
```

**For Individual Tasks:**
```bash
# Use specific workflows for focused tasks
@ANALYZER Analyze requirements for [tool_name] enhancement
@BUILDER Implement [specific_feature] for [tool_name]
@TESTER Create test suite for [tool_name]
```

### Workflow Integration

- **Linear Integration**: All workflows create and update Linear issues for tracking
- **Memory System**: Patterns and learnings are stored in agent-memory for reuse
- **Quality Gates**: Each workflow has specific success criteria and validation
- **Pattern Reuse**: >80% code reuse from existing successful implementations

### Development Rules

1. **Always use workflows** - Never implement tools manually without workflow coordination
2. **Follow handoffs** - Each workflow prepares specific outputs for the next
3. **Update Linear** - All progress must be tracked in Linear issues
4. **Store patterns** - Successful implementations must be stored in memory
5. **Validate quality** - All tools must pass validation before deployment

See `.claude/commands/README.md` for detailed workflow documentation.

## Essential Commands

### Development Setup
```bash
make install              # Install in development mode with all dependencies
```

### Testing
```bash
make test                 # Run all tests
make test-unit            # Run unit tests only
make test-mcp             # Run MCP protocol compliance tests
make test-coverage        # Run tests with coverage report

# Run specific tests
pytest tests/test_unit_fast.py -v
pytest -k "test_list"     # Run tests matching pattern
```

### Code Quality
```bash
make lint                 # Check code quality (black + ruff)
make format               # Auto-format code
```

### Building & Publishing
```bash
make build                # Build the package
make publish-test         # Upload to TestPyPI
make publish              # Upload to PyPI (requires PYPI_TOKEN)
```

## Architecture

### Core Components

1. **CLI (`automagik_tools/cli.py`)**: Main entry point using Typer
   - Commands: `list`, `serve`, `serve-all`, `version`
   - Supports stdio and SSE transports
   - Dynamic tool discovery via Python entry points

2. **Tools (`automagik_tools/tools/`)**: Self-contained plugin implementations
   - Each tool is a complete FastMCP server in its own folder
   - Must export: `create_server()`, `get_metadata()`, `get_config_class()`
   - `__main__.py` exports `mcp` for FastMCP CLI compatibility
   - Tools are auto-discovered from the tools directory
   - Currently implements Evolution API (v1 and v2) for WhatsApp

3. **Hub (`automagik_tools/hub.py`)**: Composition pattern
   - Automatically discovers and mounts all tools
   - Provides unified access point for all tools
   - Uses FastMCP's mount() pattern

4. **Testing Strategy**:
   - Unit tests for fast feedback (`test_unit_fast.py`)
   - MCP protocol compliance tests (`test_mcp_protocol.py`)
   - Integration tests for end-to-end flows (`test_integration.py`)
   - Tool-specific tests in `tests/tools/`

### Key Patterns

- **Plugin Discovery**: Tools are registered as entry points in pyproject.toml
- **Configuration**: Environment-based using Pydantic settings
- **Async First**: All MCP operations are async
- **Error Handling**: Comprehensive error recovery with proper MCP error responses

### Adding New Tools

1. Create a new module in `automagik_tools/tools/your_tool/`
2. Implement using FastMCP framework (see docs/TOOL_CREATION_GUIDE.md)
3. Register in pyproject.toml under `[project.entry-points."automagik_tools.plugins"]`
4. Add tests in `tests/tools/test_your_tool.py`
5. Update README.md with tool documentation
6. Add configuration to .env.example

### Key Files for New Tools

- **docs/TOOL_CREATION_GUIDE.md**: Comprehensive guide with templates and examples
- **.env.example**: Template for all tool configurations
- **automagik_tools/cli.py**: Add your tool's config class here
- **tests/conftest.py**: Shared test fixtures and mocks

### Testing Requirements

- All new tools must have MCP protocol compliance tests
- Minimum 30% code coverage
- Use pytest fixtures for common test setup
- Mock external dependencies (see `conftest.py` for examples)
- Test categories: unit (fast), integration, mcp (protocol)

## Future Enhancements (Planned)

### Developer Experience
1. **Tool Generator CLI**: `automagik-tools create-tool --name my-tool --type rest-api`
2. **Base Classes**: Reusable patterns for common tool types
3. **Hot Reload**: Development mode with auto-reload
4. **Tool Validator**: Check MCP compliance before deployment

### Infrastructure
1. **Tool Registry**: Central registry for discovering tools
2. **Dependency Management**: Handle tool interdependencies
3. **Performance Monitoring**: Built-in metrics and tracing
4. **Rate Limiting**: Configurable limits per tool

### Community
1. **Tool Marketplace**: Browse and install community tools
2. **Documentation Site**: Interactive tool explorer
3. **Discord Community**: Support and collaboration
4. **Tool Templates**: Quickstart templates for common integrations

## Recent Updates

### Dynamic OpenAPI Support (NEW!)
- Added `openapi` command for direct OpenAPI deployment
- No pre-generation needed: `uvx automagik-tools openapi --openapi-url https://api.example.com/openapi.json`
- Supports authentication with `--api-key` and custom base URLs with `--base-url`
- Works with all transports (stdio, SSE, HTTP)
- Uses FastMCP's native `from_openapi()` support

### Makefile Modernization (November 2025)

**Removed Commands:**
- `make tool URL=... NAME=...` - REMOVED (referenced deleted OpenAPI code generation scripts)
  - **Migration**: Use `uvx automagik-tools openapi <URL>` for dynamic OpenAPI serving
  - **Alternative**: Use `make openapi-serve URL=<url> [API_KEY=<key>]` for convenience wrapper
  - **Background**: Script `scripts/create_tool_from_openapi_v2.py` was deleted ~5 months ago (commit 071a0f8) along with 3,532+ lines of static code generation

**Valid Transport Values:**
- ✅ Correct: `stdio`, `sse`, `http`
- ❌ Invalid: `streamable-http` (old name, no longer supported)

**Architecture Notes:**
The project has fully migrated from "raw Python" execution to modern tooling:
- All Python execution uses `uv`: `$(UV) run automagik-tools <command>`
- Process management via PM2: `pm2 start ecosystem.config.cjs`
- Dynamic OpenAPI via FastMCP: No code generation needed
- Generic tool discovery: `make serve TOOL=name` works for any tool
- CLI-first design: Most commands are thin wrappers around `automagik-tools` CLI

**Shell Scripts:**
Shell scripts in `scripts/` provide convenience wrappers with presets:
- `scripts/deploy_http_dev.sh` - HTTP server deployment (dev, network, evolution, genie presets)
- `scripts/install.sh` - System-level installation
- `scripts/deploy.sh` - Production deployment
- `scripts/smoke_test.sh` - Integration testing

These are kept for complex orchestration that would be unwieldy in Makefile targets.

**Previous Updates:**
- Removed `serve-evolution` command (tool-specific, replaced by generic `serve` command)
- Removed `test-working` command (was only testing 2 specific files)
- Removed `fastmcp-*` commands (dead code - duplicated existing functionality)
- Added `watch` command to help system (was missing from help but existed)
- Kept `publish-test` command (uploads to TestPyPI for testing releases)

## Design Principles

1. **Simplicity First**: Adding a tool should be as simple as possible
2. **Convention over Configuration**: Sensible defaults with override capability
3. **Composability**: Tools should work well together
4. **Reliability**: Proper error handling and recovery
5. **Security**: Safe by default, no credential leaks
6. **Performance**: Efficient resource usage, async throughout

## Recent Planning Sessions

### Automagik Workflows Tool Development (Latest)
**Planning Complete**: Comprehensive analysis and design for automagik_workflows tool variant
- **Analyzed**: Claude workflow endpoints from Automagik agents API
- **Designed**: Humanized function interface to replace raw API calls  
- **Architecture**: Self-contained tool following automagik-tools patterns
- **Next Workflow**: BUILDER - Ready for implementation phase
- **Priority**: High - Tool provides intuitive workflow orchestration
- **Linear Project**: 769dbd16-e8b8-44d0-a7d8-dc80e1a1a334

## Memories

- Always use uv to run python or pytest, and uvx for testing the application
- USE UVUSE UV ALWAYS
- gpt 4.1 and gpt-4.1-nano are the default models of this project
- **Workflow Continuity**: Use BUILDER workflow next for automagik_workflows implementation