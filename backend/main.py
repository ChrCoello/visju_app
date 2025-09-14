from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

# Configure logging
configure_logging()
logger = get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application starting up
    logger.info("Application starting up")
    # Initialize database
    from app.core.init_db import create_tables
    create_tables()
    yield
    # Application shutting down
    logger.info("Application shutting down")

app = FastAPI(
    title="Vidarshov Gård Recording App",
    description="Application to record, transcribe, and analyze conversations about Vidarshov Gård farm history",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")



@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Vidarshov Gård Recording App API"}

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}
