"""
Test Google Drive authentication and basic functionality.
"""

import pytest
import os
from app.services.google_drive_service import GoogleDriveService
from app.core.config import settings


class TestGoogleDriveAuth:
    """Test Google Drive authentication and basic operations."""

    def test_credentials_file_exists(self, skip_if_no_credentials):
        """Test that credentials file exists."""
        assert os.path.exists(settings.GOOGLE_DRIVE_CREDENTIALS_PATH)

    def test_folder_id_configured(self, skip_if_no_folder_id):
        """Test that folder ID is configured."""
        assert settings.GOOGLE_DRIVE_FOLDER_ID is not None
        assert len(settings.GOOGLE_DRIVE_FOLDER_ID) > 0

    def test_authentication_success(self, skip_if_no_credentials):
        """Test Google Drive authentication."""
        service = GoogleDriveService()
        result = service.authenticate()
        assert result is True
        assert service.service is not None
        assert service.credentials is not None

    def test_connection(self, google_drive_service):
        """Test Google Drive connection."""
        result = google_drive_service.test_connection()

        assert result["success"] is True
        assert "user_email" in result
        assert "@" in result["user_email"]

    def test_folder_access(self, google_drive_service, skip_if_no_folder_id):
        """Test access to the configured Google Drive folder."""
        result = google_drive_service.test_folder_access()

        assert result["success"] is True
        assert "folder_name" in result
        assert "folder_id" in result
        assert result["folder_id"] == settings.GOOGLE_DRIVE_FOLDER_ID
        assert "file_count" in result

    def test_list_audio_files(self, google_drive_service, skip_if_no_folder_id):
        """Test listing audio files in the folder."""
        files = google_drive_service.list_audio_files()

        assert isinstance(files, list)
        # We don't assert a specific count since folder contents may vary

        # If files exist, check their structure
        for file_info in files:
            assert "id" in file_info
            assert "name" in file_info
            assert "mimeType" in file_info
            assert file_info["mimeType"] in [
                "audio/mp4", "audio/mpeg", "audio/wav", "audio/x-m4a"
            ]

    def test_get_file_metadata(self, google_drive_service, skip_if_no_folder_id):
        """Test getting metadata for a specific file."""
        # First get list of files
        files = google_drive_service.list_audio_files()

        if not files:
            pytest.skip("No audio files found in folder for metadata testing")

        # Test metadata retrieval for first file
        first_file = files[0]
        metadata = google_drive_service.get_file_metadata(first_file["id"])

        assert metadata is not None
        assert metadata["id"] == first_file["id"]
        assert metadata["name"] == first_file["name"]
        assert "size" in metadata
        assert "mimeType" in metadata