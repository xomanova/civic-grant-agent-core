"""
Draft Storage Tools - ADK tool wrappers for saving grant drafts to state
"""

from google.adk.tools.tool_context import ToolContext


def save_grant_draft(tool_context: ToolContext, grant_name: str, draft_content: str):
    """
    Save the completed grant application draft to state for display in the UI.
    
    Args:
        grant_name: The name of the grant this application is for
        draft_content: The full markdown content of the grant application draft
    """
    print(f"[Backend] save_grant_draft called for grant: {grant_name}, content length: {len(draft_content)}")
    
    # Save the draft to state - this will sync to frontend
    tool_context.state["grant_draft"] = draft_content
    tool_context.state["grant_draft_for_display"] = draft_content
    tool_context.state["workflow_step"] = "draft_ready"
    tool_context.state["grant_name_for_draft"] = grant_name
    
    print(f"[Backend] Grant draft saved to state")
    return f"✅ Draft saved! 👈 The grant application draft for {grant_name} is now visible on the left panel."
