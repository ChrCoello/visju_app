#!/usr/bin/env python3
"""
Simple automated test for audio conversion functionality.
"""

import sys
import os
sys.path.append('.')

from pathlib import Path
from app.services.audio_conversion_service import AudioConversionService
from app.core.logging import configure_logging, get_logger

def main():
    # Configure logging
    configure_logging()
    logger = get_logger()

    print("🎵 Simple Audio Conversion Test")
    print("=" * 40)

    # Initialize conversion service
    conversion_service = AudioConversionService()

    # Check dependencies
    deps = conversion_service.check_dependencies()
    print(f"Dependencies: {deps}")

    if not all(deps.values()):
        print("❌ Missing dependencies")
        return False

    # Get stats
    stats = conversion_service.get_conversion_stats()
    print(f"📊 Original files: {stats['original_files']}")
    print(f"📊 Converted files: {stats['converted_files']}")

    if stats['original_files'] == 0:
        print("⚠️  No audio files found")
        return False

    # Find first audio file and convert it
    originals_path = conversion_service.storage_service.get_storage_paths()['originals']

    for file_path in originals_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in conversion_service.supported_input_formats:
            print(f"🔄 Converting {file_path.name}...")

            result = conversion_service.convert_m4a_to_wav(str(file_path))

            if result.success:
                print(f"✅ Success! Output: {result.converted_path}")
                print(f"⏱️  Duration: {result.conversion_duration_ms}ms")

                # Check output file exists
                if Path(result.converted_path).exists():
                    output_size = Path(result.converted_path).stat().st_size / (1024 * 1024)
                    print(f"📊 Output size: {output_size:.2f} MB")
                    return True
            else:
                print(f"❌ Failed: {result.error_message}")
                return False

            break

    print("❌ No suitable file found to convert")
    return False

if __name__ == "__main__":
    success = main()
    print(f"\n🏁 Test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)