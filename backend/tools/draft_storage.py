"""Draft Storage Tools - ADK tool wrappers for saving grant drafts to state"""

import logging
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)


def save_grant_draft(tool_context: ToolContext, grant_name: str, draft_content: str):
    """
    Save the completed grant application draft to state for display in the UI.
    
    Args:
        grant_name: The name of the grant this application is for
        draft_content: The full markdown content of the grant application draft
    """
    # Fix escaped newlines - LLM sometimes passes literal \n instead of actual newlines
    cleaned_content = draft_content.replace('\\n', '\n')
    
    # Also fix double-escaped newlines
    cleaned_content = cleaned_content.replace('\\\\n', '\n')
    
    # Save the draft to state - this will sync to frontend
    tool_context.state["grant_draft"] = cleaned_content
    tool_context.state["grant_draft_for_display"] = cleaned_content
    tool_context.state["workflow_step"] = "draft_ready"
    tool_context.state["grant_name_for_draft"] = grant_name
    
    logger.info(f"Grant draft saved for: {grant_name}")
    return f"DONE. Draft for {grant_name} saved successfully. Do not call this tool again. Say: 'Your draft is ready! 👈 Check the left panel to review it.'"
