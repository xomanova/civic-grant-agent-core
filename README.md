# Civic Grant Agent Core

An intelligent multi-agent system for automating grant discovery, validation, and application drafting for civic organizations.

## Documentation

This project is documented using [Google Code Wiki](https://codewiki.google), an AI-powered tool that automatically generates and maintains documentation from the codebase.

<!-- Once the repository is public, the Code Wiki link will be available here -->

## Agent Flow Diagram
```mermaid
graph TD
    subgraph "User Input (Local Config)"
        A[Department Profile JSON] -- "|e.g., department_config.json|" --> B
    end

    subgraph "Agent Orchestrator (Main Program)"
        B[Start Agent Chain]
        B --> C{Trigger GrantScout}
    end

    subgraph "Agent 1: GrantScout (Researcher)"
        C --> D(LLM: Identify Search Queries)
        D -- "|Google Search Tool|" --> E[Google Search API]
        E -- "|List of Grant URLs|" --> F[Search Results]
        F --> G{Output: Potential Grant URLs}
    end

    subgraph "Agent 2: GrantValidator (Analyst)"
        G --> H{Input: Potential Grant URLs & Department Profile}
        H -- "|Iterate through URLs|" --> I(LLM: Extract Grant Details)
        I -- "|Custom Tool: EligibilityChecker|" --> J[External HTTP Request or PDF Parser]
        J -- "|Eligibility Status|" --> K(LLM: Compare to Profile)
        K -- "|Filter & Prioritize|" --> L{"Output: Validated & Prioritized Grants (JSON)"}
    end

    subgraph "Agent 3: GrantWriter (Drafter)"
        L --> M{Input: Validated Grant Details & Department Profile}
        M -- "|Gemini LLM|" --> N(LLM: Generate Grant Narrative Draft)
        N -- "|Synthesize Sections|" --> O{"Output: Draft Grant Application (Markdown/Text)"}
    end

    subgraph "Output"
        O --> P[Grant Application Draft File]
    end

    subgraph "Memory & Context"
        DepartmentProfile["Shared Session Memory:
            - Department Name
            - Type (Volunteer/Paid)
            - Needs (Equipment, Training)
            - Location
            - Mission Statement Excerpt
        "]
        DepartmentProfile --> H
        DepartmentProfile --> M
    end

    style DepartmentProfile fill:#e0f2f7,stroke:#333,stroke-width:2px,color:#000
    style E fill:#f0f8ff,stroke:#666,stroke-width:1px
    style J fill:#f0f8ff,stroke:#666,stroke-width:1px
```