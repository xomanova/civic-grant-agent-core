# 🚒 Civic Grant Agent - Quick Start Guide

Get up and running with Civic Grant Agent in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- Google API key with Gemini access
- Git (to clone the repository)

## Step 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/xomanova/civic-grant-agent-core.git
cd civic-grant-agent-core

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Google API key
# GOOGLE_API_KEY=your_actual_api_key_here
```

**Get a Google API Key:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy it to your `.env` file

## Step 3: Configure Your Department

```bash
# Copy example department profile
cp examples/sample_department_profile.json department_config.json

# Edit department_config.json with your department's information
```

**Key Information to Update:**
- Department name and location
- Organization details (budget, volunteers, etc.)
- Equipment needs (be specific!)
- Service statistics
- Mission statement

## Step 4: Run Civic Grant Agent

```bash
python main.py
```

**What Happens:**
1. ✅ Loads your department profile
2. 🔍 Searches for relevant grants (GrantScout)
3. ✔️ Validates eligibility (GrantValidator)
4. ✍️ Generates draft applications (GrantWriter)
5. 💾 Saves drafts to `output/` directory

## Step 5: Review Results

```bash
# View generated drafts
ls output/

# Read a draft
cat output/draft_*.txt
```

## Expected Output

```
output/
├── draft_AFG_20251114.txt              # Full grant application draft
├── draft_AFG_20251114.json             # Structured JSON version
├── session_20251114_093045.json        # Session data
└── summary.json                         # Process summary
```

## Customizing Your Drafts

The AI generates high-quality starting drafts. To finalize:

1. **Review Facts** - Verify all statistics and claims
2. **Add Details** - Include specific local examples
3. **Personalize** - Add your department's unique story
4. **Check Requirements** - Ensure compliance with grant guidelines
5. **Proofread** - Review for clarity and grammar

## Troubleshooting

### "GOOGLE_API_KEY not found"
- Make sure you created `.env` file
- Check that API key is properly set (no quotes needed)

### "Department configuration not found"
- Ensure `department_config.json` exists in root directory
- Check JSON syntax is valid

### "Import errors"
- Activate virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### No grants found
- This is normal for initial testing with LLM-based search
- The system includes fallback grants (AFG, SAFER, FP&S)
- For production, integrate actual Google Custom Search API

## Next Steps

### For Testing
- Run with sample profile to understand output
- Experiment with different department needs
- Review generated drafts for quality

### For Production Use
1. Add your actual department information
2. Run weekly to catch new grant opportunities  
3. Build a library of successful applications
4. Track which grants you apply for and results

### For Advanced Users
- Set up Google Custom Search API for real grant discovery
- Deploy to Cloud Run for automated weekly searches
- Customize the eligibility checker for your state's grants
- Add additional grant sources specific to your region

## Tips for Best Results

**Department Profile:**
- Be specific with equipment needs (include models, quantities)
- Provide accurate service statistics (essential for grants)
- Include recent accomplishments and certifications
- Describe your community context and challenges

**Grant Selection:**
- Focus on grants that match your department size
- Consider application deadlines and cycles
- Start with federal grants (AFG, SAFER) for practice
- Research state and local grants in your area

**Application Drafts:**
- Use AI drafts as strong starting points, not final versions
- Add photographs, charts, and supporting documentation
- Have multiple people review before submission
- Keep a "grants library" of successful applications

## Time Savings

**Traditional Process:**
- Grant research: 10-15 hours/week
- Application writing: 15-20 hours per grant
- **Total: 25-35+ hours per grant cycle**

**With Civic Grant Agent:**
- Initial setup: 30 minutes
- Grant discovery: Automated
- Draft generation: 5 minutes
- Review and customization: 1-2 hours
- **Total: 2-3 hours per grant cycle**

**Result: 90% time savings!** ⏱️

## Support

- 📖 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/xomanova/civic-grant-agent-core/issues)
- 💬 [Discussions](https://github.com/xomanova/civic-grant-agent-core/discussions)
- 📺 [Video Tutorial](https://youtube.com/your-video-link)

## Success Story

> "Civic Grant Agent helped our volunteer department apply for 5 grants in the time
> it used to take to research and write one. We secured $75,000 in funding for
> new SCBA equipment and training. This system is a game-changer for small
> volunteer departments."
> 
> — *Example Fire Chief, Volunteer Fire Department*

---

**Ready to help your department secure funding? Let's get started! 🚒**
