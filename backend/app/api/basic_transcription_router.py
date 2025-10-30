"""
API routes for basic audio transcription (mono, no speaker awareness).
Uses NB-Whisper for Norwegian language transcription without speaker detection.
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
from ..services.transcription_service import TranscriptionService

logger = get_logger()

router = APIRouter(prefix="/transcription", tags=["transcription"])

# Initialize basic transcription service
transcription_service = TranscriptionService()

class BasicTranscriptionResponse(BaseModel):
    """Response model for basic transcription results."""
    session_id: str
    success: bool
    full_text: str
    segments_count: int
    processing_duration_ms: int
    audio_duration_seconds: float
    chunks_processed: int
    model_used: str
    error_message: Optional[str] = None

@router.get("/status")
async def transcription_status():
    """Get basic transcription service status and model information."""
    try:
        model_info = {
            "model_id": transcription_service.model_id,
            "device": transcription_service.device,
            "model_loaded": transcription_service.model is not None,
            "audio_mode": "mono",
            "speaker_detection": "none"
        }

        return {
            "status": "ready",
            "service": "basic-transcription",
            "model_info": model_info,
            "supported_formats": ["wav"],
            "features": [
                "Norwegian language (NB-Whisper)",
                "GPU acceleration with CUDA",
                "Automatic chunking for long audio",
                "Mono audio processing"
            ]
        }
    except Exception as e:
        logger.error(f"Error getting transcription status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting transcription status: {str(e)}"
        )

@router.post("/transcribe/{filename}", response_model=BasicTranscriptionResponse)
async def transcribe_basic(
    filename: str,
    db: Session = Depends(get_db),
    force_retranscribe: bool = Query(default=False, description="Force re-transcription even if exists")
):
    """
    Transcribe an audio file using basic transcription (mono, no speaker detection).

    Args:
        filename: Name of the audio file (WAV format)
        db: Database session
        force_retranscribe: Force re-transcription even if transcript exists

    Returns:
        BasicTranscriptionResponse with transcription results
    """
    try:
        logger.info(f"Starting basic transcription for file: {filename}")

        # Look for file in multiple locations
        audio_path = None
        search_dirs = [
            Path("audio_files/converted"),
            Path("audio_files/originals")
        ]

        for search_dir in search_dirs:
            test_path = search_dir / filename
            if test_path.exists():
                audio_path = test_path
                break

        if not audio_path:
            raise HTTPException(
                status_code=404,
                detail=f"Audio file not found: {filename}"
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

            # Only return existing if it's a basic transcript (no speaker info)
            if existing_transcript and not force_retranscribe:
                # Check if this is a basic transcript (no speaker_info field or empty)
                is_basic = not existing_transcript.speaker_info or len(existing_transcript.speaker_info) == 0

                if is_basic:
                    logger.info(f"Using existing basic transcript for {filename}")

                    segments_count = len(existing_transcript.segments) if existing_transcript.segments else 0

                    return BasicTranscriptionResponse(
                        session_id=session_id,
                        success=True,
                        full_text=existing_transcript.full_text or "",
                        segments_count=segments_count,
                        processing_duration_ms=existing_transcript.processing_duration_ms or 0,
                        audio_duration_seconds=0.0,
                        chunks_processed=segments_count,
                        model_used=existing_transcript.model_version or "unknown"
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

        # Perform basic transcription
        logger.info(f"Starting basic transcription process for {filename}")
        result = transcription_service.transcribe_audio(str(audio_path))

        if result.success:
            # Prepare segments for JSON storage (without speaker info)
            segments_json = []
            for segment in result.segments:
                segments_json.append({
                    "text": segment.text,
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "confidence": segment.confidence
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
                # Clear speaker fields for basic transcription
                existing_transcript.has_speakers = "false"
                existing_transcript.speaker_separation_method = "none"
                existing_transcript.speakers_detected = 0
                existing_transcript.speaker_info = []
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
                    has_speakers="false",
                    speaker_separation_method="none",
                    speakers_detected=0,
                    speaker_info=[]
                )
                db.add(transcript)

            # Update session status
            if existing_session:
                existing_session.processing_status = "transcribed"
            else:
                new_session.processing_status = "transcribed"

            db.commit()

            logger.info(f"Basic transcription completed and saved for {filename}")

            return BasicTranscriptionResponse(
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

            logger.error(f"Basic transcription failed for {filename}: {result.error_message}")

            return BasicTranscriptionResponse(
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
        logger.error(f"Unexpected error during basic transcription of {filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during transcription: {str(e)}"
        )
