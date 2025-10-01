#!/usr/bin/env python3
"""
Test speaker diarization capabilities for mono recordings.
"""

import sys
import os
sys.path.append('.')

from pathlib import Path
from app.core.logging import configure_logging, get_logger

def test_speaker_diarization_options():
    configure_logging()
    logger = get_logger()

    print("🎯 Speaker Diarization Options for Mono Recordings")
    print("=" * 55)

    print("\n📊 ANALYSIS OF YOUR RECORDINGS:")
    print("- Format: Mono M4A files (single channel)")
    print("- Source: Røde Wireless Me → Easy Voice Recorder → Mixed signal")
    print("- Challenge: No channel separation to distinguish speakers")

    print("\n🛠️  AVAILABLE SOLUTIONS:")

    print("\n1. 🤖 pyannote.audio (RECOMMENDED)")
    print("   ✅ Best-in-class speaker diarization")
    print("   ✅ Works with mono recordings")
    print("   ✅ Can identify 2+ speakers automatically")
    print("   ✅ Provides timestamps for speaker changes")
    print("   ⚠️  Requires HuggingFace token (free)")
    print("   ⚠️  ~500MB model download")

    print("\n2. 🔊 Voice Activity Detection + Energy Analysis")
    print("   ✅ Lightweight approach")
    print("   ✅ Can detect speech segments")
    print("   ⚠️  Cannot distinguish between speakers")
    print("   ⚠️  Only detects when someone is speaking")

    print("\n3. 🎵 Audio Feature Analysis")
    print("   ✅ Analyze pitch, formants, spectral features")
    print("   ✅ Can group similar voice characteristics")
    print("   ⚠️  Requires manual tuning")
    print("   ⚠️  Less accurate than deep learning")

    print("\n4. 📝 Manual Speaker Labeling")
    print("   ✅ 100% accurate when done correctly")
    print("   ✅ Can be integrated into web interface")
    print("   ⚠️  Requires manual work for each recording")

    print("\n💡 RECOMMENDED APPROACH:")
    print("Combine pyannote.audio diarization with manual correction:")
    print("1. 🤖 Auto-detect speakers with pyannote.audio")
    print("2. 📝 Allow manual speaker labeling in web interface")
    print("3. 🧠 Learn from corrections to improve future detection")

    print("\n🎯 FOR YOUR USE CASE (Historical Interviews):")
    print("- Usually 1-2 speakers (interviewer + historian)")
    print("- Can pre-label known speakers (e.g., 'Interviewer', 'Historian')")
    print("- pyannote.audio should work very well")

    print("\n📋 IMPLEMENTATION PLAN:")
    print("1. Install pyannote.audio and dependencies")
    print("2. Test speaker diarization on your sample files")
    print("3. Integrate with transcription service")
    print("4. Add speaker labeling to database models")
    print("5. Update web interface to show speaker attribution")

    # Check if we can test pyannote.audio
    try:
        import torch
        print(f"\n✅ PyTorch available: {torch.__version__}")
        print("   Ready for pyannote.audio installation")
    except ImportError:
        print("\n❌ PyTorch not available")

    # Check available audio files for testing
    audio_path = Path("audio_files/converted")
    if audio_path.exists():
        wav_files = list(audio_path.glob("*.wav"))
        print(f"\n📁 Test files available: {len(wav_files)} WAV files")
        if wav_files:
            print("   Ready for speaker diarization testing")
    else:
        print("\n⚠️  No converted WAV files found for testing")

if __name__ == "__main__":
    test_speaker_diarization_options()