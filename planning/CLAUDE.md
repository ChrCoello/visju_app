# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Vidarshov Gård Historical Recording App - An application to record, transcribe, and analyze conversations with a historian about Vidarshov Gård farm in Ridabu, Norway. The app processes M4A audio files from Easy Voice Recorder (Android) uploaded to Google Drive, transcribes them using NB-Whisper, and provides intelligent analysis using LLMs.

## Development Commands

### Python Environment
- **Install dependencies**: `uv pip install -e .`
- **Run with uv**: `uv run python -m <module>`
- **Sync dependencies**: `uv pip sync` 

### Project Structure
- `backend/` - FastAPI application (currently empty)
- `frontend/` - Frontend application (currently empty)
- `pyproject.toml` - Python project configuration with Pydantic dependency
- `WORKFLOW.md` - Comprehensive technical specification

## Technical Architecture

### Core Technology Stack
- **Backend Framework**: FastAPI
- **Data Models**: Pydantic (already configured in pyproject.toml)
- **LLM Integration**: Pydantic AI
- **Logging/Observability**: Logfire
- **Database**: SQLite with SQLAlchemy ORM
- **Audio Processing**: Pydub + FFmpeg
- **Transcription**: NB-Whisper (Norwegian language support)
- **Search**: SQLite FTS5
- **Cloud Storage**: Google Drive API

### Audio Processing Pipeline
1. **Source**: M4A files from RØDE Wireless Me microphone → Easy Voice Recorder (Android) → Google Drive
2. **Processing**: M4A preserved as original, converted to WAV for transcription
3. **Transcription**: NB-Whisper for Norwegian language processing
4. **Analysis**: LLM-powered auto-tagging and summarization

### Key Data Models (from WORKFLOW.md)
- `AudioFile`: Drive integration and status tracking
- `AudioMetadata`: Duration, bitrate, sample rate validation
- `TranscriptSegment`: Timestamped transcription with confidence scores
- `SessionMetadata`: Participants, topics, historical periods
- `ExtractedTag`: LLM-generated tags with categories (time_period, person, place, practice, event)

### Database Schema
Core tables: sessions, session_metadata, transcripts, tags, summaries
- Uses JSON columns for flexible metadata storage
- Full-text search with SQLite FTS5

### API Endpoints Structure
- File Management: `/files/` - Upload, status, details
- Sessions: `/sessions/` - CRUD operations and metadata
- Transcription: `/sessions/{id}/transcribe` - NB-Whisper processing
- Analysis: `/sessions/{id}/analyze` - LLM tagging and summarization
- Search: `/search/` - Text, semantic, and tag-based search
- Export: `/export/` - PDF, JSON, and complete session packages

## Norwegian Language Considerations
- Use NB-Whisper specifically trained for Norwegian
- Handle Norwegian characters (æ, ø, å) in all text processing
- LLM prompts should be in Norwegian for better context understanding
- Consider Bokmål vs. Nynorsk dialect variations

## Development Phases
1. **Core Infrastructure**: FastAPI setup, database models, Google Drive integration
2. **Transcription Pipeline**: NB-Whisper integration, transcript processing
3. **Intelligence Layer**: Pydantic AI agents, auto-tagging, summarization
4. **Export & Polish**: Multi-format exports, advanced search, optimization

## Environment Configuration
Required environment variables:
- `GOOGLE_DRIVE_CREDENTIALS_PATH`, `GOOGLE_DRIVE_FOLDER_ID`
- `DATABASE_URL` (SQLite)
- `OPENAI_API_KEY`, `PYDANTIC_AI_MODEL`
- `LOGFIRE_TOKEN`
- `AUDIO_STORAGE_PATH`, `TEMP_PROCESSING_PATH`

## Performance Notes
- Async processing for all I/O operations
- Background task queuing for transcription and analysis
- M4A files average 30-50% smaller than MP3
- Handle large files (2+ hour interviews) with chunking
- Store both M4A (archive) and WAV (processing) formats