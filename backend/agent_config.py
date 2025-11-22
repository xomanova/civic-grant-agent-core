"""
ADK Agent Configuration
Defines the multi-agent system for grant finding and writing.
"""

from google.adk.agents import Agent, SequentialAgent, LoopAgent
from google.genai import types
import os
from dotenv import load_dotenv

# Import agent creators from sub_agents directory
from sub_agents.profile_collector_agent import create_profile_collector_agent
from sub_agents.profile_builder_agent import create_profile_builder_agent
from sub_agents.grant_scout_agent import create_grant_scout_agent
from sub_agents.grant_validator_agent import create_grant_validator_agent
from sub_agents.grant_writer_agent import create_grant_writer_agent

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
# CREATE AGENT INSTANCES
# ============================================================================

# Create agent instances using factory functions
profile_collector_agent = create_profile_collector_agent(retry_config)
profile_builder_agent = create_profile_builder_agent(retry_config)
grant_scout_agent = create_grant_scout_agent(retry_config)
grant_validator_agent = create_grant_validator_agent(retry_config)
grant_writer_agent = create_grant_writer_agent(retry_config)

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
# ROOT AGENT: Complete Grant Pipeline with Profile Building Loop
# ============================================================================

root_agent = Agent(
    name="CivicGrantAgent",
    model=Gemini(
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        retry_options=retry_config
    ),
    sub_agents=[
        profile_builder_agent,    # Loop: Collect profile until complete
        grant_scout_agent,        # Search for grants
        grant_validator_agent,    # Validate eligibility
        grant_writer_agent        # Draft application
    ],
    description="Executes grant finding pipeline: iteratively collects department profile, finds grants, validates eligibility, and drafts applications.",
)
