import time
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from app.services.google_drive_service import GoogleDriveService
from app.services.file_storage_service import FileStorageService
from app.core.logging import get_logger

logger = get_logger()

class FileSyncService:
    """Service for synchronizing files between Google Drive and local storage."""

    def __init__(self):
        self.drive_service = GoogleDriveService()
        self.storage_service = FileStorageService()

    def initialize(self) -> bool:
        """Initialize the sync service by setting up storage and authenticating with Drive."""
        try:
            # Set up local storage structure
            if not self.storage_service.setup_storage_structure():
                logger.error("Failed to set up storage structure")
                return False

            # Authenticate with Google Drive
            if not self.drive_service.authenticate():
                logger.error("Failed to authenticate with Google Drive")
                return False

            logger.info("File sync service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error initializing sync service: {e}")
            return False

    def get_drive_files(self) -> Dict[str, Dict]:
        """Get all audio files from Google Drive."""
        try:
            drive_files = {}
            raw_files = self.drive_service.list_audio_files()

            for file_info in raw_files:
                # Use filename without extension as key for comparison
                file_key = Path(file_info['name']).stem
                drive_files[file_key] = {
                    'id': file_info['id'],
                    'name': file_info['name'],
                    'size': int(file_info.get('size', 0)),
                    'modified_time': file_info.get('modifiedTime'),
                    'created_time': file_info.get('createdTime'),
                    'mime_type': file_info.get('mimeType')
                }

            logger.info(f"Found {len(drive_files)} files on Google Drive")
            return drive_files

        except Exception as e:
            logger.error(f"Error getting Drive files: {e}")
            return {}

    def compare_files(self) -> Dict[str, List[str]]:
        """Compare Drive files with local files and categorize differences."""
        try:
            drive_files = self.get_drive_files()
            local_files = self.storage_service.get_local_files()

            # Get file keys
            drive_keys = set(drive_files.keys())
            local_keys = set(local_files.keys())

            comparison_result = {
                'missing_locally': list(drive_keys - local_keys),
                'missing_on_drive': list(local_keys - drive_keys),
                'present_both': list(drive_keys & local_keys),
                'size_mismatches': []
            }

            # Check for size mismatches in files present in both
            for file_key in comparison_result['present_both']:
                drive_size = drive_files[file_key]['size']
                local_size = local_files[file_key]['size']

                if drive_size != local_size:
                    comparison_result['size_mismatches'].append({
                        'file_key': file_key,
                        'drive_size': drive_size,
                        'local_size': local_size,
                        'filename': drive_files[file_key]['name']
                    })

            logger.info(f"Comparison results:")
            logger.info(f"  Missing locally: {len(comparison_result['missing_locally'])}")
            logger.info(f"  Missing on Drive: {len(comparison_result['missing_on_drive'])}")
            logger.info(f"  Present in both: {len(comparison_result['present_both'])}")
            logger.info(f"  Size mismatches: {len(comparison_result['size_mismatches'])}")

            return comparison_result

        except Exception as e:
            logger.error(f"Error comparing files: {e}")
            return {}

    def download_missing_files(self, max_retries: int = 3) -> Dict[str, bool]:
        """Download files that are missing locally from Google Drive."""
        try:
            comparison = self.compare_files()
            missing_files = comparison.get('missing_locally', [])
            size_mismatches = comparison.get('size_mismatches', [])

            if not missing_files and not size_mismatches:
                logger.info("No files need to be downloaded")
                return {}

            # Get Drive files info
            drive_files = self.get_drive_files()
            download_results = {}

            # Download missing files
            for file_key in missing_files:
                if file_key in drive_files:
                    result = self._download_file_with_retry(
                        drive_files[file_key],
                        max_retries
                    )
                    download_results[file_key] = result

            # Re-download files with size mismatches
            for mismatch in size_mismatches:
                file_key = mismatch['file_key']
                logger.warning(f"Size mismatch for {mismatch['filename']}, re-downloading")

                if file_key in drive_files:
                    result = self._download_file_with_retry(
                        drive_files[file_key],
                        max_retries
                    )
                    download_results[f"{file_key}_rematch"] = result

            logger.info(f"Download completed. Results: {download_results}")
            return download_results

        except Exception as e:
            logger.error(f"Error downloading missing files: {e}")
            return {}

    def _download_file_with_retry(self, file_info: Dict, max_retries: int) -> bool:
        """Download a single file with retry logic."""
        filename = file_info['name']
        file_id = file_info['id']
        local_path = self.storage_service.get_original_file_path(filename)

        for attempt in range(max_retries):
            try:
                logger.info(f"Downloading {filename} (attempt {attempt + 1}/{max_retries})")

                # Download the file
                success = self.drive_service.download_file(file_id, str(local_path))

                if success:
                    # Validate the download
                    if self._validate_download(file_info, local_path):
                        logger.info(f"Successfully downloaded and validated {filename}")
                        return True
                    else:
                        logger.warning(f"Download validation failed for {filename}")
                        # Remove corrupted file
                        if local_path.exists():
                            local_path.unlink()

                # Wait before retry
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)

            except Exception as e:
                logger.error(f"Error downloading {filename} (attempt {attempt + 1}): {e}")

        logger.error(f"Failed to download {filename} after {max_retries} attempts")
        return False

    def _validate_download(self, file_info: Dict, local_path: Path) -> bool:
        """Validate that a downloaded file is complete and correct."""
        try:
            if not local_path.exists():
                logger.error(f"Downloaded file does not exist: {local_path}")
                return False

            # Check file size
            expected_size = file_info['size']
            actual_size = local_path.stat().st_size

            if expected_size != actual_size:
                logger.error(f"Size mismatch: expected {expected_size}, got {actual_size}")
                return False

            # Check if file is readable
            try:
                with open(local_path, 'rb') as f:
                    f.read(1024)  # Read first 1KB to check if file is accessible
            except Exception as e:
                logger.error(f"File is not readable: {e}")
                return False

            logger.info(f"File validation passed for {local_path.name}")
            return True

        except Exception as e:
            logger.error(f"Error validating download: {e}")
            return False

    def sync_status(self) -> Dict:
        """Get current synchronization status."""
        try:
            comparison = self.compare_files()
            storage_stats = self.storage_service.get_storage_stats()

            status = {
                'sync_comparison': comparison,
                'storage_stats': storage_stats,
                'timestamp': time.time(),
                'is_synced': len(comparison.get('missing_locally', [])) == 0 and
                           len(comparison.get('size_mismatches', [])) == 0
            }

            return status

        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {}

    def full_sync(self) -> Dict:
        """Perform a complete synchronization of Drive files to local storage."""
        try:
            logger.info("Starting full synchronization...")

            # Initialize if needed
            if not self.initialize():
                return {'success': False, 'error': 'Failed to initialize sync service'}

            # Get initial status
            initial_status = self.sync_status()

            # Download missing files
            download_results = self.download_missing_files()

            # Get final status
            final_status = self.sync_status()

            result = {
                'success': True,
                'initial_status': initial_status,
                'download_results': download_results,
                'final_status': final_status,
                'files_downloaded': len([r for r in download_results.values() if r])
            }

            logger.info(f"Full sync completed. Downloaded {result['files_downloaded']} files")
            return result

        except Exception as e:
            logger.error(f"Error during full sync: {e}")
            return {'success': False, 'error': str(e)}

def get_file_sync_service() -> FileSyncService:
    """Get a configured file sync service instance."""
    return FileSyncService()