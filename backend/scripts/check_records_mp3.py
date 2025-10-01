#!/usr/bin/env python3
"""
Check if records.mp3 has stereo channel separation from upgraded Easy Voice Recorder.
"""

import sys
import os
sys.path.append('.')

from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError
from pydub import AudioSegment
import numpy as np
from app.core.logging import configure_logging, get_logger

def check_records_mp3():
    configure_logging()
    logger = get_logger()

    print("🎧 Checking records.mp3 for Stereo Channel Separation")
    print("=" * 55)

    # Find the records.mp3 file
    file_path = Path("audio_files/originals/records.mp3")

    if not file_path.exists():
        print("❌ records.mp3 not found in audio_files/originals/")
        # Try alternative path
        alt_path = Path("audio/originals/records.mp3")
        if alt_path.exists():
            file_path = alt_path
            print(f"✅ Found at alternative path: {file_path}")
        else:
            print("❌ records.mp3 not found in audio/originals/ either")
            return False

    print(f"✅ Found: {file_path.name}")
    file_size = file_path.stat().st_size / (1024 * 1024)
    print(f"📊 File size: {file_size:.2f} MB")

    try:
        # Check MP3 metadata first
        print("\n🏷️  MP3 METADATA:")
        try:
            mp3_file = MP3(file_path)
            print(f"   Bitrate: {mp3_file.info.bitrate} bps")
            print(f"   Length: {mp3_file.info.length:.2f} seconds")
            print(f"   Sample rate: {mp3_file.info.sample_rate} Hz")
            print(f"   Channels: {mp3_file.info.channels}")
            print(f"   Mode: {mp3_file.info.mode}")

            # Check for ID3 tags
            if mp3_file.tags:
                print("   ID3 Tags found:")
                for key, value in mp3_file.tags.items():
                    print(f"     {key}: {value}")
            else:
                print("   No ID3 tags found")

        except Exception as e:
            print(f"   ⚠️  Could not read MP3 metadata: {e}")

        # Load with Pydub for detailed analysis
        print("\n🎵 AUDIO ANALYSIS:")
        audio = AudioSegment.from_file(file_path)

        print(f"   Channels: {audio.channels}")
        print(f"   Sample width: {audio.sample_width} bytes")
        print(f"   Frame rate: {audio.frame_rate} Hz")
        print(f"   Duration: {len(audio) / 1000:.2f} seconds")
        print(f"   Max dBFS: {audio.max_dBFS:.2f}")

        if audio.channels == 1:
            print("\n❌ MONO RECORDING - Still no channel separation")
            print("   💡 Try different recording settings or app")
            return False

        elif audio.channels == 2:
            print("\n🎯 STEREO RECORDING DETECTED!")
            print("🔍 Analyzing channel separation...")

            # Split channels for analysis
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
            speaker_separation_possible = False

            if left_rms > 0 and right_rms > 0:
                ratio = max(left_rms, right_rms) / min(left_rms, right_rms)
                print(f"   Channel balance ratio: {ratio:.2f}")

                if ratio > 3:
                    print("   🎯 EXCELLENT CHANNEL IMBALANCE!")
                    dominant_channel = "Left" if left_rms > right_rms else "Right"
                    print(f"   📡 Dominant channel: {dominant_channel}")
                    print("   ✅ Perfect for speaker identification!")
                    speaker_separation_possible = True
                elif ratio > 1.5:
                    print("   🎯 GOOD CHANNEL IMBALANCE!")
                    print("   ✅ Should work well for speaker identification!")
                    speaker_separation_possible = True
                else:
                    print("   ⚖️  Balanced stereo - channels may be mixed")

            elif left_rms == 0:
                print("   📡 LEFT CHANNEL IS COMPLETELY SILENT!")
                print("   ✅ Single speaker on right channel only")
                speaker_separation_possible = True
            elif right_rms == 0:
                print("   📡 RIGHT CHANNEL IS COMPLETELY SILENT!")
                print("   ✅ Single speaker on left channel only")
                speaker_separation_possible = True

            # Correlation analysis for detailed understanding
            print(f"\n🔬 DETAILED CORRELATION ANALYSIS:")

            # Sample first 30 seconds or full duration
            sample_duration = min(30000, len(audio))
            sample_audio = audio[:sample_duration]

            if sample_audio.channels == 2:
                sample_left = sample_audio.split_to_mono()[0]
                sample_right = sample_audio.split_to_mono()[1]

                # Convert to numpy arrays
                left_array = np.array(sample_left.get_array_of_samples())
                right_array = np.array(sample_right.get_array_of_samples())

                if len(left_array) > 0 and len(right_array) > 0:
                    # Calculate correlation
                    correlation = np.corrcoef(left_array, right_array)[0, 1]
                    print(f"   Cross-channel correlation: {correlation:.3f}")

                    if correlation < 0.2:
                        print("   🎯 EXTREMELY LOW CORRELATION!")
                        print("   ✅ Definitely separate microphone sources!")
                        speaker_separation_possible = True
                    elif correlation < 0.5:
                        print("   🎯 LOW CORRELATION - Different sources!")
                        print("   ✅ Very good for speaker separation!")
                        speaker_separation_possible = True
                    elif correlation < 0.8:
                        print("   ⚠️  MODERATE CORRELATION - Some mixing")
                        print("   ⚠️  May still work for speaker identification")
                    else:
                        print("   ❌ HIGH CORRELATION - Same source")

                    # Energy distribution analysis
                    left_energy = np.sum(left_array.astype(np.float64) ** 2)
                    right_energy = np.sum(right_array.astype(np.float64) ** 2)
                    total_energy = left_energy + right_energy

                    if total_energy > 0:
                        left_percent = (left_energy / total_energy) * 100
                        right_percent = (right_energy / total_energy) * 100

                        print(f"   Energy distribution:")
                        print(f"     Left channel: {left_percent:.1f}%")
                        print(f"     Right channel: {right_percent:.1f}%")

                        if abs(left_percent - right_percent) > 30:
                            print("   🎯 SIGNIFICANT ENERGY IMBALANCE!")
                            print("   ✅ Great for channel-based speaker detection!")
                            speaker_separation_possible = True

            # Final assessment
            print(f"\n💡 SPEAKER IDENTIFICATION ASSESSMENT:")
            if speaker_separation_possible:
                print("   ✅ EXCELLENT - Channel-based speaker identification possible!")
                print("   📋 Recommended implementation:")
                print("     1. Split stereo MP3 into left/right channels")
                print("     2. Transcribe each channel separately with NB-Whisper")
                print("     3. Assign speakers: Left = Speaker 1, Right = Speaker 2")
                print("     4. Merge transcripts with proper speaker attribution")
                print("     5. Handle overlapping speech appropriately")

                print(f"\n🎉 THIS IS EXACTLY WHAT WE NEEDED!")
                print("   🔧 Ready to implement stereo transcription service!")
                return True
            else:
                print("   ⚠️  LIMITED - Channels too similar for reliable separation")
                print("   💡 Consider speaker diarization as backup")
                return False

        else:
            print(f"\n⚠️ UNUSUAL CHANNEL COUNT: {audio.channels}")
            return False

    except Exception as e:
        print(f"❌ Error analyzing records.mp3: {e}")
        return False

if __name__ == "__main__":
    success = check_records_mp3()
    if success:
        print(f"\n🎉 BREAKTHROUGH! Stereo recording with channel separation achieved!")
        print("   Ready to implement channel-based speaker identification!")
    else:
        print(f"\n⚠️  Need to explore other recording options or use speaker diarization")