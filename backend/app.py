#!/usr/bin/env python3
"""
FastAPI Backend for Civic Grant Agent
Serves the ADK agent pipeline via AG-UI Protocol
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Import AG-UI ADK components
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
import sys
sys.path.append('/app')
from agent_config import civic_grant_agent

# Verify API key
if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError("GOOGLE_API_KEY environment variable not set")

# Create ADK middleware agent instance
adk_civic_grant_agent = ADKAgent(
    adk_agent=civic_grant_agent,
    app_name="civic_grant_agent",
    user_id="default_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True
)

# Initialize FastAPI app
app = FastAPI(
    title="Civic Grant Agent API",
    description="API for the multi-agent grant finding and writing system using AG-UI Protocol",
    version="2.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint (keep for Kubernetes)
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes"""
    return {
        "status": "healthy",
        "service": "civic-grant-agent-backend",
        "timestamp": datetime.now().isoformat()
    }

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "Civic Grant Agent API",
        "version": "2.0.0",
        "status": "running",
        "protocol": "AG-UI",
        "endpoints": {
            "ag_ui": "/ (AG-UI stream endpoint - POST only)",
            "health": "/health"
        }
    }

# Add the ADK endpoint - this handles all AG-UI protocol communication
# Mount at root path - GET requests go to root() above, POST requests handled by AG-UI
add_adk_fastapi_endpoint(app, adk_civic_grant_agent, path="/copilotkit")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        log_level="info"
    )
