import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session as DBSession
from app.models.db_models import AudioFile
from app.services.database_service import DatabaseService
from app.core.logging import get_logger

logger = get_logger()

class AudioFileService:
    """Service for managing AudioFile database operations."""

    def __init__(self, db: DBSession):
        self.db_service = DatabaseService(db)

    def create_audio_file(self, drive_file_info: Dict[str, Any]) -> AudioFile:
        """Create a new AudioFile record from Google Drive file info."""
        try:
            # Generate unique ID
            file_id = str(uuid.uuid4())

            # Parse timestamps
            upload_timestamp = None
            modified_time = None

            if 'createdTime' in drive_file_info:
                upload_timestamp = datetime.fromisoformat(
                    drive_file_info['createdTime'].replace('Z', '+00:00')
                )

            if 'modifiedTime' in drive_file_info:
                modified_time = datetime.fromisoformat(
                    drive_file_info['modifiedTime'].replace('Z', '+00:00')
                )

            audio_file = self.db_service.create(
                AudioFile,
                id=file_id,
                drive_id=drive_file_info['id'],
                filename=drive_file_info['name'],
                size_bytes=int(drive_file_info.get('size', 0)),
                upload_timestamp=upload_timestamp,
                modified_time=modified_time,
                mime_type=drive_file_info.get('mimeType'),
                status="detected",
                processing_status="detected"
            )

            logger.info(f"Created AudioFile record for {drive_file_info['name']}")
            return audio_file

        except Exception as e:
            logger.error(f"Error creating AudioFile record: {e}")
            raise

    def get_by_drive_id(self, drive_id: str) -> Optional[AudioFile]:
        """Get AudioFile by Google Drive file ID."""
        try:
            return self.db_service.db.query(AudioFile).filter(
                AudioFile.drive_id == drive_id
            ).first()
        except Exception as e:
            logger.error(f"Error getting AudioFile by drive_id {drive_id}: {e}")
            return None

    def get_by_status(self, status: str) -> List[AudioFile]:
        """Get AudioFiles by processing status."""
        try:
            return self.db_service.db.query(AudioFile).filter(
                AudioFile.processing_status == status
            ).all()
        except Exception as e:
            logger.error(f"Error getting AudioFiles by status {status}: {e}")
            return []

    def update_status(self, audio_file: AudioFile, status: str, **kwargs) -> AudioFile:
        """Update AudioFile status and other fields."""
        try:
            update_data = {"processing_status": status}
            update_data.update(kwargs)

            updated_file = self.db_service.update(audio_file, **update_data)
            logger.info(f"Updated AudioFile {audio_file.filename} status to {status}")
            return updated_file

        except Exception as e:
            logger.error(f"Error updating AudioFile status: {e}")
            raise

    def mark_downloaded(self, audio_file: AudioFile, local_path: str) -> AudioFile:
        """Mark an AudioFile as successfully downloaded."""
        return self.update_status(
            audio_file,
            "downloaded",
            local_path=local_path
        )

    def mark_error(self, audio_file: AudioFile, error_message: str) -> AudioFile:
        """Mark an AudioFile as having an error."""
        return self.update_status(
            audio_file,
            "error",
            error_message=error_message
        )

    def get_unprocessed_files(self) -> List[AudioFile]:
        """Get all files that haven't been fully processed."""
        try:
            return self.db_service.db.query(AudioFile).filter(
                AudioFile.processing_status.in_(["detected", "downloading", "downloaded"])
            ).all()
        except Exception as e:
            logger.error(f"Error getting unprocessed files: {e}")
            return []

    def file_exists(self, drive_id: str) -> bool:
        """Check if an AudioFile already exists for a given Drive ID."""
        return self.get_by_drive_id(drive_id) is not None

    def get_all_files(self, limit: Optional[int] = None) -> List[AudioFile]:
        """Get all AudioFiles with optional limit."""
        return self.db_service.get_all(AudioFile, limit=limit)

    def delete_audio_file(self, audio_file: AudioFile) -> bool:
        """Delete an AudioFile record."""
        try:
            self.db_service.delete(audio_file)
            logger.info(f"Deleted AudioFile record for {audio_file.filename}")
            return True
        except Exception as e:
            logger.error(f"Error deleting AudioFile: {e}")
            return False