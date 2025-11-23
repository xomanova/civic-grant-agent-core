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
from sub_agents.grant_scout_agent import create_grant_scout_agent
from sub_agents.grant_validator_agent import create_grant_validator_agent
from sub_agents.grant_writer_agent import create_grant_writer_agent
from sub_agents.orchestrator import OrchestratorAgent

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
grant_scout_agent = create_grant_scout_agent(retry_config)
grant_validator_agent = create_grant_validator_agent(retry_config)
grant_writer_agent = create_grant_writer_agent(retry_config)

# ============================================================================
# ROOT AGENT: Complete Grant Pipeline with Profile Building Loop
# ============================================================================

root_agent = OrchestratorAgent(
    name="CivicGrantAgent",
    profile_agent=profile_collector_agent,    # Use collector which has the exit tool
    scout_agent=grant_scout_agent,        # Search for grants
    validator_agent=grant_validator_agent,    # Validate eligibility
    writer_agent=grant_writer_agent,        # Draft application
    description="Executes grant finding pipeline: iteratively collects department profile, finds grants, validates eligibility, and drafts applications.",
)
