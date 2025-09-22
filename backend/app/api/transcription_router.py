"""
API routes for audio transcription using NB-Whisper.
"""

import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..core.database import get_db
from ..core.logging import get_logger
from ..models.db_models import Session as SessionModel, Transcript
from ..services.transcription_service import TranscriptionService

logger = get_logger()

router = APIRouter(prefix="/transcription", tags=["transcription"])

# Initialize transcription service (singleton)
transcription_service = TranscriptionService()

class TranscriptionResponse(BaseModel):
    """Response model for transcription results."""
    session_id: str
    success: bool
    full_text: str
    segments_count: int
    processing_duration_ms: int
    audio_duration_seconds: float
    chunks_processed: int
    model_used: str
    error_message: str = None

@router.post("/transcribe/{filename}", response_model=TranscriptionResponse)
async def transcribe_audio_file(
    filename: str,
    db: Session = Depends(get_db)
):
    """
    Transcribe an audio file and store the result in the database.

    Args:
        filename: Name of the audio file (should be WAV format)
        db: Database session

    Returns:
        TranscriptionResponse with transcription results
    """
    try:
        logger.info(f"Starting transcription for file: {filename}")

        # Check if file exists in converted audio files
        audio_path = Path("audio_files/converted") / filename
        if not audio_path.exists():
            # Also check original files
            audio_path = Path("audio_files/originals") / filename
            if not audio_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Audio file not found: {filename}"
                )

        # Check if session already exists for this filename
        existing_session = db.query(SessionModel).filter(
            SessionModel.filename == filename
        ).first()

        if existing_session:
            session_id = existing_session.id
            # Check if transcript already exists
            existing_transcript = db.query(Transcript).filter(
                Transcript.session_id == session_id
            ).first()

            if existing_transcript:
                logger.info(f"Transcript already exists for {filename}, returning existing result")
                return TranscriptionResponse(
                    session_id=session_id,
                    success=True,
                    full_text=existing_transcript.full_text or "",
                    segments_count=len(existing_transcript.segments) if existing_transcript.segments else 0,
                    processing_duration_ms=existing_transcript.processing_duration_ms or 0,
                    audio_duration_seconds=0.0,  # Not stored in existing model
                    chunks_processed=0,  # Not stored in existing model
                    model_used=existing_transcript.model_version or "unknown"
                )
        else:
            # Create new session
            session_id = str(uuid.uuid4())
            new_session = SessionModel(
                id=session_id,
                filename=filename,
                converted_path=str(audio_path),
                processing_status="transcribing"
            )
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            logger.info(f"Created new session {session_id} for {filename}")

        # Perform transcription
        logger.info(f"Starting transcription process for {filename}")
        result = transcription_service.transcribe_audio(str(audio_path))

        if result.success:
            # Prepare segments for JSON storage
            segments_json = [
                {
                    "text": segment.text,
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "confidence": segment.confidence
                }
                for segment in result.segments
            ]

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
            else:
                # Create new transcript
                transcript = Transcript(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    full_text=result.full_text,
                    segments=segments_json,
                    language=result.language_detected,
                    model_version=result.model_used,
                    processing_duration_ms=result.processing_duration_ms
                )
                db.add(transcript)

            # Update session status
            if existing_session:
                existing_session.processing_status = "transcribed"
            else:
                new_session.processing_status = "transcribed"

            db.commit()

            logger.info(f"Transcription completed and saved for {filename}")

            return TranscriptionResponse(
                session_id=session_id,
                success=True,
                full_text=result.full_text,
                segments_count=len(result.segments),
                processing_duration_ms=result.processing_duration_ms,
                audio_duration_seconds=result.audio_duration_seconds,
                chunks_processed=result.chunks_processed,
                model_used=result.model_used
            )

        else:
            # Update session with error status
            if existing_session:
                existing_session.processing_status = "error"
            else:
                new_session.processing_status = "error"
            db.commit()

            logger.error(f"Transcription failed for {filename}: {result.error_message}")

            return TranscriptionResponse(
                session_id=session_id,
                success=False,
                full_text="",
                segments_count=0,
                processing_duration_ms=result.processing_duration_ms,
                audio_duration_seconds=0.0,
                chunks_processed=0,
                model_used=result.model_used,
                error_message=result.error_message
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during transcription of {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during transcription: {str(e)}"
        )

@router.get("/status")
async def transcription_status():
    """Get transcription service status and model information."""
    try:
        model_info = transcription_service.get_model_info()
        dependencies = transcription_service.check_dependencies()

        return {
            "status": "ready" if all(dependencies.values()) else "not_ready",
            "model_info": model_info,
            "dependencies": dependencies
        }
    except Exception as e:
        logger.error(f"Error getting transcription status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting transcription status: {str(e)}"
        )

@router.get("/models")
async def available_models():
    """Get information about available transcription models."""
    return {
        "current_model": "NbAiLab/nb-whisper-small",
        "language": "Norwegian (Bokmål)",
        "description": "Small Norwegian Whisper model optimized for historical recordings",
        "features": [
            "GPU accelerated (CUDA)",
            "Chunked processing for long recordings",
            "Timestamped segments",
            "Overlap handling"
        ]
    }