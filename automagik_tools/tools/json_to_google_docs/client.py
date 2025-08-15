"""Google API Client for JSON to Google Docs tool"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from io import BytesIO

try:
    import google.auth
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

from .config import JsonToGoogleDocsConfig


class GoogleAPIClient:
    """Client for Google Drive and Docs APIs"""
    
    def __init__(self, config: 'JsonToGoogleDocsConfig'):
        if not GOOGLE_API_AVAILABLE:
            raise ImportError(
                "Google API dependencies are not installed. "
                "Please install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
        self.config = config
        self.credentials = self._get_credentials()
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
        self.docs_service = build('docs', 'v1', credentials=self.credentials)
    
    def _get_credentials(self):
        """Get Google API credentials from service account"""
        try:
            service_account_info = self.config.get_service_account_info()
            
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=[
                    'https://www.googleapis.com/auth/drive',
                    'https://www.googleapis.com/auth/documents'
                ]
            )
            
            return credentials
            
        except Exception as e:
            raise ValueError(f"Failed to create Google API credentials: {str(e)}")
    
    async def upload_docx_file(
        self,
        file_path: str,
        filename: str,
        folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload a DOCX file to Google Drive"""
        try:
            # Determine folder
            target_folder = folder_id or self.config.default_folder_id
            
            # File metadata
            file_metadata = {'name': filename}
            if target_folder:
                file_metadata['parents'] = [target_folder]
            
            # Upload file
            media = MediaIoBaseUpload(
                open(file_path, 'rb'),
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                resumable=True
            )
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink'
            ).execute()
            
            return {
                'file_id': file.get('id'),
                'name': file.get('name'),
                'url': file.get('webViewLink')
            }
            
        except HttpError as e:
            raise Exception(f"Google Drive API error: {e}")
        except Exception as e:
            raise Exception(f"Upload failed: {str(e)}")
    
    async def download_file(
        self,
        file_id: str,
        output_path: str,
        export_format: str = "docx"
    ) -> Dict[str, Any]:
        """Download a file from Google Drive"""
        try:
            # Determine export MIME type
            if export_format == "docx":
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif export_format == "pdf":
                mime_type = 'application/pdf'
            elif export_format == "txt":
                mime_type = 'text/plain'
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
            
            # Export file
            request = self.drive_service.files().export_media(
                fileId=file_id,
                mimeType=mime_type
            )
            
            # Download to file
            with open(output_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            
            # Get file size
            file_size = 0
            try:
                file_size = os.path.getsize(output_path)
            except:
                pass
            
            return {
                'file_path': output_path,
                'format': export_format,
                'size': file_size
            }
            
        except HttpError as e:
            raise Exception(f"Google Drive API error: {e}")
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")
    
    async def list_files(
        self,
        folder_id: Optional[str] = None,
        search_query: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List files in Google Drive"""
        try:
            # Build query
            query_parts = []
            
            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")
            
            if mime_type:
                query_parts.append(f"mimeType='{mime_type}'")
            
            if search_query:
                query_parts.append(f"name contains '{search_query}'")
            
            # Add trashed filter
            query_parts.append("trashed=false")
            
            query = " and ".join(query_parts) if query_parts else "trashed=false"
            
            # Execute search
            results = self.drive_service.files().list(
                q=query,
                fields="files(id,name,mimeType,createdTime,modifiedTime,webViewLink)",
                orderBy="modifiedTime desc"
            ).execute()
            
            files = results.get('files', [])
            
            return [
                {
                    'id': file['id'],
                    'name': file['name'],
                    'mime_type': file['mimeType'],
                    'created_time': file['createdTime'],
                    'modified_time': file['modifiedTime'],
                    'url': file['webViewLink']
                }
                for file in files
            ]
            
        except HttpError as e:
            raise Exception(f"Google Drive API error: {e}")
        except Exception as e:
            raise Exception(f"List files failed: {str(e)}")
    
    async def share_document(
        self,
        file_id: str,
        emails: List[str],
        role: str = "reader",
        make_public: bool = False
    ) -> Dict[str, Any]:
        """Share a document with users"""
        try:
            results = []
            
            # Share with specific emails
            for email in emails:
                permission = {
                    'type': 'user',
                    'role': role,
                    'emailAddress': email
                }
                
                result = self.drive_service.permissions().create(
                    fileId=file_id,
                    body=permission,
                    sendNotificationEmail=True,
                    fields='id'
                ).execute()
                
                results.append({
                    'email': email,
                    'permission_id': result.get('id'),
                    'role': role
                })
            
            # Make public if requested
            if make_public:
                public_permission = {
                    'type': 'anyone',
                    'role': role
                }
                
                result = self.drive_service.permissions().create(
                    fileId=file_id,
                    body=public_permission,
                    fields='id'
                ).execute()
                
                results.append({
                    'type': 'public',
                    'permission_id': result.get('id'),
                    'role': role
                })
            
            return {
                'shared_permissions': results,
                'file_id': file_id
            }
            
        except HttpError as e:
            raise Exception(f"Google Drive API error: {e}")
        except Exception as e:
            raise Exception(f"Share failed: {str(e)}")
    
    async def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Get information about a file"""
        try:
            file = self.drive_service.files().get(
                fileId=file_id,
                fields="id,name,mimeType,size,createdTime,modifiedTime,webViewLink,owners"
            ).execute()
            
            return {
                'id': file['id'],
                'name': file['name'],
                'mime_type': file['mimeType'],
                'size': file.get('size'),
                'created_time': file['createdTime'],
                'modified_time': file['modifiedTime'],
                'url': file['webViewLink'],
                'owners': [owner['emailAddress'] for owner in file.get('owners', [])]
            }
            
        except HttpError as e:
            raise Exception(f"Google Drive API error: {e}")
        except Exception as e:
            raise Exception(f"Get file info failed: {str(e)}")