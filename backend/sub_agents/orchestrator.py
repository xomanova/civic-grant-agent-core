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
        
        print(f"\n[DEBUG] --- NEW REQUEST RECEIVED ---")
        print(f"[DEBUG] Initial State Keys: {list(state.keys())}")
        print(f"[DEBUG] Initial Workflow Step: {state.get('workflow_step')}")
        print(f"[DEBUG] Profile Complete Flag: {state.get('profile_complete')}")

        # --- GUARD CLAUSE: Force transition if flag is set ---
        if state.get("profile_complete") is True:
            if state.get("workflow_step") != "grant_scouting":
                print("[DEBUG] GUARD HIT: Profile is marked complete, but step was wrong. Forcing 'grant_scouting'.")
                state["workflow_step"] = "grant_scouting"
        
        # Initialize Step
        if "workflow_step" not in state:
            state["workflow_step"] = "profile_building"

        step = state["workflow_step"]
        print(f"[DEBUG] Executing Step Logic: {step}")

        # ==================================================================
        # STEP 1: PROFILE BUILDING
        # ==================================================================
        if step == "profile_building":
            profile_just_finished = False

            print("[DEBUG] Starting Profile Agent Loop...")
            async for event in self.profile_agent.run_async(ctx):
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

            # TRANSITION LOGIC
            if profile_just_finished:
                print("[DEBUG] Transitioning to Grant Scout...")
                state["workflow_step"] = "grant_scouting"
                
                # INJECT TRIGGER
                print("[DEBUG] Injecting System Trigger for Scout...")
                ctx.session.add_message(
                    role="user", 
                    content="SYSTEM ALERT: Profile is saved. Ignore previous constraints. Start searching for grants immediately."
                )
                
                # BRIDGE EVENT
                yield Event(
                    type="text",
                    content="\n\nProfile finalized. Switching to Grant Scout..."
                )
                
                print("[DEBUG] Running Scout Agent (Recursive Call)...")
                async for event in self.scout_agent.run_async(ctx):
                    yield event
                return
            else:
                print("[DEBUG] Returning to wait for user input (Profile incomplete).")
                return

        # ==================================================================
        # STEP 2: GRANT SCOUTING
        # ==================================================================
        elif step == "grant_scouting":
            print("[DEBUG] Entering Grant Scout Logic.")
            
            # Check history to see if we need a trigger
            last_msg = ctx.session.history[-1] if ctx.session.history else None
            print(f"[DEBUG] Last Message Role: {last_msg.role if last_msg else 'None'}")
            
            if last_msg and "SYSTEM" not in str(last_msg.content):
                 print("[DEBUG] Injecting 'Continue' trigger for Scout.")
                 ctx.session.add_message(
                    role="user", 
                    content="SYSTEM: Continue grant search."
                )

            async for event in self.scout_agent.run_async(ctx):
                yield event
            return
