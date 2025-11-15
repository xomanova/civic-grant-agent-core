# Getting Started

This guide will help you set up and run the Civic Grant Agent Core system.

## Prerequisites

Before you begin, ensure you have the following:

### System Requirements

- **Operating System**: Linux, macOS, or Windows with WSL
- **Memory**: At least 4GB RAM (8GB recommended)
- **Storage**: 2GB free disk space
- **Internet Connection**: Required for API access

### Software Dependencies

- **Python**: Version 3.9 or higher
- **pip**: Python package installer
- **Git**: For version control
- **API Keys**: 
  - Google Search API key
  - Gemini API key (Google AI)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/xomanova/civic-grant-agent-core.git
cd civic-grant-agent-core
```

### 2. Set Up Python Environment

Create and activate a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
GOOGLE_SEARCH_API_KEY=your_google_search_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
GEMINI_API_KEY=your_gemini_api_key_here
```

#### Obtaining API Keys

**Google Search API**:
1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Custom Search API
4. Create credentials (API key)
5. Set up a Custom Search Engine at [Programmable Search Engine](https://programmablesearchengine.google.com/)

**Gemini API**:
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Copy the key to your `.env` file

## Configuration

### Create Department Profile

Create a configuration file for your department:

```bash
cp config/department_profile.example.json config/my_department.json
```

Edit `config/my_department.json`:

```json
{
  "department_name": "Smallville Volunteer Fire Department",
  "department_type": "volunteer",
  "location": {
    "city": "Smallville",
    "state": "KS",
    "county": "Ford County",
    "population": 15000
  },
  "needs": [
    "SCBA equipment",
    "Fire truck replacement",
    "Training facility improvements"
  ],
  "mission": "To protect life and property through fire prevention, education, and emergency response services to the Smallville community.",
  "budget": {
    "annual_budget": 250000,
    "can_provide_match": true,
    "max_match_percentage": 10
  },
  "contact": {
    "name": "John Smith",
    "title": "Fire Chief",
    "email": "chief@smallvillefd.org",
    "phone": "(555) 123-4567"
  },
  "organization_details": {
    "founded_year": 1952,
    "staff_count": 5,
    "volunteer_count": 35,
    "service_area_sq_miles": 120,
    "annual_calls": 450
  }
}
```

## Running the System

### Basic Usage

Run the complete agent pipeline:

```bash
python main.py --config config/my_department.json
```

### Run Individual Agents

Run only specific agents:

```bash
# GrantScout only
python main.py --config config/my_department.json --agent scout

# GrantValidator only (requires scout results)
python main.py --config config/my_department.json --agent validator

# GrantWriter only (requires validator results)
python main.py --config config/my_department.json --agent writer
```

### Advanced Options

```bash
# Set output directory
python main.py --config config/my_department.json --output ./results

# Increase verbosity
python main.py --config config/my_department.json --verbose

# Limit number of grants to process
python main.py --config config/my_department.json --max-grants 5

# Dry run (no API calls)
python main.py --config config/my_department.json --dry-run
```

## Output Files

The system generates several output files:

```
output/
├── scout_results.json          # URLs from GrantScout
├── validated_grants.json       # Validated and prioritized grants
├── draft_applications/         # Generated grant application drafts
│   ├── grant_001_draft.md
│   ├── grant_002_draft.md
│   └── ...
└── logs/
    ├── agent_scout.log
    ├── agent_validator.log
    └── agent_writer.log
```

## Verifying Installation

Run the test suite to verify installation:

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/test_scout.py
pytest tests/test_validator.py
pytest tests/test_writer.py

# Run with coverage report
pytest --cov=src tests/
```

## Common Issues

### API Key Errors

**Problem**: `Error: Invalid API key`

**Solution**: 
- Verify API keys in `.env` file
- Ensure no extra spaces or quotes
- Check that APIs are enabled in Google Cloud Console

### Import Errors

**Problem**: `ModuleNotFoundError`

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Rate Limiting

**Problem**: `Error: API rate limit exceeded`

**Solution**:
- Wait before retrying
- Reduce `max_results_per_query` in configuration
- Implement delays between requests
- Consider upgrading API quota

## Next Steps

- Review the [Configuration Guide](Configuration.md) for advanced settings
- Read the [Agent Documentation](Agents.md) to understand each agent
- Check the [Development Guide](Development.md) if you want to contribute
- See [Troubleshooting Guide](Troubleshooting.md) for common problems

## Quick Start Example

Complete workflow from installation to first run:

```bash
# 1. Clone and enter directory
git clone https://github.com/xomanova/civic-grant-agent-core.git
cd civic-grant-agent-core

# 2. Set up environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env with your API keys

# 4. Create department profile
cp config/department_profile.example.json config/my_department.json
# Edit my_department.json with your information

# 5. Run the system
python main.py --config config/my_department.json

# 6. Check results
ls output/draft_applications/
```

## Support

If you encounter issues:

1. Check the [FAQ](FAQ.md)
2. Review [Troubleshooting Guide](Troubleshooting.md)
3. Search existing GitHub issues
4. Open a new issue with detailed information

## What's Next?

After successfully running the system:

1. **Review Generated Drafts**: Check `output/draft_applications/`
2. **Refine Department Profile**: Adjust configuration for better results
3. **Customize Agents**: Modify agent behavior in configuration files
4. **Set Up Automation**: Schedule regular grant searches
5. **Contribute**: Share improvements back to the project
