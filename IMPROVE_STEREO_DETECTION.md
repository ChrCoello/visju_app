# Improving Speaker Detection for Stereo Recordings

## Problem Statement

When using RØDE Wireless Me microphones with stereo recording, both microphones pick up the same speaker's voice, resulting in duplicate transcriptions assigned to different speakers:

```
[Speaker 1]: Det var vel ikke sin fortrolighet hun tenkte å gi dem...
[Speaker 2]: Det var vel ikke sin fortrolighet hun tenkte å gi dem...
```

This occurs because:
- Both microphones (left/right channels) capture audio from both speakers
- Current system assigns left channel → Speaker 1, right channel → Speaker 2
- Cross-talk between microphones causes the same speech to appear on both channels

## Current Implementation

Location: [backend/app/services/speaker_aware_transcription_service.py](backend/app/services/speaker_aware_transcription_service.py)

**Current approach (lines 558-579):**
1. Analyze stereo separation using correlation and energy ratios
2. Split audio into left and right channels
3. Transcribe each channel independently
4. Assign left → Speaker 1, right → Speaker 2

**Energy filtering** (lines 206-305):
- Available but **disabled by default** (line 77: `use_energy_filtering = False`)
- Uses 100ms windows to compare channel energy
- Silences the weaker channel when energy ratio > threshold
- **Problem**: Causes significant content loss (filters out valid speech)

## Solution Options

### Option 1: Post-Processing Deduplication (Quick Fix)

**Concept**: Remove duplicate segments after transcription based on text similarity and timing.

**Implementation approach:**
1. After transcribing both channels, compare all Speaker 1 vs Speaker 2 segments
2. For segments with overlapping timestamps:
   - Calculate text similarity (e.g., Levenshtein distance or difflib)
   - If similarity > 80%, mark as duplicate
3. Keep only the segment from the channel with higher audio energy
4. Remove or merge duplicate segments

**Pros:**
- Quick to implement (~50 lines of code)
- No new dependencies
- Works with existing transcription pipeline
- Preserves all content (removes duplicates only)

**Cons:**
- Won't handle cases where both speakers actually say the same thing
- Requires tuning similarity threshold
- Post-processing overhead

**Code location**: Add to `SpeakerAwareTranscriptionService._create_speaker_attributed_text()`

---

### Option 2: pyannote.audio Diarization (Recommended for Production)

**Concept**: Replace channel-based separation with deep learning speaker diarization.

**How it works:**
1. Extract voice embeddings from audio using neural networks
2. Cluster segments by voice characteristics (not channel position)
3. Assign speaker IDs based on voice similarity
4. Works even when both microphones pick up the same speaker

**Implementation approach:**
1. Install `pyannote.audio` library
2. Obtain HuggingFace token (free)
3. Load pretrained speaker diarization pipeline
4. Process audio to get speaker segments with timestamps
5. Combine with NB-Whisper transcription
6. Map transcribed text to diarization timestamps

**Pros:**
- Industry-standard solution
- Handles cross-talk and overlapping speech
- Works with mono and stereo recordings
- Voice-based (not channel-based) speaker identification
- Can identify 2+ speakers automatically

**Cons:**
- Requires HuggingFace account and token
- ~500MB model download
- Additional processing time (~15-30% overhead)
- New dependency to maintain

**Dependencies:**
```bash
pip install pyannote.audio
```

**Code location**: Create new `PyannoteDialarizer` class or integrate into existing service

---

### Option 3: Smarter Energy-Based Assignment (Balanced Approach)

**Concept**: Assign segments to speakers based on which channel has dominant energy, rather than transcribing channels separately.

**How it works:**

#### Step 1: Unified Speech Detection
Instead of transcribing left and right channels separately:
1. Merge stereo to mono for transcription (keeps all audio)
2. Use NB-Whisper to transcribe with word-level timestamps
3. Get complete transcript with precise timing for each word/phrase

#### Step 2: Energy-Based Speaker Assignment
For each transcribed segment:
1. Extract the audio slice from both left and right channels using the segment's timestamps
2. Calculate RMS energy for left channel in that time window
3. Calculate RMS energy for right channel in that time window
4. Compare energies:
   - If `left_energy / right_energy > threshold` (e.g., 1.5): Assign to Speaker 1 (left)
   - If `right_energy / left_energy > threshold` (e.g., 1.5): Assign to Speaker 2 (right)
   - If energies are similar: Mark as "unclear" or assign to "both" (optional: skip or use heuristics)

#### Step 3: Refinement (Optional)
- Use temporal context: If speaker was just identified in previous segment, prefer same speaker for borderline cases
- Apply smoothing: Avoid rapid speaker switching (minimum segment duration)
- Handle overlaps: If both channels have high energy, mark as overlap rather than duplicate

**Implementation Details:**

```python
def _assign_speaker_by_energy(
    self,
    segment: SpeakerSegment,
    left_channel: AudioSegment,
    right_channel: AudioSegment,
    energy_threshold: float = 1.5
) -> str:
    """
    Assign speaker based on which channel has dominant energy during the segment.

    Args:
        segment: Transcribed segment with start_time and end_time
        left_channel: Left audio channel (Speaker 1)
        right_channel: Right audio channel (Speaker 2)
        energy_threshold: Ratio threshold for speaker assignment

    Returns:
        "speaker_1", "speaker_2", or "speaker_unclear"
    """
    # Extract audio slice for this segment
    start_ms = int(segment.start_time * 1000)
    end_ms = int(segment.end_time * 1000)

    left_slice = left_channel[start_ms:end_ms]
    right_slice = right_channel[start_ms:end_ms]

    # Calculate RMS energy
    left_energy = left_slice.rms
    right_energy = right_slice.rms

    # Avoid division by zero
    if right_energy < 1:
        right_energy = 1
    if left_energy < 1:
        left_energy = 1

    # Compare energy ratios
    left_to_right = left_energy / right_energy
    right_to_left = right_energy / left_energy

    if left_to_right > energy_threshold:
        return "speaker_1"  # Left channel dominant
    elif right_to_left > energy_threshold:
        return "speaker_2"  # Right channel dominant
    else:
        return "speaker_unclear"  # Both channels similar
```

**Modified Transcription Flow:**

```python
def transcribe_audio_with_speakers(self, audio_file_path: str):
    # 1. Load stereo audio
    audio, duration = self._load_and_preprocess_audio(audio_file_path)

    # 2. Split channels for energy analysis
    left_channel = audio.split_to_mono()[0]
    right_channel = audio.split_to_mono()[1]

    # 3. Transcribe MERGED mono (keeps all content)
    mono_audio = audio.set_channels(1)
    all_segments = self._transcribe_channel(mono_audio, "speaker_unknown")

    # 4. Assign speakers based on energy in each segment
    for segment in all_segments:
        speaker_id = self._assign_speaker_by_energy(
            segment,
            left_channel,
            right_channel,
            energy_threshold=1.5
        )
        segment.speaker_id = speaker_id

    # 5. Filter out "unclear" segments (optional)
    final_segments = [s for s in all_segments if s.speaker_id != "speaker_unclear"]

    # OR keep unclear segments with a marker
    # final_segments = all_segments

    return final_segments
```

**Pros:**
- Uses existing infrastructure (NB-Whisper, pydub, numpy)
- No new dependencies
- No content loss (transcribes full mono audio)
- No duplicate segments (each segment assigned once)
- Handles cross-talk better than separate channel transcription
- Configurable threshold for energy ratio

**Cons:**
- Still relies on channel separation (not voice characteristics)
- "Unclear" segments may be skipped or misassigned
- Won't work well if both speakers have similar volume on both mics
- Requires tuning energy threshold for your specific microphone setup

**Configuration:**
- Energy threshold: `1.5` (moderate) to `2.0` (aggressive)
- Lower threshold = more strict speaker assignment (more "unclear" segments)
- Higher threshold = more lenient (fewer "unclear" segments but more misassignments)

**Code location**: Modify `transcribe_audio_with_speakers()` in `SpeakerAwareTranscriptionService`

---

## Recommended Implementation Strategy

### Phase 1: Quick Win (Week 1)
Implement **Option 1 (Deduplication)** as an immediate fix:
- Add deduplication function to existing service
- Test on problematic recordings
- Tune similarity threshold

### Phase 2: Production Solution (Week 2-3)
Choose between **Option 2 (pyannote.audio)** or **Option 3 (Energy-based)**:

**Choose Option 2 if:**
- You want industry-standard solution
- You have good internet for model download
- You're okay with HuggingFace dependency
- You need to handle 3+ speakers in the future

**Choose Option 3 if:**
- You want to minimize dependencies
- You have strict control over recording setup (stereo mics)
- You only need to handle 2 speakers
- You want faster processing (no additional ML model)

### Phase 3: Refinement (Ongoing)
- Add manual speaker correction UI
- Collect user feedback on speaker assignment quality
- Fine-tune thresholds based on real-world usage

## Testing Strategy

1. **Test files**: Use recordings with known speaker segments
2. **Metrics**:
   - Duplicate segment rate (should be 0%)
   - Speaker assignment accuracy (manual verification)
   - Content loss (ensure no valid speech is removed)
3. **Edge cases**:
   - Overlapping speech
   - Very quiet speech
   - Single speaker recordings
   - Background noise

## Configuration Parameters

### Current Settings (lines 72-79 in service)
```python
correlation_threshold = 0.6          # Below this = different speakers
energy_ratio_threshold = 1.5         # Above this = significant channel difference
use_energy_filtering = False         # Currently disabled
energy_ratio_gate_threshold = 2.0    # Window-based filtering threshold
filter_window_ms = 100               # Energy calculation window
```

### Recommended Settings for Option 3
```python
use_unified_transcription = True      # Transcribe mono, assign by energy
speaker_energy_threshold = 1.5        # Energy ratio for assignment
keep_unclear_segments = True          # Keep segments with similar energy
unclear_threshold = 1.5               # Ratio below this = unclear
```

## References

- Current implementation: [backend/app/services/speaker_aware_transcription_service.py](backend/app/services/speaker_aware_transcription_service.py)
- API route: [backend/app/api/speaker_transcription_router.py](backend/app/api/speaker_transcription_router.py)
- pyannote.audio: https://github.com/pyannote/pyannote-audio
- NB-Whisper: https://huggingface.co/NbAiLab/nb-whisper-small
