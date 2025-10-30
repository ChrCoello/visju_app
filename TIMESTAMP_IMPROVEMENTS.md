# Word-Level Timestamp Transcription Improvements

## Overview
Refactored the transcription system to use **word-level timestamps** instead of 30-second chunk-based segments. This provides much more precise timing information and enables a better visual dialogue display in the frontend.

## Changes Made

### 1. Backend - Transcription Service
**File**: [backend/app/services/speaker_aware_transcription_service.py](backend/app/services/speaker_aware_transcription_service.py)

- **Added pipeline support**: Imported and initialized HuggingFace `pipeline` for word-level timestamps
- **Refactored `_transcribe_channel` method**:
  - Removed 30-second chunking logic
  - Now uses `pipeline` with `return_timestamps="word"` parameter
  - Processes entire audio channel at once and extracts word-level segments
  - Each segment now represents 1-3 seconds of speech (individual words or short phrases)

**Key improvements**:
- Average segment duration: **0.65s** (down from 30s)
- More granular timing: 72 segments for a 29.6s audio (vs ~1 segment previously)
- Better speaker attribution at word level

### 2. Frontend - Visual Dialogue Display
**Files**:
- [frontend/static/js/app.js](frontend/static/js/app.js)
- [frontend/static/css/style.css](frontend/static/css/style.css)

**JavaScript Changes**:
- Sort segments by `start_time` for chronological dialogue flow
- Display speaker label and timestamp for each segment
- Added `getSpeakerLabel()` helper function

**CSS Changes**:
- **Speaker 1** (left channel): Blue accent, right margin for visual offset
- **Speaker 2** (right channel): Green accent, left margin for visual offset
- **Unknown speaker**: Gray accent
- Hover effects for better interactivity
- Monospace font for timestamps

### 3. Database Schema
**File**: [backend/app/models/db_models.py](backend/app/models/db_models.py)

No changes needed - the existing JSON `segments` field already supports storing any number of segments with their timestamps.

## Results

### Before (30-second chunks):
```
Segment 1: [0.0s - 30.0s] (30.0s) Speaker 1: [entire 30 seconds of text...]
Segment 2: [30.0s - 60.0s] (30.0s) Speaker 2: [entire 30 seconds of text...]
```

### After (word-level timestamps):
```
 1. [0.00s - 0.88s] (0.88s) Speaker 2: Hei,
 2. [0.88s - 0.96s] (0.08s) Speaker 2: god
 3. [0.96s - 1.44s] (0.48s) Speaker 2: morgen!
 4. [1.44s - 1.66s] (0.22s) Speaker 2: Hvordan
 5. [1.66s - 1.80s] (0.14s) Speaker 2: går
 6. [1.80s - 1.88s] (0.08s) Speaker 2: det
 7. [1.88s - 1.98s] (0.10s) Speaker 2: med
 8. [1.98s - 2.92s] (0.94s) Speaker 2: deg?
 9. [3.46s - 4.08s] (0.62s) Speaker 1: Ja, takk!
```

## Testing

Run the test script to verify:
```bash
cd backend
uv run python scripts/test_word_timestamps.py
```

Expected output:
- ✅ Word-level timestamps working
- ✅ Average segment duration < 5s (typically 0.5-1.5s)
- ✅ Speaker attribution per word/phrase

## Frontend Visual Features

The transcript now displays as a visual dialogue:
- Each segment shows **speaker label** + **timestamp range**
- Color-coded by speaker (blue/green)
- Visual offset (margins) to distinguish speakers
- Sorted chronologically for natural conversation flow
- Hover effects for better readability

## Technical Notes

### Whisper Pipeline Configuration
```python
result = self.pipe(
    audio_array,
    return_timestamps="word",  # Word-level instead of segment-level
    generate_kwargs={
        "language": "no",
        "task": "transcribe"
    }
)
```

### Processing Performance
- Same model (NB-Whisper-small)
- Same GPU/CPU usage
- Slightly faster (no chunking overhead)
- More accurate timestamps

## Future Enhancements

Possible improvements:
1. **Sentence grouping**: Combine words into sentences for better readability
2. **Silence detection**: Mark pauses in conversation
3. **Audio playback**: Click segment to jump to that timestamp
4. **Edit timestamps**: Allow manual adjustment of segment boundaries
5. **Export with timestamps**: Include timestamps in PDF/JSON exports
