"""
Test complete Google Drive integration including file operations and database.
"""

import pytest
import os
import tempfile
from unittest.mock import patch
from app.services.google_drive_service import GoogleDriveService
from app.services.file_monitor_service import FileMonitorService
from app.services.audio_file_service import AudioFileService
from app.models.db_models import AudioFile
from app.core.config import settings


class TestGoogleDriveIntegration:
    """Test complete Google Drive integration functionality."""

    def test_audio_file_creation_from_drive_info(self, db_session):
        """Test creating AudioFile record from Google Drive file info."""
        # Mock Google Drive file info
        drive_file_info = {
            "id": "test_drive_id_123",
            "name": "test_recording.m4a",
            "size": "1024000",
            "mimeType": "audio/mp4",
            "createdTime": "2024-01-01T12:00:00.000Z",
            "modifiedTime": "2024-01-01T12:05:00.000Z"
        }

        audio_service = AudioFileService(db_session)
        audio_file = audio_service.create_audio_file(drive_file_info)

        assert audio_file is not None
        assert audio_file.drive_id == "test_drive_id_123"
        assert audio_file.filename == "test_recording.m4a"
        assert audio_file.size_bytes == 1024000
        assert audio_file.mime_type == "audio/mp4"
        assert audio_file.processing_status == "detected"

    def test_audio_file_status_updates(self, db_session):
        """Test updating AudioFile status through the service."""
        # Create initial audio file
        drive_file_info = {
            "id": "test_drive_id_456",
            "name": "test_update.m4a",
            "size": "2048000",
            "mimeType": "audio/mp4"
        }

        audio_service = AudioFileService(db_session)
        audio_file = audio_service.create_audio_file(drive_file_info)

        # Test status progression
        audio_file = audio_service.update_status(audio_file, "downloading")
        assert audio_file.processing_status == "downloading"

        audio_file = audio_service.mark_downloaded(audio_file, "/path/to/local/file.m4a")
        assert audio_file.processing_status == "downloaded"
        assert audio_file.local_path == "/path/to/local/file.m4a"

        audio_file = audio_service.mark_error(audio_file, "Test error message")
        assert audio_file.processing_status == "error"
        assert audio_file.error_message == "Test error message"

    def test_get_audio_file_by_drive_id(self, db_session):
        """Test retrieving AudioFile by Google Drive ID."""
        drive_file_info = {
            "id": "unique_drive_id_789",
            "name": "test_retrieve.m4a",
            "size": "512000",
            "mimeType": "audio/mp4"
        }

        audio_service = AudioFileService(db_session)
        created_file = audio_service.create_audio_file(drive_file_info)

        # Retrieve by drive ID
        retrieved_file = audio_service.get_by_drive_id("unique_drive_id_789")

        assert retrieved_file is not None
        assert retrieved_file.id == created_file.id
        assert retrieved_file.drive_id == "unique_drive_id_789"

    def test_file_monitor_completion_detection(self, google_drive_service):
        """Test file completion detection logic."""
        monitor_service = FileMonitorService(google_drive_service)

        # Mock file info
        file_info = {
            "id": "test_completion_file",
            "name": "test_completion.m4a",
            "size": "1000000"
        }

        # First check - file is new
        is_complete = monitor_service.is_file_complete(file_info)
        assert is_complete is False  # Should not be complete immediately

        # File info should be tracked now
        assert "test_completion_file" in monitor_service.file_sizes
        assert monitor_service.file_sizes["test_completion_file"] == 1000000

    @pytest.mark.skipif(
        not os.path.exists(settings.GOOGLE_DRIVE_CREDENTIALS_PATH),
        reason="Google Drive credentials not available"
    )
    def test_real_file_listing(self, google_drive_service, skip_if_no_folder_id):
        """Test listing real files from Google Drive (integration test)."""
        files = google_drive_service.list_audio_files()

        assert isinstance(files, list)

        # If files exist, validate their structure
        for file_info in files:
            assert "id" in file_info
            assert "name" in file_info
            assert "size" in file_info
            assert "mimeType" in file_info

    @pytest.mark.skipif(
        not os.path.exists(settings.GOOGLE_DRIVE_CREDENTIALS_PATH),
        reason="Google Drive credentials not available"
    )
    def test_monitor_folder_changes(self, google_drive_service, skip_if_no_folder_id):
        """Test monitoring folder for changes."""
        monitor_service = FileMonitorService(google_drive_service)

        new_files = monitor_service.scan_for_new_files()

        assert isinstance(new_files, list)

        # Check structure of detected files
        for file_info in new_files:
            assert "id" in file_info
            assert "name" in file_info
            assert "size" in file_info

    def test_file_download_mock(self, google_drive_service, test_audio_storage):
        """Test file download functionality with mocking."""
        with patch.object(google_drive_service, 'get_file_metadata') as mock_metadata, \
             patch('builtins.open'), \
             patch('googleapiclient.http.MediaIoBaseDownload') as mock_download:

            # Mock file metadata
            mock_metadata.return_value = {
                "id": "test_file_id",
                "name": "test_download.m4a"
            }

            # Mock download completion
            mock_downloader = mock_download.return_value
            mock_downloader.next_chunk.return_value = (None, True)

            # Test download
            local_path = os.path.join(test_audio_storage, "test_download.m4a")
            result = google_drive_service.download_file("test_file_id", local_path)

            assert result is True
            mock_metadata.assert_called_once_with("test_file_id")

    def test_audio_file_service_queries(self, db_session):
        """Test various query methods of AudioFileService."""
        audio_service = AudioFileService(db_session)

        # Create test files with different statuses
        test_files = [
            {"id": "file1", "name": "detected.m4a", "status": "detected"},
            {"id": "file2", "name": "downloaded.m4a", "status": "downloaded"},
            {"id": "file3", "name": "complete.m4a", "status": "complete"},
        ]

        created_files = []
        for file_data in test_files:
            drive_info = {
                "id": file_data["id"],
                "name": file_data["name"],
                "size": "1000000",
                "mimeType": "audio/mp4"
            }
            audio_file = audio_service.create_audio_file(drive_info)
            audio_service.update_status(audio_file, file_data["status"])
            created_files.append(audio_file)

        # Test get_by_status
        detected_files = audio_service.get_by_status("detected")
        test_detected_files = [f for f in detected_files if f.filename == "detected.m4a"]
        assert len(test_detected_files) == 1
        assert test_detected_files[0].filename == "detected.m4a"

        # Test get_unprocessed_files
        unprocessed = audio_service.get_unprocessed_files()
        test_unprocessed = [f for f in unprocessed if f.filename in ["detected.m4a", "downloaded.m4a"]]
        assert len(test_unprocessed) == 2  # detected and downloaded

        # Test file_exists
        assert audio_service.file_exists("file1") is True
        assert audio_service.file_exists("nonexistent") is False

        # Test get_all_files
        all_files = audio_service.get_all_files()
        test_created_files = [f for f in all_files if f.filename in ["detected.m4a", "downloaded.m4a", "complete.m4a"]]
        assert len(test_created_files) == 3