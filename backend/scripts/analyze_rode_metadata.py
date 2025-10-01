#!/usr/bin/env python3
"""
Detailed analysis of M4A metadata from Røde Wireless Me microphones.
"""

import sys
import os
sys.path.append('.')

from pathlib import Path
from mutagen.mp4 import MP4
from mutagen import File
import json
from pydub import AudioSegment
import numpy as np
from app.core.logging import configure_logging, get_logger

def analyze_rode_metadata():
    configure_logging()
    logger = get_logger()

    print("🎤 Røde Wireless Me Metadata Analysis")
    print("=" * 50)

    # Find M4A files
    audio_path = Path("audio_files/originals")
    if not audio_path.exists():
        print("❌ No audio files directory found")
        return

    m4a_files = list(audio_path.glob("*.m4a"))
    if not m4a_files:
        print("❌ No M4A files found")
        return

    print(f"📁 Found {len(m4a_files)} M4A files")

    for i, file_path in enumerate(m4a_files[:3]):  # Analyze first 3 files
        print(f"\n{'='*20} FILE {i+1}: {file_path.name} {'='*20}")

        # 1. Basic file info
        file_size = file_path.stat().st_size / (1024 * 1024)
        print(f"📊 File size: {file_size:.2f} MB")

        try:
            # 2. Mutagen metadata analysis
            print("\n🏷️  MUTAGEN METADATA:")
            audio_file = MP4(file_path)

            print("   Standard tags:")
            for key, value in audio_file.tags.items() if audio_file.tags else []:
                print(f"     {key}: {value}")

            print(f"\n   Audio info:")
            if audio_file.info:
                print(f"     Bitrate: {audio_file.info.bitrate} bps")
                print(f"     Length: {audio_file.info.length:.2f} seconds")
                print(f"     Channels: {getattr(audio_file.info, 'channels', 'Unknown')}")
                print(f"     Sample rate: {getattr(audio_file.info, 'sample_rate', 'Unknown')} Hz")

            # 3. Alternative metadata reading
            print("\n🔍 ALTERNATIVE METADATA READER:")
            generic_file = File(file_path)
            if generic_file:
                print(f"   File type: {generic_file.mime[0] if generic_file.mime else 'Unknown'}")
                print(f"   Info: {generic_file.info}")
                if hasattr(generic_file, 'tags') and generic_file.tags:
                    print("   All tags:")
                    for key, value in generic_file.tags.items():
                        print(f"     {key}: {value}")

            # 4. Pydub audio analysis
            print("\n🎵 PYDUB AUDIO ANALYSIS:")
            audio = AudioSegment.from_file(file_path)
            print(f"   Channels: {audio.channels}")
            print(f"   Sample width: {audio.sample_width} bytes")
            print(f"   Frame rate: {audio.frame_rate} Hz")
            print(f"   Duration: {len(audio) / 1000:.2f} seconds")
            print(f"   Max dBFS: {audio.max_dBFS:.2f}")

            # 5. Stereo channel analysis
            if audio.channels == 2:
                print("\n🎧 STEREO CHANNEL ANALYSIS:")

                # Split channels
                left_channel = audio.split_to_mono()[0]
                right_channel = audio.split_to_mono()[1]

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
                        print("   ⚠️  Significant channel imbalance detected!")
                        dominant_channel = "Left" if left_rms > right_rms else "Right"
                        print(f"   📡 Dominant channel: {dominant_channel}")
                    else:
                        print("   ✅ Balanced stereo recording")

                # Analyze first 10 seconds for quick channel comparison
                sample_duration = min(10000, len(audio))  # 10 seconds or full duration
                sample_audio = audio[:sample_duration]

                if sample_audio.channels == 2:
                    sample_left = sample_audio.split_to_mono()[0]
                    sample_right = sample_audio.split_to_mono()[1]

                    # Convert to numpy for detailed analysis
                    left_array = np.array(sample_left.get_array_of_samples())
                    right_array = np.array(sample_right.get_array_of_samples())

                    # Calculate correlation between channels
                    correlation = np.corrcoef(left_array, right_array)[0, 1]
                    print(f"   Channel correlation: {correlation:.3f}")

                    if correlation < 0.8:
                        print("   🎯 LOW CORRELATION - Likely different mic sources!")
                    else:
                        print("   🔗 HIGH CORRELATION - Likely same source or mixed")

            # 6. Look for device-specific metadata
            print("\n📱 DEVICE-SPECIFIC METADATA SEARCH:")

            # Common metadata fields that might contain device info
            metadata_keys_to_check = [
                'com.apple.quicktime.make',
                'com.apple.quicktime.model',
                'com.apple.quicktime.software',
                'com.apple.quicktime.creationdate',
                'com.rode.device',
                'com.rode.wireless',
                'device',
                'encoder',
                'software',
                'comment',
                'description'
            ]

            found_device_info = False
            if audio_file.tags:
                for key in metadata_keys_to_check:
                    if key in audio_file.tags:
                        print(f"   🎯 {key}: {audio_file.tags[key]}")
                        found_device_info = True

            if not found_device_info:
                print("   ℹ️  No obvious device-specific metadata found")

        except Exception as e:
            print(f"   ❌ Error analyzing {file_path.name}: {e}")

    # 7. Summary and recommendations
    print(f"\n{'='*50}")
    print("📋 ANALYSIS SUMMARY & RECOMMENDATIONS:")
    print("1. Check if stereo recordings have channel separation")
    print("2. Look for correlation differences between left/right channels")
    print("3. Examine device metadata for Røde-specific information")
    print("4. Consider timestamp analysis for speaker change detection")

    print("\n💡 NEXT STEPS:")
    print("- If channels are separated: Use channel-based speaker detection")
    print("- If channels are mixed: Implement voice activity detection")
    print("- Consider implementing speaker diarization with pyannote.audio")

if __name__ == "__main__":
    analyze_rode_metadata()