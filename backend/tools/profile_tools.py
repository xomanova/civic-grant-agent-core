"""
Profile Tools - ADK tool wrappers for managing department profiles
"""

from google.adk.tools.tool_context import ToolContext


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
    print(f"[Backend] updateDepartmentProfile saving data: {profileData}")
    
    # 1. Get current profile from state
    raw_profile = tool_context.state.get("civic_grant_profile", {})
    if not isinstance(raw_profile, dict): 
        raw_profile = {}
    print(f"[Backend] Current civic_grant_profile before merge: {raw_profile}")
    
    # 2. Deep merge the new data into existing profile
    current_profile = deep_merge(raw_profile, profileData)

    # 3. Save to State - use tool_context.state for AG-UI sync
    tool_context.state["civic_grant_profile"] = current_profile
    print(f"[Backend] civic_grant_profile after save: {tool_context.state.get('civic_grant_profile')}")
    
    return "Profile updated successfully."


def exit_profile_loop(tool_context: ToolContext, final_profile_data: dict):
    """
    Mark profile as complete and transition to grant scouting.
    Merges final_profile_data with existing profile (does not overwrite).
    
    Args:
        final_profile_data: Optional final profile data to merge. Can be empty dict {}.
    """
    print(f"[Backend] Exiting profile loop. final_profile_data: {final_profile_data}")
    
    # Get existing profile - DON'T overwrite it!
    existing_profile = tool_context.state.get("civic_grant_profile", {})
    if not isinstance(existing_profile, dict):
        existing_profile = {}
    
    print(f"[Backend] Existing profile before merge: {list(existing_profile.keys())}")
    
    # Only merge if final_profile_data has content (not empty dict)
    if final_profile_data and isinstance(final_profile_data, dict) and len(final_profile_data) > 0:
        existing_profile = deep_merge(existing_profile, final_profile_data)
        print(f"[Backend] Profile after merge: {list(existing_profile.keys())}")
    else:
        print(f"[Backend] No merge needed - using existing profile")
    
    # Save merged profile back
    tool_context.state["civic_grant_profile"] = existing_profile
    tool_context.state["profile_complete"] = True
    tool_context.state["workflow_step"] = "grant_scouting"
    
    print(f"[Backend] Final civic_grant_profile keys: {list(existing_profile.keys())}")
    print(f"[Backend] profile_complete: True, workflow_step: grant_scouting")
    
    return "Profile completed! Tell the user their profile is complete and ask them to say 'find grants' or 'search for grants' to start searching for matching grant opportunities."


def on_before_agent(callback_context):
    """Initialize civic_grant_profile state if it doesn't exist."""
    if "civic_grant_profile" not in callback_context.state:
        callback_context.state["civic_grant_profile"] = {}
        print("[Backend] Initialized civic_grant_profile in state")
    if "profile_complete" not in callback_context.state:
        callback_context.state["profile_complete"] = False
    return None
