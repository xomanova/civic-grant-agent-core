"""
Tools package for Civic Grant Agent.
Contains custom tools used by the agents.
"""

from .eligibility_checker import check_eligibility, EligibilityChecker
from .web_search import search_web
from .grants_mcp_client import search_federal_grants, get_agency_landscape, get_funding_trends

__all__ = [
    "check_eligibility", 
    "EligibilityChecker", 
    "search_web",
    "search_federal_grants",
    "get_agency_landscape", 
    "get_funding_trends"
]
