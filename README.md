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

### Audio Transcription

Check transcription service status and model information:
```bash
curl http://localhost:8000/api/v1/transcription/status
```

Get available transcription models:
```bash
curl http://localhost:8000/api/v1/transcription/models
```

Transcribe an audio file (WAV format):
```bash
curl -X POST http://localhost:8000/api/v1/transcription/transcribe/filename.wav
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
- Database storage with session management
- Duplicate detection (returns existing transcription if already processed)
- Timestamped segments with confidence tracking

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
GOOGLE_DRIVE_CREDENTIALS_PATH=secrets/credentials.json
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id
AUDIO_STORAGE_PATH=./audio_files/
TEMP_PROCESSING_PATH=./temp/
```
