# Vidarshov Gård Recording App

Application to record, transcribe, and analyze conversations about Vidarshov Gård farm history in Ridabu, Norway.

## Features

- **Google Drive Integration**: Automatic sync of M4A audio files from Easy Voice Recorder
- **Audio Conversion**: M4A to WAV conversion optimized for Norwegian speech recognition
- **File Synchronization**: Smart comparison and download of missing files
- **Audio Processing**: Metadata extraction and format validation
- **Norwegian Transcription**: NB-Whisper powered transcription with CUDA acceleration
- **Database Storage**: Session management with full transcription storage

## API Usage

### File Synchronization

Check current synchronization status:
```bash
curl http://localhost:8000/api/v1/sync/status
```

Download missing files from Google Drive:
```bash
curl -X POST http://localhost:8000/api/v1/sync/download-missing
```

Perform full synchronization:
```bash
curl -X POST http://localhost:8000/api/v1/sync/full-sync
```

Get local storage statistics:
```bash
curl http://localhost:8000/api/v1/sync/storage-stats
```

### Audio Conversion

Check conversion dependencies:
```bash
curl http://localhost:8000/api/v1/conversion/dependencies
```

Get conversion status and statistics:
```bash
curl http://localhost:8000/api/v1/conversion/status
```

Convert a specific file:
```bash
curl -X POST http://localhost:8000/api/v1/conversion/convert/filename.m4a
```

Convert all files in batch:
```bash
curl -X POST http://localhost:8000/api/v1/conversion/convert-all
```

Get file metadata:
```bash
curl http://localhost:8000/api/v1/conversion/metadata/filename.m4a
```

### Basic Transcription

Check basic transcription service status:
```bash
curl http://localhost:8000/api/v1/transcription/status
```

Transcribe an audio file (WAV format, mono processing):
```bash
curl -X POST http://localhost:8000/api/v1/transcription/transcribe/filename.wav
```

Force re-transcription of an already processed file:
```bash
curl -X POST "http://localhost:8000/api/v1/transcription/transcribe/filename.wav?force_retranscribe=true"
```

**Example Response:**
```json
{
  "session_id": "ffa67974-1035-4c6c-a04f-e8c82f7a6f05",
  "success": true,
  "full_text": "Norwegian transcription text...",
  "segments_count": 3,
  "processing_duration_ms": 13931,
  "audio_duration_seconds": 81.4,
  "chunks_processed": 3,
  "model_used": "NbAiLab/nb-whisper-small"
}
```

**Features:**
- Norwegian language optimization with NB-Whisper
- GPU acceleration (CUDA) with automatic fallback to CPU
- Intelligent chunking for long recordings (30s chunks with 1s overlap)
- Mono audio processing (no speaker detection)
- Database storage with session management
- Duplicate detection (returns existing transcription if already processed)
- Timestamped segments

**Use Case:** Single speaker recordings or when speaker separation is not needed.

---

### Speaker-Aware Transcription

Check speaker-aware transcription service status:
```bash
curl http://localhost:8000/api/v1/speaker-aware-transcription/status
```

Transcribe audio with automatic speaker detection (MP3, M4A, or WAV):
```bash
curl -X POST http://localhost:8000/api/v1/speaker-aware-transcription/transcribe/filename.mp3
```

Force re-transcription of an already processed file:
```bash
curl -X POST "http://localhost:8000/api/v1/speaker-aware-transcription/transcribe/filename.mp3?force_retranscribe=true"
```

**Example Response:**
```json
{
  "session_id": "ffa67974-1035-4c6c-a04f-e8c82f7a6f05",
  "success": true,
  "full_text": "\n\n[Speaker 1]: Norwegian text from left channel...\n\n[Speaker 2]: Norwegian text from right channel...",
  "segments": [
    {
      "text": "Norwegian text",
      "start_time": 0.0,
      "end_time": 2.5,
      "speaker_id": "speaker_1",
      "channel": "left",
      "confidence": null
    }
  ],
  "processing_duration_ms": 15420,
  "audio_duration_seconds": 120.5,
  "chunks_processed": 45,
  "model_used": "NbAiLab/nb-whisper-small",
  "has_speakers": true,
  "speakers_detected": 2,
  "speaker_separation_method": "stereo_channels",
  "speaker_info": [
    {
      "speaker_id": "speaker_1",
      "channel": "left",
      "energy_percent": 48.5,
      "silence_percent": 52.3,
      "label": "Speaker 1 (Left)"
    },
    {
      "speaker_id": "speaker_2",
      "channel": "right",
      "energy_percent": 51.5,
      "silence_percent": 49.8,
      "label": "Speaker 2 (Right)"
    }
  ]
}
```

**Features:**
- Automatic speaker detection in stereo recordings
- Stereo channel separation (left/right microphone channels)
- Word-level timestamps for precise speaker attribution
- Support for MP3, M4A, and WAV formats
- Energy-based speaker activity analysis
- Correlation analysis for channel separation detection
- Speaker-attributed transcription output
- Database storage with speaker metadata

**Use Case:** Two-person interviews recorded with stereo microphones (e.g., RØDE Wireless Me on separate channels).

## Development

### Setup
```bash
# Install dependencies
uv pip install -e .

# Run the application
cd backend && uv run uvicorn main:app --reload

# Run tests
uv run pytest
```

### Environment Configuration
Required environment variables in `backend/.env`:
```
# Development mode - disables browser caching for easier frontend development
DEVELOPMENT_MODE=True  # Set to False in production

# Google Drive configuration
GOOGLE_DRIVE_CREDENTIALS_PATH=secrets/credentials.json
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id

# Storage paths
AUDIO_STORAGE_PATH=./audio_files/
TEMP_PROCESSING_PATH=./temp/
```

**Development Mode:**
- When `DEVELOPMENT_MODE=True`: Browser caching is disabled, static files reload automatically
- When `DEVELOPMENT_MODE=False`: Browser caching is enabled for better performance in production
- Toggle this setting in `backend/.env` without code changes

**Transcription Settings:**
- `SILENCE_INTERVAL_SECONDS=7.0`: Controls how speaker chunks are created in speaker-aware transcription
  - Words are merged into chunks as long as silence gaps < this threshold
  - Higher values = longer speaking turns (fewer, larger chunks)
  - Lower values = more frequent chunk breaks (more, shorter chunks)
  - Recommended: 5-10 seconds for natural conversation flow
