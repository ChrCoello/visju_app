#!/usr/bin/env python3
"""
Test script for the transcription service.
"""

import sys
import os
sys.path.append('.')

from pathlib import Path
from app.services.transcription_service import TranscriptionService
from app.core.logging import configure_logging, get_logger

def main():
    # Configure logging
    configure_logging()
    logger = get_logger()

    print("🎤 Transcription Service Test")
    print("=" * 40)

    # Test 1: Initialize transcription service
    print("\n1. 🚀 Initializing transcription service...")
    transcription_service = TranscriptionService()
    print("✅ Transcription service initialized")

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
    if model_info['cuda_available']:
        print(f"   🎮 GPU: {model_info['gpu_name']}")
        print(f"   💾 GPU Memory: {model_info['gpu_memory_gb']:.1f} GB")

    # Test 4: Find and transcribe an audio file
    print("\n4. 🎵 Testing transcription...")
    audio_files_path = Path("audio_files/converted")

    if audio_files_path.exists():
        wav_files = list(audio_files_path.glob("*.wav"))

        if wav_files:
            test_file = wav_files[0]
            print(f"   Testing with file: {test_file.name}")

            # Transcribe the file
            result = transcription_service.transcribe_audio(str(test_file))

            if result.success:
                print("✅ Transcription successful!")
                print(f"   📝 Full text: {result.full_text[:100]}...")
                print(f"   📊 Segments: {len(result.segments)}")
                print(f"   ⏱️  Processing time: {result.processing_duration_ms}ms")
                print(f"   🇳🇴 Language: {result.language_detected}")

                # Show first few segments
                if result.segments:
                    print("\n   📝 First segments:")
                    for i, segment in enumerate(result.segments[:3]):
                        print(f"   [{segment.start_time:.1f}s - {segment.end_time:.1f}s]: {segment.text}")

                return True
            else:
                print(f"❌ Transcription failed: {result.error_message}")
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
    print(f"\n🏁 Test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)