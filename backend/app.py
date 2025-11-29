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
import logging
import sys

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Apply AG-UI/ADK patches BEFORE importing ADKAgent
from ag_ui_fix import apply_patches
apply_patches()

# Import AG-UI ADK components (after patches are applied)
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint

sys.path.append('/app')
from agent_config import root_agent
from agent_card import civic_grant_agent_card

# Verify API key
if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError("GOOGLE_API_KEY environment variable not set")

# Create ADK middleware agent instance
adk_root_agent = ADKAgent(
    adk_agent=root_agent,
    app_name="civic-grant-agent-backend",
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

# Configure CORS
origins = [
    "https://civic-grant-agent.xomanova.io",
    "https://civic-grant-agent-core.xomanova.io",
    "http://localhost:3000",
    "http://localhost:8000",
]

if os.getenv("ENVIRONMENT", "development") == "development":
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes"""
    return {
        "status": "healthy",
        "service": "civic-grant-agent-backend",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "Civic Grant Agent API",
        "version": "2.0.0",
        "status": "running",
        "protocol": "AG-UI",
        "endpoints": {
            "ag_ui": "/api/copilotkit (AG-UI stream endpoint)",
            "health": "/health",
            "agent_card": "/.well-known/agent.json"
        }
    }


@app.get("/.well-known/agent.json")
async def get_agent_card():
    """A2A Protocol Agent Card endpoint for agent discovery"""
    return civic_grant_agent_card.model_dump(by_alias=True, exclude_none=True)


# Add the ADK endpoint - handles all AG-UI protocol communication
add_adk_fastapi_endpoint(app, adk_root_agent, path="/api/copilotkit")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        log_level="info"
    )
