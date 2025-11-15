"""
Tools package for Civic Grant Agent.
Contains custom tools used by the agents.
"""

from .eligibility_checker import check_eligibility, EligibilityChecker

__all__ = ["check_eligibility", "EligibilityChecker"]
