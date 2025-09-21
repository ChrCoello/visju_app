#!/usr/bin/env python3
"""
Test script for audio conversion functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from pathlib import Path
from app.services.audio_conversion_service import AudioConversionService
from app.core.logging import configure_logging, get_logger

def main():
    # Configure logging
    configure_logging()
    logger = get_logger()

    print("🎵 Testing Audio Conversion System")
    print("=" * 50)

    # Test 1: Initialize conversion service
    print("\n1. 🚀 Initializing conversion service...")
    conversion_service = AudioConversionService()
    print("✅ Conversion service initialized")

    # Test 2: Check dependencies
    print("\n2. 🔧 Checking dependencies...")
    deps = conversion_service.check_dependencies()

    for dep_name, available in deps.items():
        status = "✅" if available else "❌"
        print(f"   {status} {dep_name}: {'Available' if available else 'Missing'}")

    missing_deps = [name for name, available in deps.items() if not available]
    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
        if 'ffmpeg' in missing_deps:
            print("   Install FFmpeg with: sudo apt install ffmpeg")
        return False

    print("✅ All dependencies available")

    # Test 3: Get conversion statistics
    print("\n3. 📊 Getting conversion statistics...")
    stats = conversion_service.get_conversion_stats()
    print(f"   📂 Original files: {stats['original_files']}")
    print(f"   🔄 Converted files: {stats['converted_files']}")
    print(f"   📈 Conversion ratio: {stats['conversion_ratio']:.2%}")

    if stats['original_files'] == 0:
        print("⚠️  No audio files found to test conversion")
        print("   Please ensure there are audio files in the originals directory")
        return False

    # Test 4: Get metadata from an original file
    print("\n4. 📋 Testing metadata extraction...")
    originals_path = conversion_service.storage_service.get_storage_paths()['originals']

    # Find first audio file
    test_file = None
    for file_path in originals_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in conversion_service.supported_input_formats:
            test_file = file_path
            break

    if test_file:
        print(f"   Testing with file: {test_file.name}")
        metadata = conversion_service.extract_metadata(str(test_file))

        if metadata:
            print("✅ Metadata extraction successful")
            print(f"   📏 Duration: {metadata.get('duration_seconds', 0):.1f} seconds")
            print(f"   📊 Size: {metadata.get('file_size_mb', 0):.2f} MB")
            print(f"   🎚️  Sample rate: {metadata.get('sample_rate', 0)} Hz")
            print(f"   🔊 Channels: {metadata.get('channels', 0)}")
        else:
            print("❌ Metadata extraction failed")
    else:
        print("❌ No test file found")

    # Test 5: Convert a single file
    if test_file:
        print(f"\n5. 🔄 Testing conversion of {test_file.name}...")

        response = input(f"Convert {test_file.name} to WAV? (y/N): ")
        if response.lower() == 'y':
            print("🔄 Starting conversion...")

            result = conversion_service.convert_m4a_to_wav(str(test_file))

            if result.success:
                print("✅ Conversion successful!")
                print(f"   📁 Output: {result.converted_path}")
                print(f"   ⏱️  Duration: {result.conversion_duration_ms}ms")

                # Verify output file
                output_path = Path(result.converted_path)
                if output_path.exists():
                    output_size = output_path.stat().st_size / (1024 * 1024)
                    print(f"   📊 Output size: {output_size:.2f} MB")

                    # Get metadata of converted file
                    converted_metadata = conversion_service.extract_metadata(str(output_path))
                    if converted_metadata:
                        print(f"   🎚️  Converted sample rate: {converted_metadata.get('sample_rate', 0)} Hz")
                        print(f"   🔊 Converted channels: {converted_metadata.get('channels', 0)}")
            else:
                print(f"❌ Conversion failed: {result.error_message}")
        else:
            print("⏭️  Skipping conversion test")

    # Test 6: Show final statistics
    print("\n6. 📈 Final conversion statistics...")
    final_stats = conversion_service.get_conversion_stats()
    print(f"   📂 Original files: {final_stats['original_files']}")
    print(f"   🔄 Converted files: {final_stats['converted_files']}")
    print(f"   📈 Conversion ratio: {final_stats['conversion_ratio']:.2%}")

    if final_stats['conversion_ratio'] > 0:
        print("✅ Audio conversion system is working!")
    else:
        print("ℹ️  No conversions performed in this test")

    print("\n🎉 Audio conversion test completed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)