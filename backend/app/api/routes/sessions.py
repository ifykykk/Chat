from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory session storage (in production, use a database)
sessions_db = {}

class SessionCreate(BaseModel):
    title: Optional[str] = "New Chat"

class SessionUpdate(BaseModel):
    title: str

class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int

@router.post("/sessions", response_model=SessionResponse)
async def create_session(session: SessionCreate):
    """Create a new chat session"""
    try:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        new_session = {
            "id": session_id,
            "title": session.title,
            "created_at": now,
            "updated_at": now,
            "messages": [],
            "message_count": 0
        }
        
        sessions_db[session_id] = new_session
        
        return SessionResponse(
            id=session_id,
            title=session.title,
            created_at=now,
            updated_at=now,
            message_count=0
        )
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating session: {str(e)}"
        )

@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(limit: int = 50):
    """Get all chat sessions"""
    try:
        sessions = list(sessions_db.values())
        
        # Sort by updated_at descending
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        
        return [
            SessionResponse(
                id=session["id"],
                title=session["title"],
                created_at=session["created_at"],
                updated_at=session["updated_at"],
                message_count=session["message_count"]
            )
            for session in sessions[:limit]
        ]
        
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting sessions: {str(e)}"
        )

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a specific session"""
    try:
        if session_id not in sessions_db:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions_db[session_id]
        
        return SessionResponse(
            id=session["id"],
            title=session["title"],
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            message_count=session["message_count"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting session: {str(e)}"
        )

@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(session_id: str, session_update: SessionUpdate):
    """Update a session"""
    try:
        if session_id not in sessions_db:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions_db[session_id]
        session["title"] = session_update.title
        session["updated_at"] = datetime.utcnow().isoformat()
        
        return SessionResponse(
            id=session["id"],
            title=session["title"],
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            message_count=session["message_count"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating session: {str(e)}"
        )

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        if session_id not in sessions_db:
            raise HTTPException(status_code=404, detail="Session not found")
        
        del sessions_db[session_id]
        
        return {"message": f"Session {session_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting session: {str(e)}"
        )