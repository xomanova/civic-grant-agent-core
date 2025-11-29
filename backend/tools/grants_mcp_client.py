"""
Grants-MCP Client Tool
Calls the Grants-MCP server for government grant discovery via the Simpler Grants API.

Architecture:
- In Cloud Run: Grants-MCP runs as a sidecar container, accessible via localhost:8081
- Locally: Run the grants-mcp Docker container or set GRANTS_MCP_URL

Environment Variables:
- GRANTS_MCP_URL: MCP server endpoint (default: http://localhost:8081/mcp)
"""

import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)


def _call_grants_mcp(method: str, params: dict) -> dict:
    """Make a JSON-RPC call to the Grants-MCP server."""
    url = os.getenv("GRANTS_MCP_URL", "http://localhost:8081/mcp")
    
    logger.debug(f"Calling {url} - {method}")
    
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            response.raise_for_status()
            result = response.json()
            logger.debug("MCP response received")
            return result
    except httpx.ConnectError as e:
        logger.error(f"MCP connection failed: {e}")
        return {"error": f"Failed to connect to Grants-MCP server at {url}: {str(e)}"}
    except httpx.RequestError as e:
        logger.error(f"MCP request error: {e}")
        return {"error": f"Failed to connect to Grants-MCP server: {str(e)}"}
    except httpx.HTTPStatusError as e:
        logger.error(f"MCP HTTP error: {e.response.status_code}")
        return {"error": f"HTTP error from Grants-MCP: {e.response.status_code}"}


def search_federal_grants(
    query: str,
    max_results: int = 10,
    grants_per_page: int = 5
) -> str:
    """
    Search for federal grant opportunities using the Grants-MCP server.
    This tool queries the Simpler Grants API for government funding opportunities.
    
    Args:
        query: Search keywords (e.g., "fire department equipment", "emergency services")
        max_results: Maximum number of results to return (default: 10)
        grants_per_page: Number of grants per page (default: 5)
    
    Returns:
        Formatted string with grant opportunities including titles, funding amounts,
        deadlines, and eligibility information.
    """
    logger.info(f"Searching federal grants: {query}")
    
    # Call the opportunity_discovery tool on Grants-MCP
    result = _call_grants_mcp("tools/call", {
        "name": "opportunity_discovery",
        "arguments": {
            "query": query,
            "max_results": max_results,
            "grants_per_page": grants_per_page
        }
    })
    
    if "error" in result:
        logger.error(f"Federal grant search failed: {result['error']}")
        return f"Error searching grants: {result['error']}"
    
    # Format the response
    try:
        content = result.get("result", {}).get("content", [])
        if not content:
            return "No grant opportunities found for your search query."
        
        # Extract text content from the response
        formatted = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                formatted.append(item.get("text", ""))
            elif isinstance(item, str):
                formatted.append(item)
        
        return "\n".join(formatted) if formatted else "No results parsed from response."
        
    except Exception as e:
        logger.error(f"Parse error: {e}")
        return f"Error parsing grants response: {str(e)}"


def get_agency_landscape(
    focus_agencies: Optional[list] = None,
    funding_category: Optional[str] = None,
    max_agencies: int = 10
) -> str:
    """
    Get an overview of grant-making agencies and their funding focus areas.
    
    Args:
        focus_agencies: Specific agency codes to analyze (e.g., ["FEMA", "DHS"])
        funding_category: Filter by funding category
        max_agencies: Maximum agencies to analyze (default: 10)
    
    Returns:
        Overview of agencies, their missions, and typical funding patterns.
    """
    args = {
        "include_opportunities": True,
        "max_agencies": max_agencies
    }
    if focus_agencies:
        args["focus_agencies"] = focus_agencies
    if funding_category:
        args["funding_category"] = funding_category
    
    result = _call_grants_mcp("tools/call", {
        "name": "agency_landscape",
        "arguments": args
    })
    
    if "error" in result:
        return f"Error getting agency landscape: {result['error']}"
    
    try:
        content = result.get("result", {}).get("content", [])
        formatted = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                formatted.append(item.get("text", ""))
        return "\n".join(formatted) if formatted else "No agency data available."
    except Exception as e:
        return f"Error parsing response: {str(e)}"


def get_funding_trends(
    time_window_days: int = 90,
    category_filter: Optional[str] = None,
    agency_filter: Optional[str] = None,
    min_award_amount: Optional[int] = None
) -> str:
    """
    Analyze funding trends and patterns for grants.
    
    Args:
        time_window_days: Analysis period in days (default: 90)
        category_filter: Filter by funding category
        agency_filter: Filter by agency
        min_award_amount: Minimum award amount filter
    
    Returns:
        Analysis of funding trends, emerging opportunities, and patterns.
    """
    args = {
        "time_window_days": time_window_days,
        "include_forecasted": True
    }
    if category_filter:
        args["category_filter"] = category_filter
    if agency_filter:
        args["agency_filter"] = agency_filter
    if min_award_amount:
        args["min_award_amount"] = min_award_amount
    
    result = _call_grants_mcp("tools/call", {
        "name": "funding_trend_scanner",
        "arguments": args
    })
    
    if "error" in result:
        return f"Error getting funding trends: {result['error']}"
    
    try:
        content = result.get("result", {}).get("content", [])
        formatted = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                formatted.append(item.get("text", ""))
        return "\n".join(formatted) if formatted else "No trend data available."
    except Exception as e:
        return f"Error parsing response: {str(e)}"
