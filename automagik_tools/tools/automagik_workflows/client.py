"""
HTTP client for Claude Code workflow API interactions
"""

import asyncio
from typing import Dict, Any, List, Optional
import httpx
from .config import AutomagikWorkflowsConfig


class ClaudeCodeClient:
    """Async HTTP client for Claude Code workflow API"""

    def __init__(self, config: AutomagikWorkflowsConfig):
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.timeout = httpx.Timeout(config.timeout)

    async def start_workflow(
        self, workflow_name: str, request_data: Dict[str, Any], persistent: bool = True
    ) -> Dict[str, Any]:
        """Start a Claude Code workflow execution"""
        endpoint = f"/api/v1/workflows/claude-code/run/{workflow_name}"
        params = {"persistent": persistent}
        return await self._make_request("POST", endpoint, json=request_data, params=params)

    async def get_workflow_status(
        self, run_id: str, debug: bool = False, detailed: bool = False
    ) -> Dict[str, Any]:
        """Get the status of a specific workflow run"""
        endpoint = f"/api/v1/workflows/claude-code/run/{run_id}/status"
        params = {}
        if debug:
            params["debug"] = debug
        if detailed:
            params["detailed"] = detailed
        return await self._make_request("GET", endpoint, params=params if params else None)

    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all available Claude Code workflows"""
        endpoint = "/api/v1/workflows/claude-code/workflows"
        result = await self._make_request("GET", endpoint)
        # Ensure we return a list even if API returns a dict
        if isinstance(result, dict) and "workflows" in result:
            return result["workflows"]
        elif isinstance(result, list):
            return result
        else:
            return []

    async def list_runs(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """List workflow runs with optional filtering and pagination"""
        endpoint = "/api/v1/workflows/claude-code/runs"
        params = filters or {}
        # Ensure page defaults are set if not provided
        if "page" not in params:
            params["page"] = 1
        if "page_size" not in params:
            params["page_size"] = 20
        return await self._make_request("GET", endpoint, params=params)

    async def kill_workflow(self, run_id: str, force: bool = False) -> Dict[str, Any]:
        """Kill a running Claude Code workflow"""
        endpoint = f"/api/v1/workflows/claude-code/run/{run_id}/kill"
        params = {"force": force} if force else None
        return await self._make_request("POST", endpoint, params=params)

    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the Automagik Agents Platform"""
        endpoint = "/api/v1/workflows/claude-code/health"
        return await self._make_request("GET", endpoint)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make an authenticated HTTP request to the Claude Code API"""
        url = f"{self.base_url}{endpoint}"
        headers = {}

        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.config.max_retries + 1):
                try:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=json,
                        params=params,
                        **kwargs,
                    )

                    # Handle different response scenarios
                    if response.status_code == 200:
                        try:
                            return response.json()
                        except ValueError:
                            return {
                                "message": response.text,
                                "status_code": response.status_code,
                            }
                    elif response.status_code == 404:
                        raise ValueError(f"Endpoint not found: {endpoint}")
                    elif response.status_code == 401:
                        raise ValueError("Authentication failed - check your API key")
                    elif response.status_code == 403:
                        raise ValueError("Access forbidden - insufficient permissions")
                    else:
                        response.raise_for_status()

                except httpx.TimeoutException:
                    if attempt == self.config.max_retries:
                        raise TimeoutError(
                            f"Request timeout after {self.config.max_retries} retries"
                        )
                    await asyncio.sleep(2**attempt)  # Exponential backoff

                except httpx.ConnectError:
                    if attempt == self.config.max_retries:
                        raise ConnectionError(f"Failed to connect to {self.base_url}")
                    await asyncio.sleep(2**attempt)

                except httpx.HTTPStatusError as e:
                    if attempt == self.config.max_retries:
                        try:
                            error_detail = e.response.json()
                        except Exception:
                            error_detail = {"message": e.response.text}
                        raise ValueError(
                            f"API error {e.response.status_code}: {error_detail}"
                        )
                    await asyncio.sleep(2**attempt)

        # This should never be reached due to the retry logic
        raise RuntimeError("Unexpected error in request handling")
