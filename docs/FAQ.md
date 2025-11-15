# Frequently Asked Questions (FAQ)

## General Questions

### What is Civic Grant Agent Core?

Civic Grant Agent Core is an AI-powered system that automates the grant discovery, validation, and application drafting process for civic organizations, particularly fire departments and emergency services.

### Who is this for?

This system is designed for:
- Fire departments (volunteer, paid, or combination)
- Emergency medical services
- Rescue organizations
- Other civic organizations seeking grants
- Grant writers and administrators

### How does it work?

The system uses three specialized AI agents:
1. **GrantScout** searches for relevant grants
2. **GrantValidator** checks eligibility and prioritizes
3. **GrantWriter** generates application drafts

### Is this free to use?

The software is open source and free to use, but you'll need API keys from Google (Search API and Gemini AI) which may have associated costs depending on your usage.

### What are the API costs?

- **Google Search API**: Free tier provides 100 queries/day; paid plans available
- **Gemini API**: Free tier available with rate limits; paid plans for higher usage

### Can I use this commercially?

Check the LICENSE file for specific terms. Generally, the software is open source, but you're responsible for complying with API provider terms of service.

## Setup and Installation

### What are the system requirements?

- Python 3.9 or higher
- 4GB RAM minimum (8GB recommended)
- Internet connection for API access
- 2GB free disk space

### Which operating systems are supported?

- Linux (Ubuntu, Debian, CentOS, etc.)
- macOS (10.14+)
- Windows 10/11 (with or without WSL)

### Do I need programming experience?

Basic command-line familiarity is helpful, but not required. The system is designed to be configured through JSON files without writing code.

### How do I get API keys?

See the [Getting Started Guide](Getting-Started.md#obtaining-api-keys) for detailed instructions on obtaining:
- Google Search API key
- Google Search Engine ID
- Gemini API key

### Can I run this without API keys?

No, the system requires API keys to function. However, you can use `--dry-run` mode for testing without making actual API calls.

### Installation failed. What should I do?

Common solutions:
1. Ensure Python 3.9+ is installed: `python --version`
2. Activate virtual environment: `source venv/bin/activate`
3. Update pip: `pip install --upgrade pip`
4. Install dependencies: `pip install -r requirements.txt`
5. Check [Troubleshooting Guide](Troubleshooting.md)

## Configuration

### Where do I configure my department information?

Create a JSON file in the `config/` directory based on the example:
```bash
cp config/department_profile.example.json config/my_department.json
```
Then edit with your department's information.

### What information do I need to provide?

Minimum required:
- Department name and type
- Location (city, state)
- List of needs
- Contact information

See [Configuration Guide](Configuration.md) for complete details.

### Can I have multiple department profiles?

Yes! Create separate JSON files for each department:
- `config/department1.json`
- `config/department2.json`

Then specify which to use: `python main.py --config config/department1.json`

### How do I customize agent behavior?

Edit `config/agent_config.json` to adjust:
- Search parameters
- Eligibility thresholds
- Writing style
- Output preferences

See [Configuration Guide](Configuration.md#agent-configuration) for options.

## Using the System

### How do I run the system?

Basic usage:
```bash
python main.py --config config/my_department.json
```

See [Getting Started Guide](Getting-Started.md#running-the-system) for more options.

### How long does it take to run?

Depends on configuration:
- **GrantScout**: 1-5 minutes (depends on searches)
- **GrantValidator**: 5-15 minutes per grant (depends on document complexity)
- **GrantWriter**: 2-5 minutes per draft

Total time varies based on number of grants found and processed.

### Can I run agents individually?

Yes! Use the `--agent` flag:
```bash
python main.py --config config.json --agent scout
python main.py --config config.json --agent validator
python main.py --config config.json --agent writer
```

### Where are the results saved?

By default in the `output/` directory:
- `output/scout_results.json` - URLs found
- `output/validated_grants.json` - Eligible grants
- `output/draft_applications/` - Generated drafts

### Can I change the output directory?

Yes:
```bash
python main.py --config config.json --output /path/to/output
```

### What format are the drafts in?

By default, drafts are generated in Markdown (.md) format, which can be easily converted to Word, PDF, or other formats.

## Grant Discovery

### How many grants will it find?

Depends on:
- Your department's needs and location
- Available grants matching criteria
- Search configuration settings

Typically 5-20 relevant grants per search.

### How does it search for grants?

GrantScout uses multiple search strategies:
- Need-based searches (e.g., "SCBA equipment grants")
- Location-specific searches
- Federal program searches (FEMA, AFG, etc.)
- Equipment-specific searches

### Can I customize search queries?

Yes! Edit `config/agent_config.json` to:
- Add custom search strategies
- Whitelist/blacklist domains
- Adjust relevance thresholds

### Will it find all available grants?

No search system is perfect. GrantScout finds grants available through web search, but some grants may not be indexed or may require manual discovery.

### Can it search for grants in specific states?

Yes, location information in your department profile is used to target location-specific grants.

## Grant Validation

### How does it determine eligibility?

GrantValidator:
1. Extracts requirements from grant documentation
2. Compares against your department profile
3. Scores based on multiple criteria
4. Flags potential issues

### What if a grant requires documents I don't have?

The system will list required documents in the validation results. You'll need to gather these before submitting.

### Can it parse PDF grant applications?

Yes, the system can parse PDF documents to extract requirements. Set `parse_pdfs: true` in configuration.

### Why are some grants marked ineligible?

Common reasons:
- Geographic restrictions
- Organization type mismatch
- Budget requirements not met
- Deadline too soon
- Missing required characteristics

### Can I override eligibility decisions?

The system provides recommendations, but final decisions are yours. Review flagged grants manually if you disagree with the assessment.

## Grant Writing

### How good are the generated drafts?

Drafts provide a solid starting point but require human review and customization. Think of them as 70-80% complete first drafts.

### What sections does it generate?

Typical sections:
- Executive summary
- Organization background
- Need statement
- Project description
- Goals and objectives
- Methods/approach
- Evaluation plan
- Budget narrative
- Sustainability

### Can I customize the writing style?

Yes! Configure in `agent_config.json`:
- `writing_style`: formal, conversational, technical
- `detail_level`: concise, standard, comprehensive
- Include/exclude examples and statistics

### Will it fill in specific dollar amounts?

The system uses information from your profile but may need manual input for specific costs. Review all budget sections carefully.

### Can it generate applications in other languages?

Currently, the system generates English-language drafts. Multi-language support may be added in future versions.

### Should I submit the drafts as-is?

**No!** Always review, edit, and customize drafts before submission. The system provides a starting point, not a final product.

## Troubleshooting

### The system is running slowly

Try:
- Reducing `max_results_per_query` in configuration
- Disabling PDF parsing if not needed
- Limiting number of grants with `--max-grants`
- Checking internet connection speed

### I'm getting rate limit errors

Solutions:
- Wait before retrying
- Reduce request frequency in configuration
- Upgrade API quota if needed
- Implement longer delays between requests

### The drafts don't match the grant requirements

Possible causes:
- Grant requirements weren't properly extracted
- Department profile incomplete
- Grant documentation unclear

Solutions:
- Verify department profile completeness
- Manually review grant requirements
- Regenerate with updated information

### API authentication failed

Check:
- API keys in `.env` file are correct
- No extra spaces or quotes in keys
- APIs are enabled in Google Cloud Console
- API keys have appropriate permissions

## Best Practices

### How often should I run the system?

Recommendations:
- **Weekly**: For active grant searching
- **Monthly**: For periodic checks
- **As needed**: When specific needs arise

### What should I do with the results?

1. Review validated grants carefully
2. Prioritize top-scoring opportunities
3. Customize drafts for each grant
4. Gather required supporting documents
5. Have stakeholders review before submission
6. Submit by deadlines

### How can I improve results?

- Keep department profile updated
- Be specific about needs
- Include detailed mission statement
- Provide accurate budget information
- Review and refine configuration settings

### Should I apply to every eligible grant?

No. Focus on:
- High-priority grants (high scores)
- Grants matching critical needs
- Feasible application timelines
- Realistic match requirements

## Technical Questions

### Can I extend the system with custom agents?

Yes! See [Development Guide](Development.md#implementing-new-agents) for instructions on creating custom agents.

### Can I integrate with other systems?

The system uses standard JSON for input/output, making integration possible. API documentation available in [API Reference](API-Reference.md).

### Is there a web interface?

Not currently, but it's on the roadmap. The system is currently CLI-based.

### Can I run this in the cloud?

Yes, the system can run on cloud platforms (AWS, Google Cloud, Azure) with appropriate configuration.

### How do I contribute improvements?

See [Contributing Guidelines](Contributing.md) for information on contributing code, documentation, or suggestions.

## Security and Privacy

### Is my department information secure?

- Data stays on your local machine
- API calls are encrypted (HTTPS)
- No data is stored by the agents
- You control all data

### What data is sent to APIs?

- **Search API**: Search queries (may include department needs/location)
- **Gemini API**: Grant requirements and department profile for draft generation

### Should I include sensitive information in the profile?

Only include information you're comfortable including in grant applications. Avoid:
- Social security numbers
- Bank account numbers
- Personal sensitive data

### Can I use this on a private/air-gapped network?

No, the system requires internet access for API calls. However, you could potentially cache results for offline review.

## Getting Help

### Where can I get more help?

1. Check this FAQ
2. Review [Troubleshooting Guide](Troubleshooting.md)
3. Read relevant documentation sections
4. Search GitHub issues
5. Open a new issue with details
6. Contact maintainers

### How do I report bugs?

See [Contributing Guidelines](Contributing.md#reporting-bugs) for bug report template and process.

### How do I request new features?

Open an issue using the feature request template. Describe the use case and proposed solution.

### Is there a community forum?

Use GitHub Discussions for questions, sharing experiences, and community support.
