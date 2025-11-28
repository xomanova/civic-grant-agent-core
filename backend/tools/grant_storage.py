"""
Grant Storage Tools - ADK tool wrappers for saving grants to state
"""

import json
from google.adk.tools.tool_context import ToolContext
from tools.grant_filters import filter_grants_by_state


def save_grants_to_state(tool_context: ToolContext, grants_json: str):
    """
    Save the validated grants to state for the frontend to display.
    Automatically filters out grants from other states.
    
    Args:
        grants_json: JSON string containing an array of grant objects.
                     Each grant should have: name, source, url, description,
                     funding_range, eligibility_score, match_reasons, priority_rank
    """
    try:
        grants = json.loads(grants_json)
        print(f"[Backend] save_grants_to_state called with {len(grants)} grants")
        
        # Get the department's state from the profile
        profile = tool_context.state.get("civic_grant_profile", {})
        dept_state = profile.get("location", {}).get("state", "")
        print(f"[Backend] Department state: {dept_state}")
        
        # Filter grants by state - remove grants from other states
        filtered_grants = filter_grants_by_state(grants, dept_state)
        print(f"[Backend] After state filtering: {len(filtered_grants)} grants (filtered out {len(grants) - len(filtered_grants)})")
        
        # Save filtered grants to state
        tool_context.state["validated_grants"] = filtered_grants
        tool_context.state["grants_for_display"] = filtered_grants
        tool_context.state["workflow_step"] = "awaiting_grant_selection"
        
        print(f"[Backend] Saved {len(filtered_grants)} grants to state")
        
        if len(filtered_grants) < len(grants):
            return f"Saved {len(filtered_grants)} grants (filtered out {len(grants) - len(filtered_grants)} state-specific grants not available in {dept_state}). The user can now see them in the UI."
        return f"Saved {len(filtered_grants)} grants. The user can now see them in the UI."
    except json.JSONDecodeError as e:
        print(f"[Backend] Failed to parse grants JSON: {e}")
        return f"Error: Invalid JSON format - {e}"
