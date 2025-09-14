from app.core.database import init_db, engine
from app.models.db_models import Session, SessionMetadata, Transcript, Tag, Summary
from app.core.logging import get_logger

logger = get_logger()

def create_tables():
    """Create all database tables."""
    try:
        logger.info("Creating database tables...")
        init_db()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def reset_database():
    """Drop and recreate all database tables."""
    try:
        logger.info("Dropping all database tables...")
        from app.core.database import Base
        Base.metadata.drop_all(bind=engine)
        logger.info("Creating database tables...")
        init_db()
        logger.info("Database reset completed successfully")
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise

if __name__ == "__main__":
    create_tables()