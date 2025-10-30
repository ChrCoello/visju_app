#!/usr/bin/env python3
"""
Test Option 3: Unified transcription with energy-based speaker assignment.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.speaker_aware_transcription_service import SpeakerAwareTranscriptionService

# Test audio file (adjust path as needed)
TEST_AUDIO_PATH = "audio_files/originals/idioten.mp3"

def test_option3():
    """Test the new unified transcription with energy-based speaker assignment."""

    print("=" * 80)
    print("Testing Option 3: Unified Transcription with Energy-Based Speaker Assignment")
    print("=" * 80)

    # Initialize service (unified transcription is enabled by default)
    service = SpeakerAwareTranscriptionService()

    print(f"\nConfiguration:")
    print(f"  - use_unified_transcription: {service.use_unified_transcription}")
    print(f"  - speaker_energy_threshold: {service.speaker_energy_threshold}")
    print(f"  - keep_unclear_segments: {service.keep_unclear_segments}")
    print(f"  - unclear_energy_threshold: {service.unclear_energy_threshold}")

    # Find audio file
    audio_path = Path(TEST_AUDIO_PATH)
    if not audio_path.exists():
        # Try alternate locations
        for alt_path in ["backend/" + TEST_AUDIO_PATH, "../" + TEST_AUDIO_PATH]:
            if Path(alt_path).exists():
                audio_path = Path(alt_path)
                break

    if not audio_path.exists():
        print(f"\n❌ Audio file not found: {TEST_AUDIO_PATH}")
        print("   Please update TEST_AUDIO_PATH in this script")
        return

    print(f"\n📁 Audio file: {audio_path}")

    # Transcribe with new method
    print(f"\n🎵 Starting transcription...")
    result = service.transcribe_audio_with_speakers(str(audio_path.absolute()))

    if result.success:
        print(f"\n✅ Transcription completed successfully!")
        print(f"\n📊 Results:")
        print(f"  - Processing time: {result.processing_duration_ms/1000:.1f}s")
        print(f"  - Audio duration: {result.audio_duration_seconds:.1f}s")
        print(f"  - Total segments: {len(result.segments)}")
        print(f"  - Speakers detected: {result.speakers_detected}")
        print(f"  - Separation method: {result.speaker_separation_method}")
        print(f"  - Characters: {len(result.full_text)}")

        # Count segments per speaker
        speaker_counts = {}
        for segment in result.segments:
            speaker_counts[segment.speaker_id] = speaker_counts.get(segment.speaker_id, 0) + 1

        print(f"\n👥 Segments per speaker:")
        for speaker_id, count in speaker_counts.items():
            print(f"  - {speaker_id}: {count} segments")

        # Show speaker info
        if result.speaker_info:
            print(f"\n🎤 Speaker details:")
            for speaker in result.speaker_info:
                print(f"  - {speaker.label}:")
                print(f"    Channel: {speaker.channel}")
                print(f"    Energy: {speaker.energy_percent:.1f}%")
                print(f"    Silence: {speaker.silence_percent:.1f}%")

        # Show first few segments to check for duplicates
        print(f"\n📝 First 10 segments (checking for duplicates):")
        print("-" * 80)
        for i, segment in enumerate(result.segments[:10]):
            speaker_label = segment.speaker_id.replace("_", " ").title()
            print(f"{i+1}. [{speaker_label}] ({segment.start_time:.1f}s-{segment.end_time:.1f}s):")
            print(f"   {segment.text}")

        # Show full text preview
        print(f"\n📄 Full transcription preview (first 1000 chars):")
        print("-" * 80)
        print(result.full_text[:1000])
        if len(result.full_text) > 1000:
            print(f"\n... ({len(result.full_text) - 1000} more characters)")

    else:
        print(f"\n❌ Transcription failed!")
        print(f"   Error: {result.error_message}")

def compare_with_old_method():
    """Compare unified transcription vs old separate channel method."""

    print("\n" + "=" * 80)
    print("COMPARISON: Unified vs Old Method")
    print("=" * 80)

    audio_path = Path(TEST_AUDIO_PATH)
    if not audio_path.exists():
        for alt_path in ["backend/" + TEST_AUDIO_PATH, "../" + TEST_AUDIO_PATH]:
            if Path(alt_path).exists():
                audio_path = Path(alt_path)
                break

    if not audio_path.exists():
        print(f"❌ Audio file not found")
        return

    # Test 1: Unified transcription (NEW)
    print(f"\n1️⃣  Testing UNIFIED transcription (Option 3 - NEW)...")
    service_new = SpeakerAwareTranscriptionService()
    service_new.use_unified_transcription = True
    result_new = service_new.transcribe_audio_with_speakers(str(audio_path.absolute()))

    # Test 2: Separate channel transcription (OLD)
    print(f"\n2️⃣  Testing SEPARATE CHANNEL transcription (OLD)...")
    service_old = SpeakerAwareTranscriptionService()
    service_old.use_unified_transcription = False
    result_old = service_old.transcribe_audio_with_speakers(str(audio_path.absolute()))

    # Compare results
    print(f"\n" + "=" * 80)
    print("📊 COMPARISON RESULTS")
    print("=" * 80)

    print(f"\n{'Metric':<30} {'Unified (NEW)':<20} {'Separate (OLD)':<20}")
    print("-" * 80)
    print(f"{'Total segments':<30} {len(result_new.segments):<20} {len(result_old.segments):<20}")
    print(f"{'Total characters':<30} {len(result_new.full_text):<20} {len(result_old.full_text):<20}")
    print(f"{'Processing time (s)':<30} {result_new.processing_duration_ms/1000:<20.1f} {result_old.processing_duration_ms/1000:<20.1f}")

    # Count speaker segments
    new_speaker_counts = {}
    for seg in result_new.segments:
        new_speaker_counts[seg.speaker_id] = new_speaker_counts.get(seg.speaker_id, 0) + 1

    old_speaker_counts = {}
    for seg in result_old.segments:
        old_speaker_counts[seg.speaker_id] = old_speaker_counts.get(seg.speaker_id, 0) + 1

    print(f"\n{'Speaker distribution':<30}")
    all_speakers = set(list(new_speaker_counts.keys()) + list(old_speaker_counts.keys()))
    for speaker in sorted(all_speakers):
        new_count = new_speaker_counts.get(speaker, 0)
        old_count = old_speaker_counts.get(speaker, 0)
        print(f"  {speaker:<28} {new_count:<20} {old_count:<20}")

    print(f"\n💡 Analysis:")
    if len(result_new.segments) < len(result_old.segments) * 0.6:
        print(f"   ✅ Unified method eliminated duplicates!")
        print(f"   Reduction: {100 * (1 - len(result_new.segments)/len(result_old.segments)):.1f}%")
    else:
        print(f"   ⚠️  Similar segment counts - may need to tune energy threshold")

if __name__ == "__main__":
    # Run basic test
    test_option3()

    # Ask if user wants comparison
    print("\n" + "=" * 80)
    response = input("\nRun comparison with old method? (y/n): ")
    if response.lower() == 'y':
        compare_with_old_method()
