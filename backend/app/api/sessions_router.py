"""
API routes for session management and viewing.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..core.database import get_db
from ..core.logging import get_logger
from ..models.db_models import Session as SessionModel, Transcript, SessionMetadata

logger = get_logger()

router = APIRouter(prefix="/sessions", tags=["sessions"])

class SessionResponse(BaseModel):
    """Response model for session information."""
    id: str
    filename: str
    processing_status: str
    created_at: str
    has_transcript: bool
    transcript_preview: Optional[str] = None

class SessionDetailResponse(BaseModel):
    """Detailed response model for a single session."""
    id: str
    filename: str
    processing_status: str
    created_at: str
    has_transcript: bool
    transcript: Optional[dict] = None
    metadata: Optional[dict] = None

@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    limit: int = Query(default=50, le=100),
    search: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Get list of all sessions with basic information.

    Args:
        limit: Maximum number of sessions to return (max 100)
        search: Optional search term to filter by filename
        db: Database session

    Returns:
        List of sessions with basic information
    """
    try:
        logger.info(f"Listing sessions with limit={limit}, search='{search}'")

        # Build query
        query = db.query(SessionModel)

        # Add search filter if provided
        if search:
            query = query.filter(SessionModel.filename.contains(search))

        # Order by creation date (newest first) and apply limit
        sessions = query.order_by(SessionModel.created_at.desc()).limit(limit).all()

        # Prepare response data
        session_responses = []
        for session in sessions:
            # Check if transcript exists
            transcript = db.query(Transcript).filter(Transcript.session_id == session.id).first()
            has_transcript = transcript is not None

            # Get transcript preview (first 100 characters)
            transcript_preview = None
            if has_transcript and transcript.full_text:
                transcript_preview = transcript.full_text[:100] + "..." if len(transcript.full_text) > 100 else transcript.full_text

            session_responses.append(SessionResponse(
                id=session.id,
                filename=session.filename,
                processing_status=session.processing_status,
                created_at=session.created_at.isoformat(),
                has_transcript=has_transcript,
                transcript_preview=transcript_preview
            ))

        logger.info(f"Found {len(session_responses)} sessions")
        return session_responses

    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving sessions: {str(e)}")

@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific session.

    Args:
        session_id: ID of the session to retrieve
        db: Database session

    Returns:
        Detailed session information including full transcript
    """
    try:
        logger.info(f"Getting session detail for: {session_id}")

        # Get session
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

        # Get transcript
        transcript = db.query(Transcript).filter(Transcript.session_id == session_id).first()
        transcript_data = None
        if transcript:
            transcript_data = {
                "full_text": transcript.full_text,
                "segments": transcript.segments,
                "language": transcript.language,
                "model_version": transcript.model_version,
                "processing_duration_ms": transcript.processing_duration_ms,
                "created_at": transcript.created_at.isoformat()
            }

        # Get metadata
        metadata = db.query(SessionMetadata).filter(SessionMetadata.session_id == session_id).first()
        metadata_data = None
        if metadata:
            metadata_data = {
                "participants": metadata.participants,
                "topics": metadata.topics,
                "historical_periods": metadata.historical_periods,
                "location_notes": metadata.location_notes,
                "session_notes": metadata.session_notes,
                "date": metadata.date.isoformat() if metadata.date else None,
                "created_at": metadata.created_at.isoformat()
            }

        response = SessionDetailResponse(
            id=session.id,
            filename=session.filename,
            processing_status=session.processing_status,
            created_at=session.created_at.isoformat(),
            has_transcript=transcript is not None,
            transcript=transcript_data,
            metadata=metadata_data
        )

        logger.info(f"Retrieved session detail for: {session.filename}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session detail for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving session: {str(e)}")

@router.get("/search/{search_term}", response_model=List[SessionResponse])
async def search_sessions(
    search_term: str,
    limit: int = Query(default=20, le=50),
    db: Session = Depends(get_db)
):
    """
    Search sessions by filename or transcript content.

    Args:
        search_term: Term to search for
        limit: Maximum number of results (max 50)
        db: Database session

    Returns:
        List of matching sessions
    """
    try:
        logger.info(f"Searching sessions for: '{search_term}'")

        # Search by filename
        filename_matches = db.query(SessionModel).filter(
            SessionModel.filename.contains(search_term)
        ).order_by(SessionModel.created_at.desc()).limit(limit).all()

        # Search by transcript content
        transcript_matches = db.query(SessionModel).join(Transcript).filter(
            Transcript.full_text.contains(search_term)
        ).order_by(SessionModel.created_at.desc()).limit(limit).all()

        # Combine and deduplicate results
        all_sessions = {session.id: session for session in filename_matches + transcript_matches}
        sessions = list(all_sessions.values())[:limit]

        # Prepare response
        session_responses = []
        for session in sessions:
            transcript = db.query(Transcript).filter(Transcript.session_id == session.id).first()
            has_transcript = transcript is not None

            # Get transcript preview with search term highlighted
            transcript_preview = None
            if has_transcript and transcript.full_text:
                text = transcript.full_text
                if search_term.lower() in text.lower():
                    # Find search term and show context
                    index = text.lower().find(search_term.lower())
                    start = max(0, index - 50)
                    end = min(len(text), index + len(search_term) + 50)
                    preview = text[start:end]
                    transcript_preview = f"...{preview}..." if start > 0 or end < len(text) else preview
                else:
                    transcript_preview = text[:100] + "..." if len(text) > 100 else text

            session_responses.append(SessionResponse(
                id=session.id,
                filename=session.filename,
                processing_status=session.processing_status,
                created_at=session.created_at.isoformat(),
                has_transcript=has_transcript,
                transcript_preview=transcript_preview
            ))

        logger.info(f"Found {len(session_responses)} matching sessions")
        return session_responses

    except Exception as e:
        logger.error(f"Error searching sessions for '{search_term}': {e}")
        raise HTTPException(status_code=500, detail=f"Error searching sessions: {str(e)}")