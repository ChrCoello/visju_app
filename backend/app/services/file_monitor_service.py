import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Set
from app.services.google_drive_service import GoogleDriveService
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger()

class FileMonitorService:
    """Service to monitor Google Drive folder for new audio files and detect completion."""

    def __init__(self, drive_service: GoogleDriveService):
        self.drive_service = drive_service
        self.known_files: Set[str] = set()
        self.file_sizes: Dict[str, int] = {}
        self.file_timestamps: Dict[str, datetime] = {}
        self.completion_wait_seconds = 60  # Wait 60 seconds to ensure file is complete

    def is_file_complete(self, file_info: Dict) -> bool:
        """
        Detect if a file upload is complete by checking if size has stabilized.
        Returns True if file appears to be completely uploaded.
        """
        file_id = file_info['id']
        current_size = int(file_info.get('size', 0))
        current_time = datetime.now()

        # If we've seen this file before
        if file_id in self.file_sizes:
            previous_size = self.file_sizes[file_id]
            previous_time = self.file_timestamps[file_id]

            # If size hasn't changed and enough time has passed
            if (current_size == previous_size and
                current_time - previous_time > timedelta(seconds=self.completion_wait_seconds)):

                logger.info(f"File {file_info['name']} appears complete (stable for {self.completion_wait_seconds}s)")
                return True

            # If size has changed, update timestamp
            elif current_size != previous_size:
                logger.info(f"File {file_info['name']} still uploading (size changed: {previous_size} -> {current_size})")
                self.file_timestamps[file_id] = current_time

        else:
            # First time seeing this file
            logger.info(f"New file detected: {file_info['name']} (size: {current_size} bytes)")
            self.file_timestamps[file_id] = current_time

        # Update size tracking
        self.file_sizes[file_id] = current_size
        return False

    def scan_for_new_files(self) -> List[Dict]:
        """Scan the Google Drive folder for new complete audio files."""
        try:
            # Get current files from Drive
            current_files = self.drive_service.list_audio_files()

            new_complete_files = []

            for file_info in current_files:
                file_id = file_info['id']

                # Check if file is complete
                if self.is_file_complete(file_info):
                    # Check if this is a new file we haven't processed
                    if file_id not in self.known_files:
                        logger.info(f"New complete file ready for processing: {file_info['name']}")
                        new_complete_files.append(file_info)
                        self.known_files.add(file_id)

            return new_complete_files

        except Exception as e:
            logger.error(f"Error scanning for new files: {e}")
            return []

    async def start_monitoring(self, check_interval_seconds: int = 30):
        """Start continuous monitoring of the Google Drive folder."""
        logger.info(f"Starting file monitoring (checking every {check_interval_seconds} seconds)")

        while True:
            try:
                new_files = self.scan_for_new_files()

                if new_files:
                    logger.info(f"Found {len(new_files)} new complete files")
                    # Here you would trigger the download and processing pipeline
                    for file_info in new_files:
                        await self.process_new_file(file_info)

                await asyncio.sleep(check_interval_seconds)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(check_interval_seconds)

    async def process_new_file(self, file_info: Dict):
        """Process a newly detected complete file."""
        try:
            logger.info(f"Processing new file: {file_info['name']}")

            # Create local file path
            local_filename = f"{file_info['id']}_{file_info['name']}"
            local_path = f"{settings.AUDIO_STORAGE_PATH}{local_filename}"

            # Download the file
            success = self.drive_service.download_file(file_info['id'], local_path)

            if success:
                logger.info(f"Successfully downloaded {file_info['name']} to {local_path}")
                # Here you would create database record and trigger further processing
                return {
                    'file_id': file_info['id'],
                    'local_path': local_path,
                    'status': 'downloaded'
                }
            else:
                logger.error(f"Failed to download {file_info['name']}")
                return {
                    'file_id': file_info['id'],
                    'status': 'download_failed'
                }

        except Exception as e:
            logger.error(f"Error processing file {file_info['name']}: {e}")
            return {
                'file_id': file_info['id'],
                'status': 'error',
                'error': str(e)
            }

def get_file_monitor_service() -> FileMonitorService:
    """Get a configured file monitor service instance."""
    drive_service = GoogleDriveService()
    drive_service.authenticate()
    return FileMonitorService(drive_service)