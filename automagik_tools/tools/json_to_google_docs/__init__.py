"""
JSON to Google Docs MCP Tool
Converts JSON data to DOCX files using Google Docs templates with placeholder substitution and markdown support
"""

import asyncio
import json
import tempfile
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .config import JsonToGoogleDocsConfig

try:
    from .client import GoogleAPIClient
    from .processor import DocumentProcessor
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    GoogleAPIClient = None
    DocumentProcessor = None

# Global configuration and client
config: Optional[JsonToGoogleDocsConfig] = None
client: Optional[GoogleAPIClient] = None
processor: Optional[DocumentProcessor] = None

# Create the FastMCP server
mcp = FastMCP("JSON to Google Docs")

@mcp.tool()
async def convert_json_to_docs(
    json_data: str,
    template_id: str,
    output_filename: str = "output.docx",
    folder_id: Optional[str] = None,
    share_with_emails: Optional[List[str]] = None,
    make_public: bool = False
) -> Dict[str, Any]:
    """
    Convert JSON data to DOCX using a Google Docs template with placeholder substitution.
    
    Args:
        json_data: JSON data as string or file path
        template_id: Google Docs template ID
        output_filename: Name for generated DOCX file
        folder_id: Google Drive folder ID (optional)
        share_with_emails: List of emails to share with (optional)
        make_public: Make document public (optional)
    
    Returns:
        Dictionary with conversion status and Google Drive URL
    """
    global client, processor
    
    if not client or not processor:
        return {"error": "Google Docs client not configured - missing service account credentials"}
    
    try:
        # Convert JSON data
        result = await processor.convert_json_to_docx(
            json_data=json_data,
            template_id=template_id,
            output_filename=output_filename,
            folder_id=folder_id
        )
        
        # Share document if requested
        if result.get("file_id") and (share_with_emails or make_public):
            await client.share_document(
                file_id=result["file_id"],
                emails=share_with_emails or [],
                make_public=make_public
            )
            result["shared"] = True
        
        return {
            "status": "success",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@mcp.tool()
async def upload_template(
    file_path: str,
    template_name: str,
    folder_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload a DOCX file as a template to Google Drive.
    
    Args:
        file_path: Path to DOCX file to upload
        template_name: Name for the template
        folder_id: Google Drive folder ID (optional)
    
    Returns:
        Dictionary with upload status and template ID
    """
    global client
    
    if not client:
        return {"error": "Google Docs client not configured"}
    
    try:
        result = await client.upload_docx_file(
            file_path=file_path,
            filename=template_name,
            folder_id=folder_id
        )
        
        return {
            "status": "success",
            "template_id": result["file_id"], 
            "template_url": result["url"],
            "filename": template_name
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

@mcp.tool()
async def share_document(
    file_id: str,
    emails: List[str],
    role: str = "reader",
    make_public: bool = False
) -> Dict[str, Any]:
    """
    Share a Google Docs document with users.
    
    Args:
        file_id: Google Drive file ID
        emails: List of email addresses to share with
        role: Permission role (reader, commenter, writer)
        make_public: Make document public
    
    Returns:
        Dictionary with sharing status
    """
    global client
    
    if not client:
        return {"error": "Google Docs client not configured"}
    
    try:
        result = await client.share_document(
            file_id=file_id,
            emails=emails,
            role=role,
            make_public=make_public
        )
        
        return {
            "status": "success",
            "shared_with": emails,
            "role": role,
            "public": make_public,
            "result": result
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

@mcp.tool()
async def list_templates(
    folder_id: Optional[str] = None,
    search_query: Optional[str] = None
) -> Dict[str, Any]:
    """
    List available Google Docs templates.
    
    Args:
        folder_id: Folder ID to search in (optional)
        search_query: Search query for templates (optional)
    
    Returns:
        Dictionary with list of templates
    """
    global client
    
    if not client:
        return {"error": "Google Docs client not configured"}
    
    try:
        templates = await client.list_files(
            folder_id=folder_id,
            search_query=search_query,
            mime_type="application/vnd.google-apps.document"
        )
        
        return {
            "status": "success",
            "templates": templates,
            "count": len(templates)
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

@mcp.tool()
async def download_document(
    file_id: str,
    output_path: str,
    format: str = "docx"
) -> Dict[str, Any]:
    """
    Download a Google Docs document in specified format.
    
    Args:
        file_id: Google Drive file ID
        output_path: Local path to save file
        format: Export format (docx, pdf, txt)
    
    Returns:
        Dictionary with download status
    """
    global client
    
    if not client:
        return {"error": "Google Docs client not configured"}
    
    try:
        result = await client.download_file(
            file_id=file_id,
            output_path=output_path,
            export_format=format
        )
        
        return {
            "status": "success",
            "file_path": output_path,
            "format": format,
            "size": result.get("size", 0)
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

@mcp.tool()
async def extract_placeholders(
    template_id: str
) -> Dict[str, Any]:
    """
    Extract placeholder {{keys}} from a Google Docs template.
    
    Args:
        template_id: Google Docs template ID
    
    Returns:
        Dictionary with list of found placeholders
    """
    global client, processor
    
    if not client or not processor:
        return {"error": "Google Docs client not configured"}
    
    try:
        # Download template temporarily
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_file:
            await client.download_file(
                file_id=template_id,
                output_path=tmp_file.name,
                export_format="docx"
            )
            
            # Extract placeholders
            placeholders = processor.extract_template_placeholders(tmp_file.name)
            
            # Clean up
            os.unlink(tmp_file.name)
            
            return {
                "status": "success",
                "template_id": template_id,
                "placeholders": placeholders,
                "count": len(placeholders)
            }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

@mcp.tool()
async def validate_json_data(
    json_data: str,
    template_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate JSON data and optionally check against template placeholders.
    
    Args:
        json_data: JSON data as string or file path
        template_id: Template ID to validate against (optional)
    
    Returns:
        Dictionary with validation results
    """
    global processor
    
    if not processor:
        return {"error": "Document processor not configured"}
    
    try:
        # Validate JSON
        validation_result = processor.validate_json_data(json_data)
        
        # Check against template if provided
        if template_id and validation_result["valid"]:
            placeholder_result = await extract_placeholders(template_id)
            if placeholder_result["status"] == "success":
                placeholders = placeholder_result["placeholders"]
                json_keys = list(validation_result["flattened_data"].keys())
                
                validation_result["template_match"] = {
                    "missing_keys": [p for p in placeholders if p not in json_keys],
                    "extra_keys": [k for k in json_keys if k not in placeholders],
                    "matched_keys": [k for k in json_keys if k in placeholders]
                }
        
        return {
            "status": "success",
            "validation": validation_result
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

def create_server(server_config: Optional[JsonToGoogleDocsConfig] = None):
    """Create JSON to Google Docs MCP server"""
    global config, client, processor
    
    # Always create fresh config to pick up environment variables
    config = server_config or JsonToGoogleDocsConfig()
    
    # Check if Google API is available
    if not GOOGLE_API_AVAILABLE:
        print("Warning: Google API dependencies not installed. JSON to Google Docs tool will have limited functionality.")
        print("         To enable full functionality, install: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return mcp
    
    # Initialize client and processor if we have service account credentials
    if config and config.service_account_json:
        try:
            client = GoogleAPIClient(config)
            processor = DocumentProcessor(config)
        except ImportError as e:
            print(f"Warning: Google API dependencies not available: {e}")
        except Exception as e:
            print(f"Warning: Failed to initialize Google API client: {e}")
    else:
        print("Warning: Google service account credentials not found")
    
    return mcp

def get_metadata() -> Dict[str, Any]:
    """Get tool metadata for discovery"""
    return {
        "name": "json-to-google-docs",
        "version": "1.0.0",
        "description": "Convert JSON data to DOCX files using Google Docs templates with placeholder substitution and markdown support",
        "author": "AutoMagik Tools",
        "category": "document-processing",
        "tags": ["json", "google-docs", "docx", "templates", "conversion", "markdown"]
    }

def get_config_class():
    """Get configuration class for this tool"""
    return JsonToGoogleDocsConfig