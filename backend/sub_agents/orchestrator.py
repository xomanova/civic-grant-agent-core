from google.adk.agents import Agent, InvocationContext
from google.adk.events import Event
from typing import AsyncGenerator
from pydantic import model_validator

def is_empty_text_event(event) -> bool:
    """Check if this is an empty text event that would crash AG-UI."""
    # Check if it's a tool call/response - those are fine
    if event.get_function_calls() or event.get_function_responses():
        return False
    
    # Check content attribute
    if hasattr(event, 'content'):
        content = event.content
        if content is not None:
            # If content is a string
            if isinstance(content, str):
                return content.strip() == ""
            # If content has parts
            if hasattr(content, 'parts'):
                for part in content.parts:
                    if hasattr(part, 'text') and part.text and part.text.strip():
                        return False
                return True  # All parts empty
    
    # Check text attribute directly  
    if hasattr(event, 'text'):
        text = event.text
        if text is not None and isinstance(text, str):
            return text.strip() == ""
    
    return False  # Not a text event or couldn't determine

class OrchestratorAgent(Agent):
    profile_agent: Agent
    finder_agent: Agent  # Combined scout + validator
    writer_agent: Agent

    # NOTE: We intentionally do NOT set self.sub_agents here.
    # If we did, ADK would auto-route subsequent messages directly to sub-agents,
    # bypassing our orchestrator logic. 
    # The orchestrator, as the root_agent, is the agent with CopilotKit Actions access for updating the UI
    # The orchestrator is also responsible for managing the workflow state transitions.

    def _check_profile_completeness(self, profile: dict) -> bool:
        """
        Check if the profile has enough information to be considered complete.
        This is the SOURCE OF TRUTH - we check actual data, not flags.
        """
        if not profile or not isinstance(profile, dict):
            return False
        
        # Minimum required fields for a complete profile
        has_name = bool(profile.get("name"))
        has_location = bool(profile.get("location", {}).get("state") or profile.get("location", {}).get("city"))
        has_needs = bool(profile.get("needs"))
        
        # Profile is complete if it has name, some location, and needs
        is_complete = has_name and has_location and has_needs
        print(f"[DEBUG] Profile completeness check: name={has_name}, location={has_location}, needs={has_needs} => {is_complete}")
        return is_complete

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        state = ctx.session.state
        
        print(f"\n[DEBUG] --- NEW REQUEST RECEIVED ---")
        print(f"[DEBUG] Session State Keys: {list(state.keys())}")
        print(f"[DEBUG] workflow_step from state: {state.get('workflow_step')}")
        print(f"[DEBUG] profile_complete from state: {state.get('profile_complete')}")
        
        # Get profile from state - this persists across requests via AG-UI session
        civic_grant_profile = state.get("civic_grant_profile", {})
        if isinstance(civic_grant_profile, dict):
            print(f"[DEBUG] civic_grant_profile keys: {list(civic_grant_profile.keys())}")
        
        # CRITICAL: Check profile completeness from ACTUAL DATA, not from flags
        # This makes us resilient to state resets
        profile_is_actually_complete = self._check_profile_completeness(civic_grant_profile)
        
        # Also check for profile set by profile_agent during this session
        department_profile = state.get("department_profile", {})
        if not profile_is_actually_complete and department_profile:
            profile_is_actually_complete = self._check_profile_completeness(department_profile)
        
        # Determine workflow step based on actual profile state
        workflow_step = state.get("workflow_step", "profile_building")
        
        # GUARD: If profile IS complete, we should be in grant_scouting regardless of what state says
        if profile_is_actually_complete and workflow_step == "profile_building":
            print("[DEBUG] GUARD HIT: Profile IS complete based on data. Advancing to grant_scouting.")
            workflow_step = "grant_scouting"
            state["workflow_step"] = "grant_scouting"
            state["profile_complete"] = True
        
        print(f"[DEBUG] Final routing decision: workflow_step={workflow_step}")

        # ==================================================================
        # STEP 1: PROFILE BUILDING
        # ==================================================================
        if workflow_step == "profile_building":
            profile_just_finished = False

            print("[DEBUG] Starting Profile Agent Loop...")
            async for event in self.profile_agent.run_async(ctx):
                # FIX: Filter out empty text events to prevent AG-UI crash
                if is_empty_text_event(event):
                    print(f"[DEBUG] Skipping empty text event to prevent frontend crash")
                    continue
                
                # Log outgoing event types
                evt_type = "ToolCall" if (event.get_function_calls() or event.get_function_responses()) else "Text/Other"
                print(f"[DEBUG] Yielding Event: {evt_type}")
                
                # Check for explicit Exit Tool usage
                if event.get_function_calls():
                    for call in event.get_function_calls():
                        print(f"[DEBUG] Tool Call Detected: {call.name}")
                        if call.name == "exit_profile_loop":
                            print("[DEBUG] !!! EXIT TOOL DETECTED !!!")
                            # Force the state update right here if the tool didn't stick
                            ctx.session.state["profile_complete"] = True
                            profile_just_finished = True

                yield event
                
                # Check state after every yield
                if ctx.session.state.get("profile_complete"):
                    print("[DEBUG] State 'profile_complete' is now TRUE.")
                    profile_just_finished = True

            print(f"[DEBUG] Profile Agent Loop Ended. Just Finished? {profile_just_finished}")
            print(f"[DEBUG] Current profile_complete state: {ctx.session.state.get('profile_complete')}")

            # TRANSITION LOGIC
            if profile_just_finished or ctx.session.state.get("profile_complete"):
                print("[DEBUG] *** TRANSITIONING TO GRANT SCOUT ***")
                state["workflow_step"] = "grant_scouting"
                
                # UPDATE SHARED STATE
                print("[DEBUG] Updating Shared State with Profile Schema...")
                # Ensure the profile is available in the key 'civic_grant_profile'
                if "civic_grant_profile" not in ctx.session.state:
                    ctx.session.state["civic_grant_profile"] = ctx.session.state.get("department_profile", {})
                
                print(f"[DEBUG] About to run scout_agent. Scout agent: {self.scout_agent}")
                print(f"[DEBUG] Scout agent name: {getattr(self.scout_agent, 'name', 'unknown')}")
                
                try:
                    print("[DEBUG] Starting Scout Agent run_async...")
                    async for event in self.scout_agent.run_async(ctx):
                        print(f"[DEBUG] Scout yielded event type: {type(event)}")
                        yield event
                    print("[DEBUG] Scout Agent run_async completed")
                except Exception as e:
                    print(f"[DEBUG] ERROR running scout agent: {type(e).__name__}: {e}")
                    import traceback
                    traceback.print_exc()
                return
            else:
                print("[DEBUG] Returning to wait for user input (Profile incomplete).")
                return

        # ==================================================================
        # STEP 2: GRANT FINDING (combined scout + validation)
        # ==================================================================
        elif workflow_step == "grant_scouting":
            print("[DEBUG] Entering Grant Finder Logic.")
            
            # Run finder agent - searches and validates grants
            print("[DEBUG] Running Finder Agent...")
            async for event in self.finder_agent.run_async(ctx):
                # Allow all events through (text + tool calls)
                if is_empty_text_event(event):
                    print(f"[DEBUG] Skipping empty text event from Finder")
                    continue
                yield event
            
            # Finder stores results in validated_grants via output_key (as string)
            # Parse JSON and copy to grants_for_display for frontend sync
            validated_grants_raw = ctx.session.state.get("validated_grants", "")
            print(f"[DEBUG] Finder output raw length: {len(validated_grants_raw) if validated_grants_raw else 0}")
            
            validated_grants = []
            if validated_grants_raw:
                import json
                import re
                try:
                    # Try to extract JSON array from the output
                    # The output might have text before/after the JSON
                    json_match = re.search(r'\[.*\]', validated_grants_raw, re.DOTALL)
                    if json_match:
                        validated_grants = json.loads(json_match.group())
                        print(f"[DEBUG] Parsed {len(validated_grants)} grants from JSON")
                    else:
                        print(f"[DEBUG] No JSON array found in output")
                except json.JSONDecodeError as e:
                    print(f"[DEBUG] Failed to parse grants JSON: {e}")
            
            if validated_grants:
                ctx.session.state["grants_for_display"] = validated_grants
                print(f"[DEBUG] Stored {len(validated_grants)} grants in grants_for_display")
            
            # Transition to awaiting user selection
            ctx.session.state["workflow_step"] = "awaiting_grant_selection"
            print("[DEBUG] Finder finished. Workflow set to awaiting_grant_selection")
            
            return

        # ==================================================================
        # STEP 3.5: AWAITING GRANT SELECTION (idle state)
        # ==================================================================
        elif workflow_step == "awaiting_grant_selection":
            print("[DEBUG] In awaiting_grant_selection - checking for selected grant...")
            
            # Check if user has selected a grant
            selected_grant = ctx.session.state.get("selected_grant_for_writing")
            
            if selected_grant:
                print(f"[DEBUG] User selected grant: {selected_grant.get('name', 'Unknown')}")
                ctx.session.state["workflow_step"] = "grant_writing"
                
                # Immediately transition to grant writing
                print("[DEBUG] Starting Grant Writer Agent...")
                async for event in self.writer_agent.run_async(ctx):
                    if is_empty_text_event(event):
                        continue
                    yield event
            else:
                # No grant selected yet - user needs to click one in the UI
                print("[DEBUG] No grant selected yet. Waiting for user selection via UI.")
            
            return

        # ==================================================================
        # STEP 4: GRANT WRITING
        # ==================================================================
        elif workflow_step == "grant_writing":
            print("[DEBUG] Entering Grant Writer Logic.")
            async for event in self.writer_agent.run_async(ctx):
                if is_empty_text_event(event):
                    continue
                yield event
            return

        else:
            print(f"[DEBUG] Unknown workflow_step: {workflow_step}")
            return
