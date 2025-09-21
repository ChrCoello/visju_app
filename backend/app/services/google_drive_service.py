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

    def list_audio_files(self, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List audio files in the specified folder."""
        if not self.service:
            logger.error("Service not authenticated")
            return []

        target_folder_id = folder_id or settings.GOOGLE_DRIVE_FOLDER_ID
        if not target_folder_id:
            logger.error("No folder ID provided")
            return []

        try:
            # Query for audio files (M4A, MP3, WAV)
            audio_mime_types = [
                "audio/mp4",
                "audio/mpeg",
                "audio/wav",
                "audio/x-m4a"
            ]

            mime_query = " or ".join([f"mimeType='{mime}'" for mime in audio_mime_types])
            query = f"'{target_folder_id}' in parents and ({mime_query})"

            results = self.service.files().list(
                q=query,
                pageSize=100,
                fields="files(id,name,mimeType,size,modifiedTime,createdTime,parents)"
            ).execute()

            files = results.get('files', [])
            logger.info(f"Found {len(files)} audio files in folder")

            return files

        except HttpError as e:
            logger.error(f"Error listing audio files: {e}")
            return []

    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed metadata for a specific file."""
        if not self.service:
            logger.error("Service not authenticated")
            return None

        try:
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields="id,name,mimeType,size,modifiedTime,createdTime,parents,webViewLink"
            ).execute()

            logger.info(f"Retrieved metadata for file: {file_metadata.get('name')}")
            return file_metadata

        except HttpError as e:
            logger.error(f"Error getting file metadata for {file_id}: {e}")
            return None

    def download_file(self, file_id: str, local_path: str) -> bool:
        """Download a file from Google Drive to local storage."""
        if not self.service:
            logger.error("Service not authenticated")
            return False

        try:
            # Get file metadata first
            file_metadata = self.get_file_metadata(file_id)
            if not file_metadata:
                return False

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Download file
            request = self.service.files().get_media(fileId=file_id)

            with open(local_path, 'wb') as local_file:
                from googleapiclient.http import MediaIoBaseDownload
                downloader = MediaIoBaseDownload(local_file, request)

                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.info(f"Download progress: {int(status.progress() * 100)}%")

            logger.info(f"Successfully downloaded {file_metadata.get('name')} to {local_path}")
            return True

        except HttpError as e:
            logger.error(f"Error downloading file {file_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading file {file_id}: {e}")
            return False

    def monitor_folder_changes(self, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for new or modified audio files since last check."""
        if not self.service:
            logger.error("Service not authenticated")
            return []

        target_folder_id = folder_id or settings.GOOGLE_DRIVE_FOLDER_ID
        if not target_folder_id:
            logger.error("No folder ID provided")
            return []

        try:
            # Get current list of files
            current_files = self.list_audio_files(target_folder_id)

            # For now, return all files (in a real implementation, you'd compare with stored state)
            new_files = []
            for file_info in current_files:
                # Check if file is "new" based on some criteria
                # This is a simplified version - you'd want to track last_checked timestamp
                new_files.append({
                    'id': file_info['id'],
                    'name': file_info['name'],
                    'size': int(file_info.get('size', 0)),
                    'mimeType': file_info['mimeType'],
                    'modifiedTime': file_info['modifiedTime'],
                    'createdTime': file_info['createdTime']
                })

            if new_files:
                logger.info(f"Found {len(new_files)} files to process")

            return new_files

        except HttpError as e:
            logger.error(f"Error monitoring folder changes: {e}")
            return []

def get_drive_service() -> GoogleDriveService:
    """Get a configured Google Drive service instance."""
    service = GoogleDriveService()
    service.authenticate()
    return service