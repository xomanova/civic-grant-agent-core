"""Grant Storage Tools - ADK tool wrappers for saving grants to state"""

import json
import logging
from google.adk.tools.tool_context import ToolContext
from tools.grant_filters import filter_grants_by_state

logger = logging.getLogger(__name__)


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
        
        # Get the department's state from the profile
        profile = tool_context.state.get("civic_grant_profile", {})
        dept_state = profile.get("location", {}).get("state", "")
        
        # Filter grants by state - remove grants from other states
        filtered_grants = filter_grants_by_state(grants, dept_state)
        filtered_count = len(grants) - len(filtered_grants)
        
        # Save filtered grants to state
        tool_context.state["validated_grants"] = filtered_grants
        tool_context.state["grants_for_display"] = filtered_grants
        tool_context.state["workflow_step"] = "awaiting_grant_selection"
        
        logger.info(f"Saved {len(filtered_grants)} grants to state (filtered {filtered_count})")
        
        if filtered_count > 0:
            return f"Saved {len(filtered_grants)} grants (filtered out {filtered_count} state-specific grants not available in {dept_state}). The user can now see them in the UI."
        return f"Saved {len(filtered_grants)} grants. The user can now see them in the UI."
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse grants JSON: {e}")
        return f"Error: Invalid JSON format - {e}"
        return f"Error: Invalid JSON format - {e}"
