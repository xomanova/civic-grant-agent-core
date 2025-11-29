"""
AG-UI/ADK Integration Fixes

Monkey-patches to fix multiple AG-UI/ADK integration issues:
1. Empty/whitespace text content crash: EventTranslator validation error
2. "Both invocation_id and new_message are None" crash when continuing session

These are bugs in ag_ui_adk that we work around here.
Issue: https://github.com/ag-ui-protocol/ag-ui/issues/735#issuecomment-3583995275
Fix PR: https://github.com/ag-ui-protocol/ag-ui/pull/745

Call apply_patches() to apply all patches before creating ADKAgent instances.
"""

import logging
from typing import AsyncGenerator

from ag_ui_adk.event_translator import EventTranslator
from ag_ui_adk.adk_agent import ADKAgent as AgUIADKAgent
from ag_ui.core import TextMessageContentEvent, BaseEvent
import ag_ui_adk.event_translator

logger = logging.getLogger(__name__)

# Store original implementations
_OriginalTextMessageContentEvent = TextMessageContentEvent
_original_translate = EventTranslator.translate
_original_run_adk_in_background = AgUIADKAgent._run_adk_in_background
_original_get_unseen_messages = AgUIADKAgent._get_unseen_messages
_original_convert_latest_message = AgUIADKAgent._convert_latest_message
_original_run = AgUIADKAgent.run


class SafeTextMessageContentEvent(TextMessageContentEvent):
    """
    Subclass that allows empty delta strings during construction.
    Replaces empty string with a sentinel that we filter out later.
    """
    _is_empty_delta: bool = False
    
    def __init__(self, **data):
        delta = data.get('delta', '')
        if delta == '':
            data['delta'] = '\u200B'  # Zero-width space (invisible)
            super().__init__(**data)
            object.__setattr__(self, '_is_empty_delta', True)
        else:
            super().__init__(**data)
            object.__setattr__(self, '_is_empty_delta', False)


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
                
                if hasattr(event, '_is_empty_delta') and event._is_empty_delta:
                    logger.debug("Filtering out empty delta event")
                    continue
                
                if hasattr(event, 'delta') and event.delta == '\u200B':
                    logger.debug("Filtering out zero-width space delta event")
                    continue
                    
                yield event
            except StopAsyncIteration:
                break
            except Exception as e:
                error_msg = str(e).lower()
                if "string_too_short" in error_msg or "at least 1 character" in error_msg or "empty string" in error_msg or "delta must not" in error_msg:
                    logger.debug("Skipped empty string validation error")
                    continue
                else:
                    logger.error(f"Translate error: {type(e).__name__}: {e}")
                    raise
    except Exception as e:
        error_msg = str(e).lower()
        if "string_too_short" in error_msg or "at least 1 character" in error_msg or "empty string" in error_msg:
            logger.debug("Skipped validation error at translate start")
            return
        raise


async def _patched_get_unseen_messages(self, input):
    """
    Patched _get_unseen_messages that:
    1. Filters out CopilotKit's system messages (we have our own instructions)
    2. Ensures user messages are never filtered out
    """
    logger.info(f"[PATCH] _get_unseen_messages called with {len(input.messages) if input.messages else 0} messages")
    
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
                if result:
                    return result + [msg]
                else:
                    return [msg]
    
    logger.warning("[PATCH] No user message found to inject")
    return result


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
    
    result = await _original_convert_latest_message(self, input, messages)
    
    if result is not None:
        logger.info(f"[PATCH] _convert_latest_message returned: {result}")
        return result
    
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


async def _patched_run_adk_in_background(self, input, adk_agent, user_id, app_name, event_queue, tool_results=None, message_batch=None):
    """
    Patched _run_adk_in_background that catches the 'Both invocation_id and new_message are None'
    ValueError and gracefully handles it instead of crashing.
    """
    from ag_ui.core import RunFinishedEvent, EventType
    
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


def apply_patches():
    """Apply all AG-UI/ADK monkey patches. Call this before creating ADKAgent instances."""
    
    # Patch 1: Fix empty text delta validation errors
    ag_ui_adk.event_translator.TextMessageContentEvent = SafeTextMessageContentEvent
    logger.info("Patched TextMessageContentEvent for empty delta handling")
    
    EventTranslator.translate = _patched_translate
    logger.info("Applied patch to EventTranslator.translate")
    
    # Patch 2: Fix message tracking issues
    AgUIADKAgent._get_unseen_messages = _patched_get_unseen_messages
    logger.info("Applied patch to ADKAgent._get_unseen_messages")
    
    AgUIADKAgent._convert_latest_message = _patched_convert_latest_message
    logger.info("Applied patch to ADKAgent._convert_latest_message")
    
    AgUIADKAgent.run = _patched_run
    logger.info("Applied patch to ADKAgent.run")
    
    AgUIADKAgent._run_adk_in_background = _patched_run_adk_in_background
    logger.info("Applied patch to ADKAgent._run_adk_in_background")
    
    logger.info("All AG-UI/ADK patches applied successfully")
