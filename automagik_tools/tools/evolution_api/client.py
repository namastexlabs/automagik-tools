"""
Evolution API HTTP Client
"""

import httpx
import asyncio
from typing import Dict, Any, Optional, List
from .config import EvolutionAPIConfig


class EvolutionAPIClient:
    """HTTP client for Evolution API v2"""
    
    def __init__(self, config: EvolutionAPIConfig):
        self.config = config
        self.base_url = config.base_url.rstrip('/')
        self.headers = {
            "Content-Type": "application/json",
            "apikey": config.api_key
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.config.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=self.headers,
                        json=data if data else None
                    )
                    
                    if response.status_code in [200, 201]:
                        return response.json()
                    elif response.status_code == 401:
                        raise ValueError("Evolution API authentication failed - check API key")
                    elif response.status_code == 403:
                        raise ValueError("Evolution API access forbidden - check permissions")
                    elif response.status_code == 404:
                        raise ValueError("Evolution API endpoint not found")
                    elif response.status_code >= 500:
                        if attempt < self.config.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        raise ValueError(f"Evolution API server error {response.status_code}")
                    else:
                        raise ValueError(f"Evolution API error {response.status_code}: {response.text}")
                        
            except httpx.TimeoutException:
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise TimeoutError(f"Request timeout after {self.config.max_retries} retries")
            except httpx.ConnectError:
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise ConnectionError(f"Connection failed after {self.config.max_retries} retries")
    
    async def send_text_message(
        self, 
        instance: str, 
        number: str, 
        message: str,
        delay: int = 0,
        linkPreview: bool = True,
        mentions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send text message via Evolution API v2"""
        data = {
            "number": number,
            "text": message,
            "delay": delay,
            "linkPreview": linkPreview
        }
        
        if mentions:
            data["mentions"] = mentions
        
        return await self._make_request(
            "POST", 
            f"/message/sendText/{instance}",
            data
        )
    
    async def send_media(
        self,
        instance: str,
        number: str,
        media: str,
        mediatype: str,
        mimetype: str,
        caption: str = "",
        fileName: str = "",
        delay: int = 0,
        linkPreview: bool = True,
        mentions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send media via Evolution API v2"""
        data = {
            "number": number,
            "media": media,
            "mediatype": mediatype,
            "mimetype": mimetype,
            "caption": caption,
            "fileName": fileName,
            "delay": delay,
            "linkPreview": linkPreview
        }
        
        if mentions:
            data["mentions"] = mentions
        
        return await self._make_request(
            "POST",
            f"/message/sendMedia/{instance}",
            data
        )
    
    async def send_audio(
        self,
        instance: str,
        number: str,
        audio: str,
        delay: int = 0,
        linkPreview: bool = True,
        mentions: Optional[List[str]] = None,
        quoted: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send audio message via Evolution API v2"""
        data = {
            "number": number,
            "audio": audio,
            "delay": delay,
            "linkPreview": linkPreview
        }
        
        if mentions:
            data["mentions"] = mentions
        if quoted:
            data["quoted"] = quoted
        
        return await self._make_request(
            "POST",
            f"/message/sendWhatsAppAudio/{instance}",
            data
        )
    
    async def send_reaction(
        self,
        instance: str,
        remote_jid: str,
        from_me: bool,
        message_id: str,
        reaction: str
    ) -> Dict[str, Any]:
        """Send reaction via Evolution API v2"""
        data = {
            "key": {
                "remoteJid": remote_jid,
                "fromMe": from_me,
                "id": message_id
            },
            "reaction": reaction
        }
        
        return await self._make_request(
            "POST",
            f"/message/sendReaction/{instance}",
            data
        )
    
    async def send_location(
        self,
        instance: str,
        number: str,
        latitude: float,
        longitude: float,
        name: str = "",
        address: str = "",
        delay: int = 0,
        mentions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send location via Evolution API v2"""
        data = {
            "number": number,
            "latitude": latitude,
            "longitude": longitude,
            "name": name,
            "address": address,
            "delay": delay
        }
        
        if mentions:
            data["mentions"] = mentions
        
        return await self._make_request(
            "POST",
            f"/message/sendLocation/{instance}",
            data
        )
    
    async def send_contact(
        self,
        instance: str,
        number: str,
        contact: List[Dict[str, str]],
        delay: int = 0,
        mentions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send contact via Evolution API v2"""
        data = {
            "number": number,
            "contact": contact,
            "delay": delay
        }
        
        if mentions:
            data["mentions"] = mentions
        
        return await self._make_request(
            "POST",
            f"/message/sendContact/{instance}",
            data
        )
    
    async def send_presence(
        self,
        instance: str,
        number: str,
        presence: str = "composing",
        delay: int = 3000
    ) -> Dict[str, Any]:
        """Send presence indicator via Evolution API v2"""
        data = {
            "number": number,
            "options": {
                "presence": presence,
                "delay": delay
            }
        }
        
        return await self._make_request(
            "POST",
            f"/chat/sendPresence/{instance}",
            data
        )