"""HTTP client for OMNI API"""
import httpx
import logging
from typing import Optional, Dict, Any, List
from .config import OmniConfig
from .models import (
    InstanceConfig, InstanceResponse, ConnectionStatus, QRCodeResponse,
    SendTextRequest, SendMediaRequest, SendAudioRequest, SendStickerRequest,
    SendContactRequest, SendReactionRequest, MessageResponse,
    TraceFilter, TraceResponse, TracePayloadResponse, TraceAnalytics,
    FetchProfileRequest, UpdateProfilePictureRequest
)

logger = logging.getLogger(__name__)


class OmniClient:
    """Async HTTP client for OMNI API"""
    
    def __init__(self, config: OmniConfig):
        self.config = config
        self.base_url = config.base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        self.timeout = httpx.Timeout(config.timeout)
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=json,
                    params=params
                )
                response.raise_for_status()
                
                # Handle empty responses
                if response.status_code == 204:
                    return {"success": True}
                
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                raise
    
    # Instance Operations
    async def list_instances(self, skip: int = 0, limit: int = 100, include_status: bool = True) -> List[InstanceResponse]:
        """List all instances"""
        params = {"skip": skip, "limit": limit, "include_status": include_status}
        data = await self._request("GET", "/api/v1/instances", params=params)
        return [InstanceResponse(**item) for item in data]
    
    async def get_instance(self, instance_name: str, include_status: bool = True) -> InstanceResponse:
        """Get specific instance"""
        params = {"include_status": include_status}
        data = await self._request("GET", f"/api/v1/instances/{instance_name}", params=params)
        return InstanceResponse(**data)
    
    async def create_instance(self, config: InstanceConfig) -> InstanceResponse:
        """Create new instance"""
        data = await self._request("POST", "/api/v1/instances", json=config.model_dump(exclude_none=True))
        return InstanceResponse(**data)
    
    async def update_instance(self, instance_name: str, config: Dict[str, Any]) -> InstanceResponse:
        """Update instance"""
        data = await self._request("PUT", f"/api/v1/instances/{instance_name}", json=config)
        return InstanceResponse(**data)
    
    async def delete_instance(self, instance_name: str) -> bool:
        """Delete instance"""
        await self._request("DELETE", f"/api/v1/instances/{instance_name}")
        return True
    
    async def set_default_instance(self, instance_name: str) -> InstanceResponse:
        """Set instance as default"""
        data = await self._request("POST", f"/api/v1/instances/{instance_name}/set-default")
        return InstanceResponse(**data)
    
    async def get_instance_status(self, instance_name: str) -> ConnectionStatus:
        """Get instance connection status"""
        data = await self._request("GET", f"/api/v1/instances/{instance_name}/status")
        return ConnectionStatus(**data)
    
    async def get_instance_qr(self, instance_name: str) -> QRCodeResponse:
        """Get instance QR code"""
        data = await self._request("GET", f"/api/v1/instances/{instance_name}/qr")
        return QRCodeResponse(**data)
    
    async def restart_instance(self, instance_name: str) -> Dict[str, Any]:
        """Restart instance"""
        return await self._request("POST", f"/api/v1/instances/{instance_name}/restart")
    
    async def logout_instance(self, instance_name: str) -> Dict[str, Any]:
        """Logout instance"""
        return await self._request("POST", f"/api/v1/instances/{instance_name}/logout")
    
    # Message Operations
    async def send_text(self, instance_name: str, request: SendTextRequest) -> MessageResponse:
        """Send text message"""
        data = await self._request(
            "POST", 
            f"/api/v1/instance/{instance_name}/send-text",
            json=request.model_dump(exclude_none=True)
        )
        return MessageResponse(**data)
    
    async def send_media(self, instance_name: str, request: SendMediaRequest) -> MessageResponse:
        """Send media message"""
        data = await self._request(
            "POST",
            f"/api/v1/instance/{instance_name}/send-media",
            json=request.model_dump(exclude_none=True)
        )
        return MessageResponse(**data)
    
    async def send_audio(self, instance_name: str, request: SendAudioRequest) -> MessageResponse:
        """Send audio message"""
        data = await self._request(
            "POST",
            f"/api/v1/instance/{instance_name}/send-audio",
            json=request.model_dump(exclude_none=True)
        )
        return MessageResponse(**data)
    
    async def send_sticker(self, instance_name: str, request: SendStickerRequest) -> MessageResponse:
        """Send sticker message"""
        data = await self._request(
            "POST",
            f"/api/v1/instance/{instance_name}/send-sticker",
            json=request.model_dump(exclude_none=True)
        )
        return MessageResponse(**data)
    
    async def send_contact(self, instance_name: str, request: SendContactRequest) -> MessageResponse:
        """Send contact message"""
        data = await self._request(
            "POST",
            f"/api/v1/instance/{instance_name}/send-contact",
            json=request.model_dump(exclude_none=True)
        )
        return MessageResponse(**data)
    
    async def send_reaction(self, instance_name: str, request: SendReactionRequest) -> MessageResponse:
        """Send reaction"""
        data = await self._request(
            "POST",
            f"/api/v1/instance/{instance_name}/send-reaction",
            json=request.model_dump(exclude_none=True)
        )
        return MessageResponse(**data)
    
    # Trace Operations
    async def list_traces(self, filters: TraceFilter) -> List[TraceResponse]:
        """List traces with filters"""
        params = {k: v for k, v in filters.model_dump(exclude_none=True).items() if v is not None}
        data = await self._request("GET", "/api/v1/traces", params=params)
        return [TraceResponse(**item) for item in data]
    
    async def get_trace(self, trace_id: str) -> TraceResponse:
        """Get specific trace"""
        data = await self._request("GET", f"/api/v1/traces/{trace_id}")
        return TraceResponse(**data)
    
    async def get_trace_payloads(self, trace_id: str, include_payload: bool = False) -> List[TracePayloadResponse]:
        """Get trace payloads"""
        params = {"include_payload": include_payload}
        data = await self._request("GET", f"/api/v1/traces/{trace_id}/payloads", params=params)
        return [TracePayloadResponse(**item) for item in data]
    
    async def get_trace_analytics(
        self, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        instance_name: Optional[str] = None
    ) -> TraceAnalytics:
        """Get trace analytics"""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if instance_name:
            params["instance_name"] = instance_name
            
        data = await self._request("GET", "/api/v1/traces/analytics/summary", params=params)
        return TraceAnalytics(**data)
    
    async def get_traces_by_phone(self, phone_number: str, limit: int = 50) -> List[TraceResponse]:
        """Get traces for phone number"""
        params = {"limit": limit}
        data = await self._request("GET", f"/api/v1/traces/phone/{phone_number}", params=params)
        return [TraceResponse(**item) for item in data]
    
    async def cleanup_traces(self, days_old: int = 30, dry_run: bool = True) -> Dict[str, Any]:
        """Cleanup old traces"""
        params = {"days_old": days_old, "dry_run": dry_run}
        return await self._request("DELETE", "/api/v1/traces/cleanup", params=params)
    
    # Profile Operations
    async def fetch_profile(self, instance_name: str, request: FetchProfileRequest) -> Dict[str, Any]:
        """Fetch user profile"""
        data = await self._request(
            "POST",
            f"/api/v1/instance/{instance_name}/fetch-profile",
            json=request.model_dump(exclude_none=True)
        )
        return data
    
    async def update_profile_picture(self, instance_name: str, request: UpdateProfilePictureRequest) -> MessageResponse:
        """Update profile picture"""
        data = await self._request(
            "POST",
            f"/api/v1/instance/{instance_name}/update-profile-picture",
            json=request.model_dump(exclude_none=True)
        )
        return MessageResponse(**data)