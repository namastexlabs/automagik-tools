# 🛠️ Tool Creation Guide

This comprehensive guide walks you through creating MCP tools for AutoMagik Tools.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Tool Anatomy](#tool-anatomy)
3. [Step-by-Step Tutorial](#step-by-step-tutorial)
4. [Advanced Features](#advanced-features)
5. [Best Practices](#best-practices)
6. [Publishing Your Tool](#publishing-your-tool)

## Quick Start

### Generate from Template

```bash
# Interactive tool creation
make new-tool

# From OpenAPI specification
make tool URL=https://api.example.com/openapi.json
```

### Manual Creation

```bash
# Create tool directory
mkdir -p automagik_tools/tools/my_tool

# Create files
touch automagik_tools/tools/my_tool/__init__.py
touch automagik_tools/tools/my_tool/config.py
touch tests/tools/test_my_tool.py
```

## Tool Anatomy

Every AutoMagik tool consists of:

```
automagik_tools/tools/my_tool/
├── __init__.py      # Main tool implementation (required)
├── config.py        # Configuration with Pydantic (optional)
├── README.md        # Tool documentation (recommended)
├── utils.py         # Helper functions (optional)
└── __main__.py      # Standalone runner (optional)
```

### Minimal Tool Example

```python
# automagik_tools/tools/my_tool/__init__.py
from fastmcp import FastMCP

# Create the MCP server instance
mcp = FastMCP("my-tool")

@mcp.tool()
async def hello(name: str) -> str:
    """Say hello to someone.
    
    Args:
        name: The person's name
        
    Returns:
        A greeting message
    """
    return f"Hello, {name}!"

# This is required for tool discovery
__all__ = ["mcp"]
```

## Step-by-Step Tutorial

Let's create a real tool - a GitHub integration.

### Step 1: Plan Your Tool

Define what your tool will do:
- List repositories
- Create issues
- Search code
- Get commit history

### Step 2: Create Configuration

```python
# automagik_tools/tools/github/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class GitHubConfig(BaseSettings):
    """GitHub tool configuration."""
    
    github_token: str
    github_api_url: str = "https://api.github.com"
    timeout: int = 30
    max_retries: int = 3
    
    class Config:
        env_prefix = "GITHUB_"
        env_file = ".env"
```

### Step 3: Implement Core Functionality

```python
# automagik_tools/tools/github/__init__.py
import httpx
from fastmcp import FastMCP
from typing import Optional, List, Dict, Any
from .config import GitHubConfig

# Initialize
mcp = FastMCP("github")
config = GitHubConfig()

# Create HTTP client with auth
def get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=config.github_api_url,
        headers={
            "Authorization": f"Bearer {config.github_token}",
            "Accept": "application/vnd.github.v3+json"
        },
        timeout=config.timeout
    )

@mcp.tool()
async def list_repos(
    user: Optional[str] = None,
    org: Optional[str] = None,
    sort: str = "updated",
    limit: int = 10
) -> List[Dict[str, Any]]:
    """List GitHub repositories.
    
    Args:
        user: Username (defaults to authenticated user)
        org: Organization name (takes precedence over user)
        sort: Sort by: created, updated, pushed, full_name
        limit: Maximum number of repositories to return
        
    Returns:
        List of repository information
    """
    async with get_client() as client:
        if org:
            url = f"/orgs/{org}/repos"
        elif user:
            url = f"/users/{user}/repos"
        else:
            url = "/user/repos"
            
        response = await client.get(
            url,
            params={"sort": sort, "per_page": limit}
        )
        response.raise_for_status()
        
        repos = response.json()
        
        # Return simplified data
        return [
            {
                "name": repo["name"],
                "full_name": repo["full_name"],
                "description": repo["description"],
                "url": repo["html_url"],
                "stars": repo["stargazers_count"],
                "language": repo["language"],
                "updated": repo["updated_at"]
            }
            for repo in repos
        ]

@mcp.tool()
async def create_issue(
    repo: str,
    title: str,
    body: Optional[str] = None,
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create a GitHub issue.
    
    Args:
        repo: Repository in format 'owner/repo'
        title: Issue title
        body: Issue description (Markdown supported)
        labels: List of label names
        assignees: List of usernames to assign
        
    Returns:
        Created issue information
    """
    async with get_client() as client:
        data = {
            "title": title,
            "body": body or "",
        }
        
        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees
            
        response = await client.post(
            f"/repos/{repo}/issues",
            json=data
        )
        response.raise_for_status()
        
        issue = response.json()
        
        return {
            "number": issue["number"],
            "title": issue["title"],
            "url": issue["html_url"],
            "state": issue["state"],
            "created_at": issue["created_at"]
        }

@mcp.tool()
async def search_code(
    query: str,
    repo: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Search for code on GitHub.
    
    Args:
        query: Search query
        repo: Limit to specific repo (owner/repo)
        language: Programming language filter
        limit: Maximum results
        
    Returns:
        List of matching code snippets
    """
    search_query = query
    if repo:
        search_query += f" repo:{repo}"
    if language:
        search_query += f" language:{language}"
        
    async with get_client() as client:
        response = await client.get(
            "/search/code",
            params={"q": search_query, "per_page": limit}
        )
        response.raise_for_status()
        
        results = response.json()
        
        return [
            {
                "name": item["name"],
                "path": item["path"],
                "repository": item["repository"]["full_name"],
                "url": item["html_url"],
                "score": item["score"]
            }
            for item in results["items"]
        ]

# Export for discovery
__all__ = ["mcp"]
```

### Step 4: Add Error Handling

```python
from fastmcp.exceptions import ToolError
import logging

logger = logging.getLogger(__name__)

@mcp.tool()
async def safe_list_repos(**kwargs) -> List[Dict[str, Any]]:
    """List repos with proper error handling."""
    try:
        return await list_repos(**kwargs)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise ToolError(
                "Authentication failed. Check your GITHUB_TOKEN",
                error_code="AUTH_FAILED"
            )
        elif e.response.status_code == 403:
            raise ToolError(
                "Rate limit exceeded. Try again later",
                error_code="RATE_LIMITED"
            )
        else:
            raise ToolError(
                f"GitHub API error: {e.response.status_code}",
                error_code="API_ERROR"
            )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise ToolError(
            "An unexpected error occurred",
            error_code="INTERNAL_ERROR"
        )
```

### Step 5: Write Tests

```python
# tests/tools/test_github.py
import pytest
from unittest.mock import patch, AsyncMock
from automagik_tools.tools.github import mcp

@pytest.mark.asyncio
async def test_list_repos():
    """Test repository listing."""
    mock_response = AsyncMock()
    mock_response.json.return_value = [
        {
            "name": "test-repo",
            "full_name": "user/test-repo",
            "description": "Test repository",
            "html_url": "https://github.com/user/test-repo",
            "stargazers_count": 42,
            "language": "Python",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
    mock_response.raise_for_status = AsyncMock()
    
    with patch('httpx.AsyncClient.get', return_value=mock_response):
        result = await mcp.tools["list_repos"].fn(user="testuser", limit=1)
        
        assert len(result) == 1
        assert result[0]["name"] == "test-repo"
        assert result[0]["stars"] == 42

@pytest.mark.asyncio
async def test_create_issue():
    """Test issue creation."""
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "number": 1,
        "title": "Test Issue",
        "html_url": "https://github.com/user/repo/issues/1",
        "state": "open",
        "created_at": "2024-01-01T00:00:00Z"
    }
    mock_response.raise_for_status = AsyncMock()
    
    with patch('httpx.AsyncClient.post', return_value=mock_response):
        result = await mcp.tools["create_issue"].fn(
            repo="user/repo",
            title="Test Issue",
            body="This is a test"
        )
        
        assert result["number"] == 1
        assert result["title"] == "Test Issue"

@pytest.mark.asyncio
async def test_auth_error():
    """Test authentication error handling."""
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401 Unauthorized",
        request=None,
        response=mock_response
    )
    
    with patch('httpx.AsyncClient.get', return_value=mock_response):
        with pytest.raises(ToolError) as exc_info:
            await mcp.tools["list_repos"].fn()
            
        assert exc_info.value.error_code == "AUTH_FAILED"
```

### Step 6: Register Your Tool

Add to `pyproject.toml`:

```toml
[project.entry-points."automagik_tools.plugins"]
github = "automagik_tools.tools.github:mcp"
```

### Step 7: Document Your Tool

```markdown
# GitHub Tool

Integrate GitHub functionality into your AI assistant.

## Features

- List repositories
- Create issues
- Search code
- View commit history

## Configuration

Set these environment variables:

```bash
GITHUB_TOKEN=ghp_your_personal_access_token
GITHUB_API_URL=https://api.github.com  # Optional
```

## Usage Examples

### List Repositories
"List my GitHub repositories"
"Show me the most recent repos from organization 'openai'"

### Create Issues
"Create an issue titled 'Bug in login' in repo 'myuser/myapp'"

### Search Code
"Search for 'async def' in Python files in the fastmcp repo"

## API Rate Limits

GitHub API has rate limits:
- Authenticated: 5,000 requests/hour
- Unauthenticated: 60 requests/hour

## Security

- Never commit your GitHub token
- Use fine-grained personal access tokens
- Limit token permissions to required scopes
```

## Advanced Features

### 1. Streaming Responses

For long-running operations:

```python
from typing import AsyncIterator

@mcp.tool()
async def analyze_repo(repo: str) -> AsyncIterator[str]:
    """Analyze a repository with streaming updates."""
    yield "Starting repository analysis...\n"
    
    # Get repo info
    async with get_client() as client:
        response = await client.get(f"/repos/{repo}")
        response.raise_for_status()
        repo_data = response.json()
        
    yield f"Repository: {repo_data['full_name']}\n"
    yield f"Stars: {repo_data['stargazers_count']}\n"
    
    # Analyze more...
    yield "Analysis complete!"
```

### 2. File Handling

For tools that work with files:

```python
import base64
from pathlib import Path

@mcp.tool()
async def upload_file(
    repo: str,
    path: str,
    content: str,
    message: str,
    branch: str = "main",
    base64_encoded: bool = False
) -> Dict[str, Any]:
    """Upload or update a file in a repository."""
    
    if not base64_encoded:
        content = base64.b64encode(content.encode()).decode()
        
    async with get_client() as client:
        # Check if file exists
        try:
            response = await client.get(
                f"/repos/{repo}/contents/{path}",
                params={"ref": branch}
            )
            file_sha = response.json()["sha"]
        except httpx.HTTPStatusError:
            file_sha = None
            
        # Upload/update file
        data = {
            "message": message,
            "content": content,
            "branch": branch
        }
        
        if file_sha:
            data["sha"] = file_sha
            
        response = await client.put(
            f"/repos/{repo}/contents/{path}",
            json=data
        )
        response.raise_for_status()
        
        return response.json()
```

### 3. Caching

For expensive operations:

```python
from functools import lru_cache
from datetime import datetime, timedelta

# In-memory cache
_cache = {}

async def cached_get_repo(repo: str) -> Dict[str, Any]:
    """Get repository with caching."""
    cache_key = f"repo:{repo}"
    
    # Check cache
    if cache_key in _cache:
        cached_data, timestamp = _cache[cache_key]
        if datetime.now() - timestamp < timedelta(minutes=5):
            return cached_data
            
    # Fetch fresh data
    async with get_client() as client:
        response = await client.get(f"/repos/{repo}")
        response.raise_for_status()
        data = response.json()
        
    # Update cache
    _cache[cache_key] = (data, datetime.now())
    
    return data
```

### 4. Pagination

Handle large result sets:

```python
@mcp.tool()
async def list_all_issues(
    repo: str,
    state: str = "open",
    max_results: int = 100
) -> List[Dict[str, Any]]:
    """List all issues with pagination."""
    all_issues = []
    page = 1
    per_page = 30
    
    async with get_client() as client:
        while len(all_issues) < max_results:
            response = await client.get(
                f"/repos/{repo}/issues",
                params={
                    "state": state,
                    "page": page,
                    "per_page": per_page
                }
            )
            response.raise_for_status()
            
            issues = response.json()
            if not issues:
                break
                
            all_issues.extend(issues)
            page += 1
            
            # Check if we have all results
            if len(issues) < per_page:
                break
                
    return all_issues[:max_results]
```

### 5. Webhooks and Events

For real-time updates:

```python
@mcp.tool()
async def setup_webhook(
    repo: str,
    url: str,
    events: List[str] = ["push", "pull_request"]
) -> Dict[str, Any]:
    """Set up a webhook for repository events."""
    async with get_client() as client:
        response = await client.post(
            f"/repos/{repo}/hooks",
            json={
                "name": "web",
                "active": True,
                "events": events,
                "config": {
                    "url": url,
                    "content_type": "json"
                }
            }
        )
        response.raise_for_status()
        
        return response.json()
```

## Best Practices

### 1. Security

```python
# Never log sensitive data
logger.info(f"Connecting to GitHub")  # Good
logger.info(f"Token: {token}")  # Bad!

# Validate inputs
@mcp.tool()
async def safe_create_file(repo: str, path: str, content: str):
    # Prevent path traversal
    if ".." in path or path.startswith("/"):
        raise ToolError("Invalid file path", error_code="INVALID_PATH")
        
    # Limit file size
    if len(content) > 1_000_000:  # 1MB
        raise ToolError("File too large", error_code="FILE_TOO_LARGE")
```

### 2. Performance

```python
# Use connection pooling
_client = None

async def get_shared_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=config.github_api_url,
            headers={"Authorization": f"Bearer {config.github_token}"}
        )
    return _client

# Clean up on shutdown
@mcp.server.lifespan
async def lifespan():
    yield
    if _client:
        await _client.aclose()
```

### 3. User Experience

```python
@mcp.tool()
async def user_friendly_search(
    query: str,
    type: str = "all"  # all, repos, issues, code
) -> Dict[str, List[Any]]:
    """Search GitHub with user-friendly results."""
    results = {}
    
    if type in ["all", "repos"]:
        results["repositories"] = await search_repos(query)
        
    if type in ["all", "issues"]:
        results["issues"] = await search_issues(query)
        
    if type in ["all", "code"]:
        results["code"] = await search_code(query)
        
    # Format for readability
    return {
        "query": query,
        "total_results": sum(len(v) for v in results.values()),
        "results": results
    }
```

## Publishing Your Tool

### 1. Validate Your Tool

```bash
# Run validation
make validate-tool TOOL=github

# Should pass:
# ✓ Tool discovery
# ✓ Parameter validation  
# ✓ Error handling
# ✓ Documentation
# ✓ Async execution
```

### 2. Test Thoroughly

```bash
# Unit tests
make test-tool TOOL=github

# Integration test
make serve TOOL=github
# Test with real MCP client
```

### 3. Document Everything

- Clear README.md
- Configuration examples
- Usage examples
- Common issues
- API limitations

### 4. Submit PR

1. Fork the repository
2. Create feature branch: `git checkout -b add-github-tool`
3. Commit changes: `git commit -m "Add GitHub integration tool"`
4. Push to fork: `git push origin add-github-tool`
5. Create Pull Request

### PR Checklist

- [ ] Tool follows FastMCP patterns
- [ ] All tests pass
- [ ] Documentation complete
- [ ] Environment variables documented
- [ ] No hardcoded secrets
- [ ] Error handling implemented
- [ ] Type hints used throughout
- [ ] Follows code style (run `make format`)

## Common Patterns

### API Client Tools

```python
class APITool:
    """Base pattern for API-based tools."""
    
    def __init__(self, config: BaseSettings):
        self.config = config
        self.client = self._create_client()
        
    def _create_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.config.api_url,
            headers=self._get_headers(),
            timeout=self.config.timeout
        )
        
    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "User-Agent": "AutoMagik-Tools/1.0"
        }
```

### Database Tools

```python
from sqlalchemy.ext.asyncio import create_async_engine

class DatabaseTool:
    """Base pattern for database tools."""
    
    def __init__(self, connection_string: str):
        self.engine = create_async_engine(connection_string)
        
    async def execute_query(self, query: str) -> List[Dict]:
        async with self.engine.connect() as conn:
            result = await conn.execute(query)
            return [dict(row) for row in result]
```

### File Processing Tools

```python
import aiofiles

class FileTool:
    """Base pattern for file processing tools."""
    
    async def read_file(self, path: str) -> str:
        async with aiofiles.open(path, 'r') as f:
            return await f.read()
            
    async def write_file(self, path: str, content: str):
        async with aiofiles.open(path, 'w') as f:
            await f.write(content)
```

## Debugging Tips

### 1. Enable Debug Mode

```python
import os
import logging

if os.getenv("DEBUG") == "true":
    logging.basicConfig(level=logging.DEBUG)
    logger.setLevel(logging.DEBUG)
```

### 2. Add Trace Points

```python
@mcp.tool()
async def traced_operation(param: str) -> str:
    logger.debug(f"Operation started: {param}")
    
    try:
        result = await do_something(param)
        logger.debug(f"Operation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Operation failed: {e}", exc_info=True)
        raise
```

### 3. Test Isolation

```python
# Test individual functions
async def test_function():
    from automagik_tools.tools.github import list_repos
    result = await list_repos(user="octocat", limit=5)
    print(result)

# Run it
import asyncio
asyncio.run(test_function())
```

## Next Steps

1. **Study existing tools**: Look at `evolution_api` and `automagik_agents`
2. **Read FastMCP docs**: Deep dive into the framework
3. **Join discussions**: Share your tool ideas
4. **Build something awesome**: The community needs your tools!

---

**Ready to build?** Start with `make new-tool` and create something amazing! 🚀