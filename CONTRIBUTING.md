# Contributing to AutoMagik Tools

Thank you for your interest in contributing to AutoMagik Tools! We're building the most comprehensive MCP tools collection, and we'd love your help.

## 🚀 Quick Start

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/automagik-tools`
3. Install dev dependencies: `make install`
4. Create a branch: `git checkout -b feature/your-feature-name`
5. Make your changes
6. Test: `make test`
7. Push and create a Pull Request

## 📋 What We're Looking For

### New Tools
- **OpenAPI-based tools**: Find interesting APIs with OpenAPI specs
- **Built-in tools**: Create new MCP tools in `automagik_tools/tools/`
- **Tool improvements**: Enhance existing tools with new features

### Code Quality
- **Tests**: Add tests for new features (aim for >80% coverage)
- **Documentation**: Update docs when adding features
- **Type hints**: Use Python type hints throughout
- **Async first**: All MCP operations should be async

## 🛠️ Development Process

### 1. Setting Up

```bash
# Clone and install
git clone https://github.com/namastexlabs/automagik-tools
cd automagik-tools
make install

# Run tests to verify setup
make test
```

### 2. Creating a New Tool

```bash
# Use the tool generator
make new-tool

# Or create manually in automagik_tools/tools/your_tool/
```

### 3. Testing

```bash
# Run all tests
make test

# Run specific tests
pytest tests/test_your_feature.py -v

# Check coverage
make test-coverage
```

### 4. Code Style

```bash
# Format code
make format

# Check linting
make lint
```

## 📝 Pull Request Guidelines

### PR Title Format
- `feat: Add new Discord tool`
- `fix: Handle rate limiting in Evolution API`
- `docs: Update OpenAPI examples`
- `test: Add tests for Spark feature`

### PR Description
Include:
- What changes you made
- Why these changes are needed
- How to test the changes
- Any breaking changes

### Checklist
- [ ] Tests pass (`make test`)
- [ ] Code is formatted (`make format`)
- [ ] Documentation updated (if needed)
- [ ] Added tests for new features
- [ ] PR title follows format

## 🧪 Testing Guidelines

### Unit Tests
```python
async def test_my_feature():
    """Test description."""
    # Arrange
    tool = MyTool()
    
    # Act
    result = await tool.process("input")
    
    # Assert
    assert result.status == "success"
```

### MCP Protocol Tests
```python
async def test_mcp_compliance():
    """Ensure tool follows MCP protocol."""
    await validate_mcp_compliance(my_tool)
```

## 📚 Documentation

When adding features, update:
- `README.md` - If adding major features
- `docs/` - API references and guides
- Tool-specific README in `automagik_tools/tools/YOUR_TOOL/`
- Docstrings in your code

## 🤝 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Assume good intentions

## 💬 Getting Help

- **Discord**: [Join our community](https://discord.gg/automagik)
- **Issues**: Check existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions

## 🎯 Priority Areas

Currently looking for contributions in:
1. **New OpenAPI integrations** - Find interesting APIs
2. **Spark improvements** - Enhance agent orchestration
3. **Documentation** - Improve examples and guides
4. **Test coverage** - Add more comprehensive tests
5. **Performance** - Optimize for large-scale usage

## 🏆 Recognition

Contributors will be:
- Listed in our README
- Mentioned in release notes
- Invited to our contributors Discord channel

---

**Thank you for contributing to AutoMagik Tools!** 🪄

Every contribution, no matter how small, helps make AI more accessible to everyone.