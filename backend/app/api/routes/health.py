from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any
import logging
from datetime import datetime
import psutil
import os

from app.services.vector_search import VectorSearchService
from app.services.knowledge_graph import KnowledgeGraphService
from app.main import get_vector_service, get_kg_service

logger = logging.getLogger(__name__)

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    services: Dict[str, Any]
    system: Dict[str, Any]

@router.get("/health", response_model=HealthResponse)
async def health_check(
    vector_service: VectorSearchService = Depends(get_vector_service),
    kg_service: KnowledgeGraphService = Depends(get_kg_service)
):
    """Comprehensive health check"""
    try:
        # Check services
        services_status = {}
        
        # Vector search service
        try:
            vector_stats = await vector_service.get_statistics()
            services_status["vector_search"] = {
                "status": "healthy",
                "documents": vector_stats.get("total_documents", 0),
                "model": vector_stats.get("model_name", "unknown")
            }
        except Exception as e:
            services_status["vector_search"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Knowledge graph service
        try:
            kg_stats = await kg_service.get_graph_statistics()
            services_status["knowledge_graph"] = {
                "status": "healthy",
                "entities": kg_stats.get("total_entities", 0),
                "relationships": kg_stats.get("total_relationships", 0)
            }
        except Exception as e:
            services_status["knowledge_graph"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # System information
        system_info = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
        }
        
        # Overall status
        overall_status = "healthy"
        for service_status in services_status.values():
            if service_status["status"] != "healthy":
                overall_status = "degraded"
                break
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            version="1.0.0",
            services=services_status,
            system=system_info
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            version="1.0.0",
            services={"error": str(e)},
            system={}
        )

@router.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}

@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}