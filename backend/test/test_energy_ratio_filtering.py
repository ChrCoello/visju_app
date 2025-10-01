"""
Test for Energy Ratio Filtering (Method 3) in speaker-aware transcription.
"""

import pytest
import numpy as np
from pydub import AudioSegment
from pydub.generators import Sine
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.speaker_aware_transcription_service import SpeakerAwareTranscriptionService


def create_synthetic_stereo_audio(duration_ms=1000, left_freq=440, right_freq=880):
    """
    Create a synthetic stereo audio with different frequencies on each channel.

    Args:
        duration_ms: Duration in milliseconds
        left_freq: Frequency for left channel (Hz)
        right_freq: Frequency for right channel (Hz)

    Returns:
        Stereo AudioSegment
    """
    # Generate sine waves for each channel
    left_channel = Sine(left_freq).to_audio_segment(duration=duration_ms)
    right_channel = Sine(right_freq).to_audio_segment(duration=duration_ms)

    # Combine into stereo
    stereo = AudioSegment.from_mono_audiosegments(left_channel, right_channel)

    return stereo


def create_stereo_with_alternating_speakers(duration_ms=2000):
    """
    Create stereo audio where speakers alternate:
    - First half: left channel loud, right channel quiet
    - Second half: left channel quiet, right channel loud

    Returns:
        Stereo AudioSegment
    """
    half_duration = duration_ms // 2

    # First half: left dominant
    left_loud = Sine(440).to_audio_segment(duration=half_duration)
    right_quiet = Sine(880).to_audio_segment(duration=half_duration).apply_gain(-20)  # 20dB quieter

    # Second half: right dominant
    left_quiet = Sine(440).to_audio_segment(duration=half_duration).apply_gain(-20)
    right_loud = Sine(880).to_audio_segment(duration=half_duration)

    # Combine
    first_half = AudioSegment.from_mono_audiosegments(left_loud, right_quiet)
    second_half = AudioSegment.from_mono_audiosegments(left_quiet, right_loud)

    return first_half + second_half


def test_energy_ratio_filtering_initialization():
    """Test that the service initializes with energy filtering enabled."""
    service = SpeakerAwareTranscriptionService()

    assert service.use_energy_filtering is True
    assert service.energy_ratio_gate_threshold == 2.0
    assert service.filter_window_ms == 100

    print("✓ Energy filtering initialization test passed")


def test_energy_ratio_filtering_basic():
    """Test basic energy ratio filtering on synthetic stereo audio."""
    service = SpeakerAwareTranscriptionService()

    # Create stereo audio with equal volume on both channels
    stereo = create_synthetic_stereo_audio(duration_ms=1000)

    # Apply filtering
    filtered_left, filtered_right = service._apply_energy_ratio_filtering(stereo)

    # Both channels should be AudioSegment instances
    assert isinstance(filtered_left, AudioSegment)
    assert isinstance(filtered_right, AudioSegment)

    # Both should be mono
    assert filtered_left.channels == 1
    assert filtered_right.channels == 1

    # Should have same duration as original
    assert abs(len(filtered_left) - len(stereo)) < 10  # Allow small difference
    assert abs(len(filtered_right) - len(stereo)) < 10

    print("✓ Basic energy filtering test passed")


def test_energy_ratio_filtering_alternating_speakers():
    """Test energy filtering with alternating speaker dominance."""
    service = SpeakerAwareTranscriptionService()

    # Create audio with alternating speakers
    stereo = create_stereo_with_alternating_speakers(duration_ms=2000)

    # Apply filtering
    filtered_left, filtered_right = service._apply_energy_ratio_filtering(stereo)

    # Get samples
    left_samples = np.array(filtered_left.get_array_of_samples())
    right_samples = np.array(filtered_right.get_array_of_samples())

    # First half: left should be mostly preserved, right mostly silenced
    first_half_samples = len(left_samples) // 2
    left_first_half_energy = np.sum(left_samples[:first_half_samples] ** 2)
    right_first_half_energy = np.sum(right_samples[:first_half_samples] ** 2)

    # Second half: right should be mostly preserved, left mostly silenced
    left_second_half_energy = np.sum(left_samples[first_half_samples:] ** 2)
    right_second_half_energy = np.sum(right_samples[first_half_samples:] ** 2)

    # Check that filtering worked correctly
    # First half: left energy should be much higher than right
    assert left_first_half_energy > right_first_half_energy * 5, \
        f"First half: left energy ({left_first_half_energy}) should be much higher than right ({right_first_half_energy})"

    # Second half: right energy should be much higher than left
    assert right_second_half_energy > left_second_half_energy * 5, \
        f"Second half: right energy ({right_second_half_energy}) should be much higher than left ({left_second_half_energy})"

    print("✓ Alternating speakers filtering test passed")
    print(f"  First half - Left energy: {left_first_half_energy:.0f}, Right energy: {right_first_half_energy:.0f}")
    print(f"  Second half - Left energy: {left_second_half_energy:.0f}, Right energy: {right_second_half_energy:.0f}")


def test_energy_ratio_filtering_mono_audio():
    """Test that mono audio is handled correctly."""
    service = SpeakerAwareTranscriptionService()

    # Create mono audio
    mono = Sine(440).to_audio_segment(duration=1000)

    # Apply filtering (should handle gracefully)
    filtered_left, filtered_right = service._apply_energy_ratio_filtering(mono)

    # Should return mono audio
    assert filtered_left.channels == 1
    assert filtered_right.channels == 1

    print("✓ Mono audio handling test passed")


def test_model_info_includes_filtering_params():
    """Test that model info includes energy filtering parameters."""
    service = SpeakerAwareTranscriptionService()

    model_info = service.get_model_info()

    assert "energy_filtering_enabled" in model_info
    assert "energy_filtering_threshold" in model_info
    assert "energy_filtering_window_ms" in model_info

    assert model_info["energy_filtering_enabled"] is True
    assert model_info["energy_filtering_threshold"] == 2.0
    assert model_info["energy_filtering_window_ms"] == 100

    print("✓ Model info includes filtering parameters test passed")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing Energy Ratio Filtering (Method 3)")
    print("="*60 + "\n")

    try:
        test_energy_ratio_filtering_initialization()
        test_energy_ratio_filtering_basic()
        test_energy_ratio_filtering_alternating_speakers()
        test_energy_ratio_filtering_mono_audio()
        test_model_info_includes_filtering_params()

        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60 + "\n")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        raise
