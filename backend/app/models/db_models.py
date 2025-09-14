from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    drive_file_id = Column(String, unique=True, nullable=True)
    filename = Column(String, nullable=False)
    original_path = Column(String, nullable=True)
    converted_path = Column(String, nullable=True)
    upload_timestamp = Column(DateTime, nullable=True)
    processing_status = Column(String, default="detected")
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    metadata_session = relationship("SessionMetadata", back_populates="session", uselist=False)
    transcript = relationship("Transcript", back_populates="session", uselist=False)
    tags = relationship("Tag", back_populates="session")
    summary = relationship("Summary", back_populates="session", uselist=False)


class SessionMetadata(Base):
    __tablename__ = "session_metadata"

    session_id = Column(String, ForeignKey("sessions.id"), primary_key=True)
    participants = Column(JSON, nullable=True)
    topics = Column(JSON, nullable=True)
    historical_periods = Column(JSON, nullable=True)
    location_notes = Column(Text, nullable=True)
    session_notes = Column(Text, nullable=True)
    date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relationship
    session = relationship("Session", back_populates="metadata")


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    full_text = Column(Text, nullable=True)
    segments = Column(JSON, nullable=True)
    language = Column(String, default="nb")
    model_version = Column(String, nullable=True)
    processing_duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relationship
    session = relationship("Session", back_populates="transcript")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    category = Column(String, nullable=False)
    value = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)
    context = Column(Text, nullable=True)
    extraction_model = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    session = relationship("Session", back_populates="tags")


class Summary(Base):
    __tablename__ = "summaries"

    session_id = Column(String, ForeignKey("sessions.id"), primary_key=True)
    summary_text = Column(Text, nullable=True)
    key_points = Column(JSON, nullable=True)
    historical_insights = Column(JSON, nullable=True)
    questions_raised = Column(JSON, nullable=True)
    related_sessions = Column(JSON, nullable=True)
    processing_model = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    session = relationship("Session", back_populates="summary")