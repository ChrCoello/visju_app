import os
import time
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone

try:
    from pydub import AudioSegment
    from pydub.exceptions import CouldntDecodeError
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

try:
    from mutagen import File as MutagenFile
    from mutagen.mp4 import MP4
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

from app.services.file_storage_service import FileStorageService
from app.models.base import ConversionResult
from app.core.logging import get_logger

logger = get_logger()

class AudioConversionService:
    """Service for converting audio files between formats and extracting metadata."""

    def __init__(self):
        self.storage_service = FileStorageService()
        self.supported_input_formats = {'.m4a', '.mp3', '.wav', '.flac', '.aac'}
        self.output_format = 'wav'

    def check_dependencies(self) -> Dict[str, bool]:
        """Check if required dependencies are available."""
        deps = {
            'pydub': PYDUB_AVAILABLE,
            'mutagen': MUTAGEN_AVAILABLE,
            'ffmpeg': self._check_ffmpeg()
        }

        logger.info(f"Dependencies check: {deps}")
        return deps

    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'],
                                  capture_output=True,
                                  timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def extract_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Extract metadata from an audio file using mutagen."""
        if not MUTAGEN_AVAILABLE:
            logger.error("Mutagen not available for metadata extraction")
            return None

        try:
            audio_file = MutagenFile(file_path)
            if audio_file is None:
                logger.warning(f"Could not read metadata from {file_path}")
                return None

            metadata = {
                'filename': Path(file_path).name,
                'file_size_bytes': Path(file_path).stat().st_size,
                'file_size_mb': Path(file_path).stat().st_size / (1024 * 1024),
            }

            # Get duration
            if hasattr(audio_file, 'info') and audio_file.info:
                metadata['duration_seconds'] = getattr(audio_file.info, 'length', 0)
                metadata['bitrate'] = getattr(audio_file.info, 'bitrate', 0)
                metadata['sample_rate'] = getattr(audio_file.info, 'sample_rate', 0)
                metadata['channels'] = getattr(audio_file.info, 'channels', 0)

            # For M4A files, get additional metadata
            if isinstance(audio_file, MP4):
                tags = audio_file.tags or {}
                metadata.update({
                    'format': 'm4a',
                    'codec': 'aac',
                    'title': tags.get('\xa9nam', [None])[0] if '\xa9nam' in tags else None,
                    'artist': tags.get('\xa9ART', [None])[0] if '\xa9ART' in tags else None,
                    'date': tags.get('\xa9day', [None])[0] if '\xa9day' in tags else None,
                })

            logger.info(f"Extracted metadata for {Path(file_path).name}: {metadata.get('duration_seconds', 0):.1f}s")
            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            return None

    def convert_m4a_to_wav(self, input_path: str, output_path: Optional[str] = None) -> ConversionResult:
        """Convert M4A file to WAV format."""
        start_time = time.time()
        input_file = Path(input_path)

        # Validate input file
        if not input_file.exists():
            error_msg = f"Input file does not exist: {input_path}"
            logger.error(error_msg)
            return ConversionResult(
                original_path=input_path,
                converted_path="",
                conversion_duration_ms=0,
                success=False,
                error_message=error_msg
            )

        if input_file.suffix.lower() not in self.supported_input_formats:
            error_msg = f"Unsupported input format: {input_file.suffix}"
            logger.error(error_msg)
            return ConversionResult(
                original_path=input_path,
                converted_path="",
                conversion_duration_ms=0,
                success=False,
                error_message=error_msg
            )

        # Determine output path
        if output_path is None:
            output_path = str(self.storage_service.get_converted_file_path(input_file.name))

        output_file = Path(output_path)

        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Check dependencies
            if not PYDUB_AVAILABLE:
                error_msg = "Pydub not available for audio conversion"
                logger.error(error_msg)
                return ConversionResult(
                    original_path=input_path,
                    converted_path="",
                    conversion_duration_ms=0,
                    success=False,
                    error_message=error_msg
                )

            logger.info(f"Starting conversion: {input_file.name} -> {output_file.name}")

            # Load the audio file
            try:
                audio = AudioSegment.from_file(input_path)
            except CouldntDecodeError as e:
                error_msg = f"Could not decode audio file: {e}"
                logger.error(error_msg)
                return ConversionResult(
                    original_path=input_path,
                    converted_path="",
                    conversion_duration_ms=0,
                    success=False,
                    error_message=error_msg
                )

            # Convert to WAV with standard settings for NB-Whisper
            # NB-Whisper typically works well with 16kHz, 16-bit, mono
            audio = audio.set_frame_rate(16000)  # 16kHz sample rate
            audio = audio.set_channels(1)        # Mono
            audio = audio.set_sample_width(2)    # 16-bit

            # Export as WAV
            audio.export(output_path, format="wav")

            conversion_time = int((time.time() - start_time) * 1000)

            # Validate output file
            if not output_file.exists() or output_file.stat().st_size == 0:
                error_msg = "Conversion failed: output file is empty or missing"
                logger.error(error_msg)
                return ConversionResult(
                    original_path=input_path,
                    converted_path="",
                    conversion_duration_ms=conversion_time,
                    success=False,
                    error_message=error_msg
                )

            logger.info(f"Conversion successful: {input_file.name} -> {output_file.name} ({conversion_time}ms)")

            return ConversionResult(
                original_path=input_path,
                converted_path=output_path,
                conversion_duration_ms=conversion_time,
                success=True,
                error_message=None
            )

        except Exception as e:
            conversion_time = int((time.time() - start_time) * 1000)
            error_msg = f"Conversion error: {e}"
            logger.error(error_msg)

            # Clean up partial output file
            if output_file.exists():
                try:
                    output_file.unlink()
                except:
                    pass

            return ConversionResult(
                original_path=input_path,
                converted_path="",
                conversion_duration_ms=conversion_time,
                success=False,
                error_message=error_msg
            )

    def batch_convert_files(self, input_directory: Optional[str] = None) -> Dict[str, ConversionResult]:
        """Convert all supported audio files in a directory."""
        if input_directory is None:
            input_directory = str(self.storage_service.get_storage_paths()['originals'])

        input_path = Path(input_directory)
        if not input_path.exists():
            logger.error(f"Input directory does not exist: {input_directory}")
            return {}

        results = {}
        audio_files = []

        # Find all audio files
        for file_path in input_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_input_formats:
                audio_files.append(file_path)

        logger.info(f"Found {len(audio_files)} audio files to convert")

        # Convert each file
        for audio_file in audio_files:
            logger.info(f"Converting {audio_file.name}...")
            result = self.convert_m4a_to_wav(str(audio_file))
            results[audio_file.name] = result

        successful = sum(1 for r in results.values() if r.success)
        logger.info(f"Batch conversion completed: {successful}/{len(results)} successful")

        return results

    def get_conversion_stats(self) -> Dict[str, Any]:
        """Get statistics about conversions."""
        paths = self.storage_service.get_storage_paths()
        originals_path = paths['originals']
        converted_path = paths['converted']

        stats = {
            'original_files': 0,
            'converted_files': 0,
            'conversion_ratio': 0.0,
            'dependencies': self.check_dependencies()
        }

        try:
            if originals_path.exists():
                original_files = [f for f in originals_path.iterdir()
                                if f.is_file() and f.suffix.lower() in self.supported_input_formats]
                stats['original_files'] = len(original_files)

            if converted_path.exists():
                converted_files = [f for f in converted_path.iterdir()
                                 if f.is_file() and f.suffix.lower() == '.wav']
                stats['converted_files'] = len(converted_files)

            if stats['original_files'] > 0:
                stats['conversion_ratio'] = stats['converted_files'] / stats['original_files']

        except Exception as e:
            logger.error(f"Error getting conversion stats: {e}")

        return stats

def get_audio_conversion_service() -> AudioConversionService:
    """Get a configured audio conversion service instance."""
    return AudioConversionService()