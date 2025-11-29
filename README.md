# Civic Grant Agent: Grant-Finder & Draft-Writer Agent

> **A free, open-source AI agent framework built for civic good.** This tool is designed to help volunteer fire departments, EMS agencies, and other public service organizations secure critical funding—no cost, no barriers, just community impact.

## 🚒 The Problem

Volunteer fire departments and EMS agencies are critically under-funded. They rely on complex grants (federal, state, corporate) and private donations, but they lack the time and expertise to find and apply for them effectively. Small volunteer departments often lose out on thousands of dollars in available funding simply because they don't have the staff to:

- **Research** grant opportunities across multiple sources
- **Evaluate** which grants they're eligible for
- **Draft** compelling, professional grant applications

For many volunteer departments, grant research and writing can consume **20+ hours per week** of limited volunteer time.

## 💡 The Solution

**Civic Grant Agent** is a free, open-source multi-agent system built with Google's Agent Developer Kit (ADK) that autonomously:

1. **Scans** the web for new, relevant grant opportunities
2. **Filters** them based on the department's specific profile (volunteer/paid, service area, equipment needs)
3. **Drafts** a high-quality initial application for the most promising grants

**Value Proposition:** This agent system turns a 20-hour/week manual research task into a 1-hour/week review task, directly increasing a department's ability to secure funding for life-saving equipment.

---

## 🚀 How to Use

**Try it live at [civic-grant-agent.xomanova.io](https://civic-grant-agent.xomanova.io)**

![Welcome Screen](assets/00_welcome_screen.png)

The workflow is simple:

1. **Tell us about your organization** - Chat with the agent to provide your department's information
2. **Review matching grants** - The agent searches and displays grants you're eligible for
3. **Generate a draft application** - Click any grant to have the agent write a professional application

### Full Workflow Demo

![Civic Grant Agent Workflow](assets/Civic%20Grant%20Agent.gif)

---

## 🎯 Why This Project Exists

### The Civic Tech Gap

While the grant-writing AI space has several commercial platforms (Grantable, GrantWriter, Grant Assistant), these are:
- **Closed-source** SaaS products with subscription fees
- **Built for general non-profits**, not specialized civic organizations
- **Too expensive** for small volunteer departments with limited budgets

Similarly, existing open-source projects target different audiences:
- **Municipal governments** (GrantWell) - for government employees, not volunteers
- **Medical/NIH grants** (Grant_Guide) - highly specialized for academic research
- **Agent components** (grants-mcp) - tools for agents, not complete systems

### Our Unique Position

**Civic Grant Agent** fills a critical gap by providing:

✅ **Open-Source & Free** - No subscription fees, no vendor lock-in, built for the public good  
✅ **Civic-Focused** - Purpose-built for volunteer fire departments, EMS, and public safety organizations  
✅ **Lightweight Core** - A flexible agent engine, not a heavy all-in-one platform  
✅ **Department Memory** - Understands the unique identity and needs of civic volunteer organizations  

**This is a not-for-profit tool.** Public service agencies are invited to use it freely to better serve their communities.

---

## 🏗️ Architecture

This system uses a **multi-agent architecture** powered by Google's ADK with a custom orchestrator and AG-UI Protocol for real-time frontend communication:

**Interactive Flow:**
```
User Chat → Orchestrator → ProfileCollector → GrantFinder → GrantWriter → UI Display
```

### Orchestrator Agent (Router)
- **Purpose**: Manages workflow state and routes requests to appropriate sub-agents
- **Features**: Handles profile completion detection, workflow transitions, and state management
- **Protocol**: Communicates with React frontend via AG-UI Protocol and CopilotKit

### Agent 1: ProfileCollector (Interviewer)
- **Tools**: Web Search, Profile Update
- **Purpose**: Conversationally gathers department information through chat
- **Features**: Enriches profiles with web search data, validates completeness
- **Output**: Complete department profile stored in session state

![Profile Building](assets/01_profile_building.png)

### Agent 2: GrantFinder (Scout + Validator)
- **Tools**: Web Search, Eligibility Checker, State Filter
- **Purpose**: Discovers grants and validates eligibility in one step
- **Features**: State-based filtering, federal grant detection, match scoring (0-100%)
- **Output**: Ranked grants displayed as interactive cards in the UI

![Grant Selection](assets/02_grant_selection.png)

### Agent 3: GrantWriter (Drafter)
- **Tools**: Save Draft
- **Purpose**: Generates professional grant application narratives
- **Output**: Complete grant draft displayed with rich markdown rendering

![Grant Drafting](assets/03_grant_drafting.png)

**State Management:** Session state syncs bidirectionally between backend and frontend via AG-UI Protocol. The frontend uses CopilotKit's `useCoAgent` hook for real-time state updates.

## Agent Flow Diagram
```mermaid
graph LR
    A[User Chat] --> B[Orchestrator Agent]
    B --> C[ProfileCollector<br/>Web Search + Profile Tools]
    C -->|civic_grant_profile| B
    B --> D[GrantFinder<br/>Search + Eligibility Check]
    D -->|grants_for_display| E[Grant Cards UI]
    E -->|User Clicks Grant| B
    B --> F[GrantWriter<br/>Draft Generation]
    F -->|grant_draft| G[Draft Viewer UI]
    
    style A fill:#e1f5ff
    style B fill:#f0f0f0
    style C fill:#fff3cd
    style D fill:#d4edda
    style F fill:#f8d7da
    style E fill:#d1ecf1
    style G fill:#d1ecf1
```

## 📋 Key Features

### Custom Orchestrator Architecture
- **Workflow State Machine**: Manages transitions between profile building, grant scouting, and draft writing
- **AG-UI Protocol**: Real-time bidirectional state sync with React frontend
- **Smart Routing**: Detects profile completeness and routes to appropriate agent

### Agent 1: ProfileCollector (Interviewer)
- **Conversational UX**: Gathers department info through natural chat interaction
- **Web Enrichment**: Uses web search to find additional department details
- **Profile Validation**: Ensures minimum required fields before advancing
- **Output**: Department profile stored in `civic_grant_profile` state key

### Agent 2: GrantFinder (Scout + Validator)
- **Comprehensive Search**: Searches FEMA AFG, SAFER, Grants.gov, Firehouse Subs, and more
- **State-Based Filtering**: Filters out grants from other states (detects state names in URLs too)
- **Eligibility Scoring**: Multi-criteria analysis with match percentage (0-100%)
- **Interactive Cards**: Grants displayed as clickable cards with match reasons
- **Output**: Validated grants stored in `grants_for_display` state key

### Agent 3: GrantWriter (Drafter)
- **Gemini-Powered**: Uses Gemini for high-quality, professional drafts
- **Tool-Based Saving**: Saves draft via tool call for reliable state sync
- **7-Section Structure**: Executive Summary, Background, Need, Project, Budget, Impact, Sustainability
- **Rich Rendering**: Draft displayed with markdown formatting in dedicated panel
- **Output**: Professional draft stored in `grant_draft` state key


## 🎯 ADK Requirements Met

This project demonstrates proficiency with Google's Agent Developer Kit:

- ✅ **Multi-Agent Architecture**: Custom orchestrator managing three specialized sub-agents
- ✅ **Custom Tools**: Web search, eligibility checker, profile updater, draft saver
- ✅ **AG-UI Protocol**: Real-time bidirectional state sync with React/CopilotKit frontend
- ✅ **State Management**: Session state shared across agents and synced to frontend
- ✅ **Effective Use of Gemini**: All agents use Gemini for natural language understanding and generation
- ✅ **Real-World Value**: Solves actual problem faced by volunteer fire departments
- ✅ **Retry Configuration**: Implements `HttpRetryOptions` for API reliability
- ✅ **Interactive UI**: Grant cards, profile display, and rich markdown draft viewer

## 🌐 Deployment

Deploy the full stack (backend + frontend) to Google Cloud Run and Firebase:

```bash
./deployment/firebase-deploy.sh
```

See `deployment/DEPLOYMENT_GUIDE.md` for detailed instructions and configuration options.

## 🎥 Demo Video

[Watch the 3-minute demo video](https://youtube.com/your-video-link) showing:
- The problem volunteer departments face
- How the agent system works
- Live demonstration of all three agents
- Real-world impact and value

## 🤝 Contributing

This project is designed to help volunteer fire departments, EMS agencies, and other civic organizations. We welcome contributions from:

- **Firefighters & First Responders** - Share your grant-writing experience and needs
- **Developers** - Improve the agent framework, add new tools, enhance performance
- **Grant Professionals** - Help refine prompts and validation logic, identify grant data sources
- **Documentation Writers** - Make this tool more accessible to non-technical users

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

This is free software for public good. Use it, modify it, share it with other civic organizations.

## 🙏 Acknowledgments

Built with Google's Agent Developer Kit for the "Agents for Good" track. 

**Special thanks to:**
- All volunteer firefighters and EMS personnel who inspired this work
- The civic tech community working to bridge the gap between technology and public service
- Public safety organizations everywhere who serve their communities despite funding challenges

## 🌟 For Civic Organizations

**This tool is for you.** If you're a volunteer fire department, EMS agency, rescue squad, or other public service organization:

- ✅ **It's completely free** - No hidden costs, no subscriptions, no trials
- ✅ **You own your data** - Run it locally, keep your department information private
- ✅ **Community-supported** - Built by people who understand your mission
- ✅ **Open to feedback** - Tell us what you need, and we'll work to make it better