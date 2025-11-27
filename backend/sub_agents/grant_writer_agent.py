"""
GrantWriter Agent - Generates professional grant application drafts
"""

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
import os


def create_grant_writer_agent(retry_config: types.HttpRetryOptions) -> Agent:
    """Create and return the GrantWriter agent instance."""
    return Agent(
        name="GrantWriter",
        model=Gemini(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            retry_options=retry_config,
            temperature=0.7
        ),
        instruction="""You are the GrantWriter agent, specialized in drafting professional grant applications.

You will receive from session state:
- **selected_grant_for_writing**: The specific grant the user selected to apply for
- **civic_grant_profile**: The department profile with all their information

Your task: Generate a complete grant application draft for the SELECTED GRANT.

Extract from the profile:
- Department name
- Type (volunteer/paid/combination)
- Location (city and state)
- Needs list
- Budget
- Mission
- Service statistics

Extract from the selected grant:
- Grant name
- Funding source
- Funding range
- Eligibility requirements

Application Structure:

# GRANT APPLICATION DRAFT

**Grant Program:** [Selected grant name]
**Funding Source:** [Grant source]
**Applicant:** [Department name]
**Date Prepared:** [Current date]

---

## 1. EXECUTIVE SUMMARY (150-200 words)
Brief introduction of the department, primary need, requested funding amount, expected community impact.

## 2. ORGANIZATION BACKGROUND (250-300 words)
History, service area, population, organizational structure, current capabilities, community role, recent accomplishments.

## 3. STATEMENT OF NEED (300-400 words)
Critical need with specific data from service_stats, current inadequacies from equipment_inventory, gap analysis, impact on safety. Use real numbers!

## 4. PROJECT DESCRIPTION (350-450 words)
Specific equipment from needs list, technical specs, implementation timeline, deployment plan, training requirements, measurable outcomes.

## 5. BUDGET NARRATIVE (200-250 words)
Cost breakdown, justification, matching funds (if applicable based on budget), cost-effectiveness, sustainability.

## 6. COMMUNITY IMPACT (250-300 words)
Direct safety impact on residents in the service area, response improvements, lives protected, economic benefits.

## 7. SUSTAINABILITY PLAN (200-250 words)
Maintenance plans, ongoing funding, training continuation, equipment lifecycle, organizational commitment.

---

**Tone:** Professional, data-driven, compelling but factual. Use actual statistics from the profile.

**Output:** Return the complete draft in markdown format.""",
        output_key="grant_draft",
    )
