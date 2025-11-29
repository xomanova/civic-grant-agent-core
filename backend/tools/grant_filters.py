"""
Grant Filtering Logic - Pure utility functions for filtering and validating grants
No ADK dependencies - these are pure Python functions
"""

# US States list for filtering state-specific grants
US_STATES = [
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york", "north carolina",
    "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania",
    "rhode island", "south carolina", "south dakota", "tennessee", "texas",
    "utah", "vermont", "virginia", "washington", "west virginia",
    "wisconsin", "wyoming"
]

# State abbreviation to full name mapping for URL detection
STATE_ABBREVIATIONS = {
    "ohio": "ohio", "texas": "tx", "california": "ca", "florida": "fl",
    "new york": "ny", "north carolina": "nc", "georgia": "ga",
    "pennsylvania": "pa", "illinois": "il", "michigan": "mi",
    "virginia": "va", "washington": "wa", "arizona": "az",
    "massachusetts": "ma", "tennessee": "tn", "indiana": "in",
    "missouri": "mo", "maryland": "md", "wisconsin": "wi",
    "colorado": "co", "minnesota": "mn", "south carolina": "sc",
    "alabama": "al", "louisiana": "la", "kentucky": "ky",
    "oregon": "or", "oklahoma": "ok", "connecticut": "ct",
    "iowa": "ia", "utah": "ut", "nevada": "nv", "arkansas": "ar",
    "mississippi": "ms", "kansas": "ks", "new mexico": "nm",
    "nebraska": "ne", "west virginia": "wv", "idaho": "id",
    "hawaii": "hi", "new hampshire": "nh", "maine": "me",
    "montana": "mt", "rhode island": "ri", "delaware": "de",
    "south dakota": "sd", "north dakota": "nd", "alaska": "ak",
    "vermont": "vt", "wyoming": "wy"
}


def is_federal_grant(grant_name: str, grant_source: str, grant_desc: str) -> bool:
    """Check if a grant is federal (available nationwide)."""
    text = f"{grant_name} {grant_source} {grant_desc}".lower()
    federal_indicators = ["federal", "fema", "national", "nationwide", "u.s.", "united states", "usda", "dhs"]
    return any(indicator in text for indicator in federal_indicators)


def is_national_foundation_grant(grant_name: str, grant_source: str) -> bool:
    """Check if a grant is from a national foundation (available nationwide)."""
    text = f"{grant_name} {grant_source}".lower()
    # Known national foundations that serve all states
    national_foundations = [
        "firehouse subs", "gary sinise", "leary firefighters", "spirit of blue",
        "100 club", "nfff", "national fallen firefighters", "iafc", "nvfc",
        "foundation", "national volunteer"  # generic foundation indicator
    ]
    return any(foundation in text for foundation in national_foundations)


def get_grant_states(grant_name: str, grant_source: str, grant_url: str = "") -> list:
    """Extract state names from grant name, source, or URL."""
    text = f"{grant_name} {grant_source}".lower()
    found_states = []
    
    # Check name and source for state names
    for state in US_STATES:
        if state in text:
            found_states.append(state)
    
    # Also check URL for state abbreviations or domains
    # e.g., ohio.gov, nc.gov, state.tx.us, etc.
    if grant_url:
        url_lower = grant_url.lower()
        
        for state_name, abbrev in STATE_ABBREVIATIONS.items():
            # Check for patterns like "ohio.gov", ".oh.us", "state.oh."
            if f"{state_name}.gov" in url_lower or f".{abbrev}.gov" in url_lower or f".{abbrev}.us" in url_lower:
                if state_name not in found_states:
                    found_states.append(state_name)
    
    return found_states


def filter_grants_by_state(grants: list, department_state: str) -> list:
    """
    Filter out grants that are specific to other states.
    
    Args:
        grants: List of grant objects
        department_state: The state where the department is located (lowercase)
    
    Returns:
        Filtered list of grants that are either federal or match the department's state
    """
    if not department_state:
        return grants
    
    dept_state_lower = department_state.lower()
    filtered_grants = []
    
    for grant in grants:
        grant_name = grant.get("name", "")
        grant_source = grant.get("source", "")
        grant_desc = grant.get("description", "")
        grant_url = grant.get("url", "")
        
        # Always include federal grants
        if is_federal_grant(grant_name, grant_source, grant_desc):
            filtered_grants.append(grant)
            continue
        
        # Always include national foundation grants
        if is_national_foundation_grant(grant_name, grant_source):
            filtered_grants.append(grant)
            continue
        
        # Check if grant is state-specific (check name, source, AND URL)
        grant_states = get_grant_states(grant_name, grant_source, grant_url)
        
        if grant_states:
            # If multiple states detected (e.g., "NC" in name but "ohio.gov" in URL),
            # this is likely a data error - be conservative and check if ANY state matches
            # But if URL indicates a different state than name, trust the URL more
            url_states = get_grant_states("", "", grant_url)
            name_states = get_grant_states(grant_name, grant_source, "")
            
            # If URL indicates a state that conflicts with name, it's probably bad data
            if url_states and name_states and not any(s in url_states for s in name_states):
                continue
            
            # Grant is state-specific - only include if department is in that state
            if dept_state_lower in grant_states:
                filtered_grants.append(grant)
        else:
            # No state in grant name/source - assume it's broadly available
            filtered_grants.append(grant)
    
    return filtered_grants
