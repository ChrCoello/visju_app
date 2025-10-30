"""
Speaker-aware transcription service that handles stereo recordings with channel separation.
"""

import torch
import librosa
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass

from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from pydantic import BaseModel
from pydub import AudioSegment

from ..core.logging import get_logger
from ..core.config import get_settings

logger = get_logger()

@dataclass
class SpeakerSegment:
    """Represents a timestamped segment with speaker attribution."""
    text: str
    start_time: float
    end_time: float
    speaker_id: str
    channel: Optional[str] = None  # "left", "right", or None for mixed
    confidence: Optional[float] = None

@dataclass
class SpeakerInfo:
    """Information about a detected speaker."""
    speaker_id: str
    channel: Optional[str] = None
    energy_percent: float = 0.0
    silence_percent: float = 0.0
    label: Optional[str] = None  # "Speaker 1", "Speaker 2", etc.

class SpeakerAwareTranscriptionResult(BaseModel):
    """Result of speaker-aware audio transcription."""
    success: bool
    full_text: str
    segments: List[SpeakerSegment]
    processing_duration_ms: int
    model_used: str
    audio_duration_seconds: float
    chunks_processed: int
    # Speaker-specific fields
    has_speakers: bool
    speakers_detected: int
    speaker_separation_method: str
    speaker_info: List[SpeakerInfo]
    error_message: Optional[str] = None
    language_detected: Optional[str] = None

class SpeakerAwareTranscriptionService:
    """Enhanced transcription service with speaker detection for stereo recordings."""

    def __init__(self):
        self.settings = get_settings()
        self.model_id = "NbAiLab/nb-whisper-small"
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        # Audio processing settings
        self.sample_rate = 16000
        self.chunk_length = 30.0
        self.overlap_length = 1.0

        # Speaker detection thresholds
        self.correlation_threshold = 0.6  # Below this = different speakers
        self.energy_ratio_threshold = 1.5  # Above this = significant channel difference

        # Energy ratio filtering settings (OLD METHOD - deprecated)
        self.use_energy_filtering = False  # Disable by default - causes significant content loss
        self.energy_ratio_gate_threshold = 2.0  # Ratio threshold for channel selection
        self.filter_window_ms = 100  # Window size for energy calculation (100ms)

        # Option 3: Unified transcription with energy-based speaker assignment (NEW METHOD)
        self.use_unified_transcription = True  # Transcribe mono, then assign speakers by energy
        self.speaker_energy_threshold = 1.5  # Energy ratio threshold for speaker assignment
        self.keep_unclear_segments = True  # Keep segments where speaker is unclear
        self.unclear_energy_threshold = 1.5  # Below this ratio = unclear speaker

        self.model = None
        self.processor = None
        self.pipe = None

        logger.info(f"SpeakerAwareTranscriptionService initialized with device: {self.device}")
        logger.info(f"Unified transcription: {'enabled' if self.use_unified_transcription else 'disabled'} (energy_threshold={self.speaker_energy_threshold})")
        logger.info(f"Energy ratio filtering (old): {'enabled' if self.use_energy_filtering else 'disabled'} (threshold={self.energy_ratio_gate_threshold})")

    def _ensure_model_loaded(self) -> bool:
        """Ensure the NB-Whisper model is loaded and ready."""
        if self.model is not None and self.processor is not None and self.pipe is not None:
            return True

        try:
            logger.info(f"Loading NB-Whisper model: {self.model_id}")

            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                self.model_id,
                torch_dtype=self.torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True
            )
            self.model.to(self.device)

            self.processor = AutoProcessor.from_pretrained(self.model_id)

            # Create pipeline for timestamp support
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model,
                tokenizer=self.processor.tokenizer,
                feature_extractor=self.processor.feature_extractor,
                device=self.device,
                torch_dtype=self.torch_dtype
            )

            logger.info("NB-Whisper model and pipeline loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load NB-Whisper model: {e}")
            return False

    def _analyze_stereo_separation(self, audio: AudioSegment) -> Tuple[bool, List[SpeakerInfo], str]:
        """
        Analyze stereo audio to determine if channels contain different speakers.

        Returns:
            (has_separation, speaker_info, separation_method)
        """
        if audio.channels != 2:
            return False, [], "mono"

        # Split channels
        left_channel = audio.split_to_mono()[0]
        right_channel = audio.split_to_mono()[1]

        # Calculate energy for each channel
        left_rms = left_channel.rms
        right_rms = right_channel.rms

        # Analyze correlation between channels
        sample_duration = min(30000, len(audio))  # 30 seconds or full duration
        sample_audio = audio[:sample_duration]

        if sample_audio.channels == 2:
            sample_left = sample_audio.split_to_mono()[0]
            sample_right = sample_audio.split_to_mono()[1]

            left_array = np.array(sample_left.get_array_of_samples())
            right_array = np.array(sample_right.get_array_of_samples())

            correlation = 0.99  # Default to high correlation
            if len(left_array) > 0 and len(right_array) > 0:
                correlation = np.corrcoef(left_array, right_array)[0, 1]

            # Calculate energy distribution
            left_energy = np.sum(left_array.astype(np.float64) ** 2)
            right_energy = np.sum(right_array.astype(np.float64) ** 2)
            total_energy = left_energy + right_energy

            if total_energy > 0:
                left_percent = (left_energy / total_energy) * 100
                right_percent = (right_energy / total_energy) * 100
            else:
                left_percent = right_percent = 50.0

            # Calculate silence percentages
            def calculate_silence_percent(channel):
                samples = np.array(channel.get_array_of_samples())
                if len(samples) > 0:
                    silence_threshold = max(50, np.max(np.abs(samples)) * 0.01)
                    silent_samples = np.sum(np.abs(samples) < silence_threshold)
                    return (silent_samples / len(samples)) * 100
                return 100

            left_silence = calculate_silence_percent(left_channel)
            right_silence = calculate_silence_percent(right_channel)

            # Determine if channels are separated
            energy_ratio = max(left_percent, right_percent) / min(left_percent, right_percent) if min(left_percent, right_percent) > 0 else 1

            logger.info(f"Stereo analysis: correlation={correlation:.3f}, energy_ratio={energy_ratio:.2f}")

            if correlation < self.correlation_threshold or energy_ratio > self.energy_ratio_threshold:
                # Good separation detected
                speaker_info = [
                    SpeakerInfo(
                        speaker_id="speaker_1",
                        channel="left",
                        energy_percent=left_percent,
                        silence_percent=left_silence,
                        label="Speaker 1 (Left)"
                    ),
                    SpeakerInfo(
                        speaker_id="speaker_2",
                        channel="right",
                        energy_percent=right_percent,
                        silence_percent=right_silence,
                        label="Speaker 2 (Right)"
                    )
                ]
                return True, speaker_info, "stereo_channels"

        return False, [], "stereo_mixed"

    def _apply_energy_ratio_filtering(self, audio: AudioSegment) -> Tuple[AudioSegment, AudioSegment]:
        """
        Apply Method 3: Energy Ratio Filtering to separate speakers in stereo audio.

        For each time window:
        - If left_energy / right_energy > threshold (2.0): keep left, silence right
        - If left_energy / right_energy < 1/threshold (0.5): keep right, silence left
        - Otherwise: keep both channels (both speaking or unclear)

        Args:
            audio: Stereo AudioSegment

        Returns:
            (filtered_left_channel, filtered_right_channel)
        """
        if audio.channels != 2:
            # Not stereo, return as-is
            mono = audio.set_channels(1)
            return mono, mono

        logger.info(f"Applying energy ratio filtering (window={self.filter_window_ms}ms, threshold={self.energy_ratio_gate_threshold})")

        # Split into left and right channels
        left_channel = audio.split_to_mono()[0]
        right_channel = audio.split_to_mono()[1]

        # Convert to numpy arrays for processing
        left_samples = np.array(left_channel.get_array_of_samples(), dtype=np.float32)
        right_samples = np.array(right_channel.get_array_of_samples(), dtype=np.float32)

        # Calculate window size in samples
        window_size = int((self.filter_window_ms / 1000.0) * audio.frame_rate)

        # Process each window
        num_windows = int(np.ceil(len(left_samples) / window_size))

        filtered_left = np.copy(left_samples)
        filtered_right = np.copy(right_samples)

        logger.info(f"Processing {num_windows} windows of {window_size} samples each")

        windows_kept_left_only = 0
        windows_kept_right_only = 0
        windows_kept_both = 0

        for i in range(num_windows):
            start_idx = i * window_size
            end_idx = min((i + 1) * window_size, len(left_samples))

            # Get window samples
            left_window = left_samples[start_idx:end_idx]
            right_window = right_samples[start_idx:end_idx]

            # Calculate energy (RMS) for each channel in this window
            left_energy = np.sqrt(np.mean(left_window ** 2))
            right_energy = np.sqrt(np.mean(right_window ** 2))

            # Avoid division by zero
            if right_energy < 1e-6:
                right_energy = 1e-6
            if left_energy < 1e-6:
                left_energy = 1e-6

            # Calculate energy ratio
            energy_ratio = left_energy / right_energy

            # Apply filtering based on energy ratio
            if energy_ratio > self.energy_ratio_gate_threshold:
                # Left channel dominates - silence right
                filtered_right[start_idx:end_idx] = 0
                windows_kept_left_only += 1
            elif energy_ratio < (1.0 / self.energy_ratio_gate_threshold):
                # Right channel dominates - silence left
                filtered_left[start_idx:end_idx] = 0
                windows_kept_right_only += 1
            else:
                # Both channels similar - keep both
                windows_kept_both += 1

        logger.info(f"Energy filtering results: {windows_kept_left_only} left-only, {windows_kept_right_only} right-only, {windows_kept_both} both")

        # Convert back to AudioSegment
        filtered_left_int = filtered_left.astype(np.int16)
        filtered_right_int = filtered_right.astype(np.int16)

        filtered_left_audio = AudioSegment(
            filtered_left_int.tobytes(),
            frame_rate=audio.frame_rate,
            sample_width=audio.sample_width,
            channels=1
        )

        filtered_right_audio = AudioSegment(
            filtered_right_int.tobytes(),
            frame_rate=audio.frame_rate,
            sample_width=audio.sample_width,
            channels=1
        )

        return filtered_left_audio, filtered_right_audio

    def _load_and_preprocess_audio(self, audio_file_path: str) -> Tuple[AudioSegment, float]:
        """Load audio file (MP3, M4A, WAV) and return AudioSegment."""
        audio_path = Path(audio_file_path)

        # Load audio with pydub (handles MP3, M4A, WAV)
        audio = AudioSegment.from_file(audio_path)
        duration = len(audio) / 1000.0  # Convert to seconds

        logger.info(f"Loaded {audio_path.suffix} audio: {duration:.1f}s, {audio.channels} channels")
        return audio, duration

    def _transcribe_channel(self, audio_channel: AudioSegment, speaker_id: str) -> List[SpeakerSegment]:
        """Transcribe a single audio channel and return speaker segments with word-level timestamps."""
        try:
            # Convert channel to proper format for NB-Whisper
            audio_mono = audio_channel.set_frame_rate(self.sample_rate).set_channels(1).set_sample_width(2)

            # Convert to numpy array
            audio_array = np.array(audio_mono.get_array_of_samples(), dtype=np.float32)

            # Normalize to [-1, 1] range
            if audio_mono.sample_width == 2:
                audio_array = audio_array / 32768.0
            elif audio_mono.sample_width == 4:
                audio_array = audio_array / 2147483648.0

            logger.info(f"Transcribing {speaker_id} with word-level timestamps (duration: {len(audio_mono)/1000.0:.1f}s)")

            # Use pipeline with word-level timestamps
            result = self.pipe(
                audio_array,
                return_timestamps="word",
                generate_kwargs={
                    "language": "no",
                    "task": "transcribe"
                }
            )

            segments = []

            if "chunks" in result:
                # Process word-level chunks
                for chunk in result["chunks"]:
                    text = chunk.get("text", "").strip()
                    timestamp = chunk.get("timestamp", (0.0, 0.0))

                    if text and timestamp:
                        start_time = timestamp[0] if timestamp[0] is not None else 0.0
                        end_time = timestamp[1] if timestamp[1] is not None else start_time + 1.0

                        segments.append(SpeakerSegment(
                            text=text,
                            start_time=start_time,
                            end_time=end_time,
                            speaker_id=speaker_id
                        ))

            logger.info(f"Extracted {len(segments)} word-level segments for {speaker_id}")

            # Merge word segments into silence-based chunks
            merged_segments = self._merge_segments_by_silence(segments)
            logger.info(f"Merged into {len(merged_segments)} silence-based chunks for {speaker_id}")

            return merged_segments

        except Exception as e:
            logger.error(f"Failed to transcribe channel for {speaker_id}: {e}")
            return []

    def _merge_segments_by_silence(self, word_segments: List[SpeakerSegment]) -> List[SpeakerSegment]:
        """
        Merge word-level segments into larger chunks based on silence intervals.

        A chunk continues as long as the gap between consecutive words is less than
        SILENCE_INTERVAL_SECONDS. When a silence > threshold is detected, a new chunk starts.

        Args:
            word_segments: List of word-level SpeakerSegment objects

        Returns:
            List of merged SpeakerSegment objects (chunks)
        """
        if not word_segments:
            return []

        silence_threshold = self.settings.SILENCE_INTERVAL_SECONDS
        merged_chunks = []

        current_chunk_words = []
        current_chunk_start = None
        current_chunk_end = None
        current_speaker = None

        for segment in word_segments:
            # Initialize first chunk
            if current_chunk_start is None:
                current_chunk_words.append(segment.text)
                current_chunk_start = segment.start_time
                current_chunk_end = segment.end_time
                current_speaker = segment.speaker_id
                continue

            # Calculate silence gap between previous segment and current
            silence_gap = segment.start_time - current_chunk_end

            # If silence gap exceeds threshold, finish current chunk and start new one
            if silence_gap > silence_threshold:
                # Create merged chunk from accumulated words
                merged_chunks.append(SpeakerSegment(
                    text=" ".join(current_chunk_words),
                    start_time=current_chunk_start,
                    end_time=current_chunk_end,
                    speaker_id=current_speaker
                ))

                # Start new chunk
                current_chunk_words = [segment.text]
                current_chunk_start = segment.start_time
                current_chunk_end = segment.end_time
                current_speaker = segment.speaker_id
            else:
                # Continue current chunk
                current_chunk_words.append(segment.text)
                current_chunk_end = segment.end_time

        # Add final chunk
        if current_chunk_words:
            merged_chunks.append(SpeakerSegment(
                text=" ".join(current_chunk_words),
                start_time=current_chunk_start,
                end_time=current_chunk_end,
                speaker_id=current_speaker
            ))

        return merged_chunks

    def _assign_speaker_by_energy(
        self,
        segment: SpeakerSegment,
        left_channel: AudioSegment,
        right_channel: AudioSegment
    ) -> str:
        """
        Assign speaker based on which channel has dominant energy during the segment.

        This is the core of Option 3: Instead of transcribing each channel separately,
        we transcribe the full mono audio and then determine which speaker said each
        segment by comparing the energy levels in the left vs right channels.

        Args:
            segment: Transcribed segment with start_time and end_time
            left_channel: Left audio channel (Speaker 1's microphone)
            right_channel: Right audio channel (Speaker 2's microphone)

        Returns:
            "speaker_1" (left channel dominant)
            "speaker_2" (right channel dominant)
            "speaker_unclear" (both channels have similar energy)
        """
        try:
            # Extract audio slice for this segment's time range
            start_ms = int(segment.start_time * 1000)
            end_ms = int(segment.end_time * 1000)

            # Ensure we don't go beyond audio length
            start_ms = max(0, start_ms)
            end_ms = min(end_ms, len(left_channel))

            # Extract the segment from both channels
            left_slice = left_channel[start_ms:end_ms]
            right_slice = right_channel[start_ms:end_ms]

            # Calculate RMS energy for each channel
            left_energy = left_slice.rms
            right_energy = right_slice.rms

            # Avoid division by zero
            if right_energy < 1:
                right_energy = 1
            if left_energy < 1:
                left_energy = 1

            # Calculate energy ratios
            left_to_right = left_energy / right_energy
            right_to_left = right_energy / left_energy

            # Assign speaker based on energy dominance
            if left_to_right > self.speaker_energy_threshold:
                return "speaker_1"  # Left channel (Speaker 1's mic) is dominant
            elif right_to_left > self.speaker_energy_threshold:
                return "speaker_2"  # Right channel (Speaker 2's mic) is dominant
            else:
                return "speaker_unclear"  # Both channels have similar energy

        except Exception as e:
            logger.warning(f"Error assigning speaker by energy: {e}")
            return "speaker_unclear"

    def _create_audio_chunks_from_segment(self, audio: AudioSegment) -> List[Tuple[AudioSegment, float, float]]:
        """Create overlapping chunks from AudioSegment."""
        chunks = []
        chunk_length_ms = int(self.chunk_length * 1000)
        overlap_length_ms = int(self.overlap_length * 1000)

        if len(audio) <= chunk_length_ms:
            chunks.append((audio, 0.0, len(audio) / 1000.0))
        else:
            start_ms = 0
            while start_ms < len(audio):
                end_ms = min(start_ms + chunk_length_ms, len(audio))

                chunk = audio[start_ms:end_ms]
                start_time = start_ms / 1000.0
                end_time = end_ms / 1000.0

                chunks.append((chunk, start_time, end_time))

                start_ms += chunk_length_ms - overlap_length_ms
                if end_ms >= len(audio):
                    break

        return chunks

    def _transcribe_chunk(self, audio_chunk: np.ndarray) -> str:
        """Transcribe a single audio chunk."""
        try:
            # Ensure correct dtype
            if audio_chunk.dtype != np.float32:
                audio_chunk = audio_chunk.astype(np.float32)

            # Process audio chunk
            inputs = self.processor(
                audio_chunk,
                sampling_rate=self.sample_rate,
                return_tensors="pt"
            )

            # Move to device and convert dtype
            inputs = {k: v.to(self.device).to(self.torch_dtype) for k, v in inputs.items()}

            # Generate transcription
            with torch.no_grad():
                generated_ids = self.model.generate(
                    inputs["input_features"],
                    max_new_tokens=128,
                    do_sample=False,
                    language="no"
                )

            # Decode transcription
            transcription = self.processor.batch_decode(
                generated_ids,
                skip_special_tokens=True
            )[0]

            return transcription.strip()

        except Exception as e:
            logger.error(f"Failed to transcribe chunk: {e}")
            return ""

    def transcribe_audio_with_speakers(self, audio_file_path: str) -> SpeakerAwareTranscriptionResult:
        """
        Transcribe audio file with automatic speaker detection and separation.

        Args:
            audio_file_path: Path to audio file (MP3, M4A, WAV)

        Returns:
            SpeakerAwareTranscriptionResult with speaker-attributed transcription
        """
        start_time = datetime.now(timezone.utc)
        audio_path = Path(audio_file_path)

        if not audio_path.exists():
            return SpeakerAwareTranscriptionResult(
                success=False,
                full_text="",
                segments=[],
                processing_duration_ms=0,
                model_used=self.model_id,
                audio_duration_seconds=0.0,
                chunks_processed=0,
                has_speakers=False,
                speakers_detected=0,
                speaker_separation_method="none",
                speaker_info=[],
                error_message=f"Audio file not found: {audio_file_path}"
            )

        if not self._ensure_model_loaded():
            return SpeakerAwareTranscriptionResult(
                success=False,
                full_text="",
                segments=[],
                processing_duration_ms=0,
                model_used=self.model_id,
                audio_duration_seconds=0.0,
                chunks_processed=0,
                has_speakers=False,
                speakers_detected=0,
                speaker_separation_method="none",
                speaker_info=[],
                error_message="Failed to load transcription model"
            )

        try:
            logger.info(f"Starting speaker-aware transcription of: {audio_path.name}")

            # Load and analyze audio
            audio, audio_duration = self._load_and_preprocess_audio(str(audio_path))

            # Analyze speaker separation
            has_separation, speaker_info, separation_method = self._analyze_stereo_separation(audio)

            all_segments = []
            chunks_processed = 0

            if has_separation and len(speaker_info) == 2:
                # Stereo recording detected - use unified transcription with energy-based assignment
                if self.use_unified_transcription:
                    logger.info("Stereo separation detected - using unified transcription with energy-based speaker assignment")

                    # Split channels for energy analysis (but don't transcribe separately)
                    left_channel = audio.split_to_mono()[0]
                    right_channel = audio.split_to_mono()[1]

                    # Transcribe MONO (merged) to get all content without duplicates
                    mono_audio = audio.set_channels(1)
                    mono_segments = self._transcribe_channel(mono_audio, "speaker_unknown")

                    # Assign speakers based on energy in each segment
                    logger.info(f"Assigning speakers to {len(mono_segments)} segments based on channel energy")
                    for segment in mono_segments:
                        speaker_id = self._assign_speaker_by_energy(segment, left_channel, right_channel)
                        segment.speaker_id = speaker_id

                    # Filter out unclear segments if configured
                    if not self.keep_unclear_segments:
                        original_count = len(mono_segments)
                        mono_segments = [s for s in mono_segments if s.speaker_id != "speaker_unclear"]
                        filtered_count = original_count - len(mono_segments)
                        if filtered_count > 0:
                            logger.info(f"Filtered out {filtered_count} unclear segments (keep_unclear_segments=False)")

                    all_segments.extend(mono_segments)
                    chunks_processed = len(mono_segments)

                    # Update speaker info with detection method
                    for sp_info in speaker_info:
                        sp_info.label = sp_info.label + " (energy-based)"

                else:
                    # OLD METHOD: Transcribe each channel separately (can create duplicates)
                    logger.info("Stereo separation detected - transcribing each channel separately (OLD METHOD)")

                    # Apply energy ratio filtering if enabled
                    if self.use_energy_filtering:
                        left_channel, right_channel = self._apply_energy_ratio_filtering(audio)
                    else:
                        left_channel = audio.split_to_mono()[0]
                        right_channel = audio.split_to_mono()[1]

                    # Transcribe left channel (Speaker 1)
                    left_segments = self._transcribe_channel(left_channel, "speaker_1")
                    all_segments.extend(left_segments)

                    # Transcribe right channel (Speaker 2)
                    right_segments = self._transcribe_channel(right_channel, "speaker_2")
                    all_segments.extend(right_segments)

                    chunks_processed = len(left_segments) + len(right_segments)

            else:
                logger.info("No speaker separation detected - transcribing as mono")

                # Convert to mono and transcribe normally
                mono_audio = audio.set_channels(1)
                mono_segments = self._transcribe_channel(mono_audio, "speaker_unknown")
                all_segments.extend(mono_segments)
                chunks_processed = len(mono_segments)

                # Update speaker info for mono
                speaker_info = [SpeakerInfo(
                    speaker_id="speaker_unknown",
                    channel=None,
                    energy_percent=100.0,
                    silence_percent=0.0,
                    label="Unknown Speaker"
                )]

            # Sort segments by start time
            all_segments.sort(key=lambda x: x.start_time)

            # Create full text
            full_text = self._create_speaker_attributed_text(all_segments)

            # Calculate processing duration
            end_time = datetime.now(timezone.utc)
            processing_duration = int((end_time - start_time).total_seconds() * 1000)

            logger.info(f"Speaker-aware transcription completed: {len(full_text)} characters, {len(all_segments)} segments, {len(speaker_info)} speakers")

            return SpeakerAwareTranscriptionResult(
                success=True,
                full_text=full_text,
                segments=all_segments,
                processing_duration_ms=processing_duration,
                model_used=self.model_id,
                audio_duration_seconds=audio_duration,
                chunks_processed=chunks_processed,
                has_speakers=has_separation,
                speakers_detected=len(speaker_info),
                speaker_separation_method=separation_method,
                speaker_info=speaker_info,
                language_detected="no"
            )

        except Exception as e:
            end_time = datetime.now(timezone.utc)
            processing_duration = int((end_time - start_time).total_seconds() * 1000)

            logger.error(f"Speaker-aware transcription failed for {audio_path.name}: {e}")

            return SpeakerAwareTranscriptionResult(
                success=False,
                full_text="",
                segments=[],
                processing_duration_ms=processing_duration,
                model_used=self.model_id,
                audio_duration_seconds=0.0,
                chunks_processed=0,
                has_speakers=False,
                speakers_detected=0,
                speaker_separation_method="error",
                speaker_info=[],
                error_message=str(e)
            )

    def _create_speaker_attributed_text(self, segments: List[SpeakerSegment]) -> str:
        """Create a readable text with speaker attribution."""
        if not segments:
            return ""

        text_parts = []
        current_speaker = None

        for segment in segments:
            if segment.speaker_id != current_speaker:
                current_speaker = segment.speaker_id
                # Map speaker IDs to readable labels
                if segment.speaker_id == "speaker_1":
                    speaker_label = "Speaker 1"
                elif segment.speaker_id == "speaker_2":
                    speaker_label = "Speaker 2"
                elif segment.speaker_id == "speaker_unclear":
                    speaker_label = "Speaker (unclear)"
                elif segment.speaker_id == "speaker_unknown":
                    speaker_label = "Speaker"
                else:
                    speaker_label = segment.speaker_id

                text_parts.append(f"\n\n[{speaker_label}]: {segment.text}")
            else:
                text_parts.append(f" {segment.text}")

        return "".join(text_parts).strip()

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded transcription model."""
        return {
            "model_id": self.model_id,
            "device": self.device,
            "torch_dtype": str(self.torch_dtype),
            "model_loaded": self.model is not None,
            "cuda_available": torch.cuda.is_available(),
            "speaker_detection": "unified_transcription_with_energy_assignment" if self.use_unified_transcription else "stereo_channel_separation",
            "supported_formats": ["mp3", "m4a", "wav"],
            "correlation_threshold": self.correlation_threshold,
            "energy_ratio_threshold": self.energy_ratio_threshold,
            # Old method (deprecated)
            "energy_filtering_enabled": self.use_energy_filtering,
            "energy_filtering_threshold": self.energy_ratio_gate_threshold,
            "energy_filtering_window_ms": self.filter_window_ms,
            # New method (Option 3)
            "unified_transcription_enabled": self.use_unified_transcription,
            "speaker_energy_threshold": self.speaker_energy_threshold,
            "keep_unclear_segments": self.keep_unclear_segments,
            "unclear_energy_threshold": self.unclear_energy_threshold
        }