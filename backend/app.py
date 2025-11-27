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
# The error happens when TextMessageContentEvent is created with delta=""
# Pydantic validates immediately and raises before any wrapper can catch it.
# 
# Solution: Patch TextMessageContentEvent class BEFORE the EventTranslator uses it

# Store original TextMessageContentEvent
_OriginalTextMessageContentEvent = TextMessageContentEvent

class SafeTextMessageContentEvent(TextMessageContentEvent):
    """
    Subclass that allows empty delta strings during construction.
    We replace empty string with a sentinel that we filter out later.
    """
    _is_empty_delta: bool = False
    
    def __init__(self, **data):
        delta = data.get('delta', '')
        if delta == '':
            # Replace empty with placeholder to pass validation, mark for skip
            data['delta'] = '\u200B'  # Zero-width space (invisible)
            super().__init__(**data)
            object.__setattr__(self, '_is_empty_delta', True)
        else:
            super().__init__(**data)
            object.__setattr__(self, '_is_empty_delta', False)

# Patch TextMessageContentEvent in the event_translator module BEFORE translate is called
import ag_ui_adk.event_translator
ag_ui_adk.event_translator.TextMessageContentEvent = SafeTextMessageContentEvent

logger.info("[STARTUP] Patched TextMessageContentEvent to handle empty deltas")

# Also patch the main translate to filter out events marked as empty
_original_translate = EventTranslator.translate

async def _patched_translate(self, adk_event, thread_id: str, run_id: str) -> AsyncGenerator[BaseEvent, None]:
    """
    Patched translate method that:
    1. Filters out events with empty/placeholder deltas
    2. Catches validation errors as a safety net
    """
    try:
        gen = _original_translate(self, adk_event, thread_id, run_id)
        
        while True:
            try:
                event = await gen.__anext__()
                
                # Filter out events marked as empty by our SafeTextMessageContentEvent
                if hasattr(event, '_is_empty_delta') and event._is_empty_delta:
                    logger.warning(f"[PATCH] Filtering out empty delta event")
                    continue
                
                # Also filter events with just zero-width space
                if hasattr(event, 'delta') and event.delta == '\u200B':
                    logger.warning(f"[PATCH] Filtering out zero-width space delta event")
                    continue
                    
                yield event
            except StopAsyncIteration:
                break
            except Exception as e:
                error_msg = str(e).lower()
                # Check if it's a validation error related to empty strings
                if "string_too_short" in error_msg or "at least 1 character" in error_msg or "empty string" in error_msg or "delta must not" in error_msg:
                    logger.warning(f"[PATCH] Caught validation error during translate iteration, skipping: {e}")
                    continue
                else:
                    logger.error(f"[PATCH] Unexpected error in translate: {type(e).__name__}: {e}")
                    raise
    except Exception as e:
        error_msg = str(e).lower()
        if "string_too_short" in error_msg or "at least 1 character" in error_msg or "empty string" in error_msg:
            logger.warning(f"[PATCH] Caught validation error at translate generator start, skipping event: {e}")
            return  # Empty generator
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
    Patched _get_unseen_messages that:
    1. Filters out CopilotKit's system messages (we have our own instructions)
    2. Ensures user messages are never filtered out
    """
    logger.info(f"[PATCH] _get_unseen_messages called with {len(input.messages) if input.messages else 0} messages")
    
    # Debug: Log ALL messages
    if input.messages:
        logger.info("[PATCH] === ALL INPUT MESSAGES ===")
        for i, msg in enumerate(input.messages):
            msg_id = getattr(msg, 'id', 'NO_ID')
            role = getattr(msg, 'role', 'NO_ROLE')
            content = getattr(msg, 'content', '')
            content_preview = str(content)[:100] if content else 'EMPTY'
            logger.info(f"[PATCH] Message {i}: id={msg_id}, role={role}, content={content_preview}")
    
    result = await _original_get_unseen_messages(self, input)
    
    logger.info(f"[PATCH] Original _get_unseen_messages returned {len(result) if result else 0} unseen messages")
    
    # Filter out system messages - CopilotKit adds these but ADK agents have their own instructions
    if result:
        filtered_result = [msg for msg in result if getattr(msg, 'role', None) != 'system']
        removed_count = len(result) - len(filtered_result)
        if removed_count > 0:
            logger.info(f"[PATCH] Filtered out {removed_count} system message(s)")
        result = filtered_result
    
    # Debug: Log UNSEEN messages after filtering
    if result:
        logger.info("[PATCH] === UNSEEN MESSAGES (after filter) ===")
        for i, msg in enumerate(result):
            msg_id = getattr(msg, 'id', 'NO_ID')
            role = getattr(msg, 'role', 'NO_ROLE')
            content = getattr(msg, 'content', '')
            content_preview = str(content)[:100] if content else 'EMPTY'
            logger.info(f"[PATCH] Unseen {i}: id={msg_id}, role={role}, content={content_preview}")
    
    # Check if the result includes a user message
    has_user_message = False
    if result:
        for msg in result:
            if getattr(msg, 'role', None) == 'user':
                has_user_message = True
                break
    
    if has_user_message:
        logger.info("[PATCH] Result includes user message, returning as-is")
        return result
    
    # No user message in result - try to find the last user message from input
    logger.info("[PATCH] No user message in result, checking input for last user message")
    if input.messages:
        for msg in reversed(input.messages):
            role = getattr(msg, 'role', None)
            content = getattr(msg, 'content', '')
            
            # Handle content that might be a string or an array
            text_content = None
            if isinstance(content, str) and content.strip():
                text_content = content
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get('type') == 'text':
                        text_content = part.get('text', '')
                        break
                    elif isinstance(part, str):
                        text_content = part
                        break
            
            if role == 'user' and text_content:
                logger.info(f"[PATCH] INJECTING last user message: '{text_content[:50]}...'")
                # Add this message to the result
                if result:
                    return result + [msg]
                else:
                    return [msg]
    
    logger.warning("[PATCH] No user message found to inject")
    return result

AgUIADKAgent._get_unseen_messages = _patched_get_unseen_messages
logger.info("[STARTUP] Applied monkey-patch to ADKAgent._get_unseen_messages for message tracking")

# Patch _convert_latest_message to find user message even when batch doesn't contain one
_original_convert_latest_message = AgUIADKAgent._convert_latest_message

async def _patched_convert_latest_message(self, input, messages=None):
    """
    Patched _convert_latest_message that falls back to finding a user message
    from the full input if the provided messages batch doesn't contain one.
    """
    from google.genai import types
    
    logger.info(f"[PATCH] _convert_latest_message called, messages param has {len(messages) if messages else 0} items")
    
    if messages:
        for i, msg in enumerate(messages):
            role = getattr(msg, 'role', 'NO_ROLE')
            content = getattr(msg, 'content', '')
            logger.info(f"[PATCH] _convert_latest_message checking msg {i}: role={role}, content={str(content)[:50] if content else 'EMPTY'}")
    
    # First, try the original method
    result = await _original_convert_latest_message(self, input, messages)
    
    if result is not None:
        logger.info(f"[PATCH] _convert_latest_message returned: {result}")
        return result
    
    # Original returned None - check if we have a system-only batch
    # If so, look for the last user message in the full input
    logger.info("[PATCH] Original returned None, checking full input for user message")
    
    if input.messages:
        for msg in reversed(input.messages):
            role = getattr(msg, 'role', None)
            content = getattr(msg, 'content', '')
            
            if role == 'user' and content:
                text_content = None
                if isinstance(content, str) and content.strip():
                    text_content = content
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get('type') == 'text':
                            text_content = part.get('text', '')
                            break
                        elif isinstance(part, str):
                            text_content = part
                            break
                
                if text_content:
                    logger.info(f"[PATCH] FALLBACK: Found user message in full input: '{text_content[:50]}...'")
                    return types.Content(
                        parts=[types.Part.from_text(text_content)],
                        role='user'
                    )
    
    logger.warning("[PATCH] _convert_latest_message returning None - no user message found anywhere")
    return None

AgUIADKAgent._convert_latest_message = _patched_convert_latest_message
logger.info("[STARTUP] Applied monkey-patch to ADKAgent._convert_latest_message with fallback")

# Patch the run() method to catch errors during iteration
_original_run = AgUIADKAgent.run

async def _patched_run(self, input):
    """
    Patched run() method that catches errors during async iteration.
    """
    from ag_ui.core import RunFinishedEvent, EventType
    
    logger.info(f"[PATCH] run() called with {len(input.messages) if input.messages else 0} messages")
    
    gen = _original_run(self, input)
    
    while True:
        try:
            event = await gen.__anext__()
            yield event
        except StopAsyncIteration:
            break
        except ValueError as e:
            error_msg = str(e)
            if "Both invocation_id and new_message are None" in error_msg:
                logger.warning(f"[PATCH] Caught ADK runner error in run(): {error_msg}")
                logger.warning("[PATCH] Sending graceful completion instead of crashing")
                
                # Send completion to avoid frontend crash
                yield RunFinishedEvent(
                    type=EventType.RUN_FINISHED,
                    thread_id=input.thread_id,
                    run_id=input.run_id
                )
                break
            else:
                raise
        except Exception as e:
            logger.error(f"[PATCH] Unexpected error in run(): {type(e).__name__}: {e}")
            raise

AgUIADKAgent.run = _patched_run
logger.info("[STARTUP] Applied monkey-patch to ADKAgent.run for error handling")

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
