import logfire
from .config import settings

def configure_logging():
    """Configure Logfire logging for the application."""
    if settings.LOGFIRE_TOKEN:
        logfire.configure(token=settings.LOGFIRE_TOKEN)
    else:
        # Configure basic logging without Logfire token
        logfire.configure()
    
    logfire.info("Logging configured for Vidarshov Gård Recording App")

def get_logger():
    """Get a configured logger instance."""
    return logfire