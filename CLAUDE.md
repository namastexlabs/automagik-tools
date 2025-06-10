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
- Added `--openapi-url` flag to `serve` command for direct OpenAPI deployment
- No pre-generation needed: `uvx automagik-tools serve --openapi-url https://api.example.com/openapi.json`
- Supports authentication with `--api-key` and custom base URLs with `--base-url`
- Works with all transports (stdio, SSE, HTTP)
- Uses FastMCP's native `from_openapi()` support

### Makefile Updates
- Removed `serve-evolution` command (tool-specific, replaced by generic `serve` command)
- Removed `test-working` command (was only testing 2 specific files)
- Removed `fastmcp-*` commands (dead code - duplicated existing functionality)
- Added generic `serve` command: `make serve TOOL=toolname TRANSPORT=stdio|sse|http`
- Added `watch` command to help system (was missing from help but existed)
- Kept `publish-test` command (uploads to TestPyPI for testing releases)
- Updated help system, examples, and documentation references

## Design Principles

1. **Simplicity First**: Adding a tool should be as simple as possible
2. **Convention over Configuration**: Sensible defaults with override capability
3. **Composability**: Tools should work well together
4. **Reliability**: Proper error handling and recovery
5. **Security**: Safe by default, no credential leaks
6. **Performance**: Efficient resource usage, async throughout

## Memories

- Always use uv to run python or pytest, and uvx for testing the application
- USE UVUSE UV ALWAYS
- gpt 4.1 and gpt-4.1-nano are the default models of this project