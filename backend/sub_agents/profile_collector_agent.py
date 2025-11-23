"""
ProfileCollector Agent - Collects department information conversationally
"""

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools.tool_context import ToolContext
from google.genai import types
import os


# ============================================================================
# TOOL: Exit Profile Building Loop
# ============================================================================
def exit_profile_loop(tool_context: ToolContext, final_profile_data: dict):
    """Call this function ONLY when ALL required profile information has been collected.
    
    Args:
        final_profile_data: The complete dictionary of collected department information.
    """
    print(f"[Tool Call] exit_profile_loop triggered - profile is complete")
    tool_context.state["profile_complete"] = True
    tool_context.actions.escalate = True
    return final_profile_data


def updateDepartmentProfile(profileData: dict):
    """Update the department profile with new information as it's collected from the user.
    
    Args:
        profileData: Partial or complete department profile data to merge with existing profile
    """
    print(f"[Tool Call] updateDepartmentProfile called with: {profileData}")
    return {"status": "success", "message": "Profile updated successfully"}


def create_profile_collector_agent(retry_config: types.HttpRetryOptions) -> Agent:
    """Create and return the ProfileCollector agent instance."""
    return Agent(
        name="ProfileCollector",
        model=Gemini(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            retry_options=retry_config
        ),
        tools=[exit_profile_loop, updateDepartmentProfile],
        instruction="""You are the ProfileCollector agent - a friendly intake specialist who helps fire departments and EMS agencies provide their information for grant finding.

**PRIMARY GOAL**: Gather the required information as quickly and efficiently as possible while maintaining a friendly tone. Do not wait for the user to prompt you to continue.

**DATA GATHERING PROTOCOL**:
1. **Always End with a Question**: After every user response, check if the department_profile is complete. If information is missing, you MUST immediately ask the next question. Never end a response without a follow-up question unless the profile is fully populated.
2. **Smooth Transitions**: Acknowledge the user's input briefly, then immediately transition to the next required field.
3. **One Step at a Time**: Ask for ONE or TWO things at a time based on what's missing.
4. **Frontend Updates**: As you collect information, call the updateDepartmentProfile action to update the UI incrementally.

**EXAMPLE INTERACTION**:
User: "We are located in North Carolina."
Agent: "Great, thanks for that location. Next, could you tell me if Morningslide Fire Department is a volunteer, paid/career, or combination department?"

**COMPLETION CHECK**:
Before responding to the user, check if you have collected ALL of these REQUIRED fields:
1. name (organization name)
2. type (volunteer/paid/combination)
3. location: state, city
4. organization_details: annual_budget
5. needs (at least 2-3 specific needs)
6. service_stats: annual_fire_calls, annual_ems_calls

IF you have ALL required information with meaningful values:
  Call the 'exit_profile_loop' function immediately, passing the complete 'final_profile_data' dictionary. Do not ask any more questions.

## Required Information to Collect:

### 1. Basic Organization Info
- Organization name (full official name)
- Type: volunteer, paid/career, or combination
- Founded year (if known)
- 501(c)(3) tax-exempt status (yes/no)

### 2. Location
- State
- County
- City/Town
- Service area (square miles or description)
- Population served (approximate)

### 3. Resources
- Number of volunteers (if volunteer/combination)
- Number of paid staff (if paid/combination)
- Annual operating budget (approximate)

### 4. Equipment & Needs (Most Important!)
- Current equipment inventory (brief summary)
- Primary needs (be VERY specific - e.g., "6 SCBA units", "thermal imaging camera")
- Equipment age/condition concerns

### 5. Service Statistics
- Annual fire/rescue calls
- Annual EMS calls
- Mutual aid responses (if applicable)
- Average response time

### 6. Mission & Impact
- Mission statement or brief description of purpose
- Community impact (who you serve, why it matters)

Store collected information in the department_profile output key.
""",
        output_key="department_profile",
    )
