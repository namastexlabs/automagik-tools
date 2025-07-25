"""Configuration for JSON to Google Docs MCP Tool"""

import json
import os
from typing import Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class JsonToGoogleDocsConfig(BaseSettings):
    """Configuration for JSON to Google Docs tool"""
    
    model_config = SettingsConfigDict(
        env_prefix="GOOGLE_DOCS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    service_account_json: Optional[str] = Field(
        default=None,
        description="Path to Google service account JSON file or JSON content as string"
    )
    
    service_account_json_content: Optional[str] = Field(
        default=None,
        description="Google service account JSON content as string (alternative to file path)"
    )
    
    default_folder_id: Optional[str] = Field(
        default=None,
        description="Default Google Drive folder ID for uploads"
    )
    
    enable_markdown_conversion: bool = Field(
        default=True,
        description="Enable conversion of markdown syntax to Word formatting"
    )
    
    default_share_type: str = Field(
        default="reader",
        description="Default sharing permission type"
    )
    
    timeout: int = Field(
        default=300,
        description="Request timeout in seconds",
        ge=30,
        le=600
    )
    
    @field_validator('service_account_json')
    @classmethod
    def validate_service_account_json(cls, v):
        if not v:
            return v
            
        # Check if it's a file path or JSON content
        if v.strip().startswith('{'):
            # It's JSON content, validate it
            try:
                json.loads(v)
                return v
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON content in service_account_json")
        else:
            # It's a file path, check if file exists
            if not os.path.exists(v):
                raise ValueError(f"Service account JSON file not found: {v}")
            return v
    
    @field_validator('default_share_type')
    @classmethod
    def validate_share_type(cls, v):
        valid_types = ["reader", "commenter", "writer", "owner"]
        if v not in valid_types:
            raise ValueError(f"share_type must be one of: {', '.join(valid_types)}")
        return v
    
    def get_service_account_info(self) -> dict:
        """Get service account information as dictionary"""
        if self.service_account_json_content:
            return json.loads(self.service_account_json_content)
        elif self.service_account_json:
            if self.service_account_json.strip().startswith('{'):
                return json.loads(self.service_account_json)
            else:
                with open(self.service_account_json, 'r') as f:
                    return json.load(f)
        else:
            raise ValueError("No service account credentials provided")
    
    def has_credentials(self) -> bool:
        """Check if service account credentials are available"""
        return bool(self.service_account_json or self.service_account_json_content)