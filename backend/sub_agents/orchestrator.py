from google.adk.agents import Agent, InvocationContext
from google.adk.events import Event
from typing import AsyncGenerator, List, Optional
from pydantic import model_validator

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

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        state = ctx.session.state
        
        # Initialize workflow step if not present
        if "workflow_step" not in state:
            state["workflow_step"] = "profile_building"
            
        step = state["workflow_step"]
        
        # Step 1: Profile Building
        if step == "profile_building":
            print(f"[Orchestrator] Entering profile_building step. State complete: {state.get('profile_complete')}")
            # Check if profile is complete
            if state.get("profile_complete"):
                print("[Orchestrator] Profile already complete. Advancing to grant_scouting.")
                # Move to next step
                state["workflow_step"] = "grant_scouting"
                # Fall through to next step immediately
                step = "grant_scouting"
            else:
                # Run profile agent
                print("[Orchestrator] Running profile_agent...")
                async for event in self.profile_agent.run_async(ctx):
                    # Filter out empty text events that might crash ag-ui-adk
                    # Check if it's a tool event (calls or responses) - keep those
                    is_tool_event = event.get_function_calls() or event.get_function_responses()
                    
                    if not is_tool_event and event.content and event.content.parts:
                        # It's likely a text event. Check if it has any actual text.
                        has_text = False
                        for part in event.content.parts:
                            if part.text and len(part.text.strip()) > 0:
                                has_text = True
                                break
                        
                        # If it has content parts but no text (and isn't a tool event), skip it
                        if not has_text:
                             print("[Orchestrator] Skipping empty text Event")
                             continue

                    yield event
                    
                    # Check if the sub-agent signaled completion via State
                    # This allows us to break the loop cleanly after the agent has responded
                    if ctx.session.state.get("profile_complete"):
                        print("[Orchestrator] Profile completion signal detected during run. Handling handoff...")
                        state["workflow_step"] = "grant_scouting"
                        step = "grant_scouting"
                        break
                
                # If we didn't complete, return to wait for user input
                if step == "profile_building":
                    print("[Orchestrator] Profile agent turn finished. Waiting for user input.")
                    return

        # Step 2: Grant Scouting
        if step == "grant_scouting":
            print("[Orchestrator] Entering grant_scouting step.")
            # Run scout agent
            async for event in self.scout_agent.run_async(ctx):
                yield event
            
            # For now, we assume scout agent runs once. 
            # If we need to transition to validation, we'd need a similar completion check.
            # But the user's request was specifically about the profile building loop.
            return
