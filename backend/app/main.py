from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import logging
from datetime import datetime
import asyncio
import os
from dotenv import load_dotenv

from app.core.config import settings
from app.api.routes import chat, sessions, data, health, realtime, upload
from app.services.rag_service import RAGService
from app.services.knowledge_graph import KnowledgeGraphService
from app.services.vector_search import VectorSearchService
from app.services.scraper_service import ScraperService
from app.core.database import init_db
from app.core.logging_config import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MOSDAC AI Chatbot API",
    description="AI-powered chatbot for MOSDAC meteorological and oceanographic data with real-time capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Global services
rag_service: Optional[RAGService] = None
kg_service: Optional[KnowledgeGraphService] = None
vector_service: Optional[VectorSearchService] = None
scraper_service: Optional[ScraperService] = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global rag_service, kg_service, vector_service, scraper_service
    
    logger.info("Starting MOSDAC AI Chatbot API...")
    
    try:
        # Initialize database
        await init_db()
        
        # Initialize services
        kg_service = KnowledgeGraphService()
        vector_service = VectorSearchService()
        scraper_service = ScraperService()
        rag_service = RAGService(kg_service, vector_service)
        
        # Load existing data if available
        await vector_service.load_index()
        await kg_service.connect()
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down MOSDAC AI Chatbot API...")
    
    if kg_service:
        await kg_service.close()
    if vector_service:
        await vector_service.close()

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="./data/uploads"), name="uploads")

# Include routers
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])
app.include_router(data.router, prefix="/api/v1", tags=["data"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(realtime.router, prefix="/api/v1/realtime", tags=["realtime"])
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "MOSDAC AI Chatbot API",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "Real-time weather data",
            "Ocean monitoring",
            "Satellite tracking",
            "File upload processing",
            "Voice input support",
            "Location-aware queries",
            "Knowledge graph integration",
            "Vector search capabilities"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

# Dependency to get services
def get_rag_service() -> RAGService:
    if rag_service is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    return rag_service

def get_kg_service() -> KnowledgeGraphService:
    if kg_service is None:
        raise HTTPException(status_code=503, detail="Knowledge Graph service not initialized")
    return kg_service

def get_vector_service() -> VectorSearchService:
    if vector_service is None:
        raise HTTPException(status_code=503, detail="Vector Search service not initialized")
    return vector_service

def get_scraper_service() -> ScraperService:
    if scraper_service is None:
        raise HTTPException(status_code=503, detail="Scraper service not initialized")
    return scraper_service

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )