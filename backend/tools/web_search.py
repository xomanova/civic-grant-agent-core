import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ============================================================================
# TOOL: Google Custom Search (Wrapper)
# Required to avoid tool mixing issues with the LLM
# ============================================================================
def search_web(query: str) -> str:
    """
    Search the web for public information about fire departments (population, address, etc).
    Use this when the user does not know a specific detail.
    
    Args:
        query: The search query string (e.g., "Morningslide Fire Department population")
    """
    print(f"[Tool Call] search_web triggered with query: {query}")
    
    try:
        # Get credentials from environment variables
        api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        cse_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        if not api_key or not cse_id:
            print("[Critical] Missing API Key or Search Engine ID in env variables")
            return "Error: Google Search API credentials not configured."

        # Build the Custom Search service
        service = build("customsearch", "v1", developerKey=api_key)
        
        # Create the request
        req = service.cse().list(q=query, cx=cse_id, num=3)
        
        # Add Referer header for API key restrictions
        # Using the backend URL as the referrer
        referer = os.getenv("BACKEND_URL")
        if referer:
            req.headers["Referer"] = referer
        
        # Execute the search
        res = req.execute()
        
        items = res.get('items', [])
        if not items:
            print(f"[Tool Call] Search completed but returned 0 items.")
            return "Search completed, but no relevant results were found."
            
        # Format the results for the LLM
        formatted_results = []
        for item in items:
            title = item.get('title', 'No Title')
            snippet = item.get('snippet', 'No snippet')
            link = item.get('link', 'No link')
            formatted_results.append(f"Title: {title}\nSnippet: {snippet}\nLink: {link}\n---")
            
        result_str = "\n".join(formatted_results)
        print(f"[Tool Call] Returning {len(formatted_results)} results.")
        return result_str

    except HttpError as e:
        error_msg = f"Google Search API Error: {e}"
        print(f"[Tool Call Error] {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected Search Error: {str(e)}"
        print(f"[Tool Call Critical Error] {error_msg}")
        return error_msg
