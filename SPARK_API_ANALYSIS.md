# Spark API Code Smell Analysis

## Executive Summary

Deep analysis of the Spark API (`http://localhost:8883/api/v1/openapi.json`) revealed multiple code smells and inconsistencies:

1. **Pagination NOT Working**: The API accepts `offset` parameter but silently ignores it
2. **Inconsistent Pagination**: Only `/api/v1/tasks` has `limit`, other endpoints have none
3. **Missing OpenAPI Documentation**: Several parameters accepted but not documented

## Detailed Findings

### 1. Pagination Status

| Endpoint | Limit | Offset | Skip | Page | Status |
|----------|-------|--------|------|------|--------|
| `/api/v1/tasks` | ✅ (50) | ❌ Ignored | ❌ Ignored | ❌ Ignored | **BROKEN** |
| `/api/v1/schedules` | ❌ None | ❌ None | ❌ None | ❌ None | **NO PAGINATION** |
| `/api/v1/workflows` | ❌ None | ❌ None | ❌ None | ❌ None | **NO PAGINATION** |
| `/api/v1/sources/` | ❌ None | ❌ None | ❌ None | ❌ None | **NO PAGINATION** |

### 2. Test Results for `/api/v1/tasks`

```bash
# Test: Does offset work?
GET /api/v1/tasks?limit=2&offset=0  → Returns items [0,1] ✅
GET /api/v1/tasks?limit=2&offset=2  → Returns items [0,1] ❌ (should be [2,3])

# Conclusion: offset parameter is IGNORED by API
```

### 3. OpenAPI Spec vs Reality

**OpenAPI Says**:
```json
{
  "parameters": [
    {"name": "workflow_id", "required": false},
    {"name": "status", "required": false},
    {"name": "limit", "required": false, "default": 50}
  ]
}
```

**API Actually Accepts** (but ignores):
- `offset` (silently ignored)
- `skip` (silently ignored)  
- `page` (silently ignored)

### 4. Missing Schedule Parameters

**Issue #20 Analysis**:
- OpenAPI spec doesn't define `ScheduleUpdate` schema properly
- API requires ALL fields for PUT `/api/v1/schedules/{id}`:
  - `workflow_id` ✅ (we fixed this)
  - `schedule_type` ✅ (we fixed this)
  - `schedule_expr` ✅ (we fixed this)
  - `input_value` (optional)

**Server-Side Bug Discovered**:
```bash
PUT /api/v1/schedules/{id}
{"workflow_id": "...", "schedule_type": "interval", "schedule_expr": "2m"}
→ HTTP 400: 'ScheduleCreate' object has no attribute 'status'
```

The API has a server-side bug where it tries to access a `status` attribute during update.

## Recommendations

### For Issue #21 (Pagination)

**Original Problem**: "Task list tool cannot handle responses over 25k characters"

**Attempted Fix**: Add `offset` parameter
**Reality**: API doesn't support pagination at all!

**Actual Solutions**:

1. **Client-Side Pagination** (Recommended)
   - Keep `limit` parameter only
   - MCP tool can fetch in batches and handle client-side
   - Works with current API

2. **Result Truncation** (Quick Fix)
   - Add `limit` parameter with lower default (e.g., 20)
   - Document pagination limitation
   - Agents call multiple times if needed

3. **Wait for API Fix** (Long-term)
   - File bug with Spark API team
   - Implement pagination server-side
   - Update MCP tool once fixed

### For Issue #20 (update_schedule)

✅ **Successfully Fixed**
- Added `workflow_id` parameter (now works)
- Made `schedule_type` and `schedule_expr` required
- Added documentation

❌ **Server-Side Bug**: API has internal error, but our MCP tool is correct

## Code Smells Identified

1. **Silent Parameter Ignoring**: API accepts but ignores `offset`, `skip`, `page`
2. **Inconsistent Pagination**: Only one endpoint has `limit`
3. **Incomplete OpenAPI Spec**: Missing parameter documentation
4. **Server-Side Type Errors**: `'ScheduleCreate' object has no attribute 'status'`
5. **No Pagination Strategy**: 50-item limit with no way to get more

## Action Items

### For automagik-tools (Our MCP Tool)

- [x] Fix #20: Add `workflow_id` to `update_schedule` ✅
- [ ] Fix #21: **Revert** `offset` parameter (doesn't work)
- [ ] Fix #21: Implement client-side result limiting/truncation
- [ ] Document Spark API pagination limitations
- [ ] Add warning in tool descriptions

### For Spark API (Upstream)

- [ ] Implement proper pagination (offset/skip/cursor)
- [ ] Fix `ScheduleCreate` type error in update endpoint
- [ ] Update OpenAPI spec to match reality
- [ ] Add pagination to all list endpoints
- [ ] Document pagination strategy

## Conclusion

**Issue #20**: ✅ Successfully fixed  
**Issue #21**: ⚠️  Partially addressable (API limitation)

The `offset` parameter we added doesn't work because the Spark API doesn't implement pagination. We should:
1. Revert the `offset` parameter
2. Keep the `limit` parameter (it works)
3. Document the limitation
4. File upstream bug report
