"""
ScholarGraph AI — Chat API Routes
Conversational AI interface with streaming responses and agent routing.
Follows existing API patterns and integrates with current architecture.
"""

import json
import asyncio
import time
from typing import Dict, List, Optional, AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.session import get_db
from database.models import User, ChatSession, ChatMessage
from agents.message_router import MessageRouter, AgentType
from agents.conversational_agent import ConversationalAgent
from auth.jwt_handler import get_current_user, get_optional_user

router = APIRouter()


class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    subject: Optional[str] = None


class ChatSessionResponse(BaseModel):
    session_id: str
    session_name: Optional[str] = None
    subject: Optional[str] = None
    message_count: int
    last_message_at: str
    created_at: str


class ChatMessageResponse(BaseModel):
    message_id: str
    session_id: str
    role: str
    content: str
    agent_type: Optional[str] = None
    created_at: str
    metadata: Optional[Dict] = None


@router.post("/stream")
async def chat_stream(
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """
    Streaming chat endpoint that routes messages to appropriate agents.
    Returns Server-Sent Events (SSE) for real-time token streaming.
    
    Follows existing API patterns with form data handling and user authentication.
    """
    # Generate or retrieve session
    if session_id:
        chat_session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.is_active == True
        ).first()
        
        if not chat_session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        # Create new session
        chat_session = ChatSession(
            user_id=current_user.id if current_user else None,
            subject=subject,
            tenant_id=current_user.tenant_id if current_user and hasattr(current_user, 'tenant_id') else None
        )
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
        session_id = chat_session.id
    
    # Store user message in database
    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=message,
        tenant_id=current_user.tenant_id if current_user and hasattr(current_user, 'tenant_id') else None
    )
    db.add(user_message)
    
    # Update session
    chat_session.message_count += 1
    chat_session.last_message_at = user_message.created_at
    if subject and not chat_session.subject:
        chat_session.subject = subject
    
    db.commit()
    db.refresh(chat_session)  # Ensure we have the latest state
    
    # Get recent message history for context (last 10 messages)
    recent_messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.desc()).limit(10).all()
    
    # Convert to context format
    context_history = []
    for msg in reversed(recent_messages):  # Chronological order
        context_history.append({
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.created_at.isoformat() if msg.created_at else None,
            "agent_type": msg.agent_type
        })

    async def generate_stream():
        """Generate streaming response with agent routing."""
        start_time = time.time()
        assistant_message_id = None
        full_response = ""
        agent_type_used = None
        
        try:
            # Initialize message router and conversational agent
            message_router = MessageRouter()
            conversational_agent = ConversationalAgent()
            
            # Route message to appropriate agent
            route_decision = await message_router.route_message(
                message,
                context_history,
                subject,
                current_user.id if current_user else None
            )
            
            # Get streaming response from routed agent
            response_generator = conversational_agent.get_streaming_response(
                route_decision,
                message,
                context_history,
                current_user
            )
            
            # Create assistant message record
            assistant_message = ChatMessage(
                session_id=session_id,
                role="assistant",
                content="",
                agent_type=route_decision.agent_type.value,
                message_metadata={
                    "route_decision": {
                        "agent_type": route_decision.agent_type.value,
                        "confidence": route_decision.confidence,
                        "reasoning": route_decision.reasoning
                    },
                    "dashboard_updates": route_decision.dashboard_updates
                },
                tenant_id=current_user.tenant_id if current_user and hasattr(current_user, 'tenant_id') else None
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)
            assistant_message_id = assistant_message.id
            agent_type_used = route_decision.agent_type.value
            
            # Stream the response
            async for token in response_generator:
                full_response += token
                
                # Send token chunk
                chunk_data = {
                    "type": "token",
                    "token": token,
                    "message_id": assistant_message_id,
                    "session_id": session_id,
                    "agent_type": agent_type_used
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
                await asyncio.sleep(0.01)  # Small delay for smooth streaming
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            # Update assistant message with full content
            assistant_message.content = full_response
            assistant_message.processing_time_ms = processing_time
            assistant_message.model_used = "openai_gpt4o"  # Could be dynamic based on actual LLM used
            db.commit()
            
            # Update session
            chat_session.message_count += 1
            chat_session.last_message_at = assistant_message.created_at
            db.commit()
            
            # Send final chunk with metadata
            final_chunk = {
                "type": "complete",
                "message_id": assistant_message_id,
                "session_id": session_id,
                "agent_type": agent_type_used,
                "processing_time_ms": processing_time,
                "dashboard_updates": route_decision.dashboard_updates,
                "route_confidence": route_decision.confidence,
                "full_content": full_response
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            
        except Exception as e:
            # Handle streaming errors
            error_chunk = {
                "type": "error",
                "error": str(e),
                "session_id": session_id,
                "message_id": assistant_message_id
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            
            # Update message with error if it was created
            if assistant_message_id:
                assistant_message.content = f"Error: {str(e)}"
                db.commit()
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
        }
    )


@router.get("/sessions/{session_id}", response_model=List[ChatMessageResponse])
async def get_session_history(
    session_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Get chat history for a specific session."""
    # Verify session exists and user has access
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check user access (tenant-based or owner)
    if (current_user and 
        session.user_id != current_user.id and 
        session.tenant_id != (current_user.tenant_id if hasattr(current_user, 'tenant_id') else None)):
        # Allow access if it's a public session (no user_id) or same tenant
        if session.user_id is not None:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get messages
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).limit(limit).all()
    
    return [
        ChatMessageResponse(
            message_id=msg.id,
            session_id=msg.session_id,
            role=msg.role,
            content=msg.content,
            agent_type=msg.agent_type,
            created_at=msg.created_at.isoformat() if msg.created_at else "",
            metadata=msg.message_metadata
        )
        for msg in messages
    ]


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_sessions(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """List active chat sessions for the current user or tenant."""
    query = db.query(ChatSession).filter(ChatSession.is_active == True)
    
    # Filter by user or tenant
    if current_user:
        if hasattr(current_user, 'tenant_id') and current_user.tenant_id:
            # Show user's sessions + tenant-wide sessions
            query = query.filter(
                (ChatSession.user_id == current_user.id) |
                (ChatSession.tenant_id == current_user.tenant_id)
            )
        else:
            # Show only user's sessions
            query = query.filter(ChatSession.user_id == current_user.id)
    else:
        # Anonymous users - no sessions
        return []
    
    sessions = query.order_by(ChatSession.last_message_at.desc()).limit(limit).all()
    
    return [
        ChatSessionResponse(
            session_id=session.id,
            session_name=session.session_name,
            subject=session.subject,
            message_count=session.message_count,
            last_message_at=session.last_message_at.isoformat() if session.last_message_at else "",
            created_at=session.created_at.isoformat() if session.created_at else ""
        )
        for session in sessions
    ]


@router.post("/sessions")
async def create_session(
    session_name: Optional[str] = None,
    subject: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Create a new chat session."""
    chat_session = ChatSession(
        user_id=current_user.id if current_user else None,
        session_name=session_name or f"Chat {int(time.time())}",
        subject=subject,
        tenant_id=current_user.tenant_id if current_user and hasattr(current_user, 'tenant_id') else None
    )
    
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    
    return ChatSessionResponse(
        session_id=chat_session.id,
        session_name=chat_session.session_name,
        subject=chat_session.subject,
        message_count=chat_session.message_count,
        last_message_at=chat_session.last_message_at.isoformat() if chat_session.last_message_at else "",
        created_at=chat_session.created_at.isoformat() if chat_session.created_at else ""
    )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """Delete a chat session (soft delete)."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check ownership
    if current_user and session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Soft delete
    session.is_active = False
    db.commit()
    
    return {"message": "Session deleted successfully"}


@router.get("/agents/capabilities")
async def get_agent_capabilities():
    """Get capabilities of all available agents."""
    router = MessageRouter()
    return {"capabilities": router.get_agent_capabilities()}


@router.get("/subjects")
async def get_supported_subjects():
    """Get list of supported academic subjects."""
    router = MessageRouter()
    return {"subjects": router.get_supported_subjects()}


@router.get("/status")
async def get_chat_status():
    """Get chat system status and LLM availability."""
    agent = ConversationalAgent()
    return {
        "status": "operational",
        "llm_status": agent.get_llm_status(),
        "supported_agents": [agent_type.value for agent_type in AgentType],
        "features": {
            "streaming_responses": True,
            "agent_routing": True,
            "dashboard_integration": True,
            "session_persistence": True,
            "multi_llm_support": True
        }
    }
