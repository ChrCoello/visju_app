# TASK.md - Development Tasks for Vidarshov Gård Recording App

## Phase 1: Core Infrastructure (Week 1-2)

### 1.1 FastAPI Application Setup
- [x] Create FastAPI application structure in `backend/`
- [x] Set up main.py with basic FastAPI app
- [x] Configure CORS and middleware
- [x] Set up Pydantic models for base data structures
- [x] Create requirements.txt or update pyproject.toml with core dependencies
- [x] Set up basic logging with Logfire
- [x] Create configuration management (environment variables)

### 1.2 Database Schema and Models
- [x] Set up SQLAlchemy ORM with SQLite
- [x] Create database models for sessions table
- [x] Create database models for session_metadata table
- [x] Create database models for transcripts table
- [x] Create database models for tags table
- [x] Create database models for summaries table
- [x] Set up database migrations/initialization
- [x] Create database connection and session management

### 1.3 Google Drive API Integration
- [x] Set up Google Drive API credentials and authentication
- [x] Create Google Drive client service
- [x] Implement folder monitoring functionality
- [x] Create file detection and metadata extraction
- [x] Implement file download from Google Drive
- [x] Set up file completion detection (avoid partial uploads)
- [x] Create AudioFile Pydantic model and database operations

### 1.4 File Synchronization and Storage
- [x] Set up local file storage structure
- [x] Check files on Google Drive
- [x] Check files in local storage
- [x] Compare Drive vs local files and identify differences
- [x] Download missing files from Drive to local storage
- [x] Create file integrity validation
- [x] Add error handling and retry mechanisms for downloads

### 1.5 Basic Audio Conversion
- [ ] Set up Pydub and FFmpeg dependencies
- [ ] Implement M4A to WAV conversion functionality
- [ ] Create audio metadata extraction with mutagen
- [ ] Set up file path management for original and converted files
- [ ] Implement conversion validation and error handling
- [ ] Create ConversionResult model and database operations

## Phase 2: Transcription Pipeline (Week 3-4)

### 2.1 NB-Whisper Integration
- [ ] Set up transformers and torch dependencies
- [ ] Install and configure NB-Whisper model (NbAiLab/nb-whisper-large)
- [ ] Create transcription service with NB-Whisper
- [ ] Implement audio file chunking for long recordings
- [ ] Set up GPU/CPU optimization for transcription
- [ ] Create progress tracking for transcription jobs

### 2.2 Transcript Processing and Storage
- [ ] Create TranscriptSegment and Transcript Pydantic models
- [ ] Implement timestamped transcript generation
- [ ] Set up confidence score tracking
- [ ] Create transcript database operations (CRUD)
- [ ] Implement transcript text processing and cleaning
- [ ] Set up full-text search indexing with SQLite FTS5

### 2.3 Basic Web Interface
- [ ] Set up frontend directory structure
- [ ] Create basic HTML/CSS interface for session viewing
- [ ] Implement file upload interface (manual upload option)
- [ ] Create session listing and detail views
- [ ] Add transcript display with timestamp navigation
- [ ] Implement basic search functionality

### 2.4 Session Management API
- [ ] Create SessionMetadata Pydantic model
- [ ] Implement sessions CRUD endpoints
- [ ] Add metadata management endpoints
- [ ] Create transcript retrieval endpoints
- [ ] Implement file upload and processing status endpoints
- [ ] Add basic authentication/session management

## Phase 3: Intelligence Layer (Week 5-6)

### 3.1 Pydantic AI Agent Setup
- [ ] Install and configure Pydantic AI
- [ ] Set up OpenAI API or local LLM integration
- [ ] Create base agent configuration and prompts
- [ ] Set up Norwegian language prompts for historical context
- [ ] Implement agent error handling and fallbacks
- [ ] Create agent monitoring and logging

### 3.2 Auto-tagging Implementation
- [ ] Create ExtractedTag and TagExtractionResult models
- [ ] Implement tag extraction agent with Norwegian prompts
- [ ] Set up tag categories (time_period, person, place, practice, event)
- [ ] Create confidence scoring system
- [ ] Implement tag storage and retrieval
- [ ] Add tag validation and deduplication

### 3.3 Summary Generation
- [ ] Create SessionSummary Pydantic model
- [ ] Implement summary generation agent
- [ ] Set up key points and insights extraction
- [ ] Create cross-session relationship detection
- [ ] Implement summary storage and versioning
- [ ] Add summary quality scoring

### 3.4 Search Functionality
- [ ] Set up SearchQuery and SearchResult models
- [ ] Implement full-text search with SQLite FTS5
- [ ] Create semantic search with sentence-transformers
- [ ] Implement tag-based filtering and search
- [ ] Set up cross-session search capabilities
- [ ] Add search result ranking and relevance scoring

## Phase 4: Export & Polish (Week 7-8)

### 4.1 Export System
- [ ] Install reportlab and jinja2 for PDF generation
- [ ] Create ExportConfig Pydantic model
- [ ] Implement PDF report generation with transcripts and metadata
- [ ] Create JSON export functionality for data analysis
- [ ] Set up complete session package exports
- [ ] Implement Google Drive upload for processed exports

### 4.2 Advanced Search Features
- [ ] Implement advanced filtering options
- [ ] Create faceted search by metadata fields
- [ ] Set up search suggestions and autocomplete
- [ ] Add search history and saved searches
- [ ] Implement batch operations on search results
- [ ] Create search analytics and usage tracking

### 4.3 Performance Optimization
- [ ] Implement caching for frequently accessed data
- [ ] Set up database query optimization
- [ ] Add pagination for large result sets
- [ ] Implement async processing optimization
- [ ] Set up resource monitoring and alerting
- [ ] Create performance benchmarking tests

### 4.4 Documentation and Testing
- [ ] Create comprehensive API documentation
- [ ] Set up unit tests for core functionality
- [ ] Implement integration tests for workflows
- [ ] Create user guide and setup instructions
- [ ] Set up continuous integration pipeline
- [ ] Perform security audit and hardening

## Optional Enhancements

### Speaker Diarization (Future Phase)
- [ ] Install and configure pyannote.audio
- [ ] Implement speaker detection and segmentation
- [ ] Create Speaker Pydantic model
- [ ] Integrate speaker attribution with transcripts
- [ ] Set up speaker identification and labeling

### Advanced Analytics
- [ ] Implement usage analytics and metrics
- [ ] Create data visualization for historical insights
- [ ] Set up trend analysis across sessions
- [ ] Add recommendation system for related content
- [ ] Create historical timeline generation

### Mobile Integration
- [ ] Create mobile-responsive web interface
- [ ] Implement push notifications for processing status
- [ ] Add offline viewing capabilities
- [ ] Create mobile app for easy recording uploads

## Environment Setup Tasks

### Development Environment
- [ ] Set up virtual environment with uv
- [ ] Configure development database
- [ ] Set up development Google Drive folder and credentials
- [ ] Configure development environment variables
- [ ] Set up development logging and monitoring

### Production Environment
- [ ] Set up production database with backups
- [ ] Configure production Google Drive integration
- [ ] Set up production logging with Logfire
- [ ] Configure production environment variables
- [ ] Set up monitoring and alerting systems

## Dependencies to Add

### Core Dependencies
```toml
fastapi = "^0.104.0"
pydantic-ai = "^0.1.0"
logfire = "^0.1.0"
sqlalchemy = "^2.0.0"
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