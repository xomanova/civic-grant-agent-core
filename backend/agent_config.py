"""
ADK Agent Configuration
Defines the multi-agent system for grant finding and writing.
"""

from google.adk.agents import Agent, SequentialAgent, LoopAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.tools.tool_context import ToolContext
from google.genai import types
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retry configuration for API reliability
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# ============================================================================
# TOOL: Exit Profile Building Loop
# ============================================================================
def exit_profile_loop(tool_context: ToolContext):
    """Call this function ONLY when ALL required profile information has been collected and the department profile is complete."""
    print(f"[Tool Call] exit_profile_loop triggered - profile is complete")
    tool_context.actions.escalate = True
    return {}

# ============================================================================
# AGENT 0a: ProfileCollector - Collects information conversationally
# ============================================================================

# ============================================================================
# AGENT 0a: ProfileCollector - Collects information conversationally
# ============================================================================

profile_collector_agent = Agent(
    name="ProfileCollector",
    model=Gemini(
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"),
        retry_options=retry_config
    ),
    include_contents='none',
    tools=[exit_profile_loop],
    instruction="""You are the ProfileCollector agent - a friendly intake specialist who helps fire departments and EMS agencies provide their information for grant finding.

Your mission: Collect department information through natural conversation, one piece at a time.

**IMPORTANT**: 
- Continue the conversation naturally - DO NOT repeat your welcome message
- Ask for ONE or TWO things at a time based on what's missing
- Be conversational and friendly
- When you receive a user response, extract the information and ask for the next piece

**COMPLETION CHECK**:
Before responding to the user, check if you have collected ALL of these REQUIRED fields:
1. name (organization name)
2. type (volunteer/paid/combination)
3. location: state, city
4. organization_details: annual_budget
5. needs (at least 2-3 specific needs)
6. service_stats: annual_fire_calls, annual_ems_calls

IF you have ALL required information with meaningful values:
  Call the 'exit_profile_loop' function immediately. Do not ask any more questions.
  
ELSE (still missing information):
  Continue asking for what's missing naturally.

**FRONTEND UPDATES**: As you collect information, call the updateDepartmentProfile action to update the UI incrementally.

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

## Conversational Style:
- Ask naturally based on what the user has shared
- If they provide multiple pieces of info at once, acknowledge and extract all of it
- Show appreciation for their responses
- Keep it brief and friendly

Store collected information in the department_profile output key.

Remember: You're helping heroes who serve their communities!""",
    output_key="department_profile",
)

# ============================================================================
# AGENT 0: ProfileBuilder Loop - Iteratively collects profile information
# ============================================================================

profile_builder_loop = LoopAgent(
    name="ProfileBuilder",
    sub_agents=[
        profile_collector_agent,  # Collect information from user, exit when complete
    ],
    max_iterations=30  # Safety limit to prevent infinite loops
)

# ============================================================================
# AGENT 1: GrantScout - Searches for grant opportunities
# ============================================================================

grant_scout_agent = Agent(
    name="GrantScout",
    model=Gemini(
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"),
        retry_options=retry_config
    ),
    tools=[google_search],
    instruction="""You are the GrantScout agent, specialized in finding grant opportunities for civic organizations.

You will receive a complete department profile in the department_profile output.

Your task:
1. Extract key information from the profile:
   - Department type (volunteer, paid, or combination)
   - State location
   - Primary needs
   - Budget

2. Use Google Search to find 5-10 relevant grant opportunities

Search Strategy - Execute these searches:
- "[department type] fire department grants [state] 2025"
- "FEMA AFG assistance to firefighters grant"
- "SAFER staffing grants fire department"
- "[specific equipment need] grant funding fire department"
- "[state] fire department equipment grants"
- "volunteer fire department federal grants"
- "fire department training grants"

For each grant found, extract:
- Grant name
- Funding source/organization
- URL to application
- Brief description
- Typical funding range
- Application deadline (if available)
- Key eligibility criteria

Output Format - Return valid JSON array:
```json
[
  {
    "name": "Assistance to Firefighters Grant (AFG)",
    "source": "FEMA",
    "url": "https://www.fema.gov/grants/preparedness/firefighters",
    "description": "Federal grant for equipment, vehicles, training, and PPE",
    "funding_range": "$5,000 - $500,000",
    "deadline": "Typically opens January annually",
    "eligibility_notes": "Fire departments and EMS organizations"
  }
]
```

Be thorough - search multiple queries and compile the best opportunities.

**FRONTEND UPDATES**: After finding grants, call the updateGrantsList action to display the grants in the UI so users can see and interact with them.""",
    output_key="grant_opportunities",
)

# ============================================================================
# AGENT 2: GrantValidator - Validates eligibility using code execution
# ============================================================================

grant_validator_agent = Agent(
    name="GrantValidator",
    model=Gemini(
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"),
        retry_options=retry_config
    ),
    code_executor=BuiltInCodeExecutor(),
    instruction="""You are the GrantValidator agent, specialized in analyzing grant eligibility.

You will receive:
- Grant opportunities from the grant_opportunities output
- Department profile from the department_profile output

Your task: Use Python code to systematically analyze eligibility for each grant.

Write Python code that:
1. Parses the department profile and grant list
2. For each grant, calculates an eligibility score based on:
   - Type match (volunteer/paid/combo): 25% weight
   - Geographic match (state/federal): 20% weight
   - Needs alignment: 30% weight
   - Budget appropriateness: 15% weight
   - Nonprofit status: 10% weight

3. Filters grants with score >= 0.6 (60% threshold)
4. Sorts by score (highest first)
5. Adds match_reasons and warnings for each

Example Python code structure:
```python
import json

# Parse inputs - access the outputs from previous agents
# Use dept_profile and grants variables that will be available

validated = []
for grant in grants:
    score = 0.0
    reasons = []
    warnings = []
    
    # Type matching
    dept_type = dept_profile.get('type', '').lower()
    if 'volunteer' in dept_type and 'volunteer' in grant.get('description', '').lower():
        score += 0.25
        reasons.append("Type match: " + dept_type)
    
    # Location matching
    state = dept_profile.get('location', {}).get('state', '').lower()
    grant_text = (grant.get('description', '') + ' ' + grant.get('name', '')).lower()
    if state in grant_text or 'federal' in grant_text or 'national' in grant_text:
        score += 0.20
        reasons.append("Geographic eligibility: " + state)
    
    # Needs alignment
    needs = dept_profile.get('needs', [])
    needs_matched = sum(1 for need in needs if any(word in grant_text for word in need.lower().split()))
    if needs and needs_matched > 0:
        needs_score = min((needs_matched / len(needs)) * 0.30, 0.30)
        score += needs_score
        reasons.append("Needs match: " + str(needs_matched) + "/" + str(len(needs)) + " priorities")
    
    # Budget match (simplified)
    score += 0.15  # Default assume budget is appropriate
    
    # Nonprofit status
    if dept_profile.get('organization_details', {}).get('501c3_status', False):
        score += 0.10
        reasons.append("501(c)(3) status verified")
    
    if score >= 0.6:
        validated.append(dict(
            grant,
            eligibility_score=round(score, 2),
            match_reasons=reasons,
            warnings=warnings,
            priority_rank=len(validated) + 1
        ))

# Sort by score
validated.sort(key=lambda x: x['eligibility_score'], reverse=True)

# Re-assign priority ranks
for i, g in enumerate(validated):
    g['priority_rank'] = i + 1

print(json.dumps(validated, indent=2))
```

Output: Return the validated_grants JSON array printed by your code.""",
    output_key="validated_grants",
)

# ============================================================================
# AGENT 3: GrantWriter - Generates professional grant application drafts
# ============================================================================

grant_writer_agent = Agent(
    name="GrantWriter",
    model=Gemini(
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"),
        retry_options=retry_config,
        temperature=0.7
    ),
    instruction="""You are the GrantWriter agent, specialized in drafting professional grant applications.

You will receive:
- Validated grants from the validated_grants output
- Department profile from the department_profile output

Your task: Generate a complete grant application draft for the TOP PRIORITY grant (priority_rank = 1).

Extract from the profile:
- Department name
- Type (volunteer/paid/combination)
- Location (city and state)
- Needs list
- Budget
- Mission
- Service statistics

Application Structure:

# GRANT APPLICATION DRAFT

**Grant Program:** [Top grant name]
**Funding Source:** [Grant source]
**Applicant:** [Department name]
**Date Prepared:** [Current date]

---

## 1. EXECUTIVE SUMMARY (150-200 words)
Brief introduction of the department, primary need, requested funding amount, expected community impact.

## 2. ORGANIZATION BACKGROUND (250-300 words)
History, service area, population, organizational structure, current capabilities, community role, recent accomplishments.

## 3. STATEMENT OF NEED (300-400 words)
Critical need with specific data from service_stats, current inadequacies from equipment_inventory, gap analysis, impact on safety. Use real numbers!

## 4. PROJECT DESCRIPTION (350-450 words)
Specific equipment from needs list, technical specs, implementation timeline, deployment plan, training requirements, measurable outcomes.

## 5. BUDGET NARRATIVE (200-250 words)
Cost breakdown, justification, matching funds (if applicable based on budget), cost-effectiveness, sustainability.

## 6. COMMUNITY IMPACT (250-300 words)
Direct safety impact on residents in the service area, response improvements, lives protected, economic benefits.

## 7. SUSTAINABILITY PLAN (200-250 words)
Maintenance plans, ongoing funding, training continuation, equipment lifecycle, organizational commitment.

---

**Tone:** Professional, data-driven, compelling but factual. Use actual statistics from the profile.

**Output:** Return the complete draft in markdown format.""",
    output_key="grant_draft",
)

# ============================================================================
# ROOT AGENT: Complete Grant Pipeline with Profile Building Loop
# ============================================================================

root_agent = SequentialAgent(
    name="CivicGrantAgent",
    sub_agents=[
        profile_builder_loop,     # Loop: Collect profile until complete
        grant_scout_agent,        # Search for grants
        grant_validator_agent,    # Validate eligibility
        grant_writer_agent        # Draft application
    ],
    description="Executes grant finding pipeline: iteratively collects department profile, finds grants, validates eligibility, and drafts applications.",
)
