# API Reference

Complete API reference for the Civic Grant Agent Core system.

## Agent APIs

### BaseAgent

Base class for all agents.

```python
class BaseAgent:
    """Base class for all agents in the system."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the agent.
        
        Args:
            config: Configuration dictionary
        """
        
    def run(self, input_data: Dict[str, Any], shared_memory: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's main task.
        
        Args:
            input_data: Input data for processing
            shared_memory: Shared session context
            
        Returns:
            Dictionary with results and metadata
            
        Raises:
            AgentException: If agent execution fails
        """
```

### GrantScout

Agent for discovering grant opportunities.

```python
class GrantScout(BaseAgent):
    """Agent for discovering relevant grant opportunities."""
    
    def run(self, department_profile: Dict, shared_memory: Dict) -> Dict:
        """Search for grant opportunities.
        
        Args:
            department_profile: Department configuration
            shared_memory: Shared session memory
            
        Returns:
            {
                "urls": List[str],
                "metadata": Dict,
                "timestamp": str
            }
        """
    
    def generate_queries(self, profile: Dict) -> List[str]:
        """Generate search queries based on department profile.
        
        Args:
            profile: Department profile dictionary
            
        Returns:
            List of search query strings
        """
    
    def search(self, query: str) -> List[Dict]:
        """Execute a single search query.
        
        Args:
            query: Search query string
            
        Returns:
            List of search result dictionaries
        """
```

### GrantValidator

Agent for validating grant eligibility.

```python
class GrantValidator(BaseAgent):
    """Agent for validating grant eligibility."""
    
    def run(self, scout_results: Dict, shared_memory: Dict) -> Dict:
        """Validate grants from scout results.
        
        Args:
            scout_results: Output from GrantScout
            shared_memory: Shared session memory
            
        Returns:
            {
                "validated_grants": List[Dict],
                "validation_summary": Dict
            }
        """
    
    def validate_grant(self, grant_url: str, profile: Dict) -> Dict:
        """Validate a single grant.
        
        Args:
            grant_url: URL of grant to validate
            profile: Department profile
            
        Returns:
            Grant validation results
        """
    
    def calculate_scores(self, grant: Dict, profile: Dict) -> Dict:
        """Calculate eligibility and priority scores.
        
        Args:
            grant: Grant information dictionary
            profile: Department profile
            
        Returns:
            Dictionary of scores
        """
```

### GrantWriter

Agent for generating grant application drafts.

```python
class GrantWriter(BaseAgent):
    """Agent for generating grant application drafts."""
    
    def run(self, validated_grants: Dict, shared_memory: Dict) -> Dict:
        """Generate draft applications.
        
        Args:
            validated_grants: Output from GrantValidator
            shared_memory: Shared session memory
            
        Returns:
            {
                "drafts": List[Dict],
                "draft_files": List[str]
            }
        """
    
    def generate_draft(self, grant: Dict, profile: Dict) -> str:
        """Generate a single draft application.
        
        Args:
            grant: Grant information
            profile: Department profile
            
        Returns:
            Draft application as markdown string
        """
    
    def generate_section(self, section: str, context: Dict) -> str:
        """Generate a specific section of the application.
        
        Args:
            section: Section name
            context: Context dictionary
            
        Returns:
            Generated section text
        """
```

## Tool APIs

### SearchTool

Google Search integration.

```python
class SearchTool:
    """Tool for executing web searches."""
    
    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Execute a search query.
        
        Args:
            query: Search query string
            num_results: Maximum results to return
            
        Returns:
            List of search result dictionaries:
            {
                "url": str,
                "title": str,
                "snippet": str
            }
            
        Raises:
            SearchException: If search fails
        """
```

### EligibilityChecker

Tool for checking grant eligibility.

```python
class EligibilityChecker:
    """Tool for checking grant eligibility."""
    
    def check_eligibility(self, grant: Dict, profile: Dict) -> Dict:
        """Check if department is eligible for grant.
        
        Args:
            grant: Grant information dictionary
            profile: Department profile dictionary
            
        Returns:
            {
                "eligible": bool,
                "score": float,
                "checks": Dict[str, str],
                "reasons": List[str]
            }
        """
    
    def extract_requirements(self, grant_url: str) -> Dict:
        """Extract requirements from grant documentation.
        
        Args:
            grant_url: URL of grant page
            
        Returns:
            Dictionary of extracted requirements
        """
```

### DocumentParser

Tool for parsing grant documents.

```python
class DocumentParser:
    """Tool for parsing various document formats."""
    
    def parse(self, url: str, doc_type: str = "auto") -> Dict:
        """Parse a document.
        
        Args:
            url: URL or path to document
            doc_type: Document type (html, pdf, docx, auto)
            
        Returns:
            {
                "text": str,
                "metadata": Dict,
                "sections": List[Dict]
            }
        """
    
    def parse_pdf(self, url: str) -> str:
        """Parse PDF document.
        
        Args:
            url: URL or path to PDF
            
        Returns:
            Extracted text content
        """
    
    def parse_html(self, url: str) -> str:
        """Parse HTML page.
        
        Args:
            url: URL of HTML page
            
        Returns:
            Extracted text content
        """
```

## Data Models

### DepartmentProfile

```python
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Location:
    city: str
    state: str
    county: str
    zip_code: str = ""
    population: int = 0

@dataclass
class Budget:
    annual_budget: float
    grant_budget: float
    can_provide_match: bool
    max_match_percentage: float
    max_match_amount: float

@dataclass
class Contact:
    name: str
    title: str
    email: str
    phone: str
    address: str = ""

@dataclass
class DepartmentProfile:
    name: str
    department_type: str
    location: Location
    needs: List[str]
    mission: str
    budget: Budget
    contact: Contact
    priority_needs: List[str] = None
    equipment_list: Dict = None
    organization_details: Dict = None
```

### Grant

```python
@dataclass
class Grant:
    grant_id: str
    url: str
    title: str
    amount_range: str
    deadline: str
    description: str = ""
    eligibility_score: float = 0.0
    match_score: float = 0.0
    feasibility_score: float = 0.0
    priority_score: float = 0.0
    eligible: bool = False
    requirements: List[str] = None
    eligibility_details: Dict = None
    flags: List[str] = None
```

### Application

```python
@dataclass
class Application:
    grant: Grant
    department: DepartmentProfile
    content: str
    sections: Dict[str, str]
    created_at: str
    status: str = "draft"
```

## Configuration Schema

### Department Profile Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["department_name", "department_type", "location", "needs"],
  "properties": {
    "department_name": {"type": "string"},
    "department_type": {
      "type": "string",
      "enum": ["volunteer", "paid", "combination"]
    },
    "location": {
      "type": "object",
      "required": ["city", "state"],
      "properties": {
        "city": {"type": "string"},
        "state": {"type": "string", "pattern": "^[A-Z]{2}$"},
        "county": {"type": "string"},
        "population": {"type": "integer", "minimum": 0}
      }
    },
    "needs": {
      "type": "array",
      "items": {"type": "string"},
      "minItems": 1
    }
  }
}
```

## CLI Interface

### Main Command

```bash
python main.py [OPTIONS]
```

**Options:**

- `--config PATH` - Path to department profile config (required)
- `--agent NAME` - Run specific agent only (scout, validator, writer)
- `--output DIR` - Output directory for results
- `--verbose` - Enable verbose logging
- `--dry-run` - Run without API calls
- `--max-grants N` - Maximum grants to process
- `--validate-config` - Validate configuration only

### Examples

```bash
# Run complete pipeline
python main.py --config config/dept.json

# Run only GrantScout
python main.py --config config/dept.json --agent scout

# Dry run for testing
python main.py --config config/dept.json --dry-run

# Verbose output
python main.py --config config/dept.json --verbose

# Limit processing
python main.py --config config/dept.json --max-grants 5
```

## Error Codes

| Code | Name | Description |
|------|------|-------------|
| 1000 | ConfigurationError | Invalid configuration |
| 1001 | MissingAPIKey | Required API key not found |
| 2000 | SearchError | Search API failure |
| 2001 | RateLimitError | API rate limit exceeded |
| 3000 | ValidationError | Grant validation failed |
| 3001 | ParsingError | Document parsing failed |
| 4000 | GenerationError | Draft generation failed |
| 5000 | UnknownError | Unexpected error |

## Exception Classes

```python
class AgentException(Exception):
    """Base exception for all agents."""
    pass

class ConfigurationError(AgentException):
    """Raised when configuration is invalid."""
    pass

class SearchException(AgentException):
    """Raised when search operation fails."""
    pass

class ValidationException(AgentException):
    """Raised when validation fails."""
    pass

class GenerationException(AgentException):
    """Raised when draft generation fails."""
    pass
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| GOOGLE_SEARCH_API_KEY | Yes | Google Search API key |
| GOOGLE_SEARCH_ENGINE_ID | Yes | Custom Search Engine ID |
| GEMINI_API_KEY | Yes | Gemini API key |
| OUTPUT_DIR | No | Default output directory |
| LOG_LEVEL | No | Logging level (DEBUG, INFO, WARNING, ERROR) |
| CACHE_DIR | No | Cache directory path |
| HTTP_PROXY | No | HTTP proxy URL |
| HTTPS_PROXY | No | HTTPS proxy URL |

## Response Formats

### GrantScout Response

```json
{
  "status": "success",
  "search_results": [
    {
      "url": "https://example.gov/grant",
      "title": "Fire Equipment Grant 2024",
      "snippet": "Grant for fire departments...",
      "relevance_score": 0.85,
      "source": "government"
    }
  ],
  "metadata": {
    "queries_executed": 5,
    "total_results": 47,
    "filtered_results": 12,
    "execution_time_seconds": 3.42,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### GrantValidator Response

```json
{
  "status": "success",
  "validated_grants": [
    {
      "grant_id": "AFG-2024-001",
      "url": "https://example.gov/grant",
      "title": "Assistance to Firefighters Grant",
      "amount_range": "$50,000 - $500,000",
      "deadline": "2024-03-15",
      "eligible": true,
      "eligibility_score": 95,
      "match_score": 88,
      "feasibility_score": 92,
      "priority_score": 91.67,
      "eligibility_details": {
        "geographic": "PASS",
        "organization_type": "PASS",
        "size_requirements": "PASS",
        "need_matching": "PASS"
      },
      "requirements": [
        "501(c)(3) status or government entity",
        "10% cost share required"
      ],
      "flags": ["Cost share required"]
    }
  ],
  "validation_summary": {
    "total_validated": 12,
    "eligible": 8,
    "ineligible": 4,
    "high_priority": 3,
    "execution_time_seconds": 45.2
  }
}
```

### GrantWriter Response

```json
{
  "status": "success",
  "drafts": [
    {
      "grant_id": "AFG-2024-001",
      "filename": "draft_AFG-2024-001_20240115.md",
      "sections_generated": [
        "executive_summary",
        "organization_background",
        "need_statement",
        "project_description"
      ],
      "word_count": 2450,
      "character_count": 14500
    }
  ],
  "metadata": {
    "drafts_generated": 3,
    "execution_time_seconds": 120.5
  }
}
```

## Rate Limits

### Google Search API

- **Default**: 100 queries per day
- **Paid**: Up to 10,000 queries per day
- **Rate**: 10 queries per second maximum

### Gemini API

- **Free Tier**: 60 requests per minute
- **Paid**: Higher limits based on plan

## Best Practices

1. **Error Handling**: Always handle API errors gracefully
2. **Rate Limiting**: Implement exponential backoff
3. **Caching**: Cache results to minimize API calls
4. **Validation**: Validate all inputs before processing
5. **Logging**: Log all important operations
6. **Testing**: Test with various configurations

## Version Information

- **API Version**: 1.0
- **Python Compatibility**: 3.9+
- **Last Updated**: 2024-01-15
