"""
ProfileCollector Agent - Collects department information conversationally
"""

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools.tool_context import ToolContext
from tools.web_search import search_web
from tools.utils import deep_update
from google.genai import types
import os

# ============================================================================
# TOOL: Exit Profile Building Loop
# ============================================================================
def exit_profile_loop(tool_context: ToolContext, final_profile_data: dict):
    """Call this function ONLY when ALL required profile information has been collected."""
    print(f"[Tool Call] exit_profile_loop triggered - profile is complete")
    
    # 1. Set the Flag
    tool_context.session.state["profile_complete"] = True
    
    # 2. Save the Data (Use the SAME key as the update tool)
    # This ensures the dictionary is perfectly up-to-date for the next agent.
    tool_context.session.state["department_profile"] = final_profile_data
    
    # Do NOT escalate here. Let the agent generate a final response.
    return "Profile data saved successfully. You may now inform the user that the profile is complete."


# ============================================================================
# TOOL: Update Department Profile - DISABLED handling via CopilotKit
# ============================================================================
def updateDepartmentProfile(tool_context: ToolContext, profileData: dict):
    """
    Update the department profile with new information using DEEP MERGE.
    """
    print(f"[Tool Call] updateDepartmentProfile called with: {profileData}")
    
    # 1. Retrieve current profile
    raw_profile = tool_context.session.state.get("department_profile", {})
    if not isinstance(raw_profile, dict):
        raw_profile = {}
    
    # 2. DEEP MERGE (The Fix)
    # Instead of raw_profile.update(profileData), we use the helper
    current_profile = deep_update(raw_profile, profileData)
    
    # 3. SAVE
    tool_context.session.state["department_profile"] = current_profile
    
    print(f"[DEBUG] Profile merged and saved. Current keys: {list(current_profile.keys())}")
    
    return {"status": "success", "message": "Profile updated successfully"}


def create_profile_collector_agent(retry_config: types.HttpRetryOptions) -> Agent:
    """Create and return the ProfileCollector agent instance."""
    return Agent(
        name="ProfileCollector",
        model=Gemini(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            retry_options=retry_config
        ),
        tools=[exit_profile_loop, search_web],
        instruction="""You are the ProfileCollector agent - a friendly intake specialist who helps fire departments and EMS agencies provide their information for grant finding.

**PRIMARY GOAL**: Gather the required information quickly.

**CRITICAL RULES (DO NOT BREAK):**
1. **EXTRACT BEFORE ASKING**: Parse user input for ALL data points...
2. **PUBLIC DATA = SEARCH**: Use search for public info...
3. **VERIFICATION BLOCKER**: If verifying, STOP and wait...
4. **TRUTH HIERARCHY**: User input > Search results. Overwrite if corrected.

**DATA GATHERING PROTOCOL**:
1. **Analyze Input**: Process "Yes/No" and new data.
2. **Search**: If City/State is known but County/Pop is missing -> Call `search_web`.
3. **Verify**: If you just found data via search, ASK the user to confirm. -> **STOP HERE.**
4. **Check Completion**: See below.

**DATA STRUCTURE RULES**:
When calling `updateDepartmentProfile`, you MUST strictly adhere to this nested JSON structure:
{
  "name": "String",
  "type": "String",
  "location": { "city": "String", "state": "String", "county": "String", "population": Number },
  "organization_details": { "budget": Number, "founded": String },
  "service_stats": { "calls": Number, "active_members": Number },
  "needs": "String or List"
}

**MISSING INFORMATION STRATEGY**:
- **County/Population**: Search -> Ask "Is that correct?" -> **WAIT.**
- **Budget/Needs**: Ask directly.

**COMPLETION CHECK (THE FINISH LINE)**:
Trigger this check after EVERY user response.
1. **Check Data**: Do you have meaningful values for Name, Type, Location (City, State, County, Pop), Budget, Needs, Stats, and Mission?
2. **Check Verification**: Did the user just confirm your data (e.g., said "Yes")?
3. **ACTION**: If (1) and (2) are true:
   - **Call `exit_profile_loop` IMMEDIATELY.**
   - Do NOT ask "Is there anything else?"
   - Do NOT say "Profile complete."
   - Just call the tool to finish.

## Required Information to Collect:
1. Name
2. Type (Volunteer/Paid)
3. Location (State, City, **County**, **Population**)
4. Budget
5. Needs
6. Service Stats (Calls)
7. Mission
""",
        # Keep this safe key we set earlier
        output_key="profile_agent_response",
    )
