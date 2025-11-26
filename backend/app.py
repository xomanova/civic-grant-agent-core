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

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import AG-UI ADK components
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from ag_ui_adk.event_translator import EventTranslator
from ag_ui.core import (
    TextMessageContentEvent, TextMessageStartEvent, TextMessageEndEvent,
    EventType, BaseEvent
)
import uuid
import sys
from typing import AsyncGenerator
sys.path.append('/app')
from agent_config import root_agent

# ============================================================================
# MONKEY-PATCH: Fix multiple AG-UI/ADK integration issues
# ============================================================================
# 1. Empty/whitespace text content crash: EventTranslator validation error
# 2. "Both invocation_id and new_message are None" crash when continuing session
#
# These are bugs in ag_ui_adk that we work around here.

from ag_ui_adk.adk_agent import ADKAgent as AgUIADKAgent

# Patch 1: Fix empty text delta validation errors
_original_translate = EventTranslator.translate

async def _patched_translate(self, adk_event, thread_id: str, run_id: str) -> AsyncGenerator[BaseEvent, None]:
    """
    Patched translate method that catches validation errors per-event
    and skips problematic events instead of crashing the whole stream.
    """
    gen = _original_translate(self, adk_event, thread_id, run_id)
    
    while True:
        try:
            event = await gen.__anext__()
            yield event
        except StopAsyncIteration:
            break
        except ValueError as e:
            error_msg = str(e)
            # Check if it's the empty delta validation error
            if "Delta must not be" in error_msg or "empty string" in error_msg.lower():
                logger.warning(f"[PATCH] Caught empty delta validation error, skipping event: {error_msg}")
                # Continue to next event instead of crashing
                continue
            else:
                # Re-raise other ValueError exceptions
                raise
        except Exception as e:
            # Log but re-raise unexpected errors
            logger.error(f"[PATCH] Unexpected error in translate: {type(e).__name__}: {e}")
            raise

EventTranslator.translate = _patched_translate
logger.info("[STARTUP] Applied monkey-patch to EventTranslator.translate for empty text handling")

# Patch 2: Fix "Both invocation_id and new_message are None" error
# This happens when ag_ui_adk can't find unseen messages but still tries to run ADK
# The root cause is message ID tracking - when a message is marked as processed,
# subsequent requests with the same messages get filtered out incorrectly.

_original_run_adk_in_background = AgUIADKAgent._run_adk_in_background
_original_get_unseen_messages = AgUIADKAgent._get_unseen_messages

async def _patched_get_unseen_messages(self, input):
    """
    Patched _get_unseen_messages that ensures new user messages are never filtered out.
    The original can incorrectly return empty when all messages appear to be processed,
    but the user just sent a new message that should be processed.
    """
    result = await _original_get_unseen_messages(self, input)
    
    if result:
        return result
    
    # If no unseen messages found, check if there's a recent user message
    # This handles the case where message tracking incorrectly filters out new messages
    if input.messages:
        # Find the last user message
        for msg in reversed(input.messages):
            role = getattr(msg, 'role', None)
            content = getattr(msg, 'content', '')
            if role == 'user' and content and isinstance(content, str) and content.strip():
                logger.info(f"[PATCH] No unseen messages found, but found last user message: '{content[:50]}...'")
                # Return just this message to be processed
                return [msg]
    
    return result

AgUIADKAgent._get_unseen_messages = _patched_get_unseen_messages
logger.info("[STARTUP] Applied monkey-patch to ADKAgent._get_unseen_messages for message tracking")

async def _patched_run_adk_in_background(self, input, adk_agent, user_id, app_name, event_queue, tool_results=None, message_batch=None):
    """
    Patched _run_adk_in_background that catches the 'Both invocation_id and new_message are None'
    ValueError and gracefully handles it instead of crashing.
    """
    from ag_ui.core import RunFinishedEvent, RunErrorEvent, EventType
    
    try:
        await _original_run_adk_in_background(
            self, input, adk_agent, user_id, app_name, event_queue, 
            tool_results=tool_results, message_batch=message_batch
        )
    except ValueError as e:
        error_msg = str(e)
        if "Both invocation_id and new_message are None" in error_msg:
            logger.warning(f"[PATCH] Caught ADK runner error: {error_msg}")
            logger.warning("[PATCH] This usually means the message was already processed. Completing gracefully.")
            
            # Send a friendly completion instead of crashing
            await event_queue.put(
                RunFinishedEvent(
                    type=EventType.RUN_FINISHED,
                    thread_id=input.thread_id,
                    run_id=input.run_id
                )
            )
            await event_queue.put(None)
        else:
            raise
    except Exception as e:
        logger.error(f"[PATCH] Unexpected error in _run_adk_in_background: {type(e).__name__}: {e}")
        raise

AgUIADKAgent._run_adk_in_background = _patched_run_adk_in_background
logger.info("[STARTUP] Applied monkey-patch to ADKAgent._run_adk_in_background for message handling")

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
# Define allowed origins based on environment
origins = [
    "https://civic-grant-agent.xomanova.io",      # Frontend
    "https://civic-grant-agent-core.xomanova.io", # Backend (self)
    "http://localhost:3000",                        # Local Frontend
    "http://localhost:8000",                        # Local Backend
]

# In development, allow all origins or expand the list
if os.getenv("ENVIRONMENT", "development") == "development":
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
add_adk_fastapi_endpoint(app, adk_root_agent, path="/api/copilotkit")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        log_level="info"
    )
