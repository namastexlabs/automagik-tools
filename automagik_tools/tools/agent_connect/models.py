"""
Data models for Message Bridge MCP tool
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Represents a message in the bridge system"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    channel_id: str
    content: str
    sender_id: str  # Tool instance/session identifier
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    in_reply_to: Optional[str] = None  # For reply tracking
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Extra user data
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary with ISO timestamp"""
        data = super().model_dump()
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ChannelInfo(BaseModel):
    """Information about a channel"""
    
    channel_id: str
    active_listeners: int = 0
    pending_messages: int = 0
    total_messages_sent: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary with ISO timestamps"""
        data = super().model_dump()
        data['created_at'] = self.created_at.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        return data