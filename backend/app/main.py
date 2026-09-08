"""
AI Interview Trainer — FastAPI Backend
=======================================
Problem Statement No. 22: Interview Trainer Agent
IBM Granite / watsonx.ai powered RAG interview preparation system.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.database.connection import init_db
from app.services.rag_service import initialize_rag
from app.services.granite_service import is_granite_configured, DEMO_MODE
from app.routes import profile, resume, interview, analytics, preparation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Initialising database...")
    init_db()
    logger.info("Loading RAG knowledge base...")
    initialize_rag()

    granite_status = "CONFIGURED" if is_granite_configured() else "NOT CONFIGURED (Demo Mode active)"
    logger.info("IBM Granite status: %s", granite_status)
    logger.info("Demo Mode: %s", DEMO_MODE)
    logger.info("AI Interview Trainer backend ready.")
    yield
    logger.info("Shutting down AI Interview Trainer backend.")


app = FastAPI(
    title="AI Interview Trainer Agent",
    description="RAG-powered interview preparation system using IBM Granite / watsonx.ai",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the React dev server
FRONTEND_ORIGINS = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,"
    "https://yeddulapavankumarreddy-create.github.io",
)
origins = [o.strip() for o in FRONTEND_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(profile.router)
app.include_router(resume.router)
app.include_router(interview.router)
app.include_router(analytics.router)
app.include_router(preparation.router)


@app.get("/")
def root():
    return {
        "app": "AI Interview Trainer Agent",
        "version": "1.0.0",
        "problem_statement": "No. 22 — Interview Trainer Agent",
        "granite_configured": is_granite_configured(),
        "demo_mode": DEMO_MODE,
        "docs": "/docs",
    }


@app.get("/api/status")
def status():
    return {
        "status": "online",
        "granite_configured": is_granite_configured(),
        "demo_mode": DEMO_MODE,
        "message": (
            "IBM Granite connected and ready."
            if is_granite_configured()
            else "Demo Mode — IBM Granite is not currently connected."
        ),
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again."},
    )
