import os
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Set
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger()

class FileStorageService:
    """Service for managing local file storage and synchronization."""

    def __init__(self):
        self.audio_storage_path = Path(settings.AUDIO_STORAGE_PATH)
        self.temp_storage_path = Path(settings.TEMP_PROCESSING_PATH)

    def setup_storage_structure(self) -> bool:
        """Create the local file storage directory structure."""
        try:
            # Create main audio storage directory
            self.audio_storage_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created audio storage directory: {self.audio_storage_path}")

            # Create subdirectories for organization
            subdirs = [
                "originals",      # Original M4A files from Drive
                "converted",      # WAV files for processing
                "processed",      # Processed/transcribed files
                "temp"           # Temporary files during processing
            ]

            for subdir in subdirs:
                subdir_path = self.audio_storage_path / subdir
                subdir_path.mkdir(exist_ok=True)
                logger.info(f"Created subdirectory: {subdir_path}")

            # Create temp processing directory
            self.temp_storage_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created temp processing directory: {self.temp_storage_path}")

            return True

        except Exception as e:
            logger.error(f"Error setting up storage structure: {e}")
            return False

    def get_local_files(self) -> Dict[str, Dict]:
        """Get all audio files currently in local storage."""
        try:
            local_files = {}
            originals_path = self.audio_storage_path / "originals"

            if not originals_path.exists():
                logger.warning(f"Originals directory does not exist: {originals_path}")
                return local_files

            # Scan for audio files
            audio_extensions = {'.m4a', '.mp3', '.wav'}

            for file_path in originals_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                    file_info = {
                        'path': str(file_path),
                        'size': file_path.stat().st_size,
                        'modified_time': file_path.stat().st_mtime,
                        'filename': file_path.name
                    }

                    # Use filename as key (without extension for comparison)
                    file_key = file_path.stem
                    local_files[file_key] = file_info

            logger.info(f"Found {len(local_files)} local audio files")
            return local_files

        except Exception as e:
            logger.error(f"Error scanning local files: {e}")
            return {}

    def get_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate MD5 hash of a file for integrity checking."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return None

    def get_storage_paths(self) -> Dict[str, Path]:
        """Get all storage directory paths."""
        return {
            'audio_storage': self.audio_storage_path,
            'originals': self.audio_storage_path / "originals",
            'converted': self.audio_storage_path / "converted",
            'processed': self.audio_storage_path / "processed",
            'temp': self.audio_storage_path / "temp",
            'temp_processing': self.temp_storage_path
        }

    def get_original_file_path(self, filename: str) -> Path:
        """Get the full path for an original audio file."""
        return self.audio_storage_path / "originals" / filename

    def get_converted_file_path(self, filename: str) -> Path:
        """Get the full path for a converted audio file."""
        # Replace extension with .wav
        base_name = Path(filename).stem
        return self.audio_storage_path / "converted" / f"{base_name}.wav"

    def file_exists_locally(self, filename: str) -> bool:
        """Check if a file exists in local storage."""
        original_path = self.get_original_file_path(filename)
        return original_path.exists()

    def get_storage_stats(self) -> Dict[str, int]:
        """Get statistics about local storage usage."""
        try:
            stats = {}
            paths = self.get_storage_paths()

            for category, path in paths.items():
                if path.exists():
                    files = list(path.glob("*"))
                    stats[category] = {
                        'file_count': len([f for f in files if f.is_file()]),
                        'total_size_mb': sum(f.stat().st_size for f in files if f.is_file()) / (1024 * 1024)
                    }
                else:
                    stats[category] = {'file_count': 0, 'total_size_mb': 0}

            return stats

        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}

def get_file_storage_service() -> FileStorageService:
    """Get a configured file storage service instance."""
    return FileStorageService()