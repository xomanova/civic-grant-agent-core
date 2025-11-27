"""
ProfileCollector Agent
"""
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.google_llm import Gemini
from google.adk.tools.tool_context import ToolContext
from tools.web_search import search_web
from google.genai import types
import os

# ============================================================================
# TOOL: Update Department Profile (Backend State Writer)
# ============================================================================
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
    def deep_merge(base: dict, updates: dict) -> dict:
        """Recursively merge updates into base dict."""
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    current_profile = deep_merge(raw_profile, profileData)

    # 3. Save to State - use tool_context.state for AG-UI sync
    tool_context.state["civic_grant_profile"] = current_profile
    print(f"[Backend] civic_grant_profile after save: {tool_context.state.get('civic_grant_profile')}")
    
    return "Profile updated successfully."

# Exit Tool
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
        # Deep merge final data into existing
        def deep_merge(base: dict, updates: dict) -> dict:
            result = base.copy()
            for key, value in updates.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
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

# Callback to initialize state before agent runs
def on_before_agent(callback_context):
    """Initialize civic_grant_profile state if it doesn't exist."""
    if "civic_grant_profile" not in callback_context.state:
        callback_context.state["civic_grant_profile"] = {}
        print("[Backend] Initialized civic_grant_profile in state")
    if "profile_complete" not in callback_context.state:
        callback_context.state["profile_complete"] = False
    return None

def create_profile_collector_agent(retry_config: types.HttpRetryOptions) -> LlmAgent:
    return LlmAgent(
        name="ProfileCollector",
        model=Gemini(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            retry_options=retry_config
        ),
        tools=[exit_profile_loop, search_web, updateDepartmentProfile],
        before_agent_callback=on_before_agent,
        
        instruction="""You are the ProfileCollector agent - a friendly intake specialist who helps fire departments and EMS agencies provide their information for grant finding.

**PRIMARY GOAL**: Gather the required information quickly.

## CRITICAL: YOU MUST CALL TOOLS TO SAVE DATA

**NEVER just display JSON in your response. You MUST call `updateDepartmentProfile` tool to save ANY data you collect.**

After extracting information from the user's message:
1. IMMEDIATELY call `updateDepartmentProfile` with the extracted data
2. THEN respond to the user

Example: If user says "We're Halls Fire Department in Clinton, NC with a $185,000 budget"
- FIRST: Call updateDepartmentProfile({"name": "Halls Fire Department", "location": {"city": "Clinton", "state": "NC"}, "organization_details": {"budget": 185000}})
- THEN: Respond to ask for missing info

**CRITICAL RULES (DO NOT BREAK):**
1. **SAVE BEFORE RESPONDING**: Always call `updateDepartmentProfile` BEFORE your text response
2. **EXTRACT BEFORE ASKING**: Parse user input for ALL data points
3. **PUBLIC DATA = SEARCH**: Use search for public info like county/population
4. **VERIFICATION BLOCKER**: If verifying search results, STOP and wait for user confirmation

**DATA STRUCTURE for updateDepartmentProfile**:
{
  "name": "String",
  "type": "String", 
  "location": { "city": "String", "state": "String", "county": "String", "population": Number },
  "organization_details": { "budget": Number, "founded": String },
  "service_stats": { "calls": Number, "active_members": Number },
  "needs": "String",
  "mission": "String"
}

**WORKFLOW**:
1. User sends message with info
2. Extract ALL data points from the message
3. **CALL `updateDepartmentProfile` with extracted data** (DO NOT SKIP THIS)
4. Check what's missing
5. If County/Pop missing: call `search_web`, then ask user to confirm
6. Respond to user about what's still needed

**COMPLETION CHECK**:
When you have: Name, Type, Location (City, State, County, Pop), Budget, Needs, Stats, and Mission:
1. Call `updateDepartmentProfile` with the complete profile one final time
2. Then call `exit_profile_loop` with the final profile data
3. After calling exit_profile_loop, tell the user: "Your profile is complete! Say **'find grants'** to start searching for matching grant opportunities."
4. Do NOT ask "Is there anything else?" - guide them to the next step

## Required Information to Collect:
1. Name
2. Type (Volunteer/Paid)
3. Location (State, City, County, Population)
4. Budget
5. Needs
6. Service Stats (Calls, Active Members)
7. Mission

""",
        output_key="profile_agent_response",
    )