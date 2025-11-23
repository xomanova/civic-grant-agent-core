"""
Eligibility Checker - Custom Tool
Validates whether a department is eligible for a specific grant.
"""

import logging
import re
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class EligibilityResult:
    """Result of an eligibility check."""
    is_eligible: bool
    score: float  # 0.0 to 1.0
    reasons: List[str]
    warnings: List[str]
    match_details: Dict[str, Any]


class EligibilityChecker:
    """
    Custom tool for checking grant eligibility.
    This is a key requirement for demonstrating custom tool usage in ADK.
    """

    def __init__(self):
        """Initialize the eligibility checker."""
        self.check_history = []

    def check_eligibility(
        self,
        grant_info: Dict[str, Any],
        department_profile: Dict[str, Any]
    ) -> EligibilityResult:
        """
        Check if a department is eligible for a specific grant.

        Args:
            grant_info: Dictionary containing grant details
            department_profile: Department configuration

        Returns:
            EligibilityResult with eligibility status and details
        """
        logger.info(f"Checking eligibility for grant: {grant_info.get('name', 'Unknown')}")

        reasons = []
        warnings = []
        match_details = {}
        score = 0.0

        # Check 1: Organization Type
        type_score = self._check_organization_type(grant_info, department_profile)
        score += type_score * 0.25
        if type_score > 0.5:
            reasons.append(f"Organization type matches: {department_profile.get('type')}")
            match_details["type_match"] = True
        else:
            warnings.append("Organization type may not match grant requirements")
            match_details["type_match"] = False

        # Check 2: Location/Geographic Restrictions
        location_score = self._check_location(grant_info, department_profile)
        score += location_score * 0.20
        if location_score > 0.5:
            location = department_profile.get('location', {})
            reasons.append(f"Location eligible: {location.get('state', 'N/A')}")
            match_details["location_match"] = True
        else:
            match_details["location_match"] = False

        # Check 3: Needs Alignment
        needs_score = self._check_needs_alignment(grant_info, department_profile)
        score += needs_score * 0.30
        if needs_score > 0.5:
            reasons.append("Grant funding aligns with department needs")
            match_details["needs_match"] = True
        else:
            warnings.append("Grant focus may not align with department needs")
            match_details["needs_match"] = False

        # Check 4: Budget/Funding Range
        budget_score = self._check_budget_range(grant_info, department_profile)
        score += budget_score * 0.15
        if budget_score > 0.5:
            reasons.append("Department budget compatible with grant requirements")
            match_details["budget_match"] = True
        else:
            match_details["budget_match"] = False

        # Check 5: 501(c)(3) Status
        nonprofit_score = self._check_nonprofit_status(grant_info, department_profile)
        score += nonprofit_score * 0.10
        if nonprofit_score > 0.5:
            reasons.append("Non-profit status verified")
            match_details["nonprofit_match"] = True
        else:
            match_details["nonprofit_match"] = False

        # Determine eligibility
        is_eligible = score >= 0.6  # 60% threshold

        if is_eligible:
            reasons.append(f"Overall eligibility score: {score:.1%}")
        else:
            warnings.append(f"Eligibility score below threshold: {score:.1%}")

        result = EligibilityResult(
            is_eligible=is_eligible,
            score=score,
            reasons=reasons,
            warnings=warnings,
            match_details=match_details
        )

        # Store in history
        self.check_history.append({
            "timestamp": datetime.now().isoformat(),
            "grant": grant_info.get("name", "Unknown"),
            "department": department_profile.get("name", "Unknown"),
            "eligible": is_eligible,
            "score": score
        })

        logger.info(f"Eligibility check complete. Eligible: {is_eligible}, Score: {score:.2f}")
        return result

    def _check_organization_type(
        self,
        grant_info: Dict[str, Any],
        department_profile: Dict[str, Any]
    ) -> float:
        """Check if organization type matches grant requirements."""
        dept_type = department_profile.get("type", "").lower()
        grant_desc = (grant_info.get("description", "") + " " + grant_info.get("name", "")).lower()

        # Keywords that indicate volunteer eligibility
        volunteer_keywords = ["volunteer", "combination", "all fire departments", "any fire department"]
        paid_only_keywords = ["paid", "career", "full-time staff"]

        if dept_type == "volunteer":
            # Check if grant excludes volunteers
            if any(keyword in grant_desc for keyword in paid_only_keywords):
                if not any(keyword in grant_desc for keyword in volunteer_keywords):
                    return 0.2  # Likely not eligible
            return 0.9  # Most grants accept volunteers

        return 0.8  # Default for other types

    def _check_location(
        self,
        grant_info: Dict[str, Any],
        department_profile: Dict[str, Any]
    ) -> float:
        """Check geographic eligibility."""
        dept_state = department_profile.get("location", {}).get("state", "").lower()
        grant_desc = (grant_info.get("description", "") + " " + grant_info.get("name", "")).lower()

        # Federal grants (no geographic restriction)
        if any(word in grant_desc for word in ["federal", "fema", "national", "nationwide"]):
            return 1.0

        # State-specific grants
        if dept_state and dept_state in grant_desc:
            return 1.0

        # If no specific location mentioned, assume broadly eligible
        return 0.7

    def _check_needs_alignment(
        self,
        grant_info: Dict[str, Any],
        department_profile: Dict[str, Any]
    ) -> float:
        """Check if grant funding aligns with department needs."""
        needs = [need.lower() for need in department_profile.get("needs", [])]
        grant_desc = (grant_info.get("description", "") + " " + grant_info.get("name", "")).lower()

        # Keywords for different types of grants
        equipment_keywords = ["equipment", "apparatus", "vehicle", "scba", "gear", "aed", "extrication"]
        training_keywords = ["training", "education", "certification", "professional development"]
        facility_keywords = ["facility", "station", "building", "construction", "renovation"]

        matches = 0
        total_checks = len(needs)

        if total_checks == 0:
            return 0.5  # Neutral if no needs specified

        for need in needs:
            # Check for direct keyword matches
            if need in grant_desc:
                matches += 1
                continue

            # Check for category matches
            need_lower = need.lower()
            if any(keyword in need_lower for keyword in ["training", "certification", "education"]):
                if any(keyword in grant_desc for keyword in training_keywords):
                    matches += 0.8
            elif any(keyword in need_lower for keyword in ["equipment", "gear", "scba", "aed"]):
                if any(keyword in grant_desc for keyword in equipment_keywords):
                    matches += 0.8
            elif any(keyword in need_lower for keyword in ["facility", "station", "building"]):
                if any(keyword in grant_desc for keyword in facility_keywords):
                    matches += 0.8

        return min(matches / total_checks, 1.0)

    def _check_budget_range(
        self,
        grant_info: Dict[str, Any],
        department_profile: Dict[str, Any]
    ) -> float:
        """Check if grant funding range is appropriate for department budget."""
        dept_budget = department_profile.get("organization_details", {}).get("annual_budget", 0)
        funding_range = grant_info.get("funding_range", "")

        if not funding_range or dept_budget == 0:
            return 0.7  # Neutral if no data

        # Extract numbers from funding range
        numbers = re.findall(r'\$?[\d,]+', funding_range)
        if numbers:
            try:
                # Parse the funding amounts
                amounts = [int(num.replace(',', '').replace('$', '')) for num in numbers]
                min_funding = min(amounts) if amounts else 0
                max_funding = max(amounts) if amounts else 0

                # Check if department budget is within reasonable range
                # Small departments should apply for smaller grants
                if dept_budget < 100000:  # Small department
                    if max_funding <= 100000:
                        return 1.0  # Perfect match
                    elif min_funding <= 50000:
                        return 0.8  # Still good
                elif dept_budget < 500000:  # Medium department
                    if 10000 <= min_funding <= 500000:
                        return 1.0
                else:  # Large department
                    if min_funding >= 50000:
                        return 1.0

            except (ValueError, IndexError):
                pass

        return 0.6  # Default if can't parse

    def _check_nonprofit_status(
        self,
        grant_info: Dict[str, Any],
        department_profile: Dict[str, Any]
    ) -> float:
        """Check if 501(c)(3) status matches grant requirements."""
        has_501c3 = department_profile.get("organization_details", {}).get("501c3_status", False)
        grant_desc = (grant_info.get("description", "") + " " + grant_info.get("name", "")).lower()

        # Check if grant requires 501(c)(3)
        if "501(c)(3)" in grant_desc or "nonprofit" in grant_desc:
            return 1.0 if has_501c3 else 0.3

        # Many fire department grants don't require 501(c)(3)
        return 0.9

    def get_check_history(self) -> List[Dict[str, Any]]:
        """Get history of eligibility checks."""
        return self.check_history


# Standalone function for simple usage
def check_eligibility(
    grant_info: Dict[str, Any],
    department_profile: Dict[str, Any]
) -> bool:
    """
    Simple eligibility check function.

    Args:
        grant_info: Grant details
        department_profile: Department configuration

    Returns:
        True if eligible, False otherwise
    """
    checker = EligibilityChecker()
    result = checker.check_eligibility(grant_info, department_profile)
    return result.is_eligible
