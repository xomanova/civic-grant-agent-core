# Development Guide

This guide is for developers who want to contribute to or extend the Civic Grant Agent Core project.

## Development Setup

### Initial Setup

1. **Fork and Clone**

```bash
git clone https://github.com/YOUR_USERNAME/civic-grant-agent-core.git
cd civic-grant-agent-core
git remote add upstream https://github.com/xomanova/civic-grant-agent-core.git
```

2. **Create Development Environment**

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

3. **Install Pre-commit Hooks**

```bash
pre-commit install
```

### Development Dependencies

The `requirements-dev.txt` includes:

- **pytest**: Testing framework
- **pytest-cov**: Code coverage
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking
- **pre-commit**: Git hooks
- **sphinx**: Documentation generation

## Project Structure

```
civic-grant-agent-core/
├── src/                        # Source code
│   ├── agents/                 # Agent implementations
│   │   ├── __init__.py
│   │   ├── base_agent.py      # Base agent class
│   │   ├── scout.py           # GrantScout agent
│   │   ├── validator.py       # GrantValidator agent
│   │   └── writer.py          # GrantWriter agent
│   ├── tools/                  # Agent tools
│   │   ├── __init__.py
│   │   ├── search_tool.py     # Google Search integration
│   │   ├── eligibility_checker.py
│   │   └── document_parser.py
│   ├── models/                 # Data models
│   │   ├── __init__.py
│   │   ├── department.py      # Department profile model
│   │   ├── grant.py           # Grant data model
│   │   └── application.py     # Application draft model
│   ├── config/                 # Configuration handling
│   │   ├── __init__.py
│   │   └── loader.py
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── logging.py
│       └── validators.py
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test fixtures
├── config/                     # Configuration files
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
├── main.py                     # Entry point
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── setup.py                    # Package setup
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore rules
├── .pre-commit-config.yaml     # Pre-commit configuration
└── README.md                   # Project README
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

- **Line Length**: Maximum 100 characters (not 79)
- **Quotes**: Use double quotes for strings
- **Imports**: Organized with `isort`
- **Formatting**: Automated with `black`

### Type Hints

Use type hints for all functions:

```python
from typing import List, Dict, Optional

def process_grants(grants: List[Dict], threshold: float = 0.7) -> List[Dict]:
    """Process grants with threshold filtering.
    
    Args:
        grants: List of grant dictionaries
        threshold: Minimum score threshold
        
    Returns:
        Filtered list of grants
    """
    return [g for g in grants if g.get("score", 0) >= threshold]
```

### Documentation

Use Google-style docstrings:

```python
def calculate_score(eligibility: float, match: float, feasibility: float) -> float:
    """Calculate composite grant score.
    
    Args:
        eligibility: Eligibility score (0-100)
        match: Match score (0-100)
        feasibility: Feasibility score (0-100)
        
    Returns:
        Composite score (0-100)
        
    Raises:
        ValueError: If any score is outside 0-100 range
        
    Example:
        >>> calculate_score(90, 80, 85)
        85.0
    """
    if not all(0 <= s <= 100 for s in [eligibility, match, feasibility]):
        raise ValueError("All scores must be between 0 and 100")
    return (eligibility + match + feasibility) / 3
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_scout.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run with verbose output
pytest -v

# Run specific test
pytest tests/unit/test_scout.py::test_search_query_generation
```

### Writing Tests

#### Unit Tests

```python
import pytest
from src.agents.scout import GrantScout

class TestGrantScout:
    @pytest.fixture
    def scout(self):
        """Create GrantScout instance for testing."""
        return GrantScout(config={"max_results": 10})
    
    def test_initialization(self, scout):
        """Test GrantScout initializes correctly."""
        assert scout is not None
        assert scout.config["max_results"] == 10
    
    def test_query_generation(self, scout):
        """Test search query generation."""
        department = {"name": "Test FD", "needs": ["SCBA"]}
        queries = scout.generate_queries(department)
        assert len(queries) > 0
        assert any("SCBA" in q for q in queries)
```

#### Integration Tests

```python
import pytest
from src.agents.scout import GrantScout
from src.agents.validator import GrantValidator

@pytest.mark.integration
class TestAgentPipeline:
    def test_scout_to_validator(self, department_profile):
        """Test data flow from Scout to Validator."""
        scout = GrantScout()
        validator = GrantValidator()
        
        # Scout finds grants
        scout_results = scout.run(department_profile)
        assert len(scout_results["urls"]) > 0
        
        # Validator processes results
        validated = validator.run(scout_results, department_profile)
        assert "validated_grants" in validated
```

#### Test Fixtures

```python
# tests/fixtures/department_profiles.py
import pytest

@pytest.fixture
def basic_department():
    """Basic department profile for testing."""
    return {
        "name": "Test Fire Department",
        "type": "volunteer",
        "location": {"city": "Testville", "state": "TS"},
        "needs": ["SCBA equipment", "Training"]
    }

@pytest.fixture
def mock_api_response():
    """Mock API response for testing."""
    return {
        "items": [
            {
                "link": "https://example.gov/grant",
                "title": "Test Grant",
                "snippet": "Grant for fire departments..."
            }
        ]
    }
```

### Mocking External APIs

```python
from unittest.mock import Mock, patch

def test_search_with_mock():
    """Test search with mocked API."""
    with patch("src.tools.search_tool.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {
            "items": [{"link": "test.com", "title": "Test"}]
        }
        
        scout = GrantScout()
        results = scout.search("test query")
        
        assert len(results) == 1
        mock_get.assert_called_once()
```

## Code Quality

### Linting

```bash
# Run flake8
flake8 src/ tests/

# Run with specific rules
flake8 --max-line-length=100 src/

# Check specific file
flake8 src/agents/scout.py
```

### Type Checking

```bash
# Run mypy on source code
mypy src/

# Run with strict mode
mypy --strict src/

# Check specific file
mypy src/agents/scout.py
```

### Code Formatting

```bash
# Format with black
black src/ tests/

# Check without modifying
black --check src/ tests/

# Format specific file
black src/agents/scout.py
```

### Pre-commit Hooks

The pre-commit hooks automatically run:

- `black` - Code formatting
- `flake8` - Linting
- `mypy` - Type checking
- `pytest` - Quick tests

To run manually:

```bash
pre-commit run --all-files
```

## Implementing New Agents

### Base Agent Structure

```python
from src.agents.base_agent import BaseAgent
from typing import Dict, Any

class MyCustomAgent(BaseAgent):
    """Description of what this agent does."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the agent.
        
        Args:
            config: Agent configuration dictionary
        """
        super().__init__(config)
        self.setup()
    
    def setup(self) -> None:
        """Set up agent-specific resources."""
        # Initialize tools, load models, etc.
        pass
    
    def run(self, input_data: Dict[str, Any], shared_memory: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's main task.
        
        Args:
            input_data: Input data for this agent
            shared_memory: Shared session memory
            
        Returns:
            Dictionary containing agent output
        """
        self.logger.info(f"Running {self.__class__.__name__}")
        
        # Agent logic here
        result = self.process(input_data)
        
        return {
            "status": "success",
            "output": result,
            "metadata": self.get_metadata()
        }
    
    def process(self, data: Dict[str, Any]) -> Any:
        """Process input data.
        
        Args:
            data: Data to process
            
        Returns:
            Processed result
        """
        # Implement agent-specific logic
        pass
```

### Adding Agent to Pipeline

```python
# In main.py or orchestrator
from src.agents.my_custom_agent import MyCustomAgent

def run_pipeline(config):
    # Existing agents
    scout = GrantScout()
    validator = GrantValidator()
    writer = GrantWriter()
    
    # Add new agent
    custom = MyCustomAgent()
    
    # Execute pipeline
    scout_results = scout.run(config, memory)
    validated = validator.run(scout_results, memory)
    custom_results = custom.run(validated, memory)  # New agent
    drafts = writer.run(custom_results, memory)
```

## Implementing New Tools

### Tool Structure

```python
from src.tools.base_tool import BaseTool

class MyCustomTool(BaseTool):
    """Description of what this tool does."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the tool."""
        super().__init__(config)
        self.initialize()
    
    def initialize(self) -> None:
        """Set up tool resources."""
        # Initialize API clients, load data, etc.
        pass
    
    def execute(self, **kwargs) -> Any:
        """Execute the tool's function.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool output
        """
        # Tool logic here
        pass
```

## Debugging

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Different log levels
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.exception("Exception with traceback")
```

### Debug Mode

Run with debug logging:

```bash
python main.py --config config.json --log-level DEBUG
```

### Interactive Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in breakpoint (Python 3.7+)
breakpoint()
```

## Performance Optimization

### Profiling

```bash
# Profile with cProfile
python -m cProfile -o profile.stats main.py --config config.json

# Analyze profile
python -m pstats profile.stats
```

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_function(param: str) -> str:
    """Function with result caching."""
    # Expensive computation
    return result
```

### Async Operations

```python
import asyncio

async def fetch_multiple_grants(urls: List[str]) -> List[Dict]:
    """Fetch multiple grants concurrently."""
    tasks = [fetch_grant(url) for url in urls]
    return await asyncio.gather(*tasks)
```

## Documentation

### Building Documentation

```bash
# Install documentation tools
pip install sphinx sphinx-rtd-theme

# Build HTML documentation
cd docs
make html

# View documentation
open _build/html/index.html
```

### Adding Documentation

1. Create new `.md` file in `docs/`
2. Add to `docs/index.md` or appropriate page
3. Build and verify

## Git Workflow

### Branch Naming

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance

Example:
```
feat(scout): add support for state-specific grant searches

Implement search query generation for state-specific grants
including state abbreviation in queries.

Closes #42
```

### Pull Request Process

1. Create feature branch
2. Make changes with tests
3. Run tests and linting
4. Push to fork
5. Create pull request
6. Address review comments
7. Merge after approval

## Release Process

1. Update version in `setup.py`
2. Update `CHANGELOG.md`
3. Create release branch
4. Run full test suite
5. Tag release
6. Merge to main
7. Deploy

## Getting Help

- Check existing documentation
- Review test examples
- Ask in GitHub Discussions
- Open an issue for bugs

## Contributing Guidelines

See [Contributing.md](Contributing.md) for detailed contribution guidelines.
