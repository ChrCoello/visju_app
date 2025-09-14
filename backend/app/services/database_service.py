from typing import Optional, List, Type, TypeVar
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.db_models import Session, Tag

logger = get_logger()
T = TypeVar('T')

class DatabaseService:
    """Service class for database operations."""

    def __init__(self, db: DBSession):
        self.db = db

    def create(self, model_class: Type[T], **kwargs) -> T:
        """Create a new record."""
        try:
            instance = model_class(**kwargs)
            self.db.add(instance)
            self.db.commit()
            self.db.refresh(instance)
            logger.info(f"Created {model_class.__name__} with ID: {getattr(instance, 'id', 'N/A')}")
            return instance
        except SQLAlchemyError as e:
            logger.error(f"Error creating {model_class.__name__}: {e}")
            self.db.rollback()
            raise

    def get_by_id(self, model_class: Type[T], record_id: str) -> Optional[T]:
        """Get a record by ID."""
        try:
            return self.db.query(model_class).filter(model_class.id == record_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {model_class.__name__} by ID {record_id}: {e}")
            raise

    def get_all(self, model_class: Type[T], limit: Optional[int] = None) -> List[T]:
        """Get all records of a model type."""
        try:
            query = self.db.query(model_class)
            if limit:
                query = query.limit(limit)
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {model_class.__name__}: {e}")
            raise

    def update(self, instance: T, **kwargs) -> T:
        """Update an existing record."""
        try:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            self.db.commit()
            self.db.refresh(instance)
            logger.info(f"Updated {instance.__class__.__name__} with ID: {getattr(instance, 'id', 'N/A')}")
            return instance
        except SQLAlchemyError as e:
            logger.error(f"Error updating {instance.__class__.__name__}: {e}")
            self.db.rollback()
            raise

    def delete(self, instance: T) -> bool:
        """Delete a record."""
        try:
            self.db.delete(instance)
            self.db.commit()
            logger.info(f"Deleted {instance.__class__.__name__} with ID: {getattr(instance, 'id', 'N/A')}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {instance.__class__.__name__}: {e}")
            self.db.rollback()
            raise

    def get_session_with_metadata(self, session_id: str) -> Optional[Session]:
        """Get session with its metadata."""
        try:
            return self.db.query(Session).filter(Session.id == session_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting session with metadata for ID {session_id}: {e}")
            raise

    def get_sessions_by_status(self, status: str) -> List[Session]:
        """Get sessions by processing status."""
        try:
            return self.db.query(Session).filter(Session.processing_status == status).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting sessions by status {status}: {e}")
            raise

    def get_tags_by_category(self, session_id: str, category: str) -> List[Tag]:
        """Get tags by session and category."""
        try:
            return self.db.query(Tag).filter(
                Tag.session_id == session_id,
                Tag.category == category
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting tags for session {session_id} and category {category}: {e}")
            raise


def get_database_service(db: DBSession = next(get_db())) -> DatabaseService:
    """Get database service instance."""
    return DatabaseService(db)