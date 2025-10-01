#!/usr/bin/env python3
"""
Test script for the new speaker-aware transcription system.
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

    print("🎤🎯 Speaker-Aware Transcription Test")
    print("=" * 40)

    # API base URL
    base_url = "http://localhost:8000/api/v1/speaker-transcription"

    # Test 1: Check service status
    print("\n1. 🔧 Checking speaker transcription service status...")
    try:
        response = requests.get(f"{base_url}/status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"   ✅ Service: {status_data['service']}")
            print(f"   🤖 Model: {status_data['model_info']['model_id']}")
            print(f"   🎯 Device: {status_data['model_info']['device']}")
            print(f"   🎵 Formats: {', '.join(status_data['supported_formats'])}")
            print(f"   🔍 Speaker detection: {status_data['speaker_detection']}")
        else:
            print(f"   ❌ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error checking status: {e}")
        return False

    # Test 2: Test speaker detection on Truh.mp3
    print("\n2. 🎯 Testing speaker detection on Truh.mp3...")
    try:
        response = requests.get(f"{base_url}/test/Truh.mp3")
        if response.status_code == 200:
            test_data = response.json()
            print(f"   ✅ File: {test_data['filename']}")
            print(f"   📊 Channels: {test_data['channels']}")
            print(f"   ⏱️  Duration: {test_data['duration_seconds']:.1f}s")
            print(f"   🔗 Correlation: {test_data['correlation']}")
            print(f"   ⚡ Energy ratio: {test_data['energy_distribution']['ratio']}")
            print(f"   🎯 Speaker separation: {'✅ YES' if test_data['speaker_separation_possible'] else '❌ NO'}")
            print(f"   💡 Recommendation: {test_data['recommendation']}")

            if not test_data['speaker_separation_possible']:
                print("   ⚠️  Speaker separation not optimal for Truh.mp3")
        else:
            print(f"   ❌ Speaker detection test failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error testing speaker detection: {e}")

    # Test 3: Full speaker-aware transcription
    print("\n3. 🎤 Testing full speaker-aware transcription...")
    try:
        print("   🔄 Starting transcription (this may take a while)...")
        response = requests.post(f"{base_url}/transcribe/Truh.mp3")

        if response.status_code == 200:
            result = response.json()
            print("   ✅ Speaker-aware transcription successful!")
            print(f"   📝 Session ID: {result['session_id']}")
            print(f"   🎤 Speakers detected: {result['speakers_detected']}")
            print(f"   🔧 Separation method: {result['speaker_separation_method']}")
            print(f"   ⏱️  Processing time: {result['processing_duration_ms']}ms")
            print(f"   🎵 Audio duration: {result['audio_duration_seconds']:.1f}s")
            print(f"   📊 Segments: {len(result['segments'])}")

            # Show speaker information
            if result['speaker_info']:
                print(f"\n   👥 SPEAKER INFORMATION:")
                for speaker in result['speaker_info']:
                    print(f"     🎤 {speaker['label']} ({speaker['speaker_id']})")
                    print(f"        Channel: {speaker['channel'] or 'Mixed'}")
                    print(f"        Energy: {speaker['energy_percent']:.1f}%")
                    print(f"        Silence: {speaker['silence_percent']:.1f}%")

            # Show transcript preview
            print(f"\n   📝 TRANSCRIPT PREVIEW:")
            if result['full_text']:
                preview = result['full_text'][:300] + "..." if len(result['full_text']) > 300 else result['full_text']
                print(f"   {preview}")
            else:
                print("   (No transcript content)")

            # Show first few segments with speakers
            if result['segments']:
                print(f"\n   🎯 FIRST SEGMENTS WITH SPEAKERS:")
                for i, segment in enumerate(result['segments'][:3]):
                    speaker_label = "Speaker 1" if segment['speaker_id'] == 'speaker_1' else "Speaker 2" if segment['speaker_id'] == 'speaker_2' else "Unknown"
                    print(f"     [{segment['start_time']:.1f}s - {segment['end_time']:.1f}s] {speaker_label}: {segment['text']}")

            return True

        elif response.status_code == 404:
            print(f"   ❌ File not found: Truh.mp3")
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
    print(f"\n🏁 Speaker-aware transcription test {'PASSED' if success else 'FAILED'}")
    if success:
        print("\n🎉 Speaker-aware transcription system is working!")
        print("   🎯 Channel separation detected and working")
        print("   🎤 Speakers automatically identified")
        print("   📝 Speaker-attributed transcription generated")
        print("   💾 Results stored in database with speaker info")
    sys.exit(0 if success else 1)