"""
ADK Agent Configuration
Defines the multi-agent system for grant finding and writing.
"""

from google.genai import types
from dotenv import load_dotenv

# Import agent creators from sub_agents directory
from sub_agents.profile_collector_agent import create_profile_collector_agent
from sub_agents.grant_finder_agent import create_grant_finder_agent
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
grant_finder_agent = create_grant_finder_agent(retry_config)  # Combined scout + validator
grant_writer_agent = create_grant_writer_agent(retry_config)

# ============================================================================
# ROOT AGENT: Complete Grant Pipeline with Profile Building Loop
# ============================================================================

root_agent = OrchestratorAgent(
    name="CivicGrantAgent",
    profile_agent=profile_collector_agent,    # Collects department profile
    finder_agent=grant_finder_agent,          # Search + validate grants (combined)
    writer_agent=grant_writer_agent,          # Draft application
    description="Executes grant finding pipeline: iteratively collects department profile, finds grants, validates eligibility, and drafts applications.",
)
