#!/usr/bin/env python3
"""
Test script for word-level timestamp transcription.
"""

import sys
import os
sys.path.append('.')

from pathlib import Path
from app.services.speaker_aware_transcription_service import SpeakerAwareTranscriptionService
from app.core.logging import configure_logging, get_logger

def main():
    # Configure logging
    configure_logging()
    logger = get_logger()

    print("🎤 Word-Level Timestamp Transcription Test")
    print("=" * 50)

    # Initialize service
    service = SpeakerAwareTranscriptionService()

    # Test file
    test_file = "audio_files/originals/Truh.mp3"

    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        print("Please ensure the test file exists in audio_files/originals/")
        return False

    print(f"\n📁 Test file: {test_file}")
    print("🔄 Starting transcription with word-level timestamps...")
    print("   (This may take a few minutes for the first run)\n")

    # Transcribe
    result = service.transcribe_audio_with_speakers(test_file)

    if not result.success:
        print(f"❌ Transcription failed: {result.error_message}")
        return False

    print("✅ Transcription successful!\n")
    print(f"📊 Results:")
    print(f"   Audio duration: {result.audio_duration_seconds:.1f}s")
    print(f"   Processing time: {result.processing_duration_ms}ms")
    print(f"   Segments extracted: {len(result.segments)}")
    print(f"   Speakers detected: {result.speakers_detected}")
    print(f"   Separation method: {result.speaker_separation_method}")

    # Show speaker info
    if result.speaker_info:
        print(f"\n👥 Speaker Information:")
        for speaker in result.speaker_info:
            print(f"   {speaker.label}:")
            print(f"      Channel: {speaker.channel or 'Mixed'}")
            print(f"      Energy: {speaker.energy_percent:.1f}%")

    # Show first 10 segments with timestamps
    print(f"\n📝 First 10 segments with word-level timestamps:")
    print("-" * 80)
    for i, segment in enumerate(result.segments[:10]):
        speaker_label = "Speaker 1" if segment.speaker_id == 'speaker_1' else "Speaker 2" if segment.speaker_id == 'speaker_2' else "Unknown"
        duration = segment.end_time - segment.start_time
        print(f"{i+1:2d}. [{segment.start_time:7.2f}s - {segment.end_time:7.2f}s] ({duration:5.2f}s) {speaker_label}: {segment.text}")

    print("-" * 80)

    # Analyze segment durations
    durations = [seg.end_time - seg.start_time for seg in result.segments]
    avg_duration = sum(durations) / len(durations) if durations else 0
    min_duration = min(durations) if durations else 0
    max_duration = max(durations) if durations else 0

    print(f"\n📊 Segment Duration Statistics:")
    print(f"   Average: {avg_duration:.2f}s")
    print(f"   Min: {min_duration:.2f}s")
    print(f"   Max: {max_duration:.2f}s")

    # Check if we're getting word-level (not 30s chunks)
    if avg_duration < 5.0:
        print(f"\n✅ SUCCESS: Word-level timestamps working! (avg {avg_duration:.2f}s per segment)")
    else:
        print(f"\n⚠️  WARNING: Segments seem long (avg {avg_duration:.2f}s). Expected word-level ~1-3s")

    return True

if __name__ == "__main__":
    success = main()
    print(f"\n{'='*50}")
    print(f"🏁 Test {'PASSED ✅' if success else 'FAILED ❌'}")
    sys.exit(0 if success else 1)
