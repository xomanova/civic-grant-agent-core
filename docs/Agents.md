# Agent Documentation

This document provides detailed information about each agent in the Civic Grant Agent Core system.

## Agent Overview

The system uses three specialized agents that work together in a pipeline:

| Agent | Role | Primary Function | Output |
|-------|------|------------------|--------|
| GrantScout | Researcher | Discover grant opportunities | List of potential grant URLs |
| GrantValidator | Analyst | Validate eligibility and prioritize | Validated grants with eligibility scores |
| GrantWriter | Drafter | Generate application drafts | Complete grant application draft |

---

## GrantScout: The Researcher Agent

### Purpose

GrantScout is responsible for discovering relevant grant opportunities by searching the web and identifying potential funding sources that match the department's needs.

### Key Responsibilities

- Analyze department profile to understand needs
- Generate effective search queries
- Execute web searches via Google Search API
- Filter and collect relevant grant URLs
- Provide initial relevance assessment

### Input Requirements

GrantScout receives:
- **Department Profile** (from shared memory):
  - Department name and type
  - Location information
  - Specific needs (equipment, training, etc.)
  - Budget constraints
  - Mission statement

### Search Strategy

GrantScout employs multiple search strategies:

1. **Need-Based Searches**: "fire department equipment grants [location]"
2. **Type-Based Searches**: "volunteer firefighter training funding"
3. **Location-Specific**: "[state/region] emergency services grants"
4. **Equipment-Specific**: "SCBA equipment grants", "fire truck funding"
5. **Federal Programs**: "FEMA fire grants", "AFG assistance"

### Output Format

```json
{
  "search_results": [
    {
      "url": "https://example.gov/grant-program",
      "title": "Fire Department Equipment Grant 2024",
      "snippet": "Funding for fire departments to purchase...",
      "relevance_score": 0.85,
      "source": "government"
    }
  ],
  "search_metadata": {
    "queries_executed": 5,
    "total_results": 47,
    "filtered_results": 12,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Configuration Options

- `max_results_per_query`: Maximum URLs to collect per search
- `relevance_threshold`: Minimum relevance score for inclusion
- `search_domains`: Whitelist/blacklist for grant sources
- `time_range`: Limit to recently posted grants

### Tools and APIs

- **Google Search API**: Primary search mechanism
- **URL Validator**: Ensures links are valid and accessible
- **Relevance Scorer**: ML-based relevance assessment
- **Deduplicator**: Removes duplicate grant opportunities

---

## GrantValidator: The Analyst Agent

### Purpose

GrantValidator examines each grant opportunity discovered by GrantScout, extracts detailed requirements, and determines eligibility based on the department profile.

### Key Responsibilities

- Fetch and parse grant documentation
- Extract eligibility criteria and requirements
- Compare requirements against department profile
- Calculate eligibility scores
- Prioritize grants based on fit and potential
- Identify missing requirements

### Input Requirements

GrantValidator receives:
- **Grant URLs** (from GrantScout)
- **Department Profile** (from shared memory)

### Validation Process

1. **Document Retrieval**: Fetch grant page and related documents
2. **Content Extraction**: Parse HTML, PDFs, and other formats
3. **Requirement Analysis**: Identify eligibility criteria
4. **Profile Matching**: Compare against department characteristics
5. **Scoring**: Calculate eligibility and priority scores
6. **Prioritization**: Rank grants by suitability

### Eligibility Checks

GrantValidator evaluates:

- **Geographic Eligibility**: Is the department in the right location?
- **Organization Type**: Does department type match requirements?
- **Size Requirements**: Budget, personnel, population served
- **Equipment/Need Matching**: Does grant fund requested items?
- **Deadline Feasibility**: Enough time to apply?
- **Match Requirements**: Can department meet matching funds?
- **Previous Awards**: Any restrictions on past recipients?

### Scoring System

Each grant receives multiple scores:

- **Eligibility Score** (0-100): Likelihood of qualifying
- **Match Score** (0-100): How well needs align with grant purpose
- **Feasibility Score** (0-100): Ability to complete application and requirements
- **Priority Score** (0-100): Composite score for ranking

### Output Format

```json
{
  "validated_grants": [
    {
      "grant_id": "AFG-2024-001",
      "url": "https://www.fema.gov/grants/...",
      "title": "Assistance to Firefighters Grant",
      "eligibility_score": 95,
      "match_score": 88,
      "feasibility_score": 92,
      "priority_score": 91.67,
      "amount_range": "$50,000 - $500,000",
      "deadline": "2024-03-15",
      "eligible": true,
      "eligibility_details": {
        "geographic": "PASS",
        "organization_type": "PASS",
        "size_requirements": "PASS",
        "need_matching": "PASS"
      },
      "requirements": [
        "501(c)(3) status or government entity",
        "Serve population under 100,000",
        "10% cost share required"
      ],
      "flags": [
        "Cost share required",
        "Tight deadline (45 days)"
      ]
    }
  ],
  "validation_summary": {
    "total_validated": 12,
    "eligible": 8,
    "ineligible": 4,
    "high_priority": 3
  }
}
```

### Custom Tools

**EligibilityChecker Tool**: A specialized component that:
- Extracts structured data from grant documents
- Applies business logic for eligibility determination
- Handles multiple document formats (HTML, PDF, DOCX)
- Caches parsed documents for efficiency

### Configuration Options

- `eligibility_threshold`: Minimum score for "eligible" status
- `priority_cutoff`: How many top grants to recommend
- `deadline_buffer`: Minimum days before deadline
- `document_timeout`: Max time to parse documents

---

## GrantWriter: The Drafter Agent

### Purpose

GrantWriter creates comprehensive, well-structured grant application drafts based on validated grant opportunities and department information.

### Key Responsibilities

- Analyze grant application requirements
- Extract key questions and required sections
- Generate compelling narrative content
- Synthesize department information with grant requirements
- Format output for readability and submission
- Suggest supporting documents

### Input Requirements

GrantWriter receives:
- **Validated Grant Details** (from GrantValidator)
- **Department Profile** (from shared memory)
- **Grant Application Template** (extracted from grant documentation)

### Writing Process

1. **Requirement Analysis**: Identify all required sections and questions
2. **Content Planning**: Outline response structure
3. **Narrative Generation**: Use Gemini LLM to create content
4. **Department Integration**: Weave in specific department details
5. **Formatting**: Structure content for submission
6. **Review Checklist**: Generate completion checklist

### Content Generation Strategies

GrantWriter employs several strategies:

- **Storytelling**: Compelling narratives about department needs and impact
- **Data Integration**: Incorporating statistics and concrete numbers
- **Mission Alignment**: Showing how grant supports department mission
- **Community Impact**: Emphasizing benefits to the community
- **Sustainability**: Demonstrating long-term planning

### Output Sections

Typical grant application draft includes:

1. **Executive Summary**: Overview of request and need
2. **Organization Background**: Department history and mission
3. **Need Statement**: Detailed explanation of the problem
4. **Project Description**: What will be done with funding
5. **Goals and Objectives**: Specific, measurable outcomes
6. **Methods/Approach**: How objectives will be achieved
7. **Evaluation Plan**: Measuring success
8. **Budget Narrative**: Justification for requested funds
9. **Sustainability**: Long-term impact and continuation
10. **Qualifications**: Why department is suited for this project

### Output Format

The draft is generated in Markdown format:

```markdown
# Grant Application Draft
## [Grant Name]

**Applicant**: [Department Name]  
**Amount Requested**: $[Amount]  
**Date**: [Current Date]

---

## Executive Summary

[Generated compelling summary...]

## Organization Background

[Department history and mission...]

## Need Statement

[Detailed explanation of need...]

[Additional sections...]

---

## Supporting Documents Checklist

- [ ] IRS 501(c)(3) determination letter
- [ ] Board resolution authorizing application
- [ ] Current budget
- [ ] Letters of support
- [ ] Equipment quotes

## Next Steps

1. Review and refine draft content
2. Gather supporting documents
3. Have board review and approve
4. Submit before deadline: [Date]
```

### LLM Configuration

GrantWriter uses **Gemini LLM** with:

- **Temperature**: 0.7 (balanced creativity and consistency)
- **Max Tokens**: Varies by section (500-2000)
- **System Prompt**: Instructions for grant writing style
- **Context Window**: Full grant requirements + department profile

### Quality Assurance

GrantWriter includes:

- **Requirement Verification**: Ensuring all questions are addressed
- **Character/Word Limits**: Respecting stated limits
- **Tone Consistency**: Professional and appropriate
- **Fact Checking**: Flagging unsupported claims
- **Completeness Check**: Identifying missing information

### Configuration Options

- `writing_style`: formal, conversational, technical
- `detail_level`: concise, standard, comprehensive
- `include_examples`: true/false for including case studies
- `budget_detail`: summary or itemized

---

## Agent Communication

### Shared Memory Schema

All agents access a shared session memory:

```python
{
  "department_profile": {
    "name": str,
    "type": str,
    "location": dict,
    "needs": list,
    "mission": str,
    "budget": dict,
    "contact": dict
  },
  "scout_results": [...],
  "validated_grants": [...],
  "draft_applications": [...]
}
```

### Error Handling

Each agent implements:

- **Retry Logic**: For transient API failures
- **Fallback Strategies**: Alternative approaches when primary fails
- **Error Reporting**: Detailed logs for debugging
- **Graceful Degradation**: Continue with partial results when possible

### Logging and Monitoring

Each agent logs:

- Start and end timestamps
- Input parameters
- Key decisions and scores
- Errors and warnings
- Output summaries

---

## Best Practices

### For GrantScout

- Use diverse search queries to maximize coverage
- Filter out clearly irrelevant results early
- Cache search results to avoid redundant API calls
- Respect API rate limits

### For GrantValidator

- Parse documents efficiently with timeouts
- Cache parsed documents
- Clearly document ineligibility reasons
- Flag borderline cases for human review

### For GrantWriter

- Maintain consistent tone throughout draft
- Include specific department details
- Avoid generic or template-like language
- Flag sections needing human input
- Respect word/character limits

---

## Future Enhancements

### Potential Agent Additions

- **GrantTracker**: Monitor application status and deadlines
- **GrantReviewer**: Quality assurance for drafts
- **GrantOptimizer**: Suggest improvements to applications
- **CommunicationAgent**: Handle correspondence with grantors

### Agent Improvements

- Multi-language support
- Learning from past applications
- User preference adaptation
- Collaborative editing features
