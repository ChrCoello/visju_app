#!/usr/bin/env python3
"""
Check if Stardew.m4a is recorded in stereo with channel separation.
"""

import sys
import os
sys.path.append('.')

from pathlib import Path
from mutagen.mp4 import MP4
from pydub import AudioSegment
import numpy as np
from app.core.logging import configure_logging, get_logger

def check_stardew_audio():
    configure_logging()
    logger = get_logger()

    print("🎧 Checking Stardew.m4a for Stereo Channel Separation")
    print("=" * 55)

    # Find the Stardew.m4a file
    file_path = Path("audio_files/originals/Stardew.m4a")

    if not file_path.exists():
        print("❌ Stardew.m4a not found in audio_files/originals/")
        return False

    print(f"✅ Found: {file_path.name}")
    file_size = file_path.stat().st_size / (1024 * 1024)
    print(f"📊 File size: {file_size:.2f} MB")

    try:
        # Load with Pydub for detailed analysis
        print("\n🎵 AUDIO ANALYSIS:")
        audio = AudioSegment.from_file(file_path)

        print(f"   Channels: {audio.channels}")
        print(f"   Sample width: {audio.sample_width} bytes")
        print(f"   Frame rate: {audio.frame_rate} Hz")
        print(f"   Duration: {len(audio) / 1000:.2f} seconds")
        print(f"   Max dBFS: {audio.max_dBFS:.2f}")

        if audio.channels == 1:
            print("\n❌ MONO RECORDING - No channel separation available")
            return False

        elif audio.channels == 2:
            print("\n🎯 STEREO RECORDING DETECTED!")
            print("🔍 Analyzing channel separation...")

            # Split channels
            left_channel = audio.split_to_mono()[0]
            right_channel = audio.split_to_mono()[1]

            print(f"\n📊 CHANNEL COMPARISON:")
            print(f"   Left channel max dBFS: {left_channel.max_dBFS:.2f}")
            print(f"   Right channel max dBFS: {right_channel.max_dBFS:.2f}")

            # Calculate RMS for each channel
            left_rms = left_channel.rms
            right_rms = right_channel.rms

            print(f"   Left channel RMS: {left_rms}")
            print(f"   Right channel RMS: {right_rms}")

            # Check if channels are significantly different
            if left_rms > 0 and right_rms > 0:
                ratio = max(left_rms, right_rms) / min(left_rms, right_rms)
                print(f"   Channel balance ratio: {ratio:.2f}")

                if ratio > 2:
                    print("   🎯 SIGNIFICANT CHANNEL IMBALANCE!")
                    dominant_channel = "Left" if left_rms > right_rms else "Right"
                    print(f"   📡 Dominant channel: {dominant_channel}")
                    print("   💡 This suggests different mic sources per channel!")
                else:
                    print("   ⚖️  Balanced stereo - may be mixed signal")

            elif left_rms == 0:
                print("   📡 LEFT CHANNEL IS SILENT - Right channel only!")
                print("   💡 Single microphone on right channel")
            elif right_rms == 0:
                print("   📡 RIGHT CHANNEL IS SILENT - Left channel only!")
                print("   💡 Single microphone on left channel")

            # Detailed correlation analysis
            print(f"\n🔬 DETAILED CHANNEL ANALYSIS:")

            # Analyze first 30 seconds for correlation
            sample_duration = min(30000, len(audio))  # 30 seconds or full duration
            sample_audio = audio[:sample_duration]

            if sample_audio.channels == 2:
                sample_left = sample_audio.split_to_mono()[0]
                sample_right = sample_audio.split_to_mono()[1]

                # Convert to numpy for analysis
                left_array = np.array(sample_left.get_array_of_samples())
                right_array = np.array(sample_right.get_array_of_samples())

                # Calculate correlation between channels
                if len(left_array) > 0 and len(right_array) > 0:
                    correlation = np.corrcoef(left_array, right_array)[0, 1]
                    print(f"   Channel correlation: {correlation:.3f}")

                    if correlation < 0.3:
                        print("   🎯 VERY LOW CORRELATION - Definitely different sources!")
                        print("   ✅ Perfect for speaker identification by channel!")
                    elif correlation < 0.7:
                        print("   🎯 LOW CORRELATION - Likely different mic sources!")
                        print("   ✅ Good for speaker identification by channel!")
                    elif correlation < 0.9:
                        print("   ⚠️  MODERATE CORRELATION - Some mixing but distinguishable")
                        print("   ⚠️  May work for speaker identification")
                    else:
                        print("   ❌ HIGH CORRELATION - Same source or heavy mixing")
                        print("   ❌ Channel separation won't help with speakers")

                # Check for silent periods in each channel
                silent_threshold = 500  # Adjust based on your audio
                left_silent_samples = np.sum(np.abs(left_array) < silent_threshold)
                right_silent_samples = np.sum(np.abs(right_array) < silent_threshold)

                total_samples = len(left_array)
                left_silent_percent = (left_silent_samples / total_samples) * 100
                right_silent_percent = (right_silent_samples / total_samples) * 100

                print(f"   Left channel silence: {left_silent_percent:.1f}%")
                print(f"   Right channel silence: {right_silent_percent:.1f}%")

                if abs(left_silent_percent - right_silent_percent) > 20:
                    print("   🎯 DIFFERENT SILENCE PATTERNS - Great for speaker detection!")

            print(f"\n💡 SPEAKER IDENTIFICATION POTENTIAL:")
            if audio.channels == 2 and (ratio > 2 or correlation < 0.7):
                print("   ✅ EXCELLENT - Can use channel-based speaker identification!")
                print("   📋 Implementation approach:")
                print("     - Left channel = Speaker 1")
                print("     - Right channel = Speaker 2")
                print("     - Transcribe each channel separately")
                print("     - Merge transcripts with speaker labels")
                return True
            else:
                print("   ⚠️  LIMITED - Channels too similar for reliable speaker ID")
                print("   💡 Consider speaker diarization instead")
                return False

        else:
            print(f"\n⚠️ UNUSUAL CHANNEL COUNT: {audio.channels}")
            return False

    except Exception as e:
        print(f"❌ Error analyzing Stardew.m4a: {e}")
        return False

if __name__ == "__main__":
    success = check_stardew_audio()
    print(f"\n🏁 Analysis {'SUCCESSFUL' if success else 'NEEDS ALTERNATIVE APPROACH'}")