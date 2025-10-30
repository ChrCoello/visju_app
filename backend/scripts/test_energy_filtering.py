#!/usr/bin/env python3
"""
Test speaker-aware transcription with different energy filtering settings.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.speaker_aware_transcription_service import SpeakerAwareTranscriptionService

TEST_AUDIO_PATH = "backend/audio_files/originals/Testwerner.mp3"

def test_transcription(use_energy_filtering: bool, threshold: float = 2.0):
    """Test transcription with specific energy filtering settings."""

    service = SpeakerAwareTranscriptionService()
    service.use_energy_filtering = use_energy_filtering
    service.energy_ratio_gate_threshold = threshold

    print(f"\n{'='*80}")
    print(f"Testing with energy_filtering={use_energy_filtering}, threshold={threshold}")
    print('='*80)

    audio_path = Path(TEST_AUDIO_PATH)
    result = service.transcribe_audio_with_speakers(str(audio_path.absolute()))

    if result.success:
        print(f"\n✅ Success!")
        print(f"   Processing time: {result.processing_duration_ms/1000:.1f}s")
        print(f"   Segments: {len(result.segments)}")
        print(f"   Characters: {len(result.full_text)}")
        print(f"   Speakers: {result.speakers_detected}")

        print(f"\n📝 TRANSCRIPTION:")
        print("-" * 80)
        print(result.full_text)

        return result
    else:
        print(f"❌ Failed: {result.error_message}")
        return None

def main():
    print("🎵 Energy Filtering Comparison Test")
    print("=" * 80)

    # Test 1: Energy filtering DISABLED (should get all content)
    result_no_filter = test_transcription(use_energy_filtering=False)

    # Test 2: Energy filtering ENABLED with threshold 2.0 (current default)
    result_filter_20 = test_transcription(use_energy_filtering=True, threshold=2.0)

    # Test 3: Energy filtering ENABLED with lower threshold 1.5 (less aggressive)
    result_filter_15 = test_transcription(use_energy_filtering=True, threshold=1.5)

    # Comparison
    if result_no_filter and result_filter_20 and result_filter_15:
        print(f"\n{'='*80}")
        print("📊 COMPARISON SUMMARY")
        print('='*80)
        print(f"{'Setting':<40} {'Characters':<15} {'Segments':<15}")
        print("-" * 80)
        print(f"{'No filtering (keep all audio)':<40} {len(result_no_filter.full_text):<15} {len(result_no_filter.segments):<15}")
        print(f"{'Filtering threshold=2.0 (aggressive)':<40} {len(result_filter_20.full_text):<15} {len(result_filter_20.segments):<15}")
        print(f"{'Filtering threshold=1.5 (moderate)':<40} {len(result_filter_15.full_text):<15} {len(result_filter_15.segments):<15}")

        print(f"\n💡 RECOMMENDATION:")
        if len(result_no_filter.full_text) > len(result_filter_20.full_text) * 1.1:
            print("   Energy filtering is removing significant content!")
            print(f"   Content loss: {100 * (1 - len(result_filter_20.full_text)/len(result_no_filter.full_text)):.1f}%")
            print("   Consider disabling energy filtering or using a lower threshold.")
        else:
            print("   Energy filtering is working well without significant content loss.")

if __name__ == "__main__":
    main()
