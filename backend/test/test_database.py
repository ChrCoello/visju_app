from app.models.db_models import Session, SessionMetadata, Transcript, Tag, Summary, AudioFile
from app.services.database_service import DatabaseService


class TestDatabaseModels:
    """Test database model creation and relationships."""

    def test_create_session(self, db_session):
        """Test creating a session record."""
        db_service = DatabaseService(db_session)

        session = db_service.create(
            Session,
            id="test_session_1",
            filename="test_recording.m4a",
            processing_status="detected"
        )

        assert session.id == "test_session_1"
        assert session.filename == "test_recording.m4a"
        assert session.processing_status == "detected"
        assert session.created_at is not None

    def test_session_metadata_relationship(self, db_session):
        """Test session and metadata relationship."""
        db_service = DatabaseService(db_session)

        # Create session
        session = db_service.create(
            Session,
            id="test_session_meta",
            filename="test_meta.m4a"
        )

        # Create metadata
        metadata = db_service.create(
            SessionMetadata,
            session_id="test_session_meta",
            participants=["Interviewer", "Historian"],
            topics=["Farm history", "Agricultural practices"]
        )

        # Test relationship
        db_session.refresh(session)
        assert session.session_metadata is not None
        assert session.session_metadata.participants == ["Interviewer", "Historian"]

    def test_audio_file_model(self, db_session):
        """Test AudioFile model creation."""
        db_service = DatabaseService(db_session)

        audio_file = db_service.create(
            AudioFile,
            id="test_audio_1",
            drive_id="drive_123",
            filename="recording.m4a",
            size_bytes=1024000,
            mime_type="audio/mp4",
            processing_status="detected"
        )

        assert audio_file.drive_id == "drive_123"
        assert audio_file.filename == "recording.m4a"
        assert audio_file.size_bytes == 1024000
        assert audio_file.processing_status == "detected"

    def test_transcript_model(self, db_session):
        """Test Transcript model creation."""
        db_service = DatabaseService(db_session)

        # Create session first
        session = db_service.create(
            Session,
            id="test_session_transcript",
            filename="test.m4a"
        )

        # Create transcript
        transcript = db_service.create(
            Transcript,
            id="transcript_1",
            session_id="test_session_transcript",
            full_text="This is a test transcript",
            segments=[
                {"start_time": 0.0, "end_time": 5.0, "text": "Hello", "confidence": 0.95}
            ],
            language="nb",
            model_version="nb-whisper-large"
        )

        assert transcript.session_id == "test_session_transcript"
        assert transcript.full_text == "This is a test transcript"
        assert transcript.language == "nb"

    def test_tag_model(self, db_session):
        """Test Tag model creation."""
        db_service = DatabaseService(db_session)

        # Create session first
        session = db_service.create(
            Session,
            id="test_session_tags",
            filename="test.m4a"
        )

        # Create tag
        tag = db_service.create(
            Tag,
            id="tag_1",
            session_id="test_session_tags",
            category="person",
            value="Ole Hansen",
            confidence=0.88,
            context="He was talking about Ole Hansen from the neighboring farm"
        )

        assert tag.session_id == "test_session_tags"
        assert tag.category == "person"
        assert tag.value == "Ole Hansen"
        assert tag.confidence == 0.88

    def test_summary_model(self, db_session):
        """Test Summary model creation."""
        db_service = DatabaseService(db_session)

        # Create session first
        session = db_service.create(
            Session,
            id="test_session_summary",
            filename="test.m4a"
        )

        # Create summary
        summary = db_service.create(
            Summary,
            session_id="test_session_summary",
            summary_text="This session discussed farm practices in the 1940s",
            key_points=["Agricultural methods", "Family history", "Land ownership"],
            historical_insights=["Traditional farming techniques", "Post-war changes"]
        )

        assert summary.session_id == "test_session_summary"
        assert "farm practices" in summary.summary_text
        assert len(summary.key_points) == 3

    def test_database_service_operations(self, db_session):
        """Test DatabaseService CRUD operations."""
        db_service = DatabaseService(db_session)

        # Create
        session = db_service.create(
            Session,
            id="crud_test",
            filename="crud_test.m4a",
            processing_status="detected"
        )

        # Read
        retrieved = db_service.get_by_id(Session, "crud_test")
        assert retrieved is not None
        assert retrieved.filename == "crud_test.m4a"

        # Update
        updated = db_service.update(session, processing_status="processing")
        assert updated.processing_status == "processing"

        # Get all
        all_sessions = db_service.get_all(Session)
        assert len(all_sessions) >= 1

        # Delete
        success = db_service.delete(session)
        assert success is True

        # Verify deletion
        deleted = db_service.get_by_id(Session, "crud_test")
        assert deleted is None