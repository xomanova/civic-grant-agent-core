import logging
from google.adk.agents import Agent, InvocationContext
from google.adk.events import Event
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

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
        logger.debug(f"Profile check: name={has_name}, loc={has_location}, needs={has_needs} => {is_complete}")
        return is_complete

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        state = ctx.session.state
        
        workflow_step = state.get("workflow_step", "profile_building")
        logger.debug(f"Request received - workflow: {workflow_step}")
        
        # Get profile from state - this persists across requests via AG-UI session
        civic_grant_profile = state.get("civic_grant_profile", {})
        
        # CRITICAL: Check profile completeness from ACTUAL DATA, not from flags
        # This makes us resilient to state resets
        profile_is_actually_complete = self._check_profile_completeness(civic_grant_profile)
        
        # Also check for profile set by profile_agent during this session
        department_profile = state.get("department_profile", {})
        if not profile_is_actually_complete and department_profile:
            profile_is_actually_complete = self._check_profile_completeness(department_profile)
        
        # Determine workflow step based on actual profile state
        # (workflow_step already retrieved above)
        
        # GUARD: If profile IS complete, we should be in grant_scouting regardless of what state says
        if profile_is_actually_complete and workflow_step == "profile_building":
            logger.debug("Profile complete - advancing to grant_scouting")
            workflow_step = "grant_scouting"
            state["workflow_step"] = "grant_scouting"
            state["profile_complete"] = True

        # ==================================================================
        # STEP 1: PROFILE BUILDING
        # ==================================================================
        if workflow_step == "profile_building":
            profile_just_finished = False
            async for event in self.profile_agent.run_async(ctx):
                # FIX: Filter out empty text events to prevent AG-UI crash
                if is_empty_text_event(event):
                    continue
                
                # Check for explicit Exit Tool usage
                if event.get_function_calls():
                    for call in event.get_function_calls():
                        if call.name == "exit_profile_loop":
                            # Force the state update right here if the tool didn't stick
                            ctx.session.state["profile_complete"] = True
                            profile_just_finished = True

                yield event
                
                # Check state after every yield
                if ctx.session.state.get("profile_complete"):
                    profile_just_finished = True

            # TRANSITION LOGIC - Set state but DON'T auto-run finder
            # Let the user send a new message like "find grants" to trigger finder
            if profile_just_finished or ctx.session.state.get("profile_complete"):
                state["workflow_step"] = "grant_scouting"
                
                # Ensure the profile is available in the key 'civic_grant_profile'
                if "civic_grant_profile" not in ctx.session.state:
                    ctx.session.state["civic_grant_profile"] = ctx.session.state.get("department_profile", {})
                
                # DON'T auto-run finder here - the exit_profile_loop tool tells user to say "find grants"
                return
            else:
                return

        # ==================================================================
        # STEP 2: GRANT FINDING (combined scout + validation)
        # ==================================================================
        elif workflow_step == "grant_scouting":
            # Run finder agent - searches and validates grants
            async for event in self.finder_agent.run_async(ctx):
                # Allow all events through (text + tool calls)
                if is_empty_text_event(event):
                    continue
                yield event
            
            # Ensure workflow advances (tool should have set this, but double-check)
            if ctx.session.state.get("workflow_step") != "awaiting_grant_selection":
                ctx.session.state["workflow_step"] = "awaiting_grant_selection"
            
            return

        # ==================================================================
        # STEP 3.5: AWAITING GRANT SELECTION (idle state)
        # ==================================================================
        elif workflow_step == "awaiting_grant_selection":
            # Check if user has selected a grant
            selected_grant = ctx.session.state.get("selected_grant_for_writing")
            
            if selected_grant:
                ctx.session.state["workflow_step"] = "grant_writing"
                
                # Immediately transition to grant writing
                async for event in self.writer_agent.run_async(ctx):
                    if is_empty_text_event(event):
                        continue
                    yield event
            
            return

        # ==================================================================
        # STEP 4: GRANT WRITING
        # ==================================================================
        elif workflow_step == "grant_writing":
            # The grant writer uses save_grant_draft tool to save draft to state
            # We just need to pass through events and suppress the draft text from chat
            async for event in self.writer_agent.run_async(ctx):
                if is_empty_text_event(event):
                    continue
                
                # Check if this is a text event - suppress draft content from chat
                has_text = False
                event_text = ""
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts'):
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                has_text = True
                                event_text = part.text
                                break
                
                if has_text:
                    # Only yield short messages (acknowledgements), suppress long draft text
                    if len(event_text.strip()) < 200:
                        yield event
                else:
                    # Non-text events (tool calls, tool responses) pass through
                    yield event
            
            return

        else:
            logger.warning(f"Unknown workflow_step: {workflow_step}")
            return
