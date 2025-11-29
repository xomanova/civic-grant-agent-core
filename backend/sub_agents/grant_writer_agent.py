"""GrantWriter Agent - Generates professional grant application drafts
"""

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from tools.draft_storage import save_grant_draft
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
        # Note: We don't use output_key here because we use save_grant_draft tool
        # to explicitly save the draft content to state
        instruction="""You are the GrantWriter agent. Your job is to call save_grant_draft exactly ONCE.

## WORKFLOW
1. Call save_grant_draft with the grant name and complete draft content
2. After the tool returns, say: "👈 Your draft is ready! Scroll down to review it."
3. STOP. Do not call the tool again.

## HOW TO CALL THE TOOL

save_grant_draft(
    grant_name="[name of grant from selected_grant_for_writing]",
    draft_content="[complete markdown draft - see structure below]"
)

## DRAFT STRUCTURE (for draft_content parameter)

# Grant Application Draft

**Grant Program:** [grant name]
**Funding Source:** [source]  
**Applicant:** [department name]

---

## 1. Executive Summary
~150 words: Department intro, primary need, funding request, community impact.

## 2. Organization Background  
~200 words: History, service area, population served, structure, capabilities.

## 3. Statement of Need
~250 words: Critical need with real numbers from profile, current gaps, safety impact.

## 4. Project Description
~250 words: Equipment details, implementation timeline, training plan, outcomes.

## 5. Budget Narrative
~150 words: Cost breakdown, justification, matching funds if applicable.

## 6. Community Impact
~150 words: Safety improvements, response time gains, lives protected.

## 7. Sustainability Plan
~150 words: Maintenance, ongoing funding, equipment lifecycle.

---

## DATA SOURCES
- selected_grant_for_writing: The grant to apply for
- civic_grant_profile: Department info (name, location, needs, budget, mission)

## RULES
- You MUST call save_grant_draft - this is not optional
- Do NOT output any text before or after the tool call
- Use real data from civic_grant_profile
- The draft_content should be complete markdown""",
        tools=[save_grant_draft]
    )
