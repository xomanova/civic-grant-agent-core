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
            # Check if profile is complete
            if state.get("profile_complete"):
                # Move to next step
                state["workflow_step"] = "grant_scouting"
                # Fall through to next step immediately
                step = "grant_scouting"
            else:
                # Run profile agent
                async for event in self.profile_agent.run_async(ctx):
                    yield event
                
                # Check if it just completed
                if state.get("profile_complete"):
                    state["workflow_step"] = "grant_scouting"
                    step = "grant_scouting"
                    # Fall through to next step
                else:
                    # After profile agent returns (end of turn), we stop.
                    # The state check will happen on next turn.
                    return

        # Step 2: Grant Scouting
        if step == "grant_scouting":
            # Run scout agent
            async for event in self.scout_agent.run_async(ctx):
                yield event
            
            # For now, we assume scout agent runs once. 
            # If we need to transition to validation, we'd need a similar completion check.
            # But the user's request was specifically about the profile building loop.
            return
