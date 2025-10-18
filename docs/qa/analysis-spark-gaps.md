# Analysis: Spark MCP Tool - Feature Gaps

## Overview
- **Name**: spark (enhancement)
- **Type**: Enhancement to existing tool
- **Complexity**: Low-Medium
- **Estimated Time**: 2-3 hours
- **Status**: Existing tool with 68% API coverage

## Executive Summary

The Spark MCP tool is **MISSING 8 key tools** (32% of API functionality). The good news: **all client methods already exist** in `client.py` - they just need to be exposed as MCP tools in `__init__.py`.

### Coverage Analysis
| Feature Category | API Endpoints | MCP Tools | Coverage % | Gap |
|-----------------|---------------|-----------|------------|-----|
| Health | 1 | 1 | 100% | ✅ Complete |
| Workflows | 6 | 5 | 83% | ⚠️ Minor |
| Remote Workflows | 3 | 2 | 67% | ⚠️ Moderate |
| Tasks | 3 | 2 | 67% | ⚠️ Moderate |
| Schedules | 7 | 5 | 71% | ⚠️ Moderate |
| Sources | 5 | 2 | 40% | ❌ Major |
| **TOTAL** | **25** | **17** | **68%** | **32% Missing** |

## Missing Features Detail

### 1. Remote Workflow Operations ⚠️

**Missing:**
- `get_remote_workflow(flow_id, source_url)` - Get detailed remote workflow info

**Impact:** Cannot inspect remote workflows before syncing them.

**Client Status:** ✅ Method exists at `client.py:115-122`
```python
async def get_remote_workflow(
    self, workflow_id: str, source_url: str
) -> Dict[str, Any]:
```

**Fix Required:** Add MCP tool wrapper in `__init__.py`

---

### 2. Task Management ⚠️

**Missing:**
- `delete_task(task_id)` - Delete task execution

**Impact:** Cannot clean up failed or old task executions.

**Client Status:** ✅ Method exists at `client.py:158-160`
```python
async def delete_task(self, task_id: str) -> Dict[str, Any]:
```

**Fix Required:** Add MCP tool wrapper in `__init__.py`

---

### 3. Schedule Management ⚠️

**Missing:**
- `get_schedule(schedule_id)` - Get specific schedule details
- `update_schedule(schedule_id, ...)` - Modify existing schedule

**Impact:**
- Cannot inspect individual schedules
- Cannot modify schedules without deleting and recreating

**Client Status:** ✅ Both methods exist
```python
# client.py:189-191
async def get_schedule(self, schedule_id: str) -> Dict[str, Any]:

# client.py:193-210
async def update_schedule(
    self, schedule_id: str, schedule_type, schedule_expr, input_value
) -> Dict[str, Any]:
```

**Fix Required:** Add MCP tool wrappers in `__init__.py`

---

### 4. Source Management ❌ CRITICAL

**Missing:**
- `get_source(source_id)` - Get specific source details
- `update_source(source_id, ...)` - Modify existing source

**Impact:**
- Cannot inspect source configuration
- Cannot update source URLs or API keys without deletion
- **40% of source management functionality missing**

**Client Status:** ✅ Both methods exist
```python
# client.py:242-244
async def get_source(self, source_id: str) -> Dict[str, Any]:

# client.py:246-261
async def update_source(
    self, source_id: str, name, url, api_key
) -> Dict[str, Any]:
```

**Fix Required:** Add MCP tool wrappers in `__init__.py`

---

### 5. Parameter Gaps

**Issues Found:**

1. **sync_workflow** - Missing `source_url` parameter
   - API requires: `source_url` (query param)
   - MCP has: Only `workflow_id`, `input_component`, `output_component`
   - **Current implementation will fail** - API requires source_url

2. **list_remote_workflows** - Missing `simplified` parameter
   - API supports: `simplified` boolean (default: true)
   - MCP has: Only `source_url`
   - Impact: Cannot get full workflow details when listing

3. **list_sources** - Missing `status` filter
   - API supports: `status` filter (active/inactive)
   - MCP has: No parameters
   - Impact: Cannot filter sources by status

## Requirements

### Functional Requirements
1. ✅ Expose all existing client methods as MCP tools
2. ✅ Add missing parameters to existing tools
3. ✅ Maintain consistent error handling
4. ✅ Follow existing documentation patterns

### Technical Requirements
- **Authentication**: X-API-Key header (already implemented)
- **API Version**: 0.3.7
- **Rate Limits**: None documented
- **Dependencies**: No new dependencies needed

## Similar Tools Analysis

### Reference: Evolution Tool (`automagik_tools/tools/evolution/`)
- **Pattern**: Same structure - client.py + __init__.py wrapper
- **Approach**: All client methods exposed as @mcp.tool() decorated functions
- **Error Handling**: Try/catch with ctx.error() logging
- **Documentation**: Comprehensive docstrings with examples

**Key Pattern to Follow:**
```python
@mcp.tool()
async def tool_name(param: str, ctx: Optional[Context] = None) -> str:
    """
    Description.

    Args:
        param: Description

    Returns description.
    """
    global client
    if not client:
        raise ValueError("Tool not configured")

    try:
        result = await client.method_name(param)
        return json.dumps(result, indent=2)
    except Exception as e:
        if ctx:
            ctx.error(f"Failed: {str(e)}")
        raise
```

## Implementation Plan

### Phase 1: Add Missing Tools (1 hour)

**File:** `automagik_tools/tools/spark/__init__.py`

Add 6 new MCP tools:

1. **get_remote_workflow**
```python
@mcp.tool()
async def get_remote_workflow(
    workflow_id: str,
    source_url: str,
    ctx: Optional[Context] = None
) -> str:
    """Get detailed information about a remote workflow."""
```

2. **delete_task**
```python
@mcp.tool()
async def delete_task(
    task_id: str,
    ctx: Optional[Context] = None
) -> str:
    """Delete a task execution."""
```

3. **get_schedule**
```python
@mcp.tool()
async def get_schedule(
    schedule_id: str,
    ctx: Optional[Context] = None
) -> str:
    """Get specific schedule details."""
```

4. **update_schedule**
```python
@mcp.tool()
async def update_schedule(
    schedule_id: str,
    schedule_type: Optional[str] = None,
    schedule_expr: Optional[str] = None,
    input_value: Optional[str] = None,
    ctx: Optional[Context] = None
) -> str:
    """Update an existing schedule."""
```

5. **get_source**
```python
@mcp.tool()
async def get_source(
    source_id: str,
    ctx: Optional[Context] = None
) -> str:
    """Get specific workflow source details."""
```

6. **update_source**
```python
@mcp.tool()
async def update_source(
    source_id: str,
    name: Optional[str] = None,
    url: Optional[str] = None,
    api_key: Optional[str] = None,
    ctx: Optional[Context] = None
) -> str:
    """Update a workflow source configuration."""
```

### Phase 2: Fix Parameter Gaps (0.5 hours)

**File:** `automagik_tools/tools/spark/__init__.py` + `client.py`

1. **Fix sync_workflow** - Add source_url parameter
```python
@mcp.tool()
async def sync_workflow(
    workflow_id: str,
    source_url: str,  # ADD THIS
    input_component: str = "input",
    output_component: str = "output",
    ctx: Optional[Context] = None,
) -> str:
```

Update client call to pass source_url as query param.

2. **Fix list_remote_workflows** - Add simplified parameter
```python
@mcp.tool()
async def list_remote_workflows(
    source_url: str,
    simplified: bool = True,  # ADD THIS
    ctx: Optional[Context] = None
) -> str:
```

3. **Fix list_sources** - Add status filter
```python
@mcp.tool()
async def list_sources(
    status: Optional[str] = None,  # ADD THIS
    ctx: Optional[Context] = None
) -> str:
```

### Phase 3: Update Client Methods (0.5 hours)

**File:** `automagik_tools/tools/spark/client.py`

1. Update `sync_workflow` to accept and pass `source_url`:
```python
async def sync_workflow(
    self,
    workflow_id: str,
    source_url: str,  # ADD THIS
    input_component: str = "input",
    output_component: str = "output",
) -> Dict[str, Any]:
    params = {
        "source_url": source_url,  # ADD THIS
        "input_component": input_component,
        "output_component": output_component,
    }
```

2. Update `list_remote_workflows` to accept `simplified`:
```python
async def list_remote_workflows(
    self, source_url: str, simplified: bool = True  # ADD THIS
) -> List[Dict[str, Any]]:
    params = {
        "source_url": source_url,
        "simplified": simplified  # ADD THIS
    }
```

3. Update `list_sources` to accept `status` filter:
```python
async def list_sources(
    self, status: Optional[str] = None  # ADD THIS
) -> List[Dict[str, Any]]:
    params = {}
    if status:  # ADD THIS
        params["status"] = status
    return await self.request("GET", "/api/v1/sources/", params=params)
```

### Phase 4: Testing (1 hour)

**File:** `tests/tools/test_spark.py` (create if doesn't exist)

Add tests for new tools:
```python
async def test_get_remote_workflow(spark_client):
    """Test getting remote workflow details"""
    # Mock the client response
    # Call the tool
    # Assert correct API call

async def test_delete_task(spark_client):
    """Test task deletion"""
    # ...

async def test_schedule_operations(spark_client):
    """Test get/update schedule"""
    # ...

async def test_source_operations(spark_client):
    """Test get/update source"""
    # ...

async def test_parameter_fixes(spark_client):
    """Test sync_workflow with source_url"""
    # Test simplified parameter
    # Test status filter
```

## File Structure

No new files needed - only modifications:

```
automagik_tools/tools/spark/
├── __init__.py          # ✏️ ADD 6 new tools + fix 3 existing
├── __main__.py          # ✅ No changes needed
├── config.py            # ✅ No changes needed
├── client.py            # ✏️ Fix 3 method signatures
└── models.py            # ✅ No changes needed

tests/tools/
└── test_spark.py        # ✏️ Add tests for new functionality
```

## Risk Assessment

### Complexity Risks: ✅ LOW
- All client methods already exist and work
- Just need MCP tool wrappers
- Following established patterns

### Dependency Risks: ✅ NONE
- No new dependencies needed
- All required libraries already in use

### API Limitations: ⚠️ MINOR
- `sync_workflow` currently broken due to missing source_url
- This is a bug fix, not a limitation

### Testing Challenges: ✅ LOW
- Can follow existing test patterns
- Mock responses straightforward
- Client methods already tested

## Success Criteria

- [x] Analysis complete
- [ ] All 6 missing tools implemented
- [ ] All 3 parameter gaps fixed
- [ ] Tests passing (maintain >30% coverage)
- [ ] MCP compliance verified
- [ ] Documentation updated
- [ ] Hub integration confirmed

## Time Estimate Breakdown

| Phase | Task | Time |
|-------|------|------|
| 1 | Add 6 new MCP tool wrappers | 1.0h |
| 2 | Fix 3 parameter gaps | 0.5h |
| 3 | Update 3 client methods | 0.5h |
| 4 | Add comprehensive tests | 1.0h |
| **Total** | **Implementation** | **3.0h** |

## Priority Recommendation

**HIGH PRIORITY** - Critical functionality missing:
1. **Source management** - 60% missing, cannot update configs
2. **sync_workflow bug** - Currently broken without source_url
3. **Schedule updates** - Cannot modify without recreate

**Impact:** Users cannot fully manage their Spark workflows via MCP without these features.

## Next Steps for BUILDER

1. Start with Phase 3 (client fixes) - fixes the bug
2. Then Phase 1 (new tools) - adds missing functionality
3. Phase 2 (parameter additions) - completes coverage
4. Finally Phase 4 (testing) - ensures quality

**Estimated completion:** 3 hours of focused development

---

**Analyst:** Claude Code
**Date:** 2025-10-17
**Tool Version:** 1.0.0 (to be 1.1.0)
**API Version:** 0.3.7
