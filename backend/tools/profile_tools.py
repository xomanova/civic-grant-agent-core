"""Profile Tools - ADK tool wrappers for managing department profiles"""

import logging
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)


def deep_merge(base: dict, updates: dict) -> dict:
    """Recursively merge updates into base dict."""
    result = base.copy()
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def updateDepartmentProfile(tool_context: ToolContext, profileData: dict):
    """
    Update the department profile with new information.
    """
    # 1. Get current profile from state
    raw_profile = tool_context.state.get("civic_grant_profile", {})
    if not isinstance(raw_profile, dict): 
        raw_profile = {}
    
    # 2. Deep merge the new data into existing profile
    current_profile = deep_merge(raw_profile, profileData)

    # 3. Save to State - use tool_context.state for AG-UI sync
    tool_context.state["civic_grant_profile"] = current_profile
    
    return "Profile updated successfully."


def exit_profile_loop(tool_context: ToolContext, final_profile_data: dict):
    """
    Mark profile as complete and transition to grant scouting.
    Merges final_profile_data with existing profile (does not overwrite).
    
    Args:
        final_profile_data: Optional final profile data to merge. Can be empty dict {}.
    """
    # Get existing profile - DON'T overwrite it!
    existing_profile = tool_context.state.get("civic_grant_profile", {})
    if not isinstance(existing_profile, dict):
        existing_profile = {}
    
    # Only merge if final_profile_data has content (not empty dict)
    if final_profile_data and isinstance(final_profile_data, dict) and len(final_profile_data) > 0:
        existing_profile = deep_merge(existing_profile, final_profile_data)
    
    # Save merged profile back
    tool_context.state["civic_grant_profile"] = existing_profile
    tool_context.state["profile_complete"] = True
    tool_context.state["workflow_step"] = "grant_scouting"
    
    return "Profile completed! Tell the user their profile is complete and ask them to say 'find grants' or 'search for grants' to start searching for matching grant opportunities."


def on_before_agent(callback_context):
    """Initialize civic_grant_profile state if it doesn't exist."""
    if "civic_grant_profile" not in callback_context.state:
        callback_context.state["civic_grant_profile"] = {}
    if "profile_complete" not in callback_context.state:
        callback_context.state["profile_complete"] = False
    return None
