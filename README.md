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

This system uses a **multi-agent pipeline** powered by Google's ADK `SequentialAgent`:

**Pipeline Flow:**
```
Department Profile → GrantScout → GrantValidator → GrantWriter → Complete Draft
```

### Agent 1: GrantScout (Researcher)
- **Tools**: Google Search
- **Purpose**: Discovers grant opportunities from the web
- **Output**: JSON array of potential grants with URLs, descriptions, and deadlines

### Agent 2: GrantValidator (Analyst)
- **Tools**: Built-in Code Executor
- **Purpose**: Analyzes eligibility using Python scoring algorithm
- **Output**: Validated grants ranked by eligibility score (0.0-1.0)

### Agent 3: GrantWriter (Drafter)
- **Tools**: Gemini language model (temperature=0.7)
- **Purpose**: Generates professional grant application narratives
- **Output**: Complete grant draft with all required sections

**State Management:** Each agent's output is stored in session state and automatically injected into the next agent's context using placeholder variables (e.g., `{grant_opportunities}`, `{validated_grants}`).

## Agent Flow Diagram
```mermaid
graph LR
    A[User Input:<br/>Department Profile] --> B[SequentialAgent Pipeline]
    B --> C[Agent 1: GrantScout<br/>Google Search]
    C -->|grant_opportunities| D[Agent 2: GrantValidator<br/>Code Execution]
    D -->|validated_grants| E[Agent 3: GrantWriter<br/>Gemini Text Generation]
    E -->|grant_draft| F[Complete Application]
    
    style A fill:#e1f5ff
    style C fill:#fff3cd
    style D fill:#d4edda
    style E fill:#f8d7da
    style F fill:#d1ecf1
```

## 📋 Key Features

### Multi-Agent Pipeline Architecture
- **SequentialAgent Orchestration**: Agents automatically pass outputs to the next agent in the pipeline
- **State Management**: Session state stores intermediate results using `output_key` parameters
- **Variable Injection**: Automatic placeholder replacement (e.g., `{grant_opportunities}`)

### Agent 1: GrantScout (Researcher)
- **Built-in Tools**: Uses Google Search API to find grant opportunities
- **Smart Queries**: Generates targeted search queries based on department needs
- **Comprehensive Coverage**: Searches federal, state, and corporate grant programs
- **Output**: JSON array of grant opportunities stored in `grant_opportunities` state key

### Agent 2: GrantValidator (Analyst)
- **Code Execution**: Uses Python to systematically score grant eligibility
- **Multi-Criteria Analysis**: Evaluates 5 dimensions (type, location, needs, budget, nonprofit status)
- **Automated Scoring**: Calculates eligibility scores (0.0-1.0) programmatically
- **Output**: Validated and ranked grants stored in `validated_grants` state key

### Agent 3: GrantWriter (Drafter)
- **Gemini-Powered**: Leverages Gemini's advanced language model for high-quality drafts
- **Context-Aware**: Uses department profile and validated grants from previous agents
- **Structured Output**: Generates complete grant applications with 7 required sections
- **Output**: Professional draft stored in `grant_draft` state key


## 🎯 ADK Requirements Met

This project demonstrates proficiency with Google's Agent Developer Kit:

- ✅ **Multi-Agent Architecture**: Uses `SequentialAgent` to orchestrate three specialized agents
- ✅ **Built-in Tools**: Google Search tool in GrantScout agent
- ✅ **Code Execution**: `BuiltInCodeExecutor` in GrantValidator for systematic eligibility analysis
- ✅ **State Management**: Agents pass outputs via session state using `output_key` parameters
- ✅ **Variable Injection**: Automatic placeholder replacement (`{grant_opportunities}`, `{validated_grants}`)
- ✅ **Effective Use of Gemini**: GrantWriter leverages Gemini for high-quality text generation
- ✅ **Real-World Value**: Solves actual problem faced by volunteer fire departments
- ✅ **Retry Configuration**: Implements `HttpRetryOptions` for API reliability

## 🌐 Deployment

### Deploy to Google Cloud Run with Skaffold (Recommended)

Deploy both frontend and backend services to Cloud Run using Skaffold:

```bash
# Set your GCP project
export GCP_PROJECT="your-project-id"

# One-command deployment with Skaffold
skaffold run -p cloudrun --default-repo=gcr.io/${GCP_PROJECT}

# Or use the automated deployment script
chmod +x deployment/deploy-cloudrun-skaffold.sh
./deployment/deploy-cloudrun-skaffold.sh
```

### Alternative: Cloud Build

```bash
# Build and deploy using Cloud Build
gcloud builds submit --config deployment/cloudbuild.yaml
```

### Local Development with Kubernetes

```bash
# Create local k3d cluster
k3d cluster create civic-grant-agent

# Deploy with Skaffold
skaffold dev
```

See `deployment/` and `cloudrun/` directories for detailed deployment instructions.


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
- **Grant Professionals** - Help refine prompts and validation logic
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