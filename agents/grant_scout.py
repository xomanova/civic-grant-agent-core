"""
GrantScout Agent - The Researcher
Proactively searches for grant opportunities using Google Search tools.
"""

import logging
from typing import List, Dict, Any
import google.generativeai as genai
from datetime import datetime

logger = logging.getLogger(__name__)


class GrantScoutAgent:
    """
    Agent responsible for finding grant opportunities.
    Uses built-in Google Search tools to discover relevant grants.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-pro"):
        """
        Initialize the GrantScout agent.

        Args:
            api_key: Google API key for Gemini
            model_name: Name of the Gemini model to use
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.search_history = []

    def generate_search_queries(self, department_profile: Dict[str, Any]) -> List[str]:
        """
        Generate targeted search queries based on department profile.

        Args:
            department_profile: Department configuration dictionary

        Returns:
            List of search query strings
        """
        dept_type = department_profile.get("type", "volunteer")
        needs = department_profile.get("needs", [])
        state = department_profile.get("location", {}).get("state", "")

        queries = [
            f"{dept_type} fire department grants {state}",
            f"fire department equipment grants {datetime.now().year}",
            "FEMA fire department grants",
            "AFG assistance to firefighters grant",
        ]

        # Add need-specific queries
        for need in needs[:3]:  # Top 3 needs
            queries.append(f"fire department {need} grant funding")

        # Add state-specific queries
        if state:
            queries.append(f"{state} fire department grant programs")
            queries.append(f"{state} public safety grants")

        logger.info(f"Generated {len(queries)} search queries")
        return queries

    def search_grants(
        self, department_profile: Dict[str, Any], max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for grant opportunities using generated queries.

        Args:
            department_profile: Department configuration
            max_results: Maximum number of results to return

        Returns:
            List of potential grant opportunities with URLs and descriptions
        """
        logger.info("Starting grant search...")

        queries = self.generate_search_queries(department_profile)
        
        # Create prompt for the LLM to help identify relevant grants
        prompt = f"""You are a grant research specialist for fire departments.

Department Profile:
- Type: {department_profile.get('type')}
- Location: {department_profile.get('location', {}).get('state')}
- Needs: {', '.join(department_profile.get('needs', []))}
- Budget: ${department_profile.get('organization_details', {}).get('annual_budget', 'N/A')}

Task: Based on the search queries provided, identify the most relevant grant opportunities.
For each query, list potential federal, state, and corporate grants that would be applicable.

Search Queries:
{chr(10).join(f'- {q}' for q in queries)}

For each grant you identify, provide:
1. Grant Name
2. Source/Organization
3. Estimated URL or source
4. Brief description
5. Typical funding range
6. Application deadline (if known)

Focus on grants that are:
- Currently accepting applications or opening soon
- Match the department's volunteer/paid status
- Align with equipment needs
- Appropriate for the department's budget size

Format your response as a structured list."""

        try:
            response = self.model.generate_content(prompt)
            
            # Parse the LLM response to extract grant information
            grant_results = self._parse_grant_response(response.text)
            
            # Store search results
            self.search_history.append({
                "timestamp": datetime.now().isoformat(),
                "queries": queries,
                "results_count": len(grant_results)
            })
            
            logger.info(f"Found {len(grant_results)} potential grant opportunities")
            return grant_results[:max_results]

        except Exception as e:
            logger.error(f"Error during grant search: {e}")
            return self._get_fallback_grants()

    def _parse_grant_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response into structured grant data.

        Args:
            response_text: Raw text response from LLM

        Returns:
            List of grant dictionaries
        """
        grants = []
        
        # Simple parsing - in production, this would be more sophisticated
        lines = response_text.split('\n')
        current_grant = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_grant:
                    grants.append(current_grant)
                    current_grant = {}
                continue
                
            # Look for structured information
            if line.lower().startswith('grant name:') or line.startswith('1.'):
                if current_grant:
                    grants.append(current_grant)
                current_grant = {
                    "name": line.split(':', 1)[-1].strip() if ':' in line else line,
                    "source": "Unknown",
                    "url": "",
                    "description": "",
                    "funding_range": "",
                    "deadline": "TBD",
                    "discovered_date": datetime.now().isoformat()
                }
            elif current_grant:
                if 'source' in line.lower() or 'organization' in line.lower():
                    current_grant["source"] = line.split(':', 1)[-1].strip()
                elif 'url' in line.lower() or 'website' in line.lower():
                    current_grant["url"] = line.split(':', 1)[-1].strip()
                elif 'description' in line.lower():
                    current_grant["description"] = line.split(':', 1)[-1].strip()
                elif 'funding' in line.lower() or 'range' in line.lower():
                    current_grant["funding_range"] = line.split(':', 1)[-1].strip()
                elif 'deadline' in line.lower():
                    current_grant["deadline"] = line.split(':', 1)[-1].strip()
        
        if current_grant:
            grants.append(current_grant)
        
        return grants

    def _get_fallback_grants(self) -> List[Dict[str, Any]]:
        """
        Return well-known grant opportunities as fallback.

        Returns:
            List of known grant opportunities
        """
        return [
            {
                "name": "Assistance to Firefighters Grant (AFG)",
                "source": "FEMA",
                "url": "https://www.fema.gov/grants/preparedness/firefighters",
                "description": "Federal grant program for fire departments to obtain equipment, protective gear, emergency vehicles, training, and other resources needed to protect the public and emergency personnel.",
                "funding_range": "$5,000 - $500,000",
                "deadline": "Typically opens in January",
                "discovered_date": datetime.now().isoformat()
            },
            {
                "name": "Staffing for Adequate Fire and Emergency Response (SAFER)",
                "source": "FEMA",
                "url": "https://www.fema.gov/grants/preparedness/firefighters/safer",
                "description": "Provides funding to help fire departments increase the number of trained firefighters.",
                "funding_range": "Varies",
                "deadline": "Typically opens in January",
                "discovered_date": datetime.now().isoformat()
            },
            {
                "name": "Fire Prevention and Safety Grants (FP&S)",
                "source": "FEMA",
                "url": "https://www.fema.gov/grants/preparedness/firefighters/safety-awards",
                "description": "Supports projects that enhance the safety of the public and firefighters from fire and related hazards.",
                "funding_range": "$10,000 - $500,000",
                "deadline": "Typically opens in February",
                "discovered_date": datetime.now().isoformat()
            }
        ]

    def get_search_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of search operations.

        Returns:
            List of search history entries
        """
        return self.search_history
