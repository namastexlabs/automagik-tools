# Architecture Plan: Automagik Tool Enhancement

## 📋 Executive Summary

**Project**: Enhance the automagik MCP tool to align with updated API specifications from `http://localhost:28881/api/v1/openapi.json`

**Scope**: Critical bug fixes, new endpoint integration, and user experience improvements

**Estimated Effort**: 3-4 hours total across workflows

**Priority**: HIGH - Tool currently has broken endpoints and missing functionality

## 🔍 Current State Analysis

### Issues Identified

1. **CRITICAL: Broken Claude-Code Endpoints**
   - Current implementation uses `/api/v1/agent/claude-code/...`
   - API has moved to `/api/v1/workflows/claude-code/...`
   - All 4 Claude-Code functions broken

2. **LIMITED: Basic Agent Parameters**
   - Current `run_agent()` only accepts `message_content`
   - New API supports 20+ parameters for orchestration, media, workspace paths

3. **INCONSISTENT: Return Types**
   - Mix of `str` and `Dict[str, Any]` returns
   - Should consistently return enhanced markdown strings

4. **MISSING: User-Friendly Functions**
   - Technical function names not intuitive
   - Need simple aliases for common operations

## 🎯 Proposed Architecture

### Phase 1: Critical Fixes (HIGH PRIORITY)

#### 1.1 Endpoint Migration
**Files**: `automagik_tools/tools/automagik/__init__.py`

**Changes**:
```python
# OLD (broken)
"/api/v1/agent/claude-code/{workflow_name}/run"

# NEW (working)  
"/api/v1/workflows/claude-code/run/{workflow_name}"
```

**Functions to Fix**:
- `run_claude_code_workflow()` 
- `get_claude_code_run_status()`
- `list_claude_code_workflows()`
- `get_claude_code_health()`

#### 1.2 Return Type Consistency
**Issue**: `get_run_status()` returns `Dict[str, Any]` while others return `str`

**Fix**: Change all API functions to return enhanced markdown strings

### Phase 2: Enhanced Functionality (HIGH PRIORITY)

#### 2.1 Simple User Functions
Add human-readable aliases:

```python
@mcp.tool()
async def chat_agent(agent_name: str, message: str) -> str:
    """Chat with an AI agent - simple and direct"""
    return await run_agent(agent_name, message)

@mcp.tool() 
async def run_workflow(workflow_name: str, task_description: str, **kwargs) -> str:
    """Run a Claude-Code workflow for development tasks"""
    return await run_claude_code_workflow(workflow_name, data={
        "message": task_description,
        **kwargs
    })

@mcp.tool()
async def list_workflows() -> str:
    """Show all available Claude-Code workflows"""
    return await list_claude_code_workflows()

@mcp.tool()
async def check_workflow_progress(run_id: str) -> str:
    """Check progress of a development workflow"""
    return await get_claude_code_run_status(run_id)
```

#### 2.2 Enhanced Agent Parameters
Extend `run_agent()` and `run_agent_async()` to support:

```python
async def run_agent(
    agent_name: str, 
    message_content: str,
    session_id: Optional[str] = None,
    session_name: Optional[str] = None,
    user_id: Optional[str] = None,
    max_turns: Optional[int] = None,
    workspace_paths: Optional[Dict[str, str]] = None,
    orchestration_config: Optional[Dict[str, Any]] = None,
    # ... other new parameters
) -> str:
```

## 🏗️ Implementation Strategy

### Workflow Coordination

**ORCHESTRATOR** → **ANALYZER** → **BUILDER** → **TESTER** → **VALIDATOR**

#### 1. ANALYZER Tasks
- Parse current OpenAPI spec in detail
- Compare with existing implementation line-by-line
- Identify all discrepancies and new features
- Create detailed implementation checklist
- Research patterns from existing tools

#### 2. BUILDER Tasks  
- Fix Claude-Code endpoint URLs (4 functions)
- Add simple user-friendly function aliases (4 functions)
- Enhance run_agent with comprehensive parameters
- Fix return type consistency
- Update all function documentation

#### 3. TESTER Tasks
- Test all endpoint fixes with real API
- Validate new function aliases work correctly
- Test enhanced parameters functionality
- Ensure backward compatibility
- Create regression test suite

#### 4. VALIDATOR Tasks
- Run lint and format checks
- Validate MCP protocol compliance
- Test tool discovery and mounting
- Performance testing
- Security review of new parameters

## 📊 Risk Assessment

### HIGH Risk
- **API Breaking Changes**: New parameters might not be backward compatible
- **Authentication**: Enhanced parameters may require different auth
- **Performance**: More parameters could impact response times

### MEDIUM Risk  
- **Testing Complexity**: More parameters mean more test combinations
- **Documentation**: Need to update examples and guides

### LOW Risk
- **Endpoint URLs**: Simple string changes, low risk
- **Function Aliases**: Additive changes, no breaking impact

## 🎯 Success Criteria

### Functional Requirements
- [ ] All Claude-Code endpoints working with new URLs
- [ ] Simple aliases (chat_agent, run_workflow, etc.) functional
- [ ] Enhanced agent parameters accepted and processed
- [ ] Consistent return types (all strings with AI enhancement)
- [ ] Backward compatibility maintained

### Quality Requirements  
- [ ] All tests passing (>30% coverage maintained)
- [ ] Lint and format checks pass
- [ ] MCP protocol compliance verified
- [ ] Tool discovery working in hub
- [ ] Performance within acceptable bounds

### User Experience
- [ ] Simple functions work intuitively
- [ ] Complex parameters optional with good defaults
- [ ] Error messages helpful and actionable
- [ ] Documentation updated with examples

## 📅 Timeline Estimate

### ANALYZER: 45 minutes
- OpenAPI deep analysis: 20 min
- Pattern research: 15 min  
- Implementation planning: 10 min

### BUILDER: 90 minutes
- Endpoint fixes: 20 min
- Simple functions: 30 min
- Enhanced parameters: 30 min
- Documentation updates: 10 min

### TESTER: 60 minutes
- Fix validation tests: 20 min
- New function tests: 25 min
- Integration testing: 15 min

### VALIDATOR: 45 minutes
- Quality checks: 20 min
- MCP compliance: 15 min
- Performance testing: 10 min

**Total: 4 hours 20 minutes**

## 🚀 Immediate Next Steps

1. **Create Linear Epic** for automagik tool enhancement
2. **Dispatch to ANALYZER** with OpenAPI spec and current tool analysis
3. **Set up Linear tracking** for each workflow phase
4. **Prepare memory context** with existing automagik tool patterns

## 📞 Required Inputs for ANALYZER

```json
{
  "tool_name": "automagik",
  "current_issues": [
    "Claude-Code endpoints broken - wrong URLs",
    "Limited agent parameters - missing orchestration options", 
    "Inconsistent return types",
    "No user-friendly function names"
  ],
  "openapi_url": "http://localhost:28881/api/v1/openapi.json",
  "priority": "high",
  "existing_tool_path": "automagik_tools/tools/automagik/",
  "enhancement_type": "critical_fixes_and_improvements",
  "target_functions": [
    "run_claude_code_workflow", 
    "get_claude_code_run_status",
    "list_claude_code_workflows", 
    "get_claude_code_health",
    "run_agent",
    "run_agent_async"
  ],
  "new_functions_requested": [
    "chat_agent",
    "run_workflow", 
    "list_workflows",
    "check_workflow_progress"
  ]
}
```

## 💡 Long-term Vision

This enhancement positions the automagik tool as:
- **Primary interface** to automagik-agents API
- **User-friendly gateway** for non-technical users  
- **Complete feature coverage** of the API capabilities
- **Reference implementation** for other API tools

---

**APPROVAL REQUIRED**: Please review this architecture plan and approve to proceed with ANALYZER workflow dispatch.