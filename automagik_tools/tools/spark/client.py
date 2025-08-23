"""HTTP client for Spark API"""

from typing import Optional, Dict, Any, List
import httpx
import json
from .config import SparkConfig
from .models import TaskStatus


class SparkClient:
    """HTTP client for interacting with Spark API"""

    def __init__(self, config: SparkConfig):
        self.config = config
        self.headers = {
            "X-API-Key": config.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to Spark API"""
        url = f"{self.config.base_url}{endpoint}"

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=json_data,
                )
                response.raise_for_status()

                # Handle different response types
                if response.headers.get("content-type", "").startswith("application/json"):
                    return response.json()
                else:
                    return {"result": response.text}

            except httpx.HTTPStatusError as e:
                error_detail = e.response.text
                try:
                    error_json = e.response.json()
                    error_detail = error_json.get("detail", error_detail)
                except:
                    pass
                raise ValueError(f"HTTP {e.response.status_code}: {error_detail}")
            except httpx.RequestError as e:
                raise ValueError(f"Request failed: {str(e)}")

    # Health endpoint
    async def get_health(self) -> Dict[str, Any]:
        """Get API health status"""
        return await self.request("GET", "/health")

    # Workflow endpoints
    async def list_workflows(
        self, source: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List all synchronized workflows"""
        params = {"limit": limit}
        if source:
            params["source"] = source
        return await self.request("GET", "/api/v1/workflows", params=params)

    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get specific workflow details"""
        return await self.request("GET", f"/api/v1/workflows/{workflow_id}")

    async def run_workflow(
        self, workflow_id: str, input_data: str
    ) -> Dict[str, Any]:
        """Execute a workflow with input data"""
        # The API expects a raw JSON string, so we need special handling
        url = f"{self.config.base_url}/api/v1/workflows/{workflow_id}/run"
        headers = {**self.headers, "Content-Type": "application/json"}
        
        # Wrap the input string in quotes to make it valid JSON
        import json
        json_input = json.dumps(input_data)
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                response = await client.post(
                    url=url,
                    headers=headers,
                    content=json_input,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                return {
                    "error": str(e),
                    "status_code": e.response.status_code,
                    "detail": e.response.text,
                }

    async def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Delete a workflow"""
        return await self.request("DELETE", f"/api/v1/workflows/{workflow_id}")

    # Remote workflow endpoints
    async def list_remote_workflows(self, source_url: str) -> List[Dict[str, Any]]:
        """List available workflows from remote source"""
        params = {"source_url": source_url}
        return await self.request("GET", "/api/v1/workflows/remote", params=params)

    async def get_remote_workflow(
        self, workflow_id: str, source_url: str
    ) -> Dict[str, Any]:
        """Get specific remote workflow details"""
        params = {"source_url": source_url}
        return await self.request(
            "GET", f"/api/v1/workflows/remote/{workflow_id}", params=params
        )

    async def sync_workflow(
        self,
        workflow_id: str,
        input_component: str = "input",
        output_component: str = "output",
    ) -> Dict[str, Any]:
        """Sync workflow from remote source"""
        params = {
            "input_component": input_component,
            "output_component": output_component,
        }
        return await self.request(
            "POST", f"/api/v1/workflows/sync/{workflow_id}", params=params
        )

    # Task endpoints
    async def list_tasks(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List task executions"""
        params = {"limit": limit}
        if workflow_id:
            params["workflow_id"] = workflow_id
        if status:
            params["status"] = status
        return await self.request("GET", "/api/v1/tasks", params=params)

    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get specific task details"""
        return await self.request("GET", f"/api/v1/tasks/{task_id}")

    async def delete_task(self, task_id: str) -> Dict[str, Any]:
        """Delete a task"""
        return await self.request("DELETE", f"/api/v1/tasks/{task_id}")

    # Schedule endpoints
    async def list_schedules(
        self, workflow_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all schedules"""
        params = {}
        if workflow_id:
            params["workflow_id"] = workflow_id
        return await self.request("GET", "/api/v1/schedules", params=params)

    async def create_schedule(
        self,
        workflow_id: str,
        schedule_type: str,
        schedule_expr: str,
        input_value: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new schedule"""
        data = {
            "workflow_id": workflow_id,
            "schedule_type": schedule_type,
            "schedule_expr": schedule_expr,
        }
        if input_value:
            data["input_value"] = input_value
        return await self.request("POST", "/api/v1/schedules", json_data=data)

    async def get_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Get specific schedule details"""
        return await self.request("GET", f"/api/v1/schedules/{schedule_id}")

    async def update_schedule(
        self,
        schedule_id: str,
        schedule_type: Optional[str] = None,
        schedule_expr: Optional[str] = None,
        input_value: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a schedule"""
        data = {}
        if schedule_type:
            data["schedule_type"] = schedule_type
        if schedule_expr:
            data["schedule_expr"] = schedule_expr
        if input_value is not None:
            data["input_value"] = input_value
        return await self.request(
            "PUT", f"/api/v1/schedules/{schedule_id}", json_data=data
        )

    async def delete_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Delete a schedule"""
        return await self.request("DELETE", f"/api/v1/schedules/{schedule_id}")

    async def enable_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Enable a schedule"""
        return await self.request("POST", f"/api/v1/schedules/{schedule_id}/enable")

    async def disable_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Disable a schedule"""
        return await self.request("POST", f"/api/v1/schedules/{schedule_id}/disable")

    # Source endpoints
    async def list_sources(self) -> List[Dict[str, Any]]:
        """List all configured sources"""
        return await self.request("GET", "/api/v1/sources/")

    async def add_source(
        self, name: str, source_type: str, url: str, api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a new workflow source"""
        data = {
            "name": name,
            "source_type": source_type,
            "url": url,
        }
        if api_key:
            data["api_key"] = api_key
        return await self.request("POST", "/api/v1/sources/", json_data=data)

    async def get_source(self, source_id: str) -> Dict[str, Any]:
        """Get specific source details"""
        return await self.request("GET", f"/api/v1/sources/{source_id}")

    async def update_source(
        self,
        source_id: str,
        name: Optional[str] = None,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a source"""
        data = {}
        if name:
            data["name"] = name
        if url:
            data["url"] = url
        if api_key:
            data["api_key"] = api_key
        return await self.request(
            "PUT", f"/api/v1/sources/{source_id}", json_data=data
        )

    async def delete_source(self, source_id: str) -> Dict[str, Any]:
        """Delete a source"""
        return await self.request("DELETE", f"/api/v1/sources/{source_id}")