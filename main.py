#!/usr/bin/env python3
"""
Civic Grant Agent - Main Orchestrator
Coordinates all three agents to find and draft grant applications.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

from agents.grant_scout import GrantScoutAgent
from agents.grant_validator import GrantValidatorAgent
from agents.grant_writer import GrantWriterAgent
from utils.session_manager import SessionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('firehouse_ai.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class GrantFinderOrchestrator:
    """
    Main orchestrator for the Civic Grant Agent grant-finding system.
    Coordinates GrantScout, GrantValidator, and GrantWriter agents.
    """

    def __init__(self, config_path: str = "department_config.json"):
        """
        Initialize the Civic Grant Agent system.

        Args:
            config_path: Path to department configuration file
        """
        # Load environment variables
        load_dotenv()
        
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        self.model_name = os.getenv("GEMINI_MODEL", "gemini-pro")
        self.temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))
        self.output_dir = Path(os.getenv("OUTPUT_DIR", "output"))
        
        # Initialize session manager
        self.session = SessionManager(config_path)
        
        # Initialize agents
        logger.info("Initializing Civic Grant Agent agents...")
        self.scout = GrantScoutAgent(self.api_key, self.model_name)
        self.validator = GrantValidatorAgent(self.api_key, self.model_name)
        self.writer = GrantWriterAgent(self.api_key, self.model_name, self.temperature)
        
        logger.info("Civic Grant Agent initialized successfully")

    def run(self, max_grants: int = 5) -> Dict[str, Any]:
        """
        Run the complete grant-finding and drafting pipeline.

        Args:
            max_grants: Maximum number of grant drafts to create

        Returns:
            Dictionary with results summary
        """
        logger.info("=" * 60)
        logger.info("CIVIC GRANT AGENT - GRANT FINDER & DRAFT WRITER")
        logger.info("=" * 60)
        
        try:
            # Step 1: Load department profile (Session Memory)
            logger.info("\n[Step 1/4] Loading Department Profile...")
            department_profile = self.session.load_department_profile()
            logger.info(f"Department: {department_profile.get('name')}")
            logger.info(f"Type: {department_profile.get('type')}")
            logger.info(f"Primary Needs: {', '.join(department_profile.get('needs', [])[:3])}")
            
            self.session.log_agent_interaction(
                "SessionManager",
                "load_profile",
                {"department": department_profile.get("name")}
            )

            # Step 2: Search for grants (GrantScout)
            logger.info("\n[Step 2/4] Searching for Grant Opportunities...")
            self.session.log_agent_interaction("GrantScout", "search_start")
            
            grant_opportunities = self.scout.search_grants(department_profile)
            logger.info(f"Found {len(grant_opportunities)} potential grants")
            
            self.session.update_context("grant_opportunities", grant_opportunities)
            self.session.log_agent_interaction(
                "GrantScout",
                "search_complete",
                {"grants_found": len(grant_opportunities)}
            )

            # Step 3: Validate grants (GrantValidator with Custom Tool)
            logger.info("\n[Step 3/4] Validating Grant Eligibility...")
            self.session.log_agent_interaction("GrantValidator", "validation_start")
            
            validated_grants = self.validator.validate_grants(
                grant_opportunities,
                department_profile
            )
            logger.info(f"Validated {len(validated_grants)} eligible grants")
            
            self.session.update_context("validated_grants", validated_grants)
            self.session.log_agent_interaction(
                "GrantValidator",
                "validation_complete",
                {"grants_eligible": len(validated_grants)}
            )

            # Step 4: Write grant drafts (GrantWriter using Gemini)
            logger.info("\n[Step 4/4] Generating Grant Application Drafts...")
            self.session.log_agent_interaction("GrantWriter", "drafting_start")
            
            drafts = []
            grants_to_draft = validated_grants[:max_grants]
            
            for i, grant in enumerate(grants_to_draft, 1):
                logger.info(f"\nDrafting application {i}/{len(grants_to_draft)}: {grant.get('name')}")
                
                draft = self.writer.write_grant_application(grant, department_profile)
                drafts.append(draft)
                
                # Save draft to file
                self._save_draft(draft)
            
            self.session.update_context("drafts", drafts)
            self.session.log_agent_interaction(
                "GrantWriter",
                "drafting_complete",
                {"drafts_created": len(drafts)}
            )

            # Generate summary
            results = self._generate_summary(
                grant_opportunities,
                validated_grants,
                drafts,
                department_profile
            )

            # Save session
            self.session.save_session(str(self.output_dir))
            
            logger.info("\n" + "=" * 80)
            logger.info("CIVIC GRANT AGENT - PROCESS COMPLETE")
            logger.info("=" * 80)
            logger.info(f"Total grants found: {len(grant_opportunities)}")
            logger.info(f"Eligible grants: {len(validated_grants)}")
            logger.info(f"Drafts created: {len(drafts)}")
            logger.info(f"Output directory: {self.output_dir}")
            
            return results

        except Exception as e:
            logger.error(f"Error in pipeline: {e}", exc_info=True)
            raise

    def _save_draft(self, draft: Dict[str, Any]) -> Path:
        """
        Save a grant draft to file.

        Args:
            draft: Draft dictionary

        Returns:
            Path to saved draft file
        """
        self.output_dir.mkdir(exist_ok=True)
        
        # Create filename
        grant_name = draft.get("grant_name", "unknown").replace(" ", "_").replace("/", "-")
        filename = f"draft_{grant_name}_{datetime.now().strftime('%Y%m%d')}.txt"
        filepath = self.output_dir / filename
        
        # Save full text
        with open(filepath, 'w') as f:
            f.write(draft.get("full_text", ""))
        
        # Also save structured JSON
        json_filepath = filepath.with_suffix('.json')
        with open(json_filepath, 'w') as f:
            json.dump(draft, f, indent=2)
        
        logger.info(f"Saved draft to {filepath}")
        return filepath

    def _generate_summary(
        self,
        grant_opportunities: List[Dict[str, Any]],
        validated_grants: List[Dict[str, Any]],
        drafts: List[Dict[str, Any]],
        department_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate summary of the entire process.

        Args:
            grant_opportunities: All discovered grants
            validated_grants: Eligible grants
            drafts: Created drafts
            department_profile: Department configuration

        Returns:
            Summary dictionary
        """
        summary = {
            "session": self.session.get_session_summary(),
            "department": {
                "name": department_profile.get("name"),
                "type": department_profile.get("type"),
                "needs": department_profile.get("needs")
            },
            "grants": {
                "total_found": len(grant_opportunities),
                "eligible": len(validated_grants),
                "eligibility_rate": len(validated_grants) / len(grant_opportunities) if grant_opportunities else 0
            },
            "drafts": {
                "total_created": len(drafts),
                "grant_names": [d.get("grant_name") for d in drafts]
            },
            "output_directory": str(self.output_dir)
        }
        
        # Save summary
        summary_file = self.output_dir / "summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Saved summary to {summary_file}")
        return summary


def main():
    """Main entry point."""
    try:
        # Initialize and run Civic Grant Agent
        ai = GrantFinderOrchestrator()
        results = ai.run(max_grants=3)  # Generate up to 3 drafts
        
        print("\n" + "=" * 80)
        print("SUCCESS! Civic Grant Agent has completed the grant search and drafting process.")
        print("=" * 80)
        print(f"\nResults:")
        print(f"  - Grants found: {results['grants']['total_found']}")
        print(f"  - Grants eligible: {results['grants']['eligible']}")
        print(f"  - Drafts created: {results['drafts']['total_created']}")
        print(f"\nOutput saved to: {results['output_directory']}")
        print("\nNext steps:")
        print("  1. Review the draft applications in the output/ directory")
        print("  2. Customize and refine the drafts for each specific grant")
        print("  3. Verify all facts, figures, and requirements")
        print("  4. Submit applications before deadlines")
        print("\nGood luck with your grant applications! 🚒")
        
        return 0

    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
        return 130
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nError: {e}")
        print("Check firehouse_ai.log for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
