from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.services.rag_service import RAGService
from app.main import get_rag_service

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default"
    location: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    entities: List[Dict[str, Any]]
    confidence: float
    session_id: str
    timestamp: str
    query_type: str
    reasoning: Optional[str] = None

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Process chat message and return AI response"""
    try:
        logger.info(f"Processing chat request: {request.query[:100]}...")
        
        # Process query with RAG
        if request.location:
            rag_response = await rag_service.handle_geospatial_query(
                request.query, request.location
            )
        else:
            rag_response = await rag_service.process_query(
                request.query, request.session_id
            )
        
        # Log successful response
        background_tasks.add_task(
            log_chat_interaction,
            request.query,
            rag_response.answer,
            request.session_id,
            rag_response.confidence
        )
        
        return ChatResponse(
            answer=rag_response.answer,
            sources=rag_response.sources,
            entities=rag_response.entities,
            confidence=rag_response.confidence,
            session_id=request.session_id,
            timestamp=datetime.utcnow().isoformat(),
            query_type=rag_response.query_type,
            reasoning=rag_response.reasoning
        )
        
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )

@router.get("/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Get chat history for a session"""
    try:
        history = await rag_service.get_conversation_history(session_id)
        return {
            "session_id": session_id,
            "history": history[-limit:],  # Return last N messages
            "total_messages": len(history)
        }
    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving chat history: {str(e)}"
        )

@router.delete("/chat/history/{session_id}")
async def clear_chat_history(
    session_id: str,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Clear chat history for a session"""
    try:
        await rag_service.clear_conversation_history(session_id)
        return {"message": f"Chat history cleared for session {session_id}"}
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing chat history: {str(e)}"
        )

async def log_chat_interaction(query: str, response: str, session_id: str, confidence: float):
    """Background task to log chat interactions"""
    try:
        # This would typically log to a database or analytics service
        logger.info(f"Chat interaction logged - Session: {session_id}, Confidence: {confidence}")
    except Exception as e:
        logger.error(f"Failed to log chat interaction: {e}")