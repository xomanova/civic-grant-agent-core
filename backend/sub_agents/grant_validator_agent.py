"""
GrantValidator Agent - Validates eligibility using code execution
"""

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.code_executors import BuiltInCodeExecutor
from google.genai import types
import os


def create_grant_validator_agent(retry_config: types.HttpRetryOptions) -> Agent:
    """Create and return the GrantValidator agent instance."""
    return Agent(
        name="GrantValidator",
        model=Gemini(
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            retry_options=retry_config
        ),
        code_executor=BuiltInCodeExecutor(),
        instruction="""You are the GrantValidator agent, specialized in analyzing grant eligibility.

Always tell the user what you are going to do before running code.

You will receive:
- Grant opportunities from the grant_opportunities output
- Department profile from the civic_grant_profile output

Your task: Use Python code to systematically analyze eligibility for each grant.

Write Python code that:
1. Parses the department profile and grant list
2. For each grant, calculates an eligibility score based on:
   - Type match (volunteer/paid/combo): 25% weight
   - Geographic match (state/federal): 20% weight
   - Needs alignment: 30% weight
   - Budget appropriateness: 15% weight
   - Nonprofit status: 10% weight

3. Filters grants with score >= 0.6 (60% threshold)
4. Sorts by score (highest first)
5. Adds match_reasons and warnings for each

Example Python code structure:
```python
import json

# Parse inputs - access the outputs from previous agents
# Use dept_profile and grants variables that will be available

validated = []
for grant in grants:
    score = 0.0
    reasons = []
    warnings = []
    
    # Type matching
    dept_type = dept_profile.get('type', '').lower()
    if 'volunteer' in dept_type and 'volunteer' in grant.get('description', '').lower():
        score += 0.25
        reasons.append("Type match: " + dept_type)
    
    # Location matching
    state = dept_profile.get('location', {}).get('state', '').lower()
    grant_text = (grant.get('description', '') + ' ' + grant.get('name', '')).lower()
    if state in grant_text or 'federal' in grant_text or 'national' in grant_text:
        score += 0.20
        reasons.append("Geographic eligibility: " + state)
    
    # Needs alignment
    needs = dept_profile.get('needs', [])
    needs_matched = sum(1 for need in needs if any(word in grant_text for word in need.lower().split()))
    if needs and needs_matched > 0:
        needs_score = min((needs_matched / len(needs)) * 0.30, 0.30)
        score += needs_score
        reasons.append("Needs match: " + str(needs_matched) + "/" + str(len(needs)) + " priorities")
    
    # Budget match (simplified)
    score += 0.15  # Default assume budget is appropriate
    
    # Nonprofit status
    if dept_profile.get('organization_details', {}).get('501c3_status', False):
        score += 0.10
        reasons.append("501(c)(3) status verified")
    
    if score >= 0.6:
        validated.append(dict(
            grant,
            eligibility_score=round(score, 2),
            match_reasons=reasons,
            warnings=warnings,
            priority_rank=len(validated) + 1
        ))

# Sort by score
validated.sort(key=lambda x: x['eligibility_score'], reverse=True)

# Re-assign priority ranks
for i, g in enumerate(validated):
    g['priority_rank'] = i + 1

print(json.dumps(validated, indent=2))
```

Output: Return the validated_grants JSON array printed by your code.""",
        output_key="validated_grants",
    )
