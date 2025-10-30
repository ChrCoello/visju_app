#!/usr/bin/env python3
"""
Compare basic transcription vs speaker-aware transcription services.
Directly calls both transcription services and saves results to database.
"""

import sys
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.transcription_service import TranscriptionService
from app.services.speaker_aware_transcription_service import SpeakerAwareTranscriptionService
from app.models.db_models import Session as SessionModel, Transcript
from app.core.database import get_db
from app.core.logging import get_logger

logger = get_logger()

TEST_AUDIO_PATH = "audio_files/originals/Testwerner.mp3"

def print_transcription_comparison(basic_result, speaker_result):
    """Print a comparison of both transcription results."""
    print("\n" + "="*80)
    print("📊 TRANSCRIPTION COMPARISON")
    print("="*80)

    # Basic stats
    print("\n📈 STATISTICS:")
    print(f"{'Metric':<30} {'Basic':<25} {'Speaker-Aware':<25}")
    print("-" * 80)
    print(f"{'Processing Time':<30} {basic_result.processing_duration_ms/1000:.1f}s{'':<19} {speaker_result.processing_duration_ms/1000:.1f}s")
    print(f"{'Segments':<30} {len(basic_result.segments):<25} {len(speaker_result.segments)}")
    print(f"{'Text Length':<30} {len(basic_result.full_text):<25} {len(speaker_result.full_text)}")
    print(f"{'Chunks Processed':<30} {basic_result.chunks_processed:<25} {speaker_result.chunks_processed}")
    print(f"{'Speakers Detected':<30} {'N/A':<25} {speaker_result.speakers_detected}")
    print(f"{'Has Speaker Separation':<30} {'N/A':<25} {'Yes' if speaker_result.has_speakers else 'No'}")

    if speaker_result.has_speakers:
        print(f"{'Separation Method':<30} {'N/A':<25} {speaker_result.speaker_separation_method}")

    # Full text comparison
    print("\n📝 BASIC TRANSCRIPTION:")
    print("-" * 80)
    print(basic_result.full_text[:800])
    if len(basic_result.full_text) > 800:
        print(f"... ({len(basic_result.full_text)} total characters)")

    print("\n👥 SPEAKER-AWARE TRANSCRIPTION:")
    print("-" * 80)
    print(speaker_result.full_text[:1200])
    if len(speaker_result.full_text) > 1200:
        print(f"... ({len(speaker_result.full_text)} total characters)")

    # Speaker info if available
    if speaker_result.speaker_info:
        print("\n🎤 SPEAKER INFORMATION:")
        print("-" * 80)
        for speaker in speaker_result.speaker_info:
            print(f"{speaker.label}:")
            print(f"  Channel: {speaker.channel}")
            print(f"  Energy: {speaker.energy_percent:.1f}%")
            print(f"  Silence: {speaker.silence_percent:.1f}%")

def save_to_database(result, service_name: str, filename: str, db):
    """Save transcription result to database."""
    try:
        # Create session
        session_id = str(uuid.uuid4())
        session = SessionModel(
            id=session_id,
            filename=f"{filename} - {service_name}",
            original_path=str(Path(TEST_AUDIO_PATH).absolute()),
            processing_status="transcribed"
        )
        db.add(session)
        db.flush()

        # Prepare segments for JSON storage
        if hasattr(result, 'has_speakers') and result.has_speakers:
            # Speaker-aware segments
            segments_json = []
            for segment in result.segments:
                segments_json.append({
                    "text": segment.text,
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "speaker_id": segment.speaker_id,
                    "channel": segment.channel,
                    "confidence": segment.confidence
                })

            # Prepare speaker info
            speaker_info_json = []
            for speaker in result.speaker_info:
                speaker_info_json.append({
                    "speaker_id": speaker.speaker_id,
                    "channel": speaker.channel,
                    "energy_percent": speaker.energy_percent,
                    "silence_percent": speaker.silence_percent,
                    "label": speaker.label
                })

            transcript = Transcript(
                id=str(uuid.uuid4()),
                session_id=session_id,
                full_text=result.full_text,
                segments=segments_json,
                language=result.language_detected,
                model_version=result.model_used,
                processing_duration_ms=result.processing_duration_ms,
                has_speakers="true",
                speaker_separation_method=result.speaker_separation_method,
                speakers_detected=result.speakers_detected,
                speaker_info=speaker_info_json
            )
        else:
            # Basic segments
            segments_json = []
            for segment in result.segments:
                segments_json.append({
                    "text": segment.text,
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "confidence": segment.confidence
                })

            transcript = Transcript(
                id=str(uuid.uuid4()),
                session_id=session_id,
                full_text=result.full_text,
                segments=segments_json,
                language=result.language_detected,
                model_version=result.model_used,
                processing_duration_ms=result.processing_duration_ms
            )

        db.add(transcript)
        db.commit()

        logger.info(f"Saved {service_name} transcription to database with session_id: {session_id}")
        return session_id

    except Exception as e:
        logger.error(f"Error saving {service_name} transcription to database: {e}")
        db.rollback()
        return None

def main():
    print("🎵 Transcription Service Comparison Tool")
    print("=" * 80)

    # Check if file exists
    if not Path(TEST_AUDIO_PATH).exists():
        print(f"❌ Error: File not found: {TEST_AUDIO_PATH}")
        return

    audio_path = Path(TEST_AUDIO_PATH)
    print(f"✅ Found test file: {audio_path.name}")
    file_size = audio_path.stat().st_size / (1024 * 1024)
    print(f"   Size: {file_size:.2f} MB")

    # Initialize services
    print("\n🔧 Initializing transcription services...")
    basic_service = TranscriptionService()
    speaker_service = SpeakerAwareTranscriptionService()

    # Run basic transcription
    print("\n🎙️  Running BASIC transcription...")
    print("-" * 80)
    basic_result = basic_service.transcribe_audio(str(audio_path.absolute()))

    if not basic_result.success:
        print(f"❌ Basic transcription failed: {basic_result.error_message}")
        return

    print(f"✅ Basic transcription completed!")
    print(f"   Duration: {basic_result.processing_duration_ms/1000:.1f}s")
    print(f"   Segments: {len(basic_result.segments)}")
    print(f"   Characters: {len(basic_result.full_text)}")

    # Run speaker-aware transcription
    print("\n👥 Running SPEAKER-AWARE transcription...")
    print("-" * 80)
    speaker_result = speaker_service.transcribe_audio_with_speakers(str(audio_path.absolute()))

    if not speaker_result.success:
        print(f"❌ Speaker-aware transcription failed: {speaker_result.error_message}")
        return

    print(f"✅ Speaker-aware transcription completed!")
    print(f"   Duration: {speaker_result.processing_duration_ms/1000:.1f}s")
    print(f"   Segments: {len(speaker_result.segments)}")
    print(f"   Characters: {len(speaker_result.full_text)}")
    print(f"   Speakers: {speaker_result.speakers_detected}")

    # Print comparison
    print_transcription_comparison(basic_result, speaker_result)

    # Save to database
    print("\n💾 Saving results to database...")
    print("-" * 80)
    db = next(get_db())
    try:
        basic_session_id = save_to_database(basic_result, "Basic", audio_path.name, db)
        speaker_session_id = save_to_database(speaker_result, "Speaker-Aware", audio_path.name, db)

        print("\n" + "="*80)
        print("✅ COMPARISON COMPLETE!")
        print("="*80)
        if basic_session_id:
            print(f"\n📋 Basic transcription session ID: {basic_session_id}")
            print(f"   View at: http://127.0.0.1:8000/api/v1/sessions/{basic_session_id}")
        if speaker_session_id:
            print(f"\n📋 Speaker-aware transcription session ID: {speaker_session_id}")
            print(f"   View at: http://127.0.0.1:8000/api/v1/sessions/{speaker_session_id}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
