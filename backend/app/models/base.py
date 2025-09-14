from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class AudioFile(BaseModel):
    drive_id: str
    filename: str
    size_bytes: int
    upload_timestamp: datetime
    status: Literal["detected", "downloading", "processing", "complete"]


class AudioMetadata(BaseModel):
    duration_seconds: float
    bitrate: int
    sample_rate: int
    file_size_mb: float
    format: str = "m4a"


class ConversionResult(BaseModel):
    original_path: str
    converted_path: str
    conversion_duration_ms: int
    success: bool
    error_message: Optional[str] = None


class SessionMetadata(BaseModel):
    session_id: str
    date: datetime
    participants: List[str]
    topics: List[str]
    historical_periods: List[str]
    location_notes: Optional[str] = None
    session_notes: Optional[str] = None


class TranscriptSegment(BaseModel):
    start_time: float
    end_time: float
    text: str
    confidence: float
    speaker_id: Optional[str] = None


class Transcript(BaseModel):
    session_id: str
    segments: List[TranscriptSegment]
    language: str = "nb"
    model_version: str
    processing_duration_ms: int


class ExtractedTag(BaseModel):
    category: Literal["time_period", "person", "place", "practice", "event"]
    value: str
    confidence: float
    context: str


class TagExtractionResult(BaseModel):
    session_id: str
    tags: List[ExtractedTag]
    processing_model: str
    extraction_timestamp: datetime


class SessionSummary(BaseModel):
    session_id: str
    key_points: List[str]
    historical_insights: List[str]
    questions_raised: List[str]
    related_sessions: List[str]
    summary_text: str


class SearchQuery(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10
    search_type: Literal["text", "semantic", "tags"] = "text"


class SearchResult(BaseModel):
    session_id: str
    relevance_score: float
    matching_segments: List[TranscriptSegment]
    summary: str


class ExportConfig(BaseModel):
    session_ids: List[str]
    include_audio: bool = True
    include_transcript: bool = True
    include_summary: bool = True
    include_tags: bool = True
    format: Literal["pdf", "json", "complete"] = "pdf"


class Speaker(BaseModel):
    speaker_id: str
    label: str
    segments: List[tuple[float, float]]