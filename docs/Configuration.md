# Configuration Guide

This guide covers all configuration options for the Civic Grant Agent Core system.

## Configuration Files Overview

The system uses several configuration files:

```
config/
├── department_profile.json      # Your department information
├── agent_config.json           # Agent behavior settings
├── api_config.json             # API endpoints and settings
└── output_config.json          # Output formatting preferences
```

## Department Profile Configuration

### Basic Information

```json
{
  "department_name": "Your Department Name",
  "department_type": "volunteer|paid|combination",
  "location": {
    "city": "City Name",
    "state": "State Code (2 letters)",
    "county": "County Name",
    "zip_code": "12345",
    "population": 50000
  }
}
```

**Fields**:
- `department_name`: Official name of your department
- `department_type`: Type of department (affects eligibility for certain grants)
  - `volunteer`: All volunteer firefighters
  - `paid`: Full-time paid firefighters
  - `combination`: Mix of volunteer and paid
- `location`: Geographic information (required for location-based grants)

### Needs and Requirements

```json
{
  "needs": [
    "SCBA equipment",
    "Fire truck",
    "Training materials",
    "Station improvements"
  ],
  "priority_needs": [
    "SCBA equipment",
    "Fire truck"
  ],
  "equipment_list": {
    "current": ["Engine 1 (2005)", "Tanker 2 (1998)"],
    "needed": ["New pumper truck", "Rescue equipment"]
  }
}
```

**Fields**:
- `needs`: List of all equipment, training, or facility needs
- `priority_needs`: Most critical needs (prioritized in grant matching)
- `equipment_list`: Current inventory and needed items

### Budget Information

```json
{
  "budget": {
    "annual_budget": 250000,
    "grant_budget": 50000,
    "can_provide_match": true,
    "max_match_percentage": 10,
    "max_match_amount": 25000
  }
}
```

**Fields**:
- `annual_budget`: Total annual operating budget
- `grant_budget`: Amount available for grant-funded projects
- `can_provide_match`: Whether department can provide matching funds
- `max_match_percentage`: Maximum match as percentage of grant
- `max_match_amount`: Maximum absolute dollar amount for match

### Organization Details

```json
{
  "organization_details": {
    "founded_year": 1952,
    "staff_count": 5,
    "volunteer_count": 35,
    "service_area_sq_miles": 120,
    "annual_calls": 450,
    "certifications": ["ISO Class 4", "State Certified"],
    "affiliations": ["State Firefighters Association"]
  }
}
```

### Mission and Background

```json
{
  "mission": "Your department's mission statement...",
  "background": "Brief history of your department...",
  "community_impact": "Description of your community service..."
}
```

### Contact Information

```json
{
  "contact": {
    "name": "Chief Name",
    "title": "Fire Chief",
    "email": "chief@department.org",
    "phone": "(555) 123-4567",
    "address": "123 Main St, City, State 12345"
  }
}
```

## Agent Configuration

### GrantScout Settings

```json
{
  "scout": {
    "max_results_per_query": 10,
    "relevance_threshold": 0.6,
    "search_domains": {
      "whitelist": ["*.gov", "*.org"],
      "blacklist": ["example-scam.com"]
    },
    "search_strategies": [
      "need_based",
      "location_based",
      "equipment_specific",
      "federal_programs"
    ],
    "cache_results": true,
    "cache_ttl_hours": 24
  }
}
```

**Options**:
- `max_results_per_query`: Maximum URLs per search query (1-50)
- `relevance_threshold`: Minimum relevance score (0.0-1.0)
- `search_domains`: Control which domains to include/exclude
- `search_strategies`: Which search approaches to use
- `cache_results`: Cache search results to avoid redundant API calls
- `cache_ttl_hours`: How long to keep cached results

### GrantValidator Settings

```json
{
  "validator": {
    "eligibility_threshold": 70,
    "priority_cutoff": 5,
    "deadline_buffer_days": 30,
    "document_timeout_seconds": 60,
    "parse_pdfs": true,
    "max_pdf_pages": 50,
    "scoring_weights": {
      "eligibility": 0.4,
      "match": 0.3,
      "feasibility": 0.3
    },
    "auto_exclude": {
      "past_deadline": true,
      "insufficient_time": true,
      "clearly_ineligible": true
    }
  }
}
```

**Options**:
- `eligibility_threshold`: Minimum score to be considered "eligible" (0-100)
- `priority_cutoff`: Number of top grants to recommend
- `deadline_buffer_days`: Minimum days before deadline to consider
- `document_timeout_seconds`: Max time to parse each document
- `parse_pdfs`: Whether to parse PDF documents
- `max_pdf_pages`: Maximum PDF pages to parse
- `scoring_weights`: How to weight different score components
- `auto_exclude`: Automatic exclusion criteria

### GrantWriter Settings

```json
{
  "writer": {
    "llm_model": "gemini-pro",
    "temperature": 0.7,
    "max_tokens_per_section": 1000,
    "writing_style": "formal",
    "detail_level": "comprehensive",
    "include_examples": true,
    "include_statistics": true,
    "budget_detail": "itemized",
    "format": "markdown",
    "sections": [
      "executive_summary",
      "organization_background",
      "need_statement",
      "project_description",
      "goals_objectives",
      "methods",
      "evaluation",
      "budget_narrative",
      "sustainability"
    ]
  }
}
```

**Options**:
- `llm_model`: Which Gemini model to use
- `temperature`: Creativity level (0.0-1.0, higher = more creative)
- `max_tokens_per_section`: Token limit per section
- `writing_style`: `formal`, `conversational`, or `technical`
- `detail_level`: `concise`, `standard`, or `comprehensive`
- `include_examples`: Include case studies and examples
- `include_statistics`: Include relevant statistics
- `budget_detail`: `summary` or `itemized`
- `format`: Output format (`markdown`, `docx`, `pdf`)
- `sections`: Which sections to include in draft

## API Configuration

### Google Search API

```json
{
  "google_search": {
    "api_key": "env:GOOGLE_SEARCH_API_KEY",
    "search_engine_id": "env:GOOGLE_SEARCH_ENGINE_ID",
    "rate_limit": {
      "requests_per_day": 100,
      "requests_per_minute": 10
    },
    "retry": {
      "max_attempts": 3,
      "backoff_factor": 2
    }
  }
}
```

### Gemini API

```json
{
  "gemini": {
    "api_key": "env:GEMINI_API_KEY",
    "model": "gemini-pro",
    "rate_limit": {
      "requests_per_minute": 60
    },
    "retry": {
      "max_attempts": 3,
      "backoff_factor": 2
    },
    "safety_settings": {
      "harassment": "BLOCK_NONE",
      "hate_speech": "BLOCK_NONE",
      "sexually_explicit": "BLOCK_NONE",
      "dangerous_content": "BLOCK_NONE"
    }
  }
}
```

## Output Configuration

### File Paths and Naming

```json
{
  "output": {
    "base_directory": "./output",
    "subdirectories": {
      "scout_results": "scout",
      "validated_grants": "validated",
      "draft_applications": "drafts",
      "logs": "logs"
    },
    "filename_patterns": {
      "scout_results": "scout_results_{timestamp}.json",
      "validated_grants": "validated_grants_{timestamp}.json",
      "draft": "draft_{grant_id}_{timestamp}.md"
    },
    "timestamp_format": "%Y%m%d_%H%M%S"
  }
}
```

### Logging Configuration

```json
{
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": {
      "console": {
        "enabled": true,
        "level": "INFO"
      },
      "file": {
        "enabled": true,
        "level": "DEBUG",
        "filename": "output/logs/agent.log",
        "max_bytes": 10485760,
        "backup_count": 5
      }
    }
  }
}
```

## Environment Variables

Create a `.env` file with the following variables:

```bash
# API Keys
GOOGLE_SEARCH_API_KEY=your_google_search_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
GEMINI_API_KEY=your_gemini_api_key

# Optional: Override default settings
OUTPUT_DIR=./custom_output
LOG_LEVEL=DEBUG
CACHE_DIR=./cache

# Optional: Proxy settings (if needed)
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080
```

## Advanced Configuration

### Custom Search Queries

Create custom search query templates:

```json
{
  "custom_search_queries": [
    "{department_type} fire department {need} grants {state}",
    "emergency services funding {need} {county}",
    "{need} grants fire department population {population_range}"
  ]
}
```

### Eligibility Rules

Define custom eligibility rules:

```json
{
  "custom_eligibility_rules": [
    {
      "name": "population_check",
      "condition": "grant.max_population >= department.location.population",
      "message": "Population exceeds maximum allowed"
    },
    {
      "name": "budget_check",
      "condition": "department.budget.annual_budget >= grant.min_budget",
      "message": "Department budget below minimum requirement"
    }
  ]
}
```

### Writing Templates

Customize writing templates:

```json
{
  "writing_templates": {
    "executive_summary": "Template for executive summary...",
    "need_statement": "Template for need statement..."
  }
}
```

## Configuration Best Practices

1. **Start Simple**: Use default configuration initially
2. **Incremental Changes**: Adjust one setting at a time
3. **Test Configuration**: Use `--dry-run` flag to test without API calls
4. **Version Control**: Keep configuration files in version control
5. **Sensitive Data**: Never commit API keys (use `.env` file)
6. **Documentation**: Comment your configuration changes
7. **Backup**: Keep backup of working configurations

## Configuration Validation

Validate your configuration:

```bash
python main.py --validate-config config/my_department.json
```

This checks:
- Required fields are present
- Values are within valid ranges
- API keys are accessible
- File paths exist

## Loading Configuration in Code

```python
from src.config import load_config

# Load all configurations
config = load_config(
    department_profile="config/my_department.json",
    agent_config="config/agent_config.json",
    api_config="config/api_config.json"
)

# Access configuration values
scout_settings = config.agents.scout
max_results = scout_settings.max_results_per_query
```

## Configuration Profiles

Create profiles for different scenarios:

```bash
config/
├── profiles/
│   ├── small_volunteer_dept.json
│   ├── large_paid_dept.json
│   ├── rural_combination_dept.json
│   └── urban_department.json
```

Use profiles:

```bash
python main.py --profile config/profiles/small_volunteer_dept.json
```

## Troubleshooting Configuration

### Invalid Configuration Error

Check for:
- JSON syntax errors
- Missing required fields
- Invalid value types
- Out-of-range values

### API Connection Issues

Verify:
- API keys are correct
- APIs are enabled
- Network connectivity
- Proxy settings (if applicable)

### Performance Issues

Adjust:
- Reduce `max_results_per_query`
- Increase `cache_ttl_hours`
- Set lower `document_timeout_seconds`
- Disable PDF parsing if not needed
