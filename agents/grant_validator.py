"""
GrantValidator Agent - The Analyst
Validates grant eligibility using custom tools and session memory.
"""

import logging
from typing import List, Dict, Any
import google.generativeai as genai
from datetime import datetime
from tools.eligibility_checker import EligibilityChecker

logger = logging.getLogger(__name__)


class GrantValidatorAgent:
    """
    Agent responsible for validating and prioritizing grant opportunities.
    Uses custom eligibility checker tool and session memory.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-pro"):
        """
        Initialize the GrantValidator agent.

        Args:
            api_key: Google API key for Gemini
            model_name: Name of the Gemini model to use
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.eligibility_checker = EligibilityChecker()
        self.validation_history = []

    def validate_grants(
        self,
        grant_opportunities: List[Dict[str, Any]],
        department_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Validate and prioritize grant opportunities.

        Args:
            grant_opportunities: List of grant opportunities from GrantScout
            department_profile: Department configuration (session memory)

        Returns:
            List of validated and prioritized grants
        """
        logger.info(f"Validating {len(grant_opportunities)} grant opportunities...")

        validated_grants = []

        for grant in grant_opportunities:
            # Use custom eligibility checker tool
            eligibility_result = self.eligibility_checker.check_eligibility(
                grant, department_profile
            )

            # Enhance grant data with eligibility information
            grant_with_validation = {
                **grant,
                "eligibility": {
                    "is_eligible": eligibility_result.is_eligible,
                    "score": eligibility_result.score,
                    "reasons": eligibility_result.reasons,
                    "warnings": eligibility_result.warnings,
                    "match_details": eligibility_result.match_details
                },
                "validated_date": datetime.now().isoformat()
            }

            if eligibility_result.is_eligible:
                validated_grants.append(grant_with_validation)
                logger.info(
                    f"✓ {grant.get('name')} - Eligible (Score: {eligibility_result.score:.1%})"
                )
            else:
                logger.info(
                    f"✗ {grant.get('name')} - Not Eligible (Score: {eligibility_result.score:.1%})"
                )

        # Prioritize grants using LLM
        prioritized_grants = self._prioritize_grants(validated_grants, department_profile)

        # Store validation results
        self.validation_history.append({
            "timestamp": datetime.now().isoformat(),
            "total_grants": len(grant_opportunities),
            "eligible_grants": len(validated_grants),
            "department": department_profile.get("name")
        })

        logger.info(f"Validation complete. {len(prioritized_grants)} eligible grants found.")
        return prioritized_grants

    def _prioritize_grants(
        self,
        validated_grants: List[Dict[str, Any]],
        department_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Prioritize validated grants based on relevance and urgency.

        Args:
            validated_grants: List of eligible grants
            department_profile: Department configuration

        Returns:
            Sorted list of grants by priority
        """
        if not validated_grants:
            return []

        # Create prompt for LLM to help prioritize
        grants_summary = "\n".join([
            f"- {g.get('name')} (Score: {g['eligibility']['score']:.1%}, Source: {g.get('source')})"
            for g in validated_grants
        ])

        prompt = f"""You are a grant advisor for fire departments.

Department Profile:
- Name: {department_profile.get('name')}
- Type: {department_profile.get('type')}
- Top Needs: {', '.join(department_profile.get('needs', [])[:3])}
- Budget: ${department_profile.get('organization_details', {}).get('annual_budget', 'N/A')}

Eligible Grants:
{grants_summary}

Task: Rank these grants from highest to lowest priority based on:
1. Alignment with department's top needs
2. Likelihood of success (eligibility score)
3. Funding amount appropriateness
4. Application deadline urgency
5. Strategic value

Provide a ranking with brief justification for each grant's position.
Format: Just list the grant names in priority order, one per line."""

        try:
            response = self.model.generate_content(prompt)
            priority_order = self._parse_priority_response(response.text, validated_grants)
            
            # Reorder grants based on LLM recommendation
            prioritized = []
            remaining = validated_grants.copy()
            
            for grant_name in priority_order:
                for grant in remaining:
                    if grant_name.lower() in grant.get('name', '').lower():
                        grant['priority_rank'] = len(prioritized) + 1
                        prioritized.append(grant)
                        remaining.remove(grant)
                        break
            
            # Add any remaining grants
            for grant in remaining:
                grant['priority_rank'] = len(prioritized) + 1
                prioritized.append(grant)
            
            return prioritized

        except Exception as e:
            logger.error(f"Error prioritizing grants: {e}")
            # Fallback: sort by eligibility score
            return sorted(
                validated_grants,
                key=lambda g: g['eligibility']['score'],
                reverse=True
            )

    def _parse_priority_response(
        self,
        response_text: str,
        validated_grants: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Parse LLM priority response into ordered list of grant names.

        Args:
            response_text: Raw LLM response
            validated_grants: List of grants to match against

        Returns:
            Ordered list of grant names
        """
        lines = response_text.split('\n')
        priority_order = []
        
        for line in lines:
            line = line.strip()
            # Remove numbering, bullets, etc.
            line = line.lstrip('0123456789.-*• ')
            if line:
                priority_order.append(line)
        
        return priority_order

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary of validation activities.

        Returns:
            Dictionary with validation statistics
        """
        if not self.validation_history:
            return {}

        total_processed = sum(h['total_grants'] for h in self.validation_history)
        total_eligible = sum(h['eligible_grants'] for h in self.validation_history)

        return {
            "total_validations": len(self.validation_history),
            "total_grants_processed": total_processed,
            "total_grants_eligible": total_eligible,
            "average_eligibility_rate": total_eligible / total_processed if total_processed > 0 else 0,
            "history": self.validation_history
        }
