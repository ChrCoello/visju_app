#!/usr/bin/env python3
"""
Compare unified transcription vs old separate channel method.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.speaker_aware_transcription_service import SpeakerAwareTranscriptionService

TEST_AUDIO_PATH = "audio_files/originals/idioten.mp3"

def main():
    """Compare unified transcription vs old separate channel method."""

    print("=" * 80)
    print("COMPARISON: Unified vs Old Method")
    print("=" * 80)

    audio_path = Path(TEST_AUDIO_PATH)
    if not audio_path.exists():
        for alt_path in ["backend/" + TEST_AUDIO_PATH, "../" + TEST_AUDIO_PATH]:
            if Path(alt_path).exists():
                audio_path = Path(alt_path)
                break

    if not audio_path.exists():
        print(f"❌ Audio file not found: {TEST_AUDIO_PATH}")
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

    print(f"\n{'Speaker distribution:':<30}")
    all_speakers = set(list(new_speaker_counts.keys()) + list(old_speaker_counts.keys()))
    for speaker in sorted(all_speakers):
        new_count = new_speaker_counts.get(speaker, 0)
        old_count = old_speaker_counts.get(speaker, 0)
        print(f"  {speaker:<28} {new_count:<20} {old_count:<20}")

    # Analyze duplicates
    print(f"\n💡 Analysis:")
    if len(result_new.segments) < len(result_old.segments) * 0.6:
        reduction = 100 * (1 - len(result_new.segments)/len(result_old.segments))
        print(f"   ✅ Unified method eliminated duplicates!")
        print(f"   Segment reduction: {reduction:.1f}%")
        print(f"   This indicates the old method was creating ~{reduction:.0f}% duplicate segments")
    elif len(result_new.segments) < len(result_old.segments):
        reduction = 100 * (1 - len(result_new.segments)/len(result_old.segments))
        print(f"   ✅ Unified method reduced segments by {reduction:.1f}%")
    else:
        print(f"   ⚠️  Similar segment counts - may need to tune energy threshold")

    # Show first few segments from each
    print(f"\n📝 First 3 segments comparison:")
    print("=" * 80)
    print("\nUNIFIED METHOD (NEW):")
    print("-" * 80)
    for i, seg in enumerate(result_new.segments[:3]):
        print(f"{i+1}. [{seg.speaker_id}] ({seg.start_time:.1f}s): {seg.text[:80]}...")

    print("\nSEPARATE CHANNEL METHOD (OLD):")
    print("-" * 80)
    for i, seg in enumerate(result_old.segments[:3]):
        print(f"{i+1}. [{seg.speaker_id}] ({seg.start_time:.1f}s): {seg.text[:80]}...")

if __name__ == "__main__":
    main()
