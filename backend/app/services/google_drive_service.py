import os
from typing import Optional, List, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger()

class GoogleDriveService:
    """Service for Google Drive API operations."""

    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    def __init__(self):
        self.service = None
        self.credentials = None

    def authenticate(self) -> bool:
        """Authenticate with Google Drive API using service account."""
        try:
            if not os.path.exists(settings.GOOGLE_DRIVE_CREDENTIALS_PATH):
                logger.error(f"Credentials file not found: {settings.GOOGLE_DRIVE_CREDENTIALS_PATH}")
                return False

            logger.info(f"Loading credentials from: {settings.GOOGLE_DRIVE_CREDENTIALS_PATH}")

            self.credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_DRIVE_CREDENTIALS_PATH,
                scopes=self.SCOPES
            )

            self.service = build('drive', 'v3', credentials=self.credentials)
            logger.info("Google Drive API authentication successful")
            return True

        except Exception as e:
            logger.error(f"Google Drive authentication failed: {e}")
            return False

    def test_connection(self) -> Dict[str, Any]:
        """Test the Google Drive connection and return status."""
        if not self.service:
            return {
                "success": False,
                "error": "Service not authenticated. Call authenticate() first."
            }

        try:
            # Test by getting about info
            about = self.service.about().get(fields="user").execute()
            user_email = about.get('user', {}).get('emailAddress', 'Unknown')

            logger.info(f"Connected to Google Drive as: {user_email}")

            return {
                "success": True,
                "user_email": user_email,
                "service_account": user_email
            }

        except HttpError as e:
            logger.error(f"Google Drive connection test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def test_folder_access(self, folder_id: Optional[str] = None) -> Dict[str, Any]:
        """Test access to the specified folder."""
        if not self.service:
            return {
                "success": False,
                "error": "Service not authenticated"
            }

        target_folder_id = folder_id or settings.GOOGLE_DRIVE_FOLDER_ID
        if not target_folder_id:
            return {
                "success": False,
                "error": "No folder ID provided"
            }

        try:
            # Get folder metadata
            folder = self.service.files().get(
                fileId=target_folder_id,
                fields="id,name,parents,permissions"
            ).execute()

            logger.info(f"Successfully accessed folder: {folder.get('name')} (ID: {folder.get('id')})")

            # List a few files to test read access
            files_result = self.service.files().list(
                q=f"'{target_folder_id}' in parents",
                pageSize=5,
                fields="files(id,name,mimeType,size,modifiedTime)"
            ).execute()

            files = files_result.get('files', [])

            return {
                "success": True,
                "folder_name": folder.get('name'),
                "folder_id": folder.get('id'),
                "file_count": len(files),
                "sample_files": [
                    {
                        "name": f.get('name'),
                        "id": f.get('id'),
                        "mimeType": f.get('mimeType')
                    } for f in files[:3]
                ]
            }

        except HttpError as e:
            logger.error(f"Folder access test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "folder_id": target_folder_id
            }

def get_drive_service() -> GoogleDriveService:
    """Get a configured Google Drive service instance."""
    service = GoogleDriveService()
    service.authenticate()
    return service