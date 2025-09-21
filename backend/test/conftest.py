"""
Pytest configuration and fixtures for testing.
"""

import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import Base
from app.core.config import settings
from app.core.logging import configure_logging
from app.services.google_drive_service import GoogleDriveService


@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    """Configure logging for all tests."""
    configure_logging()


@pytest.fixture(scope="session")
def test_database():
    """Create a test database session."""
    # Use in-memory SQLite for tests
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    # Create tables
    Base.metadata.create_all(bind=test_engine)

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    yield TestSessionLocal

    # Cleanup
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(test_database):
    """Get a database session for testing."""
    session = test_database()
    try:
        yield session
    finally:
        session.rollback()  # Rollback any uncommitted changes
        session.close()


@pytest.fixture
def google_drive_service():
    """Create and authenticate a Google Drive service for testing."""
    service = GoogleDriveService()
    if not service.authenticate():
        pytest.skip("Google Drive authentication failed - check credentials")
    return service


@pytest.fixture
def skip_if_no_credentials():
    """Skip test if Google Drive credentials are not available."""
    if not os.path.exists(settings.GOOGLE_DRIVE_CREDENTIALS_PATH):
        pytest.skip(f"Credentials file not found: {settings.GOOGLE_DRIVE_CREDENTIALS_PATH}")


@pytest.fixture
def skip_if_no_folder_id():
    """Skip test if Google Drive folder ID is not configured."""
    if not settings.GOOGLE_DRIVE_FOLDER_ID:
        pytest.skip("GOOGLE_DRIVE_FOLDER_ID not configured")


@pytest.fixture
def test_audio_storage(tmp_path):
    """Create a temporary directory for audio file testing."""
    audio_dir = tmp_path / "audio_files"
    audio_dir.mkdir()
    return str(audio_dir)