# Analysis: Wait Utility MCP Tool

## 📋 Overview
- **Name**: wait
- **Type**: utility  
- **Complexity**: low
- **Estimated Time**: 1-2 hours
- **Priority**: medium
- **Risk Level**: minimal

## 🎯 Requirements

### Functional Requirements
- **wait_seconds(duration: float)** - Basic time delay with second precision
- **wait_minutes(duration: float)** - Minute-based delays (converted to seconds internally)
- **wait_until_timestamp(timestamp: str)** - Wait until specific ISO timestamp
- **wait_with_progress(duration: float, interval: float = 1.0)** - Wait with progress updates

### Technical Requirements
- **Authentication**: None required (utility tool)
- **API Version**: N/A (no external API)
- **Rate Limits**: None (internal async delays)
- **Dependencies**: Built-in Python only (asyncio, datetime, time)
- **Configuration**: Max duration limits, default progress intervals
- **Async Support**: Full async/await throughout
- **Cancellation**: Support AsyncCancelledError handling
- **Validation**: Duration limits, timestamp parsing, progress intervals

## 🔍 Similar Tools Analysis

### automagik_workflows (Primary Pattern)
- **Pattern**: Simple FastMCP server with 4 core functions
- **Structure**: `__init__.py`, `config.py`, `__main__.py` 
- **Config**: Pydantic BaseSettings with `model_config` and `Field(alias=...)`
- **Functions**: Clear `@mcp.tool()` decorations with detailed docstrings
- **Error Handling**: Try/catch with Context logging integration
- **Strengths**: Clean, minimal, follows all automagik-tools patterns
- **Reuse Target**: >90% structural similarity

### Configuration Pattern (From automagik_workflows)
```python
class WaitConfig(BaseSettings):
    max_duration: int = Field(
        default=3600,  # 1 hour max
        description="Maximum wait duration in seconds",
        alias="WAIT_MAX_DURATION",
    )
    
    default_progress_interval: float = Field(
        default=1.0,
        description="Default progress reporting interval",
        alias="WAIT_DEFAULT_PROGRESS_INTERVAL",
    )
    
    model_config = {
        "env_prefix": "WAIT_",
        "env_file": ".env",
        "env_file_encoding": "utf-8", 
        "case_sensitive": False,
        "extra": "ignore",
    }
```

## 📁 Implementation Plan

### File Structure
```
automagik_tools/tools/wait/
├── __init__.py       # FastMCP server with get_metadata(), get_config_class(), create_server()
├── __main__.py       # CLI entry point with transport support  
├── config.py         # Pydantic settings with model_config
└── README.md         # Tool documentation (optional)

tests/tools/
├── test_wait.py              # Unit tests with mocked asyncio.sleep
├── test_wait_mcp.py         # MCP protocol compliance  
└── test_wait_integration.py # Real integration tests
```

### Key Components

#### 1. Server Creation (`__init__.py`)
- FastMCP server setup: `mcp = FastMCP("Wait Utility", instructions="...")`
- Global config instance management
- 4 tool functions with `@mcp.tool()` decorators
- Required functions: `get_metadata()`, `get_config_class()`, `create_server()`
- Context integration for progress reporting

#### 2. Configuration (`config.py`)  
- Environment variables with `WAIT_` prefix
- Duration limits and validation
- Progress interval settings
- Pydantic v2 settings with proper `model_config`

#### 3. CLI Integration
- Register in `automagik_tools/cli.py` config classes
- Add to `.env.example` with documentation
- Auto-discovery via tools directory (no manual entry points needed)

## 🧪 Testing Strategy

### Unit Tests (Fast - Mocked)
- Mock `asyncio.sleep()` for instant test execution
- Test all function signatures and parameter validation
- Test configuration loading and validation
- Test error conditions (negative durations, invalid timestamps)
- Test cancellation scenarios with `AsyncCancelledError`

### MCP Protocol Tests
- Verify tool registration and function discovery
- Test function signatures match specifications
- Validate metadata export and config class export
- Ensure Hub mounting compatibility

### Integration Tests (Real timing)
- Use very short durations (0.1 seconds) for timing accuracy
- Test real progress reporting with Context
- Validate actual wait behavior end-to-end
- Test cancellation timing

### Coverage Target
- **Minimum**: 30% (automagik-tools standard)
- **Target**: 60% (simple utility should achieve high coverage)

## ⚠️ Risk Assessment

### Complexity Risks
- **None** - Simple utility with straightforward async delays

### Dependency Risks  
- **None** - Uses only built-in Python asyncio, datetime, time modules

### API Limitations
- **None** - No external APIs, no rate limits

### Testing Challenges
- **Timing sensitivity** - Use mocks for unit tests, short waits for integration
- **Progress reporting** - Test Context integration carefully

## 🎯 Success Criteria
- [ ] All 4 functions implemented and working
- [ ] Configuration system working with environment variables
- [ ] Tests passing with >30% coverage
- [ ] Tool serves standalone: `uvx automagik-tools serve wait`
- [ ] Hub integration successful: `uvx automagik-tools serve-all`
- [ ] Progress reporting working with Context
- [ ] Proper async cancellation support
- [ ] Documentation complete in `.env.example`

## 📊 Implementation Specifications

### Function Signatures
```python
@mcp.tool()
async def wait_seconds(duration: float, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """Wait for specified number of seconds"""

@mcp.tool() 
async def wait_minutes(duration: float, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """Wait for specified number of minutes"""

@mcp.tool()
async def wait_until_timestamp(timestamp: str, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """Wait until specific ISO 8601 timestamp"""

@mcp.tool()
async def wait_with_progress(
    duration: float, 
    interval: float = 1.0, 
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """Wait with progress updates at specified intervals"""
```

### Configuration Integration
- Add `from automagik_tools.tools.wait.config import WaitConfig` to `automagik_tools/cli.py`
- Add `WaitConfig` to config classes dictionary
- Add environment variables to `.env.example`

### Environment Variables
```bash
# Wait Utility Configuration
WAIT_MAX_DURATION=3600      # Maximum wait duration (seconds)
WAIT_DEFAULT_PROGRESS_INTERVAL=1.0  # Default progress interval
```

## 🚀 Handoff to BUILDER

This analysis provides BUILDER with:
- ✅ **Clear Requirements** - 4 functions with specific signatures
- ✅ **Proven Pattern** - automagik_workflows template to follow exactly
- ✅ **File Structure** - Exact files needed and their contents
- ✅ **Configuration** - Environment variables and Pydantic setup
- ✅ **Testing Plan** - Comprehensive test coverage strategy
- ✅ **Integration Steps** - CLI registration and documentation updates

**Pattern Reuse**: 90% structural similarity to automagik_workflows
**Implementation Confidence**: Very High (simple utility, proven patterns)
**Risk Level**: Minimal (no external dependencies, well-understood requirements)

Ready for BUILDER implementation phase! 🎯