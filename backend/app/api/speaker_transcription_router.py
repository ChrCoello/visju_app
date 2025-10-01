"""
API routes for speaker-aware audio transcription with support for MP3, M4A, and WAV files.
"""

import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from ..core.database import get_db
from ..core.logging import get_logger
from ..models.db_models import Session as SessionModel, Transcript
from ..services.speaker_aware_transcription_service import SpeakerAwareTranscriptionService

logger = get_logger()

router = APIRouter(prefix="/transcription", tags=["transcription"])

# Initialize speaker-aware transcription service
speaker_transcription_service = SpeakerAwareTranscriptionService()

class SpeakerInfo(BaseModel):
    """Speaker information model."""
    speaker_id: str
    channel: Optional[str] = None
    energy_percent: float
    silence_percent: float
    label: Optional[str] = None

class SpeakerSegment(BaseModel):
    """Transcription segment with speaker attribution."""
    text: str
    start_time: float
    end_time: float
    speaker_id: str
    channel: Optional[str] = None
    confidence: Optional[float] = None

class SpeakerTranscriptionResponse(BaseModel):
    """Response model for speaker-aware transcription results."""
    session_id: str
    success: bool
    full_text: str
    segments: List[SpeakerSegment]
    processing_duration_ms: int
    audio_duration_seconds: float
    chunks_processed: int
    model_used: str
    # Speaker-specific fields
    has_speakers: bool
    speakers_detected: int
    speaker_separation_method: str
    speaker_info: List[SpeakerInfo]
    error_message: Optional[str] = None

@router.post("/transcribe/{filename}", response_model=SpeakerTranscriptionResponse)
async def transcribe_audio_with_speakers(
    filename: str,
    db: Session = Depends(get_db),
    force_retranscribe: bool = Query(default=False, description="Force re-transcription even if exists")
):
    """
    Transcribe an audio file with automatic speaker detection and store results in database.

    Supports MP3, M4A, and WAV files with automatic speaker separation for stereo recordings.

    Args:
        filename: Name of the audio file
        db: Database session
        force_retranscribe: Force re-transcription even if transcript exists

    Returns:
        SpeakerTranscriptionResponse with speaker-attributed transcription
    """
    try:
        logger.info(f"Starting speaker-aware transcription for file: {filename}")

        # Look for file in multiple locations and formats
        audio_path = None
        supported_extensions = ['.mp3', '.m4a', '.wav']
        search_dirs = [
            Path("audio_files/originals"),
            Path("audio_files/converted"),
            Path("audio_files/channels")
        ]

        # Try exact filename first
        for search_dir in search_dirs:
            test_path = search_dir / filename
            if test_path.exists():
                audio_path = test_path
                break

        # If not found, try different extensions
        if not audio_path:
            base_name = Path(filename).stem
            for search_dir in search_dirs:
                for ext in supported_extensions:
                    test_path = search_dir / (base_name + ext)
                    if test_path.exists():
                        audio_path = test_path
                        break
                if audio_path:
                    break

        if not audio_path:
            raise HTTPException(
                status_code=404,
                detail=f"Audio file not found: {filename} (searched MP3, M4A, WAV formats)"
            )

        logger.info(f"Found audio file: {audio_path}")

        # Check if session exists
        existing_session = db.query(SessionModel).filter(
            SessionModel.filename == filename
        ).first()

        if existing_session:
            session_id = existing_session.id

            # Check if transcript exists and if we should reuse it
            existing_transcript = db.query(Transcript).filter(
                Transcript.session_id == session_id
            ).first()

            if existing_transcript and not force_retranscribe:
                logger.info(f"Using existing transcript for {filename}")

                # Convert database segments to response format
                segments = []
                if existing_transcript.segments:
                    for seg in existing_transcript.segments:
                        segments.append(SpeakerSegment(
                            text=seg.get('text', ''),
                            start_time=seg.get('start_time', 0.0),
                            end_time=seg.get('end_time', 0.0),
                            speaker_id=seg.get('speaker_id', 'speaker_unknown'),
                            channel=seg.get('channel'),
                            confidence=seg.get('confidence')
                        ))

                # Convert speaker info
                speaker_info = []
                if existing_transcript.speaker_info:
                    for speaker in existing_transcript.speaker_info:
                        speaker_info.append(SpeakerInfo(
                            speaker_id=speaker.get('speaker_id', ''),
                            channel=speaker.get('channel'),
                            energy_percent=speaker.get('energy_percent', 0.0),
                            silence_percent=speaker.get('silence_percent', 0.0),
                            label=speaker.get('label')
                        ))

                return SpeakerTranscriptionResponse(
                    session_id=session_id,
                    success=True,
                    full_text=existing_transcript.full_text or "",
                    segments=segments,
                    processing_duration_ms=existing_transcript.processing_duration_ms or 0,
                    audio_duration_seconds=0.0,  # Not stored in existing model
                    chunks_processed=0,  # Not stored in existing model
                    model_used=existing_transcript.model_version or "unknown",
                    has_speakers=existing_transcript.has_speakers == "true",
                    speakers_detected=existing_transcript.speakers_detected or 1,
                    speaker_separation_method=existing_transcript.speaker_separation_method or "unknown",
                    speaker_info=speaker_info
                )
        else:
            # Create new session
            session_id = str(uuid.uuid4())
            new_session = SessionModel(
                id=session_id,
                filename=filename,
                original_path=str(audio_path),
                processing_status="transcribing"
            )
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            logger.info(f"Created new session {session_id} for {filename}")

        # Perform speaker-aware transcription
        logger.info(f"Starting speaker-aware transcription process for {filename}")
        result = speaker_transcription_service.transcribe_audio_with_speakers(str(audio_path))

        if result.success:
            # Prepare segments for JSON storage
            segments_json = []
            for segment in result.segments:
                segments_json.append({
                    "text": segment.text,
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "speaker_id": segment.speaker_id,
                    "channel": segment.channel,
                    "confidence": segment.confidence
                })

            # Prepare speaker info for JSON storage
            speaker_info_json = []
            for speaker in result.speaker_info:
                speaker_info_json.append({
                    "speaker_id": speaker.speaker_id,
                    "channel": speaker.channel,
                    "energy_percent": speaker.energy_percent,
                    "silence_percent": speaker.silence_percent,
                    "label": speaker.label
                })

            # Create or update transcript record
            existing_transcript = db.query(Transcript).filter(
                Transcript.session_id == session_id
            ).first()

            if existing_transcript:
                # Update existing transcript
                existing_transcript.full_text = result.full_text
                existing_transcript.segments = segments_json
                existing_transcript.language = result.language_detected
                existing_transcript.model_version = result.model_used
                existing_transcript.processing_duration_ms = result.processing_duration_ms
                existing_transcript.has_speakers = "true" if result.has_speakers else "false"
                existing_transcript.speaker_separation_method = result.speaker_separation_method
                existing_transcript.speakers_detected = result.speakers_detected
                existing_transcript.speaker_info = speaker_info_json
            else:
                # Create new transcript
                transcript = Transcript(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    full_text=result.full_text,
                    segments=segments_json,
                    language=result.language_detected,
                    model_version=result.model_used,
                    processing_duration_ms=result.processing_duration_ms,
                    has_speakers="true" if result.has_speakers else "false",
                    speaker_separation_method=result.speaker_separation_method,
                    speakers_detected=result.speakers_detected,
                    speaker_info=speaker_info_json
                )
                db.add(transcript)

            # Update session status
            if existing_session:
                existing_session.processing_status = "transcribed"
            else:
                new_session.processing_status = "transcribed"

            db.commit()

            logger.info(f"Speaker-aware transcription completed and saved for {filename}")

            # Convert result to response format
            response_segments = []
            for segment in result.segments:
                response_segments.append(SpeakerSegment(
                    text=segment.text,
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    speaker_id=segment.speaker_id,
                    channel=segment.channel,
                    confidence=segment.confidence
                ))

            response_speakers = []
            for speaker in result.speaker_info:
                response_speakers.append(SpeakerInfo(
                    speaker_id=speaker.speaker_id,
                    channel=speaker.channel,
                    energy_percent=speaker.energy_percent,
                    silence_percent=speaker.silence_percent,
                    label=speaker.label
                ))

            return SpeakerTranscriptionResponse(
                session_id=session_id,
                success=True,
                full_text=result.full_text,
                segments=response_segments,
                processing_duration_ms=result.processing_duration_ms,
                audio_duration_seconds=result.audio_duration_seconds,
                chunks_processed=result.chunks_processed,
                model_used=result.model_used,
                has_speakers=result.has_speakers,
                speakers_detected=result.speakers_detected,
                speaker_separation_method=result.speaker_separation_method,
                speaker_info=response_speakers
            )

        else:
            # Update session with error status
            if existing_session:
                existing_session.processing_status = "error"
            else:
                new_session.processing_status = "error"
            db.commit()

            logger.error(f"Speaker-aware transcription failed for {filename}: {result.error_message}")

            return SpeakerTranscriptionResponse(
                session_id=session_id,
                success=False,
                full_text="",
                segments=[],
                processing_duration_ms=result.processing_duration_ms,
                audio_duration_seconds=0.0,
                chunks_processed=0,
                model_used=result.model_used,
                has_speakers=False,
                speakers_detected=0,
                speaker_separation_method="error",
                speaker_info=[],
                error_message=result.error_message
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during speaker-aware transcription of {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during transcription: {str(e)}"
        )

@router.get("/status")
async def speaker_transcription_status():
    """Get speaker-aware transcription service status and model information."""
    try:
        model_info = speaker_transcription_service.get_model_info()

        return {
            "status": "ready",
            "service": "speaker-aware-transcription",
            "model_info": model_info,
            "supported_formats": ["mp3", "m4a", "wav"],
            "speaker_detection": "automatic_stereo_channel_separation"
        }
    except Exception as e:
        logger.error(f"Error getting speaker transcription status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting transcription status: {str(e)}"
        )

