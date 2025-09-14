# WORKFILE.md - Vidarshov Gård Historical Recording App

## Project Overview
Building an application to record, transcribe, and analyze conversations with a historian about Vidarshov Gård farm in Ridabu, Norway. The app processes M4A audio files from Easy Voice Recorder (Android) uploaded to Google Drive, transcribes them using NB-Whisper, and provides intelligent analysis using LLMs.

## Technical Stack
- **Backend Framework**: FastAPI
- **Data Models**: Pydantic
- **LLM Integration**: Pydantic AI
- **Logging/Observability**: Logfire
- **Database**: SQLite with SQLAlchemy ORM
- **Audio Processing**: Pydub + FFmpeg
- **Transcription**: NB-Whisper (Norwegian)
- **Search**: SQLite FTS5
- **Cloud Storage**: Google Drive API

## Audio Source Configuration
- **Recording Device**: RØDE Wireless Me microphone system
- **Recording App**: Easy Voice Recorder (Android)
- **Audio Format**: M4A (AAC MP4, 44kHz sample rate)
- **Storage**: Automatic upload to Google Drive folder
- **Processing**: M4A preserved as original, converted to WAV for transcription

## Complete Processing Workflow

### 1. File Detection & Monitoring
**Objective**: Detect new M4A files uploaded to Google Drive

**Implementation Steps**:
- Set up Google Drive API authentication
- Monitor specific Drive folder for new M4A files
- Implement file completion detection (avoid partial uploads)
- Queue files for processing using FastAPI background tasks

**Technologies**:
- `watchdog` - File system monitoring
- `google-api-python-client` - Drive API integration
- `FastAPI BackgroundTasks` - Async processing queue
- `Pydantic` - File metadata models
- `Logfire` - Monitor detection events and errors

**Key Models**:
```python
class AudioFile(BaseModel):
    drive_id: str
    filename: str
    size_bytes: int
    upload_timestamp: datetime
    status: Literal["detected", "downloading", "processing", "complete"]
```

### 2. File Download & Validation
**Objective**: Download M4A files locally and validate integrity

**Implementation Steps**:
- Download files from Google Drive to local storage
- Validate file integrity and audio format
- Extract basic metadata (duration, bitrate, sample rate)
- Create initial database record

**Technologies**:
- `google-api-python-client` - File download
- `mutagen` - M4A metadata extraction
- `pathlib` - File path management
- `Pydantic` - Validation schemas
- `SQLAlchemy` - Database operations

**Key Models**:
```python
class AudioMetadata(BaseModel):
    duration_seconds: float
    bitrate: int
    sample_rate: int
    file_size_mb: float
    format: str = "m4a"
```

### 3. Audio Format Conversion
**Objective**: Convert M4A to WAV for NB-Whisper compatibility

**Implementation Steps**:
- Convert M4A → WAV using pydub/ffmpeg
- Preserve original M4A file
- Validate conversion success
- Update database with both file paths

**Technologies**:
- `pydub` - Audio conversion
- `ffmpeg` - Conversion backend
- `FastAPI BackgroundTasks` - Async conversion
- `Logfire` - Conversion monitoring

**Key Models**:
```python
class ConversionResult(BaseModel):
    original_path: Path
    converted_path: Path
    conversion_duration_ms: int
    success: bool
    error_message: Optional[str] = None
```

### 4. Metadata Management
**Objective**: Collect and structure session metadata

**Implementation Steps**:
- Parse filename for automatic metadata extraction
- Create API endpoints for manual metadata entry
- Implement structured metadata storage
- Support historical themes and custom fields

**Technologies**:
- `FastAPI` - REST API for metadata CRUD
- `Pydantic` - Metadata validation
- `SQLAlchemy` - Database ORM

**Key Models**:
```python
class SessionMetadata(BaseModel):
    session_id: str
    date: date
    participants: List[str]
    topics: List[str]
    historical_periods: List[str]
    location_notes: Optional[str]
    session_notes: Optional[str]
```

### 5. Speech-to-Text Transcription
**Objective**: Generate Norwegian transcripts using NB-Whisper

**Implementation Steps**:
- Load NB-Whisper model (`NbAiLab/nb-whisper-large`)
- Process WAV files through transcription pipeline
- Handle long audio files with chunking
- Generate timestamped transcripts with confidence scores

**Technologies**:
- `transformers` - NB-Whisper model
- `torch` - ML backend
- `FastAPI BackgroundTasks` - Async transcription
- `Pydantic` - Transcript models

**Key Models**:
```python
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
```

### 6. Speaker Diarization (Optional)
**Objective**: Identify and attribute speakers in conversations

**Implementation Steps**:
- Apply speaker diarization to audio
- Map speaker segments to transcript
- Generate speaker-attributed transcripts

**Technologies**:
- `pyannote.audio` - Speaker diarization
- Integration with transcript generation

**Key Models**:
```python
class Speaker(BaseModel):
    speaker_id: str
    label: str  # "Interviewer", "Historian", etc.
    segments: List[Tuple[float, float]]  # (start, end) times
```

### 7. LLM-Powered Auto-Tagging
**Objective**: Extract structured tags and themes using LLM analysis

**Implementation Steps**:
- Create Pydantic AI agent for tag extraction
- Process transcripts through LLM with Norwegian historical context
- Extract categories: time periods, people, places, agricultural practices
- Store tags with confidence scores

**Technologies**:
- `Pydantic AI` - Agent orchestration
- `OpenAI API` or local LLM - Intelligence backend
- `FastAPI` - Tag management endpoints

**Key Models**:
```python
class ExtractedTag(BaseModel):
    category: Literal["time_period", "person", "place", "practice", "event"]
    value: str
    confidence: float
    context: str  # Surrounding text where tag was found

class TagExtractionResult(BaseModel):
    session_id: str
    tags: List[ExtractedTag]
    processing_model: str
    extraction_timestamp: datetime
```

**LLM Prompt Template**:
```
Analyze this Norwegian historical conversation about Vidarshov Gård:
[TRANSCRIPT]

Extract relevant tags in categories:
- Tidsperioder (time periods)
- Personer/familier (people/families)  
- Steder (places/farm areas)
- Jordbrukspraksis (agricultural practices)
- Historiske hendelser (historical events)

Return structured JSON with confidence scores.
```

### 8. Content Analysis & Summarization
**Objective**: Generate intelligent summaries and insights

**Implementation Steps**:
- Create summary generation agent
- Extract key historical facts and insights
- Generate session summaries
- Link related sessions and topics

**Technologies**:
- `Pydantic AI` - Multi-agent workflows
- `OpenAI API` - Summarization
- `FastAPI` - Analysis endpoints

**Key Models**:
```python
class SessionSummary(BaseModel):
    session_id: str
    key_points: List[str]
    historical_insights: List[str]
    questions_raised: List[str]
    related_sessions: List[str]
    summary_text: str
```

### 9. Search & Discovery
**Objective**: Enable full-text and semantic search across sessions

**Implementation Steps**:
- Implement SQLite FTS5 for full-text search
- Generate semantic embeddings for content
- Create tag-based filtering
- Build cross-session search capabilities

**Technologies**:
- `SQLite FTS5` - Full-text indexing
- `sentence-transformers` - Semantic embeddings
- `FastAPI` - Search API

**Key Models**:
```python
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
```

### 10. Export & Sharing
**Objective**: Generate multiple output formats for research use

**Implementation Steps**:
- Create PDF reports with transcripts and metadata
- Generate JSON exports for data analysis
- Package complete session materials
- Upload processed files back to Google Drive

**Technologies**:
- `reportlab` - PDF generation
- `jinja2` - Report templating
- `Google Drive API` - Upload exports

**Key Models**:
```python
class ExportConfig(BaseModel):
    session_ids: List[str]
    include_audio: bool = True
    include_transcript: bool = True
    include_summary: bool = True
    include_tags: bool = True
    format: Literal["pdf", "json", "complete"] = "pdf"
```

## Database Schema

### Core Tables
```sql
-- Sessions table
sessions (
    id TEXT PRIMARY KEY,
    drive_file_id TEXT UNIQUE,
    filename TEXT,
    original_path TEXT,
    converted_path TEXT,
    upload_timestamp DATETIME,
    processing_status TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)

-- Session metadata
session_metadata (
    session_id TEXT REFERENCES sessions(id),
    participants JSON,
    topics JSON,
    historical_periods JSON,
    location_notes TEXT,
    session_notes TEXT
)

-- Transcripts
transcripts (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    full_text TEXT,
    segments JSON,
    language TEXT DEFAULT 'nb',
    model_version TEXT,
    processing_duration_ms INTEGER
)

-- Tags
tags (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    category TEXT,
    value TEXT,
    confidence REAL,
    context TEXT,
    extraction_model TEXT
)

-- Summaries
summaries (
    session_id TEXT REFERENCES sessions(id),
    summary_text TEXT,
    key_points JSON,
    historical_insights JSON,
    questions_raised JSON,
    related_sessions JSON
)
```

## API Endpoints Structure

### File Management
- `POST /files/upload` - Manual file upload
- `GET /files/{file_id}` - File details
- `GET /files/{file_id}/status` - Processing status

### Sessions
- `GET /sessions/` - List all sessions
- `POST /sessions/` - Create session with metadata
- `GET /sessions/{session_id}` - Session details
- `PUT /sessions/{session_id}/metadata` - Update metadata

### Transcription
- `POST /sessions/{session_id}/transcribe` - Start transcription
- `GET /sessions/{session_id}/transcript` - Get transcript
- `GET /sessions/{session_id}/transcript/segments` - Timestamped segments

### Analysis
- `POST /sessions/{session_id}/analyze` - Start LLM analysis
- `GET /sessions/{session_id}/tags` - Get extracted tags
- `GET /sessions/{session_id}/summary` - Get summary

### Search
- `POST /search/` - Search across sessions
- `GET /search/tags` - Search by tags
- `GET /search/semantic` - Semantic search

### Export
- `POST /export/` - Generate exports
- `GET /export/{export_id}/download` - Download export

## Development Phases

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] FastAPI application setup
- [ ] Database schema and models
- [ ] Google Drive API integration
- [ ] File monitoring and download
- [ ] Basic audio conversion

### Phase 2: Transcription Pipeline (Week 3-4)
- [ ] NB-Whisper integration
- [ ] Transcript processing and storage
- [ ] Basic web interface
- [ ] Session management API

### Phase 3: Intelligence Layer (Week 5-6)
- [ ] Pydantic AI agent setup
- [ ] Auto-tagging implementation
- [ ] Summary generation
- [ ] Search functionality

### Phase 4: Export & Polish (Week 7-8)
- [ ] Export system
- [ ] Advanced search features
- [ ] Performance optimization
- [ ] Documentation

## Configuration & Setup

### Environment Variables
```bash
# Google Drive API
GOOGLE_DRIVE_CREDENTIALS_PATH=./credentials.json
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id

# Database
DATABASE_URL=sqlite:///./vidarshov.db

# LLM Configuration
OPENAI_API_KEY=your_openai_key
PYDANTIC_AI_MODEL=gpt-4

# Logfire
LOGFIRE_TOKEN=your_logfire_token

# Audio Processing
AUDIO_STORAGE_PATH=./audio_files/
TEMP_PROCESSING_PATH=./temp/
```

### Required Python Dependencies
```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
pydantic = "^2.5.0"
pydantic-ai = "^0.0.1"
logfire = "^0.1.0"
sqlalchemy = "^2.0.0"
sqlite-fts4 = "^1.0.0"
google-api-python-client = "^2.100.0"
google-auth = "^2.23.0"
pydub = "^0.25.0"
mutagen = "^1.47.0"
transformers = "^4.35.0"
torch = "^2.1.0"
sentence-transformers = "^2.2.0"
reportlab = "^4.0.0"
jinja2 = "^3.1.0"
watchdog = "^3.0.0"
uvicorn = "^0.24.0"
```

## Implementation Notes

### Audio Processing Considerations
- M4A files average 30-50% smaller than equivalent MP3
- Conversion M4A → WAV adds ~5-10 seconds per hour of audio
- Store both formats: M4A for archive, WAV for processing
- Handle large files (2+ hour interviews) with chunking

### Norwegian Language Specifics
- Use NB-Whisper specifically trained for Norwegian
- Consider Bokmål vs. Nynorsk dialect variations
- LLM prompts should be in Norwegian for better context understanding
- Handle Norwegian characters (æ, ø, å) in all text processing

### Performance Optimization
- Async processing for all I/O operations
- Background task queuing for long-running operations
- Caching for frequently accessed transcripts
- Batch processing for multiple file operations

### Error Handling & Resilience
- Retry mechanisms for API calls
- Graceful degradation when services unavailable
- Comprehensive logging with Logfire
- Data backup and recovery procedures

This workfile provides the complete technical specification for implementing the Vidarshov Gård recording application. Each component is clearly defined with technologies, models, and implementation steps.