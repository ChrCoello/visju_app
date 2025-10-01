#!/usr/bin/env python3
"""
Check Truh.mp3 for stereo channel separation and split channels if successful.
"""

import sys
import os
sys.path.append('.')

from pathlib import Path
from mutagen.mp3 import MP3
from pydub import AudioSegment
import numpy as np
from app.core.logging import configure_logging, get_logger

def check_and_split_truh_stereo():
    configure_logging()
    logger = get_logger()

    print("🎯 Checking Truh.mp3 for Channel Separation Success")
    print("=" * 55)

    # Find the Truh.mp3 file
    file_path = Path("audio_files/originals/Truh.mp3")

    if not file_path.exists():
        print("❌ Truh.mp3 not found in audio_files/originals/")
        return False

    print(f"✅ Found: {file_path.name}")
    file_size = file_path.stat().st_size / (1024 * 1024)
    print(f"📊 File size: {file_size:.2f} MB")

    try:
        # Check MP3 metadata
        print("\n🏷️  MP3 METADATA:")
        try:
            mp3_file = MP3(file_path)
            print(f"   Bitrate: {mp3_file.info.bitrate} bps")
            print(f"   Length: {mp3_file.info.length:.2f} seconds")
            print(f"   Sample rate: {mp3_file.info.sample_rate} Hz")
            print(f"   Channels: {mp3_file.info.channels}")
            print(f"   Mode: {mp3_file.info.mode}")
        except Exception as e:
            print(f"   ⚠️  Could not read MP3 metadata: {e}")

        # Load audio for analysis
        print("\n🎵 AUDIO ANALYSIS:")
        audio = AudioSegment.from_file(file_path)

        print(f"   Channels: {audio.channels}")
        print(f"   Sample width: {audio.sample_width} bytes")
        print(f"   Frame rate: {audio.frame_rate} Hz")
        print(f"   Duration: {len(audio) / 1000:.2f} seconds")
        print(f"   Max dBFS: {audio.max_dBFS:.2f}")

        if audio.channels == 1:
            print("\n❌ STILL MONO - Channel separation not achieved")
            return False

        elif audio.channels == 2:
            print("\n🎯 STEREO DETECTED - Analyzing separation quality...")

            # Split channels for detailed analysis
            left_channel = audio.split_to_mono()[0]
            right_channel = audio.split_to_mono()[1]

            print(f"\n📊 CHANNEL ANALYSIS:")
            print(f"   Left channel max dBFS: {left_channel.max_dBFS:.2f}")
            print(f"   Right channel max dBFS: {right_channel.max_dBFS:.2f}")

            # Calculate RMS for energy comparison
            left_rms = left_channel.rms
            right_rms = right_channel.rms

            print(f"   Left channel RMS: {left_rms}")
            print(f"   Right channel RMS: {right_rms}")

            # Channel balance analysis
            separation_quality = "UNKNOWN"
            speaker_identification_possible = False

            if left_rms > 0 and right_rms > 0:
                ratio = max(left_rms, right_rms) / min(left_rms, right_rms)
                print(f"   Channel balance ratio: {ratio:.2f}")

                if ratio > 5:
                    separation_quality = "EXCELLENT"
                    speaker_identification_possible = True
                    print("   🎯 EXCELLENT SEPARATION!")
                elif ratio > 2:
                    separation_quality = "GOOD"
                    speaker_identification_possible = True
                    print("   🎯 GOOD SEPARATION!")
                elif ratio > 1.3:
                    separation_quality = "MODERATE"
                    speaker_identification_possible = True
                    print("   ⚠️  MODERATE SEPARATION")
                else:
                    separation_quality = "POOR"
                    print("   ❌ POOR SEPARATION - Still mixed")

            elif left_rms == 0:
                print("   📡 LEFT CHANNEL SILENT - Single speaker on RIGHT!")
                separation_quality = "PERFECT"
                speaker_identification_possible = True
            elif right_rms == 0:
                print("   📡 RIGHT CHANNEL SILENT - Single speaker on LEFT!")
                separation_quality = "PERFECT"
                speaker_identification_possible = True

            # Correlation analysis
            print(f"\n🔬 CORRELATION ANALYSIS:")
            sample_duration = min(30000, len(audio))
            sample_audio = audio[:sample_duration]

            if sample_audio.channels == 2:
                sample_left = sample_audio.split_to_mono()[0]
                sample_right = sample_audio.split_to_mono()[1]

                left_array = np.array(sample_left.get_array_of_samples())
                right_array = np.array(sample_right.get_array_of_samples())

                if len(left_array) > 0 and len(right_array) > 0:
                    correlation = np.corrcoef(left_array, right_array)[0, 1]
                    print(f"   Cross-channel correlation: {correlation:.3f}")

                    if correlation < 0.3:
                        print("   🎯 VERY LOW CORRELATION - Excellent separation!")
                        speaker_identification_possible = True
                    elif correlation < 0.6:
                        print("   🎯 LOW CORRELATION - Good separation!")
                        speaker_identification_possible = True
                    elif correlation < 0.8:
                        print("   ⚠️  MODERATE CORRELATION - Some separation")
                    else:
                        print("   ❌ HIGH CORRELATION - Still mixed")

                    # Energy distribution
                    left_energy = np.sum(left_array.astype(np.float64) ** 2)
                    right_energy = np.sum(right_array.astype(np.float64) ** 2)
                    total_energy = left_energy + right_energy

                    if total_energy > 0:
                        left_percent = (left_energy / total_energy) * 100
                        right_percent = (right_energy / total_energy) * 100

                        print(f"   Energy distribution:")
                        print(f"     Left channel: {left_percent:.1f}%")
                        print(f"     Right channel: {right_percent:.1f}%")

            # If separation is good, create channel splits for testing
            if speaker_identification_possible:
                print(f"\n🎉 SUCCESS! Channel separation achieved!")
                print(f"   Quality: {separation_quality}")

                # Create output directory for split channels
                output_dir = Path("audio_files/channels")
                output_dir.mkdir(exist_ok=True)

                # Export left and right channels separately
                left_path = output_dir / "Truh_left_speaker.wav"
                right_path = output_dir / "Truh_right_speaker.wav"

                print(f"\n📁 Exporting channel splits:")

                # Export as WAV for best quality transcription
                left_channel.export(str(left_path), format="wav")
                right_channel.export(str(right_path), format="wav")

                print(f"   ✅ Left channel: {left_path.name}")
                print(f"   ✅ Right channel: {right_path.name}")

                # Test if channels have different content by analyzing silence
                print(f"\n🔍 CONTENT ANALYSIS:")

                def analyze_silence(channel, name):
                    # Simple silence detection
                    samples = np.array(channel.get_array_of_samples())
                    if len(samples) > 0:
                        # Calculate percentage of near-silent samples
                        silence_threshold = max(50, np.max(np.abs(samples)) * 0.01)  # 1% of max amplitude
                        silent_samples = np.sum(np.abs(samples) < silence_threshold)
                        silence_percent = (silent_samples / len(samples)) * 100

                        print(f"   {name} silence: {silence_percent:.1f}%")
                        return silence_percent
                    return 100

                left_silence = analyze_silence(left_channel, "Left")
                right_silence = analyze_silence(right_channel, "Right")

                if abs(left_silence - right_silence) > 20:
                    print("   🎯 DIFFERENT SILENCE PATTERNS - Great speaker separation!")

                print(f"\n💡 IMPLEMENTATION READY:")
                print("   ✅ Channel-based speaker identification possible!")
                print("   📋 Next steps:")
                print("     1. Update transcription service for stereo processing")
                print("     2. Transcribe left channel as Speaker 1")
                print("     3. Transcribe right channel as Speaker 2")
                print("     4. Merge transcripts with speaker attribution")
                print("     5. Handle any overlapping speech")

                return True

            else:
                print(f"\n❌ INSUFFICIENT SEPARATION")
                print(f"   Quality: {separation_quality}")
                print("   💡 May need to adjust Røde settings or try speaker diarization")
                return False

        else:
            print(f"\n⚠️ UNUSUAL CHANNEL COUNT: {audio.channels}")
            return False

    except Exception as e:
        print(f"❌ Error analyzing Truh.mp3: {e}")
        return False

if __name__ == "__main__":
    success = check_and_split_truh_stereo()
    if success:
        print(f"\n🎉 BREAKTHROUGH ACHIEVED!")
        print("   🎯 Stereo channel separation working!")
        print("   🚀 Ready to implement speaker-aware transcription!")
    else:
        print(f"\n⚠️  Channel separation still needs work")
        print("   💡 Consider speaker diarization as alternative")