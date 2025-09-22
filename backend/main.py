from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

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

# Mount static files
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="../frontend/templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    logger.info("Root endpoint accessed")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/sessions", response_class=HTMLResponse)
async def sessions_view(request: Request):
    logger.info("Sessions view accessed")
    return templates.TemplateResponse("sessions.html", {"request": request})

@app.get("/sessions/{session_id}", response_class=HTMLResponse)
async def session_detail_view(request: Request, session_id: str):
    logger.info(f"Session detail view accessed for: {session_id}")
    return templates.TemplateResponse("session_detail.html", {"request": request, "session_id": session_id})

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}
