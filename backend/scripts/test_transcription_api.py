#!/usr/bin/env python3
"""
Test script for the transcription API endpoint.
"""

import sys
import os
sys.path.append('.')

import requests
import json
from pathlib import Path
from app.core.logging import configure_logging, get_logger

def main():
    # Configure logging
    configure_logging()
    logger = get_logger()

    print("🎤 Transcription API Test")
    print("=" * 30)

    # API base URL
    base_url = "http://localhost:8000/api/v1/transcription"

    # Test 1: Check transcription service status
    print("\n1. 🔧 Checking transcription service status...")
    try:
        response = requests.get(f"{base_url}/status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"   ✅ Status: {status_data['status']}")
            print(f"   🤖 Model: {status_data['model_info']['model_id']}")
            print(f"   🎯 Device: {status_data['model_info']['device']}")
        else:
            print(f"   ❌ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error checking status: {e}")
        return False

    # Test 2: Check available models
    print("\n2. 📋 Checking available models...")
    try:
        response = requests.get(f"{base_url}/models")
        if response.status_code == 200:
            models_data = response.json()
            print(f"   ✅ Current model: {models_data['current_model']}")
            print(f"   🇳🇴 Language: {models_data['language']}")
        else:
            print(f"   ❌ Models check failed: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Error checking models: {e}")

    # Test 3: Find a test file
    print("\n3. 🎵 Finding test audio file...")
    test_files = [
        "Random-sample.wav",
        "Test-discussion.wav",
        "20250914_test.wav"
    ]

    test_file = None
    for filename in test_files:
        if Path(f"audio_files/converted/{filename}").exists():
            test_file = filename
            print(f"   ✅ Found test file: {filename}")
            break

    if not test_file:
        print("   ⚠️  No test files found, using first available file")
        converted_path = Path("audio_files/converted")
        if converted_path.exists():
            wav_files = list(converted_path.glob("*.wav"))
            if wav_files:
                test_file = wav_files[0].name
                print(f"   ✅ Using: {test_file}")

    if not test_file:
        print("   ❌ No WAV files found for testing")
        return False

    # Test 4: Transcribe the audio file
    print(f"\n4. 🔊 Testing transcription with {test_file}...")
    try:
        response = requests.post(f"{base_url}/transcribe/{test_file}")

        if response.status_code == 200:
            result = response.json()
            print("   ✅ Transcription successful!")
            print(f"   📝 Session ID: {result['session_id']}")
            print(f"   📝 Full text: {result['full_text']}")
            print(f"   📊 Segments: {result['segments_count']}")
            print(f"   ⏱️  Processing time: {result['processing_duration_ms']}ms")
            print(f"   🎵 Audio duration: {result['audio_duration_seconds']:.1f}s")
            print(f"   🔄 Chunks processed: {result['chunks_processed']}")
            print(f"   🤖 Model used: {result['model_used']}")

            # Test 5: Try transcribing the same file again (should return existing result)
            print(f"\n5. 🔄 Testing duplicate transcription...")
            response2 = requests.post(f"{base_url}/transcribe/{test_file}")
            if response2.status_code == 200:
                result2 = response2.json()
                if result2['session_id'] == result['session_id']:
                    print("   ✅ Correctly returned existing transcription")
                else:
                    print("   ⚠️  Created new session instead of using existing")
            else:
                print(f"   ❌ Duplicate test failed: {response2.status_code}")

            return True

        elif response.status_code == 404:
            print(f"   ❌ File not found: {test_file}")
            return False
        else:
            print(f"   ❌ Transcription failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   ❌ Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   ❌ Raw response: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Error during transcription: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n🏁 Transcription API test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)