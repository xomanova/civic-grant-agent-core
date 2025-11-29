# AHA Moments & Creative Solutions

This document captures the lessons learned, unexpected behaviors discovered, and creative workarounds developed while building the Civic Grant Agent using Google ADK, CopilotKit, and the AG-UI protocol.

---

## Table of Contents
1. [Google ADK Behaviors](#google-adk-behaviors)
2. [AG-UI Protocol Discoveries](#ag-ui-protocol-discoveries)
3. [CopilotKit Integration Challenges](#copilotkit-integration-challenges)
4. [State Management Saga](#state-management-saga)
5. [Orchestrator Control Flow](#orchestrator-control-flow)
6. [Tool Function Gotchas](#tool-function-gotchas)

---

## Google ADK Behaviors

### 🔍 Sub-Agent Auto-Routing Takeover

**Problem**: When you register agents as `self.sub_agents` in an orchestrator, Google ADK automatically routes subsequent messages directly to the last active sub-agent, **completely bypassing** your orchestrator logic.

**Discovery**: After the first message, our `_run_async_impl` in the orchestrator was never being called again. The session "stuck" to `ProfileCollector` and continued there for all subsequent messages.

**Solution**: Don't register sub-agents in `self.sub_agents`. Instead, keep them as instance attributes and manually call `agent.run_async(ctx)` when needed. This forces every message through the orchestrator's routing logic.

```python
# ❌ DON'T DO THIS - ADK will auto-route to sub-agents
@model_validator(mode='after')
def set_sub_agents(self):
    self.sub_agents = [self.profile_agent, self.scout_agent, ...]
    return self

# ✅ DO THIS - Orchestrator stays in control
# Just keep agents as attributes, don't set self.sub_agents
# Then manually route: async for event in self.profile_agent.run_async(ctx): yield event
```

---

### 🔍 State Resets After Streaming

**Problem**: Backend logs showed `"Streaming completed, state reset"` after every agent response. State set during tool calls would disappear by the next request.

**Discovery**: The AG-UI ADK middleware's session management doesn't persist state across requests by default. The `ctx.session.state` is ephemeral within a single streaming response.

**Impact**: `profile_complete = True` set in one request would be `False` in the next request, causing the orchestrator to always route back to profile building.

---

### 🔍 Tool Parameter Default Values Break Gemini API

**Problem**: Adding `= None` as a default value to a tool function parameter caused a 400 error:
```
Invalid JSON payload received. Unknown name "additional_properties"
```

**Root Cause**: When Google ADK converts Python function signatures to Gemini tool schemas, optional parameters with default values create invalid schema structures.

**Solution**: Keep all tool parameters required, but handle empty/null values gracefully in the function body.

```python
# ❌ Breaks Gemini API
def exit_profile_loop(tool_context: ToolContext, final_profile_data: dict = None):

# ✅ Works - handle empty dict in function body
def exit_profile_loop(tool_context: ToolContext, final_profile_data: dict):
    if not final_profile_data:
        final_profile_data = {}  # Handle empty case
```

---

## AG-UI Protocol Discoveries

### 🔍 State Hydration from Frontend

**AHA Moment**: The AG-UI ADK middleware already hydrates session state from the frontend's `input.state`!

Found in `ag_ui_adk/adk_agent.py` around line 1046:
```python
await self._session_manager.update_session_state(input.thread_id, app_name, user_id, input.state)
```

This means `useCoAgent`'s state IS available in `ctx.session.state` on the backend - we just weren't using it correctly.

---

### 🔍 Empty Text Events Crash the Frontend

**Problem**: The frontend would crash with validation errors when receiving empty text content from the backend.

**Root Cause**: AG-UI's `TextMessageContentEvent` validates that `delta` is non-empty. When ADK yielded events with empty string content, the validation failed.

**Solution**: Monkey-patch `TextMessageContentEvent` to handle empty deltas, and filter out empty text events in the orchestrator before yielding.

```python
def is_empty_text_event(event) -> bool:
    """Check if this is an empty text event that would crash AG-UI."""
    if hasattr(event, 'content'):
        content = event.content
        if hasattr(content, 'parts'):
            for part in content.parts:
                if hasattr(part, 'text') and part.text and part.text.strip():
                    return False
            return True  # All parts empty
    return False
```

---

### 🔍 Duplicate Final Response Events

**Discovery**: AG-UI ADK sends duplicate "final response" events at the end of streaming, causing double-rendering on the frontend.

**Log evidence**: `"Skipping final response event (duplicate content detected from finished stream)"`

**Solution**: The middleware already handles this, but be aware when debugging - you'll see these skip messages in logs.

---

## CopilotKit Integration Challenges

### 🔍 useCoAgent vs useCopilotReadable

**Key Insight**: These serve different purposes:

| Hook | Purpose | Where Data Goes |
|------|---------|-----------------|
| `useCopilotReadable` | Inject data into LLM context/prompt | Agent's instruction context |
| `useCoAgent` | Bidirectional state sync | `ctx.session.state` on backend |

For workflow state (`workflow_step`, `profile_complete`), use `useCoAgent` so the backend can read AND write it.

For read-only context (like current profile for display), `useCopilotReadable` works.

---

### 🔍 Frontend State Push Creates Infinite Loops

**Problem**: When frontend pushed state to backend, and backend returned updated state, the frontend would push again, creating an infinite render loop.

**Console evidence**: Endless "MainContent Rendering" logs

**Root Cause**: React useEffect with `departmentProfile` in dependencies would trigger on every backend sync, which would push state, which would trigger another sync...

**Solution**: Only push state on specific triggers (new message sent), not on every state change. Use refs to track message counts and prevent re-pushing.

---

### 🔍 State Sync Direction Matters

**AHA Moment**: The profile data flow should be:
- **Backend → Frontend**: Profile data, workflow_step advancement, profile_complete flag
- **Frontend → Backend**: Only on NEW message (hydrate current state for routing)

Trying to make it bidirectional at all times caused race conditions where stale frontend state would overwrite fresh backend state.

---

## State Management Saga

### 🔍 The Empty Profile Paradox

**Problem**: `civic_grant_profile = {}` but `profile_complete = true` - how?

**Root Cause**: The `exit_profile_loop` tool was **overwriting** the entire profile with whatever the LLM passed (often `{}`), rather than merging.

**Solution**: Make `exit_profile_loop` merge with existing profile instead of replacing:

```python
def exit_profile_loop(tool_context: ToolContext, final_profile_data: dict):
    existing_profile = tool_context.state.get("civic_grant_profile", {})
    if final_profile_data and len(final_profile_data) > 0:
        existing_profile = deep_merge(existing_profile, final_profile_data)
    tool_context.state["civic_grant_profile"] = existing_profile  # Preserve existing!
```

---

### 🔍 Workflow Step Regression Prevention

**Problem**: Frontend would push `workflow_step: "profile_building"` even after backend advanced to `"grant_scouting"`, causing regression.

**Solution**: Frontend only advances workflow, never regresses (except explicit reset):

```javascript
const stepOrder = ["profile_building", "grant_scouting", "grant_validation", "grant_writing"];
setWorkflowStep(prev => {
    const prevIndex = stepOrder.indexOf(prev);
    const newIndex = stepOrder.indexOf(agentState.workflow_step);
    // Only update if advancing OR if it's a reset to profile_building
    if (newIndex > prevIndex || agentState.workflow_step === "profile_building") {
        return agentState.workflow_step;
    }
    return prev;
});
```

---

### 🔍 Data-Driven Routing Guard

**Problem**: Flags like `profile_complete` could get out of sync or reset. How to ensure correct routing?

**Solution**: Check the actual profile DATA, not just the flag:

```python
def _check_profile_completeness(self, profile: dict) -> bool:
    """SOURCE OF TRUTH - check actual data, not flags."""
    has_name = bool(profile.get("name"))
    has_location = bool(profile.get("location", {}).get("state"))
    has_needs = bool(profile.get("needs"))
    return has_name and has_location and has_needs

# In routing logic:
if profile_is_actually_complete and workflow_step == "profile_building":
    workflow_step = "grant_scouting"  # Force correct routing
```

---

## Orchestrator Control Flow

### 🔍 Single-Run vs Multi-Turn Confusion

**Problem**: Assumed `_run_async_impl` would be called for each user message. Actually, once a sub-agent takes over, it handles subsequent messages directly.

**Mental Model Correction**:
- With `sub_agents` registered: Orchestrator runs ONCE, then ADK auto-routes
- Without `sub_agents`: Orchestrator runs for EVERY message

---

### 🔍 Transition Within Same Request

**Discovery**: When profile completes, we can immediately transition to grant scouting within the same request by calling `scout_agent.run_async(ctx)` after the profile agent finishes.

```python
if profile_just_finished:
    state["workflow_step"] = "grant_scouting"
    async for event in self.scout_agent.run_async(ctx):
        yield event
    return
```

This provides seamless UX - user says "that's correct", profile saves, and grant search begins in one response.

---

## Tool Function Gotchas

### 🔍 tool_context.state vs ctx.session.state

**Discovery**: In tool functions, use `tool_context.state`. In agent `_run_async_impl`, use `ctx.session.state`. They reference the same underlying state, but the access pattern differs.

---

### 🔍 Tools Must Return Strings

**Problem**: Returning complex objects from tools caused serialization issues.

**Solution**: Always return a string message. If you need to pass data, put it in `tool_context.state`.

```python
def my_tool(tool_context: ToolContext, data: dict):
    tool_context.state["my_data"] = data  # Store complex data in state
    return "Data saved successfully."  # Return simple string
```

---

## Summary of Key Principles

1. **Don't register sub_agents** if you want orchestrator control for every message
2. **State is ephemeral** between requests unless explicitly synced via AG-UI
3. **Profile data flows from backend** → Workflow progression flows from backend → Frontend only pushes on new messages
4. **Check actual data** not flags for critical routing decisions
5. **Merge, don't overwrite** when updating accumulated state
6. **Filter empty events** before yielding to prevent frontend crashes
7. **No default parameter values** in tool functions for Gemini API

---

## Tool Type Annotations & Gemini API

### 🔍 List Parameters Without Item Types Break Gemini API

**Problem**: Tool function with `grants: list` parameter caused a 400 Bad Request error:
```
GenerateContentRequest.tools[0].function_declarations[1].parameters.properties[grants].items: missing field
```

**Root Cause**: When ADK converts Python function signatures to Gemini tool schemas, a bare `list` type doesn't specify what type of items are in the list. The Gemini API requires the `items` field to be present in array schemas.

**Discovery**: The Gemini API schema validation is strict. `list[str]` or `list[dict]` might work, but complex nested types (like a list of grant objects with specific fields) create unwieldy schemas.

**Solution**: Accept a JSON string instead of a list, then parse it server-side:

```python
# ❌ Breaks Gemini API - "items: missing field"
def save_grants_to_state(tool_context: ToolContext, grants: list):
    tool_context.state["grants"] = grants

# ✅ Works - accept JSON string, parse in function
def save_grants_to_state(tool_context: ToolContext, grants_json: str):
    """
    Args:
        grants_json: JSON string containing an array of grant objects
    """
    import json
    grants = json.loads(grants_json)
    tool_context.state["grants"] = grants
```

**Instruction Update**: Tell the agent to pass a JSON string:
```
Call save_grants_to_state(grants_json='[{"name": "Grant Name", ...}]')
```

---

### 🔍 output_key Captures Last Text, Gets Overwritten

**Problem**: Using `output_key="validated_grants"` to capture agent output seemed to work, but the value would get overwritten by subsequent messages.

**Root Cause**: `output_key` captures the **last text output** from the agent's response. If the user sends a follow-up message and the agent responds with "Sorry, I can't help with that", that text overwrites the previously stored grants.

**Example of failure**:
```python
# After finder runs, validated_grants = '[{"name": "AFG Grant"...}]' ✓
# User sends: "tell me more about the first one"
# Agent responds: "Sorry, I can't create an application draft without..."
# Now validated_grants = "Sorry, I can't create an application draft..." ✗
```

**Solution**: Use tool-based state saving instead of `output_key` for data that needs to persist:

```python
# ❌ Gets overwritten by subsequent agent text output
Agent(
    name="GrantFinder",
    output_key="validated_grants",  # Fragile!
    ...
)

# ✅ Explicit tool saves to state - won't be overwritten
def save_grants_to_state(tool_context: ToolContext, grants_json: str):
    grants = json.loads(grants_json)
    tool_context.state["validated_grants"] = grants
    tool_context.state["grants_for_display"] = grants  # For frontend sync
    return f"Saved {len(grants)} grants"

Agent(
    name="GrantFinder", 
    tools=[search_web, save_grants_to_state],  # Tool saves explicitly
    instruction="...You MUST call save_grants_to_state before your final message..."
)
```

---

### 🔍 CopilotKit Actions Only Available to Root Agent

**Problem**: Tried to have sub-agents (GrantFinder) call frontend actions to display grants. Actions were never triggered.

**Discovery**: CopilotKit actions registered via `useCopilotAction` are only available to the **root agent** (orchestrator). Sub-agents cannot see or call these actions.

**Why**: The action definitions are passed in the initial request context. When the orchestrator delegates to a sub-agent, that sub-agent has its own tool set defined in its constructor, not the frontend actions.

**Solution**: Sub-agents must use `tool_context.state` to write data that syncs to frontend via `useCoAgent`. The frontend then reacts to state changes.

```javascript
// Frontend: Sync grants from backend state
const { state: agentState } = useCoAgent({ name: "Orchestrator" });

useEffect(() => {
    if (agentState.grants_for_display) {
        setGrants(agentState.grants_for_display);
    }
}, [agentState.grants_for_display]);
```

---

### 🔍 LoopAgent Doesn't Accept `agent` Parameter

**Problem**: Tried to use `LoopAgent` to wrap a sub-agent for iterative refinement:
```python
LoopAgent(
    name="GrantFinder",
    agent=my_finder_agent,  # ❌ Error!
    max_iterations=5
)
```

**Error**: Pydantic validation error - `agent` is not a valid parameter.

**Discovery**: `LoopAgent` in Google ADK works differently than expected. It doesn't wrap another agent; it's designed for specific iteration patterns with its own configuration.

**Solution**: For simple "run once and capture output" cases, just use a regular `Agent`. If you need iteration, implement the loop in the orchestrator.

---

*Last updated: November 27, 2025*

---

## State-Based Grant Filtering

### 🔍 Grants from Other State Organizations Match Incorrectly

**Problem**: When searching for grants, the system was returning grants from state-specific organizations (e.g., "Ohio State Fire Marshal") as high matches for departments in other states (e.g., North Carolina).

**Root Cause**: The grant finder agent relied on LLM scoring which didn't have awareness of the department's state when evaluating eligibility. State names appearing in grant organization names weren't being properly cross-referenced against the department's location.

**Solution**: Implemented server-side state filtering in `save_grants_to_state`:

1. Added a comprehensive list of US state names
2. When grants are saved, extract any state names from the grant name/source
3. If a grant is state-specific (has state names in its name/source):
   - Include it only if the department is in that state
   - Filter it out if the department is in a different state
4. Federal grants (FEMA, DHS, etc.) are always included regardless of state

```python
def filter_grants_by_state(grants: list, department_state: str) -> list:
    """Filter out grants specific to other states."""
    for grant in grants:
        # Federal grants always pass
        if is_federal_grant(grant_name, grant_source, grant_desc):
            filtered_grants.append(grant)
            continue
        
        # Check if grant is state-specific
        grant_states = get_grant_states(grant_name, grant_source)
        
        if grant_states:
            # Only include if department is in that state
            if dept_state_lower in grant_states:
                filtered_grants.append(grant)
            # Otherwise, filter it out
```

**Key Insight**: Client-side filtering wouldn't work here because the grants are saved to state before reaching the frontend. Server-side filtering ensures only relevant grants are ever shown.

---

## Grant Writer Output Control

### 🔍 Grant Writer Outputs Full Markdown to Chat

**Problem**: The grant writer agent was outputting the entire grant application draft as markdown text in the chat window, making for a poor UX when the draft should be displayed in a dedicated UI panel.

**Root Cause**: The agent was using `output_key="grant_draft"` which captures the last text output. The instructions told it to "return the complete draft in markdown format", so it did exactly that - to the chat.

**Solution**: Changed from text output to tool-based state saving:

1. Added a `save_grant_draft` tool that saves the draft to state
2. Updated instructions to tell the agent to:
   - Generate the draft internally (not output to chat)
   - Call `save_grant_draft(draft_markdown='...', grant_name='...')`
   - Only output a short acknowledgement to chat

```python
def save_grant_draft(tool_context: ToolContext, draft_markdown: str, grant_name: str):
    """Save the draft to state for UI display."""
    tool_context.state["grant_draft"] = draft_markdown
    tool_context.state["grant_draft_for_display"] = draft_markdown
    return f"Draft saved. Now output ONLY: '👈 The grant application draft for {grant_name} is ready for review.'"
```

**Key Pattern**: When you want an agent to produce output for a UI panel instead of the chat:
1. Create a tool that saves the output to state
2. Instruct the agent to call that tool
3. Have the frontend sync that state key to the appropriate UI component
4. Tell the agent to output only a short confirmation message

**Why Not Just Parse Chat Output?**: Parsing markdown from chat output is fragile. The agent might add commentary, the format might vary, or the AG-UI protocol might chunk the text differently. Using a tool guarantees the exact content you want ends up in state.
