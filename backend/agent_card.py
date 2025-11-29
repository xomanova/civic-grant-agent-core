"""
A2A Protocol Agent Card for Civic Grant Agent
Defines the agent's capabilities, skills, and metadata for discovery.
"""

from typing import List, Optional
from pydantic import BaseModel


# ============================================================================
# A2A TYPES (inline definitions to avoid dependency issues)
# ============================================================================

class AgentSkill(BaseModel):
    """Describes a specific capability or function the agent can perform."""
    id: str
    name: str
    description: str
    tags: List[str] = []
    examples: List[str] = []
    inputModes: List[str] = ["text/plain"]
    outputModes: List[str] = ["text/plain"]


class AgentCapabilities(BaseModel):
    """Specifies supported A2A features."""
    streaming: bool = False
    pushNotifications: bool = False
    stateTransitionHistory: bool = False


class AgentProvider(BaseModel):
    """Information about the agent provider."""
    organization: str
    url: str


class AgentCard(BaseModel):
    """A2A Agent Card - digital business card for the agent."""
    name: str
    description: str
    url: str
    version: str
    defaultInputModes: List[str] = ["text/plain"]
    defaultOutputModes: List[str] = ["text/plain"]
    capabilities: AgentCapabilities = AgentCapabilities()
    skills: List[AgentSkill] = []
    documentationUrl: Optional[str] = None
    provider: Optional[AgentProvider] = None
    supportsAuthenticatedExtendedCard: bool = False


# ============================================================================
# AGENT SKILLS
# ============================================================================

# Skill 1: Profile Collection
profile_skill = AgentSkill(
    id="profile_collector",
    name="Department Profile Collection",
    description="Conversationally gathers information about volunteer fire departments, EMS agencies, and civic organizations including location, equipment needs, budget, and service area.",
    tags=["intake", "profile", "fire department", "ems", "civic", "interview"],
    examples=[
        "I am the chief of Halls Volunteer Fire Department in Tennessee",
        "We need funding for new SCBA equipment",
        "Our department serves a population of 15,000",
    ],
    inputModes=["text/plain"],
    outputModes=["text/plain", "application/json"],
)

# Skill 2: Grant Discovery & Validation
grant_finder_skill = AgentSkill(
    id="grant_finder",
    name="Grant Discovery & Eligibility Validation",
    description="Searches federal, state, and foundation grant opportunities. Validates eligibility based on department profile, filters by geographic region, and scores match quality (0-100%).",
    tags=["grants", "funding", "fema", "afg", "safer", "eligibility", "search"],
    examples=[
        "Find grants for volunteer fire departments in North Carolina",
        "Search for SCBA equipment funding opportunities",
        "What FEMA grants are available for EMS agencies?",
    ],
    inputModes=["text/plain", "application/json"],
    outputModes=["text/plain", "application/json"],
)

# Skill 3: Grant Application Drafting
grant_writer_skill = AgentSkill(
    id="grant_writer",
    name="Grant Application Drafting",
    description="Generates professional grant application narratives with 7-section structure: Executive Summary, Background, Statement of Need, Project Description, Budget Justification, Expected Impact, and Sustainability Plan.",
    tags=["writing", "application", "narrative", "draft", "proposal"],
    examples=[
        "Write a grant application for the AFG grant",
        "Draft an application for SCBA equipment funding",
        "Generate a proposal for the Firehouse Subs Foundation grant",
    ],
    inputModes=["text/plain", "application/json"],
    outputModes=["text/plain", "text/markdown"],
)

# ============================================================================
# AGENT CARD
# ============================================================================

civic_grant_agent_card = AgentCard(
    name="Civic Grant Agent Core",
    description="AI-powered grant discovery and application writing assistant for volunteer fire departments, EMS agencies, and civic organizations. Autonomously interviews departments, searches funding opportunities, validates eligibility, and drafts professional applications.",
    url="https://civic-grant-agent-core.xomanova.io/api/a2a",
    version="2.0.0",
    defaultInputModes=["text/plain"],
    defaultOutputModes=["text/plain", "text/markdown", "application/json"],
    capabilities=AgentCapabilities(
        streaming=True,
        pushNotifications=False,
        stateTransitionHistory=True,
    ),
    skills=[
        profile_skill,
        grant_finder_skill,
        grant_writer_skill,
    ],
    documentationUrl="https://github.com/xomanova/civic-grant-agent-core",
    provider=AgentProvider(
        organization="xomanova",
        url="https://github.com/xomanova",
    ),
    supportsAuthenticatedExtendedCard=False,
)
