"""Configuration for Gemini Assistant MCP Tool"""

import os
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GeminiAssistantConfig(BaseSettings):
    """Configuration for Gemini Assistant tool"""
    
    model_config = SettingsConfigDict(
        env_prefix="GEMINI_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    api_key: str = Field(
        description="Google Gemini API key",
        min_length=1
    )
    
    model: str = Field(
        default="gemini-2.0-flash-exp",
        description="Gemini model to use for consultations"
    )
    
    session_timeout: int = Field(
        default=3600,
        description="Session timeout in seconds (default: 1 hour)",
        ge=60,
        le=86400
    )
    
    max_tokens: int = Field(
        default=8192,
        description="Maximum tokens per response",
        ge=1,
        le=32768
    )
    
    temperature: float = Field(
        default=0.7,
        description="Temperature for response generation",
        ge=0.0,
        le=2.0
    )
    
    max_sessions: int = Field(
        default=10,
        description="Maximum concurrent sessions",
        ge=1,
        le=100
    )
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Gemini API key is required")
        return v.strip()
    
    @validator('model')
    def validate_model(cls, v):
        valid_models = [
            "gemini-2.5-pro",
            "gemini-2.0-flash-exp",
            "gemini-2.0-flash-thinking-exp-1219",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
            "gemini-1.5-pro",
            "gemini-1.0-pro"
        ]
        if v not in valid_models:
            raise ValueError(f"Model must be one of: {', '.join(valid_models)}")
        return v