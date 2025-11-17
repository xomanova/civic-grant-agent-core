#!/usr/bin/env python3
"""
FastAPI Backend for Civic Grant Agent
Serves the ADK agent pipeline via REST API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime

# Load environment variables
load_dotenv()

# Import ADK components
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import sys
sys.path.append('/app')
from agent_config import civic_grant_agent

# Verify API key
if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError("GOOGLE_API_KEY environment variable not set")

# Initialize FastAPI app
app = FastAPI(
    title="Civic Grant Agent API",
    description="API for the multi-agent grant finding and writing system",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global configuration
APP_NAME = "civic_grant_agent"
session_service = InMemorySessionService()
runner = Runner(
    agent=civic_grant_agent,
    app_name=APP_NAME,
    session_service=session_service
)

# Pydantic models for API
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    session_id: Optional[str] = None
    history: Optional[List[Message]] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    agent_name: str
    timestamp: str

class SessionInfo(BaseModel):
    session_id: str
    user_id: str
    created_at: str
    message_count: int

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes"""
    return {
        "status": "healthy",
        "service": "civic-grant-agent-backend",
        "timestamp": datetime.now().isoformat()
    }

# Main chat endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message through the agent pipeline.
    
    The agent will:
    1. Collect department profile (ProfileBuilder)
    2. Search for grants (GrantScout)
    3. Validate eligibility (GrantValidator)
    4. Draft applications (GrantWriter)
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create or get session
        try:
            session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=request.user_id,
                session_id=session_id
            )
        except:
            session = await session_service.get_session(
                app_name=APP_NAME,
                user_id=request.user_id,
                session_id=session_id
            )
        
        # Create message content
        content = types.Content(
            role="user",
            parts=[types.Part(text=request.message)]
        )
        
        # Collect agent response
        response_text = ""
        agent_name = "CivicGrantAgent"
        
        # Run the agent and collect response
        async for event in runner.run_async(
            user_id=request.user_id,
            session_id=session.id,
            new_message=content
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text and part.text.strip() and part.text != "None":
                        response_text += part.text
                    elif part.executable_code:
                        response_text += "\n[Executing code...]\n"
                    elif part.code_execution_result:
                        if part.code_execution_result.output:
                            response_text += f"\n[Code output: {part.code_execution_result.output}]\n"
            
            # Capture agent name from event
            if event.author:
                agent_name = event.author
        
        return ChatResponse(
            response=response_text.strip() or "Processing your request...",
            session_id=session_id,
            agent_name=agent_name,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

# Get session info endpoint
@app.get("/api/session/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str, user_id: str = "default_user"):
    """Get information about a specific session"""
    try:
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        
        return SessionInfo(
            session_id=session.id,
            user_id=user_id,
            created_at=session.created_at if hasattr(session, 'created_at') else datetime.now().isoformat(),
            message_count=len(session.events) if hasattr(session, 'events') else 0
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found: {str(e)}")

# Create new session endpoint
@app.post("/api/session/new")
async def create_new_session(user_id: str = "default_user"):
    """Create a new chat session"""
    try:
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        
        return {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "Civic Grant Agent API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "/api/chat",
            "health": "/health",
            "session": "/api/session/{session_id}",
            "new_session": "/api/session/new"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        log_level="info"
    )
