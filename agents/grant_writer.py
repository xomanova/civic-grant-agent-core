"""
GrantWriter Agent - The Drafter
Generates professional grant application drafts using Gemini.
"""

import logging
from typing import Dict, Any, List
import google.generativeai as genai
from datetime import datetime

logger = logging.getLogger(__name__)


class GrantWriterAgent:
    """
    Agent responsible for drafting grant applications.
    Leverages Gemini's advanced language model for high-quality text generation.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-pro", temperature: float = 0.7):
        """
        Initialize the GrantWriter agent.

        Args:
            api_key: Google API key for Gemini
            model_name: Name of the Gemini model to use
            temperature: Creativity level (0.0-1.0)
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name,
            generation_config={"temperature": temperature}
        )
        self.drafts_created = []

    def write_grant_application(
        self,
        grant_info: Dict[str, Any],
        department_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a complete grant application draft.

        Args:
            grant_info: Validated grant opportunity details
            department_profile: Department configuration (session memory)

        Returns:
            Dictionary containing the draft application
        """
        logger.info(f"Drafting application for: {grant_info.get('name')}")

        # Generate each section of the grant application
        sections = {
            "executive_summary": self._write_executive_summary(grant_info, department_profile),
            "organization_background": self._write_organization_background(department_profile),
            "needs_statement": self._write_needs_statement(grant_info, department_profile),
            "project_description": self._write_project_description(grant_info, department_profile),
            "budget_narrative": self._write_budget_narrative(grant_info, department_profile),
            "community_impact": self._write_community_impact(department_profile),
            "sustainability": self._write_sustainability_plan(department_profile)
        }

        # Compile complete draft
        draft = {
            "grant_name": grant_info.get("name"),
            "grant_source": grant_info.get("source"),
            "department_name": department_profile.get("name"),
            "created_date": datetime.now().isoformat(),
            "sections": sections,
            "full_text": self._compile_full_draft(sections, grant_info, department_profile)
        }

        # Track draft creation
        self.drafts_created.append({
            "grant_name": grant_info.get("name"),
            "department": department_profile.get("name"),
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"Draft completed for: {grant_info.get('name')}")
        return draft

    def _write_executive_summary(
        self,
        grant_info: Dict[str, Any],
        department_profile: Dict[str, Any]
    ) -> str:
        """Generate executive summary section."""
        prompt = f"""Write a compelling executive summary for a grant application.

Grant: {grant_info.get('name')}
Organization: {department_profile.get('name')}
Type: {department_profile.get('type')} fire department
Location: {department_profile.get('location', {}).get('city')}, {department_profile.get('location', {}).get('state')}

Key Points to Include:
- Brief introduction of the department
- Primary need being addressed
- Requested funding amount (if known)
- Expected impact on community safety

Keep it to 150-200 words. Make it compelling and professional.
"""
        return self._generate_section(prompt)

    def _write_organization_background(self, department_profile: Dict[str, Any]) -> str:
        """Generate organization background section."""
        org_details = department_profile.get('organization_details', {})
        location = department_profile.get('location', {})

        prompt = f"""Write an organization background section for a grant application.

Department: {department_profile.get('name')}
Founded: {org_details.get('founded', 'N/A')}
Type: {department_profile.get('type')}
Service Area: {location.get('city')}, {location.get('county')} County, {location.get('state')}
Population Served: {location.get('service_area_population', 'N/A')}
Volunteers: {org_details.get('volunteers', 'N/A')}
Annual Budget: ${org_details.get('annual_budget', 'N/A'):,}

Mission: {department_profile.get('mission')}

Write 250-300 words covering:
- History and establishment
- Service area and population
- Organizational structure
- Current capabilities and resources
- Community role and reputation

Professional tone, third person."""
        return self._generate_section(prompt)

    def _write_needs_statement(
        self,
        grant_info: Dict[str, Any],
        department_profile: Dict[str, Any]
    ) -> str:
        """Generate needs statement section."""
        needs = department_profile.get('needs', [])
        stats = department_profile.get('service_stats', {})

        prompt = f"""Write a compelling needs statement for a fire department grant application.

Department: {department_profile.get('name')}
Primary Needs: {', '.join(needs[:3])}

Service Statistics:
- Annual Fire Calls: {stats.get('annual_fire_calls', 'N/A')}
- Annual EMS Calls: {stats.get('annual_ems_calls', 'N/A')}
- Mutual Aid Responses: {stats.get('mutual_aid_responses', 'N/A')}

Equipment Status: {department_profile.get('equipment_inventory', {}).get('condition', 'N/A')}

Write 300-400 words that:
- Clearly articulates the critical need
- Uses specific data and statistics
- Explains why current resources are inadequate
- Describes the gap between current state and desired state
- Emphasizes impact on firefighter safety and community protection
- Creates urgency without being dramatic

Use factual, professional language."""
        return self._generate_section(prompt)

    def _write_project_description(
        self,
        grant_info: Dict[str, Any],
        department_profile: Dict[str, Any]
    ) -> str:
        """Generate project description section."""
        needs = department_profile.get('needs', [])

        prompt = f"""Write a detailed project description for acquiring {needs[0] if needs else 'equipment'}.

Department: {department_profile.get('name')}
Grant: {grant_info.get('name')}
Primary Need: {needs[0] if needs else 'equipment'}

Write 350-450 words covering:
- Specific equipment/resource to be acquired
- Technical specifications (if applicable)
- Implementation timeline
- How it will be deployed/used
- Training requirements
- Integration with existing resources
- Measurable outcomes and success metrics

Be specific and detailed. Show you have a clear plan."""
        return self._generate_section(prompt)

    def _write_budget_narrative(
        self,
        grant_info: Dict[str, Any],
        department_profile: Dict[str, Any]
    ) -> str:
        """Generate budget narrative section."""
        prompt = f"""Write a budget narrative for a fire department grant application.

Grant Funding Range: {grant_info.get('funding_range', 'TBD')}
Department Annual Budget: ${department_profile.get('organization_details', {}).get('annual_budget', 0):,}

Write 200-250 words:
- Break down major cost categories
- Justify each expense
- Explain any matching funds or in-kind contributions
- Describe financial sustainability
- Show cost-effectiveness

Use realistic estimates for fire department equipment and training."""
        return self._generate_section(prompt)

    def _write_community_impact(self, department_profile: Dict[str, Any]) -> str:
        """Generate community impact section."""
        prompt = f"""Write a community impact statement for a fire department grant.

Department: {department_profile.get('name')}
Service Area Population: {department_profile.get('location', {}).get('service_area_population', 'N/A')}
Community Impact Context: {department_profile.get('community_impact', '')}

Write 250-300 words describing:
- Direct impact on community safety
- Response time improvements
- Lives and property protected
- Economic impact (property saved, insurance ratings)
- Secondary benefits (training, mutual aid, community confidence)
- Long-term community benefits

Use compelling but factual language."""
        return self._generate_section(prompt)

    def _write_sustainability_plan(self, department_profile: Dict[str, Any]) -> str:
        """Generate sustainability plan section."""
        prompt = f"""Write a sustainability plan for a fire department grant.

Department: {department_profile.get('name')}
Type: {department_profile.get('type')}

Write 200-250 words covering:
- Long-term maintenance and upkeep plans
- Funding sources for ongoing costs
- Training continuation
- Equipment lifecycle planning
- Organizational commitment
- Community support

Show the grant investment will have lasting value."""
        return self._generate_section(prompt)

    def _generate_section(self, prompt: str) -> str:
        """
        Use Gemini to generate a section of text.

        Args:
            prompt: The prompt for generating content

        Returns:
            Generated text
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating section: {e}")
            return f"[Error generating section: {str(e)}]"

    def _compile_full_draft(
        self,
        sections: Dict[str, str],
        grant_info: Dict[str, Any],
        department_profile: Dict[str, Any]
    ) -> str:
        """
        Compile all sections into a complete grant application draft.

        Args:
            sections: Dictionary of all generated sections
            grant_info: Grant information
            department_profile: Department configuration

        Returns:
            Complete formatted draft
        """
        draft_parts = [
            "=" * 80,
            f"GRANT APPLICATION DRAFT",
            "=" * 80,
            "",
            f"Grant Program: {grant_info.get('name')}",
            f"Funding Source: {grant_info.get('source')}",
            f"Applicant: {department_profile.get('name')}",
            f"Date Prepared: {datetime.now().strftime('%B %d, %Y')}",
            "",
            "=" * 80,
            "",
            "EXECUTIVE SUMMARY",
            "-" * 80,
            sections.get('executive_summary', ''),
            "",
            "",
            "ORGANIZATION BACKGROUND",
            "-" * 80,
            sections.get('organization_background', ''),
            "",
            "",
            "STATEMENT OF NEED",
            "-" * 80,
            sections.get('needs_statement', ''),
            "",
            "",
            "PROJECT DESCRIPTION",
            "-" * 80,
            sections.get('project_description', ''),
            "",
            "",
            "BUDGET NARRATIVE",
            "-" * 80,
            sections.get('budget_narrative', ''),
            "",
            "",
            "COMMUNITY IMPACT",
            "-" * 80,
            sections.get('community_impact', ''),
            "",
            "",
            "SUSTAINABILITY PLAN",
            "-" * 80,
            sections.get('sustainability', ''),
            "",
            "=" * 80,
            "END OF DRAFT",
            "=" * 80,
            "",
            "Note: This is an AI-generated draft. Please review, edit, and customize",
            "before submission. Verify all facts, figures, and compliance with",
            "specific grant requirements.",
        ]

        return "\n".join(draft_parts)

    def get_drafts_summary(self) -> Dict[str, Any]:
        """
        Get summary of drafts created.

        Returns:
            Dictionary with draft statistics
        """
        return {
            "total_drafts": len(self.drafts_created),
            "drafts": self.drafts_created
        }
