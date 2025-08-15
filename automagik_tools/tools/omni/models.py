"""Pydantic models for OMNI API requests and responses"""
from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


# Enums
class ChannelType(str, Enum):
    WHATSAPP = "whatsapp"
    SLACK = "slack"
    DISCORD = "discord"


class InstanceOperation(str, Enum):
    LIST = "list"
    GET = "get"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SET_DEFAULT = "set_default"
    STATUS = "status"
    QR = "qr"
    RESTART = "restart"
    LOGOUT = "logout"


class MessageType(str, Enum):
    TEXT = "text"
    MEDIA = "media"
    AUDIO = "audio"
    STICKER = "sticker"
    CONTACT = "contact"
    REACTION = "reaction"


class TraceOperation(str, Enum):
    LIST = "list"
    GET = "get"
    GET_PAYLOADS = "get_payloads"
    ANALYTICS = "analytics"
    BY_PHONE = "by_phone"
    CLEANUP = "cleanup"


class ProfileOperation(str, Enum):
    FETCH = "fetch"
    UPDATE_PICTURE = "update_picture"


# Instance Models
class InstanceConfig(BaseModel):
    """Instance configuration model"""
    name: str
    channel_type: ChannelType = ChannelType.WHATSAPP
    evolution_url: Optional[str] = None
    evolution_key: Optional[str] = None
    whatsapp_instance: Optional[str] = None
    session_id_prefix: Optional[str] = None
    webhook_base64: Optional[bool] = True
    phone_number: Optional[str] = None
    auto_qr: Optional[bool] = True
    integration: Optional[str] = None
    agent_api_url: Optional[str] = None
    agent_api_key: Optional[str] = None
    default_agent: Optional[str] = None
    agent_timeout: Optional[int] = 60
    is_default: Optional[bool] = False
    is_active: Optional[bool] = True


class InstanceResponse(InstanceConfig):
    """Instance response with additional fields"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    evolution_status: Optional[Dict[str, Any]] = None


class ConnectionStatus(BaseModel):
    """Connection status response"""
    instance_name: str
    channel_type: str
    status: str
    channel_data: Optional[Dict[str, Any]] = None


class QRCodeResponse(BaseModel):
    """QR code response"""
    instance_name: str
    qr_code: Optional[str] = None
    qr_url: Optional[str] = None
    connection_type: str
    status: str


# Message Models
class SendTextRequest(BaseModel):
    """Text message request"""
    model_config = ConfigDict(populate_by_name=True)
    
    phone_number: str = Field(..., description="Phone number with country code", alias="phone")
    text: str = Field(..., description="Message text", alias="message") 
    quoted_message_id: Optional[str] = None
    delay: Optional[int] = Field(None, description="Delay in milliseconds")


class SendMediaRequest(BaseModel):
    """Media message request"""
    model_config = ConfigDict(populate_by_name=True)
    
    phone_number: str = Field(..., description="Phone number with country code", alias="phone")
    media_url: str = Field(..., description="URL of the media file")
    media_type: Literal["image", "video", "document"] = "image"
    caption: Optional[str] = None
    filename: Optional[str] = None
    quoted_message_id: Optional[str] = None
    delay: Optional[int] = None


class SendAudioRequest(BaseModel):
    """Audio message request"""
    model_config = ConfigDict(populate_by_name=True)
    
    phone_number: str = Field(..., description="Phone number with country code", alias="phone")
    audio_url: str = Field(..., description="URL of the audio file")
    ptt: bool = Field(True, description="Send as voice note")
    quoted_message_id: Optional[str] = None
    delay: Optional[int] = None


class SendStickerRequest(BaseModel):
    """Sticker message request"""
    model_config = ConfigDict(populate_by_name=True)
    
    phone_number: str = Field(..., description="Phone number with country code", alias="phone")
    sticker_url: str = Field(..., description="URL of the sticker file")
    quoted_message_id: Optional[str] = None
    delay: Optional[int] = None


class ContactInfo(BaseModel):
    """Contact information"""
    full_name: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    organization: Optional[str] = None
    url: Optional[str] = None


class SendContactRequest(BaseModel):
    """Contact message request"""
    model_config = ConfigDict(populate_by_name=True)
    
    phone_number: str = Field(..., description="Phone number with country code", alias="phone")
    contacts: List[ContactInfo]
    quoted_message_id: Optional[str] = None
    delay: Optional[int] = None


class SendReactionRequest(BaseModel):
    """Reaction message request"""
    model_config = ConfigDict(populate_by_name=True)
    
    phone_number: str = Field(..., description="Phone number with country code", alias="phone")
    message_id: str = Field(..., description="ID of message to react to")
    emoji: str = Field(..., description="Emoji reaction")


class MessageResponse(BaseModel):
    """Generic message response"""
    success: bool
    message_id: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None


# Trace Models
class TraceFilter(BaseModel):
    """Trace filter parameters"""
    phone: Optional[str] = None
    instance_name: Optional[str] = None
    trace_status: Optional[str] = None
    message_type: Optional[str] = None
    session_name: Optional[str] = None
    agent_session_id: Optional[str] = None
    has_media: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 50
    offset: int = 0


class TraceResponse(BaseModel):
    """Trace response model"""
    id: str
    instance_name: str
    sender_phone: str
    message_type: Optional[str] = None
    status: str
    session_name: Optional[str] = None
    agent_session_id: Optional[str] = None
    has_media: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    payload_count: int = 0
    error: Optional[str] = None


class TracePayloadResponse(BaseModel):
    """Trace payload response"""
    id: str
    trace_id: str
    payload_type: str
    direction: str
    payload: Optional[Dict[str, Any]] = None
    created_at: datetime


class TraceAnalytics(BaseModel):
    """Trace analytics summary"""
    total_traces: int
    by_status: Dict[str, int]
    by_instance: Dict[str, int]
    by_message_type: Dict[str, int]
    avg_processing_time: Optional[float] = None
    error_rate: Optional[float] = None
    time_range: Dict[str, Any]


# Profile Models
class FetchProfileRequest(BaseModel):
    """Profile fetch request"""
    user_id: Optional[str] = None
    phone_number: Optional[str] = None


class UpdateProfilePictureRequest(BaseModel):
    """Profile picture update request"""
    picture_url: str = Field(..., description="URL of the new profile picture")


# Unified Message Request
MessageRequestType = Union[
    SendTextRequest,
    SendMediaRequest,
    SendAudioRequest,
    SendStickerRequest,
    SendContactRequest,
    SendReactionRequest
]