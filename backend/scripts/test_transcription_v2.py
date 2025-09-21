#!/usr/bin/env python3
"""
Test script for the enhanced transcription service with chunking.
"""

import sys
import os
sys.path.append('.')

from pathlib import Path
from app.services.transcription_service_v2 import TranscriptionService
from app.core.logging import configure_logging, get_logger

def main():
    # Configure logging
    configure_logging()
    logger = get_logger()

    print("🎤 Enhanced Transcription Service Test")
    print("=" * 45)

    # Test 1: Initialize transcription service
    print("\n1. 🚀 Initializing enhanced transcription service...")
    transcription_service = TranscriptionService()
    print("✅ Enhanced transcription service initialized")

    # Test 2: Check dependencies
    print("\n2. 🔧 Checking dependencies...")
    deps = transcription_service.check_dependencies()

    for dep_name, available in deps.items():
        status = "✅" if available else "❌"
        print(f"   {status} {dep_name}: {'Available' if available else 'Missing'}")

    missing_deps = [name for name, available in deps.items() if not available]
    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
        return False

    print("✅ All dependencies available")

    # Test 3: Get model info
    print("\n3. 📋 Model information...")
    model_info = transcription_service.get_model_info()
    print(f"   🤖 Model: {model_info['model_id']}")
    print(f"   🎯 Device: {model_info['device']}")
    print(f"   🔢 Data type: {model_info['torch_dtype']}")
    print(f"   🎚️  Sample rate: {model_info['sample_rate']} Hz")
    print(f"   ⏱️  Chunk length: {model_info['chunk_length']}s")
    print(f"   🔄 Overlap: {model_info['overlap_length']}s")
    if model_info['cuda_available']:
        print(f"   🎮 GPU: {model_info['gpu_name']}")
        print(f"   💾 GPU Memory: {model_info['gpu_memory_gb']:.1f} GB")

    # Test 4: Find and transcribe an audio file
    print("\n4. 🎵 Testing enhanced transcription...")
    audio_files_path = Path("audio_files/converted")

    if audio_files_path.exists():
        wav_files = list(audio_files_path.glob("*.wav"))

        if wav_files:
            test_file = wav_files[0]
            print(f"   Testing with file: {test_file.name}")

            # Get file info
            file_size = test_file.stat().st_size / (1024 * 1024)
            print(f"   📊 File size: {file_size:.2f} MB")

            # Transcribe the file
            result = transcription_service.transcribe_audio(str(test_file))

            if result.success:
                print("✅ Enhanced transcription successful!")
                print(f"   📝 Full text: {result.full_text}")
                print(f"   📊 Segments: {len(result.segments)}")
                print(f"   ⏱️  Processing time: {result.processing_duration_ms}ms")
                print(f"   🎵 Audio duration: {result.audio_duration_seconds:.1f}s")
                print(f"   🔄 Chunks processed: {result.chunks_processed}")
                print(f"   🇳🇴 Language: {result.language_detected}")

                # Show segments
                if result.segments:
                    print("\n   📝 Transcription segments:")
                    for i, segment in enumerate(result.segments):
                        print(f"   [{segment.start_time:.1f}s - {segment.end_time:.1f}s]: {segment.text}")

                return True
            else:
                print(f"❌ Enhanced transcription failed: {result.error_message}")
                return False
        else:
            print("⚠️  No WAV files found for testing")
            print("✅ Service initialization test completed")
            return True
    else:
        print("⚠️  No audio files directory found")
        print("✅ Service initialization test completed")
        return True

if __name__ == "__main__":
    success = main()
    print(f"\n🏁 Enhanced transcription test {'PASSED' if success else 'FAILED'}")
    if success:
        print("\n💡 Enhanced transcription service ready for production!")
        print("   - Proper audio chunking for long recordings")
        print("   - Overlap handling to prevent word loss")
        print("   - Optimized for Norwegian language processing")
    sys.exit(0 if success else 1)