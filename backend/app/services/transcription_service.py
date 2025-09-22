"""
Enhanced transcription service using NB-Whisper with proper audio chunking for long recordings.
"""

import torch
import librosa
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass

from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
from pydantic import BaseModel

from ..core.logging import get_logger
from ..core.config import get_settings

logger = get_logger()

@dataclass
class TranscriptionSegment:
    """Represents a timestamped segment of transcription."""
    text: str
    start_time: float
    end_time: float
    confidence: Optional[float] = None

class TranscriptionResult(BaseModel):
    """Result of audio transcription."""
    success: bool
    full_text: str
    segments: List[TranscriptionSegment]
    processing_duration_ms: int
    model_used: str
    audio_duration_seconds: float
    chunks_processed: int
    error_message: Optional[str] = None
    language_detected: Optional[str] = None

class TranscriptionService:
    """Enhanced service for transcribing audio files using NB-Whisper with proper chunking."""

    def __init__(self):
        self.settings = get_settings()
        self.model_id = "NbAiLab/nb-whisper-small"
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        # Audio processing settings
        self.sample_rate = 16000  # NB-Whisper expects 16kHz
        self.chunk_length = 30.0  # 30 seconds per chunk
        self.overlap_length = 1.0  # 1 second overlap between chunks

        self.model = None
        self.processor = None

        logger.info(f"TranscriptionService initialized with device: {self.device}")

    def _ensure_model_loaded(self) -> bool:
        """Ensure the NB-Whisper model is loaded and ready."""
        if self.model is not None and self.processor is not None:
            return True

        try:
            logger.info(f"Loading NB-Whisper model: {self.model_id}")

            # Load model
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                self.model_id,
                torch_dtype=self.torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True
            )
            self.model.to(self.device)

            # Load processor
            self.processor = AutoProcessor.from_pretrained(self.model_id)

            logger.info("NB-Whisper model loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load NB-Whisper model: {e}")
            return False

    def _load_and_preprocess_audio(self, audio_file_path: str) -> Tuple[np.ndarray, float]:
        """
        Load audio file and preprocess it for transcription.

        Returns:
            Tuple of (audio_array, duration_seconds)
        """
        # Load audio with librosa, resample to 16kHz
        audio, _ = librosa.load(audio_file_path, sr=self.sample_rate, mono=True)
        duration = len(audio) / self.sample_rate

        logger.info(f"Loaded audio: {duration:.1f}s, {len(audio)} samples")
        return audio, duration

    def _create_audio_chunks(self, audio: np.ndarray) -> List[Tuple[np.ndarray, float, float]]:
        """
        Split long audio into overlapping chunks for processing.

        Returns:
            List of (chunk_audio, start_time, end_time) tuples
        """
        chunks = []
        chunk_samples = int(self.chunk_length * self.sample_rate)
        overlap_samples = int(self.overlap_length * self.sample_rate)

        if len(audio) <= chunk_samples:
            # Audio is short enough, return as single chunk
            chunks.append((audio, 0.0, len(audio) / self.sample_rate))
        else:
            # Split into overlapping chunks
            start_sample = 0
            while start_sample < len(audio):
                end_sample = min(start_sample + chunk_samples, len(audio))

                chunk_audio = audio[start_sample:end_sample]
                start_time = start_sample / self.sample_rate
                end_time = end_sample / self.sample_rate

                chunks.append((chunk_audio, start_time, end_time))

                # Move start for next chunk (with overlap)
                start_sample += chunk_samples - overlap_samples

                if end_sample >= len(audio):
                    break

        logger.info(f"Created {len(chunks)} audio chunks")
        return chunks

    def _transcribe_chunk(self, audio_chunk: np.ndarray) -> str:
        """Transcribe a single audio chunk."""
        try:
            # Convert to float32 if needed and ensure proper range
            if audio_chunk.dtype != np.float32:
                audio_chunk = audio_chunk.astype(np.float32)

            # Process audio chunk
            inputs = self.processor(
                audio_chunk,
                sampling_rate=self.sample_rate,
                return_tensors="pt"
            )

            # Move inputs to device and convert to correct dtype
            inputs = {k: v.to(self.device).to(self.torch_dtype) for k, v in inputs.items()}

            # Generate transcription
            with torch.no_grad():
                generated_ids = self.model.generate(
                    inputs["input_features"],
                    max_new_tokens=128,
                    do_sample=False,
                    language="no"  # Force Norwegian
                )

            # Decode the transcription
            transcription = self.processor.batch_decode(
                generated_ids,
                skip_special_tokens=True
            )[0]

            return transcription.strip()

        except Exception as e:
            logger.error(f"Failed to transcribe chunk: {e}")
            return ""

    def transcribe_audio(self, audio_file_path: str) -> TranscriptionResult:
        """
        Transcribe an audio file using NB-Whisper with proper chunking.

        Args:
            audio_file_path: Path to the audio file

        Returns:
            TranscriptionResult with full text and timestamped segments
        """
        start_time = datetime.now(timezone.utc)
        audio_path = Path(audio_file_path)

        if not audio_path.exists():
            return TranscriptionResult(
                success=False,
                full_text="",
                segments=[],
                processing_duration_ms=0,
                model_used=self.model_id,
                audio_duration_seconds=0.0,
                chunks_processed=0,
                error_message=f"Audio file not found: {audio_file_path}"
            )

        if not self._ensure_model_loaded():
            return TranscriptionResult(
                success=False,
                full_text="",
                segments=[],
                processing_duration_ms=0,
                model_used=self.model_id,
                audio_duration_seconds=0.0,
                chunks_processed=0,
                error_message="Failed to load transcription model"
            )

        try:
            logger.info(f"Starting transcription of: {audio_path.name}")

            # Load and preprocess audio
            audio, audio_duration = self._load_and_preprocess_audio(str(audio_path))

            # Create audio chunks
            chunks = self._create_audio_chunks(audio)

            # Transcribe each chunk
            segments = []
            full_text_parts = []

            for i, (chunk_audio, start_time_chunk, end_time_chunk) in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)} ({start_time_chunk:.1f}s - {end_time_chunk:.1f}s)")

                chunk_text = self._transcribe_chunk(chunk_audio)

                if chunk_text:
                    # Remove overlap text from previous chunk (simple approach)
                    if i > 0 and len(full_text_parts) > 0:
                        # Check for word overlap and remove duplicates
                        prev_words = full_text_parts[-1].split()[-3:]  # Last 3 words
                        chunk_words = chunk_text.split()

                        # Find overlap and remove from current chunk
                        for j in range(min(len(prev_words), len(chunk_words))):
                            if prev_words[-j-1:] == chunk_words[:j+1]:
                                chunk_text = " ".join(chunk_words[j+1:])
                                break

                    if chunk_text.strip():
                        segments.append(TranscriptionSegment(
                            text=chunk_text,
                            start_time=start_time_chunk,
                            end_time=end_time_chunk,
                            confidence=None
                        ))
                        full_text_parts.append(chunk_text)

            # Combine all text
            full_text = " ".join(full_text_parts).strip()

            # Calculate processing duration
            end_time = datetime.now(timezone.utc)
            processing_duration = int((end_time - start_time).total_seconds() * 1000)

            logger.info(f"Transcription completed: {len(full_text)} characters, {len(segments)} segments")

            return TranscriptionResult(
                success=True,
                full_text=full_text,
                segments=segments,
                processing_duration_ms=processing_duration,
                model_used=self.model_id,
                audio_duration_seconds=audio_duration,
                chunks_processed=len(chunks),
                language_detected="no"
            )

        except Exception as e:
            end_time = datetime.now(timezone.utc)
            processing_duration = int((end_time - start_time).total_seconds() * 1000)

            logger.error(f"Transcription failed for {audio_path.name}: {e}")

            return TranscriptionResult(
                success=False,
                full_text="",
                segments=[],
                processing_duration_ms=processing_duration,
                model_used=self.model_id,
                audio_duration_seconds=0.0,
                chunks_processed=0,
                error_message=str(e)
            )

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded transcription model."""
        return {
            "model_id": self.model_id,
            "device": self.device,
            "torch_dtype": str(self.torch_dtype),
            "model_loaded": self.model is not None,
            "cuda_available": torch.cuda.is_available(),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "gpu_memory_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3 if torch.cuda.is_available() else None,
            "sample_rate": self.sample_rate,
            "chunk_length": self.chunk_length,
            "overlap_length": self.overlap_length
        }

    def check_dependencies(self) -> Dict[str, bool]:
        """Check if all dependencies for transcription are available."""
        deps = {}

        try:
            import torch
            deps['torch'] = True
        except ImportError:
            deps['torch'] = False

        try:
            import transformers
            deps['transformers'] = True
        except ImportError:
            deps['transformers'] = False

        try:
            import librosa
            deps['librosa'] = True
        except ImportError:
            deps['librosa'] = False

        deps['cuda'] = torch.cuda.is_available()

        try:
            from transformers import AutoProcessor
            AutoProcessor.from_pretrained(self.model_id)
            deps['nb_whisper_model'] = True
        except Exception:
            deps['nb_whisper_model'] = False

        return deps

    def unload_model(self):
        """Unload the model to free memory."""
        if self.model is not None:
            del self.model
            self.model = None

        if self.processor is not None:
            del self.processor
            self.processor = None

        # Clear CUDA cache if using GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info("Transcription model unloaded")