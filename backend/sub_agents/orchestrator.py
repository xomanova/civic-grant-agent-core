from google.adk.agents import Agent, InvocationContext
from google.adk.events import Event
from typing import AsyncGenerator, List, Optional
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
    scout_agent: Agent
    validator_agent: Agent
    writer_agent: Agent

    @model_validator(mode='after')
    def set_sub_agents(self):
        self.sub_agents = [
            self.profile_agent,
            self.scout_agent,
            self.validator_agent,
            self.writer_agent
        ]
        return self

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
        print(f"[DEBUG] state_authority: {state.get('state_authority')}")
        print(f"[DEBUG] workflow_step from state: {state.get('workflow_step')}")
        print(f"[DEBUG] profile_complete from state: {state.get('profile_complete')}")
        
        # RELAY SYSTEM: Backend should have authority when processing
        # Frontend sets state_authority="backend" when sending a message
        authority = state.get("state_authority", "backend")
        if authority != "backend":
            print(f"[DEBUG] WARNING: state_authority is '{authority}', expected 'backend'. Proceeding anyway.")
        
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
        # STEP 2: GRANT SCOUTING
        # ==================================================================
        elif workflow_step == "grant_scouting":
            print("[DEBUG] Entering Grant Scout Logic.")
            
            print("[DEBUG] Running Scout Agent...")
            async for event in self.scout_agent.run_async(ctx):
                if is_empty_text_event(event):
                    print(f"[DEBUG] Skipping empty text event from Scout")
                    continue
                yield event
            return

        # ==================================================================
        # STEP 3: GRANT VALIDATION
        # ==================================================================
        elif workflow_step == "grant_validation":
            print("[DEBUG] Entering Grant Validator Logic.")
            async for event in self.validator_agent.run_async(ctx):
                if is_empty_text_event(event):
                    continue
                yield event
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
