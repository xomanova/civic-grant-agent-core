# Troubleshooting Guide

This guide helps you diagnose and fix common issues with Civic Grant Agent Core.

## Installation Issues

### Python Version Error

**Problem**: `ERROR: Python 3.9+ required`

**Cause**: Using an older Python version

**Solution**:
```bash
# Check Python version
python --version

# Install Python 3.9+ from python.org
# Or use pyenv:
pyenv install 3.9.16
pyenv local 3.9.16
```

### Pip Installation Fails

**Problem**: `ERROR: Could not install packages`

**Cause**: Outdated pip or conflicting dependencies

**Solution**:
```bash
# Upgrade pip
pip install --upgrade pip

# Install with verbose output to see errors
pip install -r requirements.txt -v

# Try installing dependencies one at a time
pip install requests
pip install beautifulsoup4
# etc.
```

### Virtual Environment Issues

**Problem**: Commands not found or wrong Python version

**Cause**: Virtual environment not activated

**Solution**:
```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Verify activation (should show venv path)
which python
```

### Module Not Found Error

**Problem**: `ModuleNotFoundError: No module named 'X'`

**Cause**: Missing dependency or wrong environment

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt

# Verify installation
pip list | grep <module-name>
```

## Configuration Issues

### Invalid Configuration Error

**Problem**: `ConfigurationError: Invalid department profile`

**Cause**: JSON syntax error or missing required fields

**Solution**:
```bash
# Validate JSON syntax
python -m json.tool config/my_department.json

# Check for required fields
python main.py --validate-config config/my_department.json

# Compare with example
diff config/my_department.json config/department_profile.example.json
```

### API Key Errors

**Problem**: `Error: Invalid API key` or `Authentication failed`

**Solutions**:

1. **Check .env file exists**:
```bash
ls -la .env
```

2. **Verify API keys have no extra spaces**:
```bash
# .env should look like:
GOOGLE_SEARCH_API_KEY=AIza...
# NOT:
GOOGLE_SEARCH_API_KEY = AIza...  # Extra spaces!
# NOT:
GOOGLE_SEARCH_API_KEY="AIza..."  # Quotes!
```

3. **Verify APIs are enabled**:
- Visit [Google Cloud Console](https://console.cloud.google.com/)
- Check that Custom Search API is enabled
- Verify API key permissions

4. **Test API key directly**:
```bash
# Test with curl
curl "https://www.googleapis.com/customsearch/v1?key=YOUR_KEY&cx=YOUR_CX&q=test"
```

### Missing Environment Variables

**Problem**: `KeyError: 'GOOGLE_SEARCH_API_KEY'`

**Cause**: .env file not loaded or variable not set

**Solution**:
```bash
# Create .env from example
cp .env.example .env

# Edit .env with your keys
nano .env

# Verify environment variables are loaded
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('GOOGLE_SEARCH_API_KEY'))"
```

## Runtime Issues

### Rate Limit Exceeded

**Problem**: `Error: API rate limit exceeded` or `429 Too Many Requests`

**Causes**:
- Too many requests in short time
- Exceeded daily quota
- Concurrent requests

**Solutions**:

1. **Wait and retry**:
```bash
# Wait 60 seconds and try again
sleep 60
python main.py --config config.json
```

2. **Reduce request rate**:
```json
// In config/agent_config.json
{
  "scout": {
    "max_results_per_query": 5,  // Reduce from 10
    "delay_between_requests": 2   // Add delay in seconds
  }
}
```

3. **Check quota usage**:
- Visit Google Cloud Console
- Check API usage dashboard
- Consider upgrading quota

4. **Enable caching**:
```json
{
  "scout": {
    "cache_results": true,
    "cache_ttl_hours": 24
  }
}
```

### Connection Timeout

**Problem**: `Timeout Error: Request timed out`

**Causes**:
- Slow internet connection
- Server not responding
- Firewall blocking requests

**Solutions**:

1. **Check internet connection**:
```bash
ping google.com
curl https://www.googleapis.com
```

2. **Increase timeout**:
```json
{
  "validator": {
    "document_timeout_seconds": 120  // Increase from 60
  }
}
```

3. **Check firewall/proxy**:
```bash
# Set proxy if needed
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

4. **Test specific URLs**:
```bash
curl -I https://www.fema.gov  # Should return 200
```

### Memory Issues

**Problem**: `MemoryError` or system becomes unresponsive

**Causes**:
- Processing too many grants
- Large PDF documents
- Insufficient RAM

**Solutions**:

1. **Limit grants processed**:
```bash
python main.py --config config.json --max-grants 5
```

2. **Disable PDF parsing**:
```json
{
  "validator": {
    "parse_pdfs": false
  }
}
```

3. **Reduce batch size**:
```json
{
  "validator": {
    "batch_size": 5  // Process fewer grants at once
  }
}
```

4. **Increase swap space** (Linux):
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Slow Performance

**Problem**: System runs very slowly

**Solutions**:

1. **Enable caching**:
```json
{
  "scout": {
    "cache_results": true
  },
  "validator": {
    "cache_parsed_documents": true
  }
}
```

2. **Reduce scope**:
- Limit `max_results_per_query`
- Increase `relevance_threshold`
- Disable non-essential features

3. **Check system resources**:
```bash
# CPU usage
top

# Memory usage
free -h

# Disk I/O
iostat
```

4. **Run in parts**:
```bash
# Run agents separately
python main.py --config config.json --agent scout
python main.py --config config.json --agent validator
python main.py --config config.json --agent writer
```

## Output Issues

### No Results Generated

**Problem**: Agents run but produce no output

**Causes**:
- Search found no relevant grants
- All grants failed validation
- Output directory permission issues

**Solutions**:

1. **Check logs**:
```bash
cat output/logs/agent_scout.log
cat output/logs/agent_validator.log
```

2. **Lower thresholds**:
```json
{
  "scout": {
    "relevance_threshold": 0.5  // Lower from 0.7
  },
  "validator": {
    "eligibility_threshold": 60  // Lower from 70
  }
}
```

3. **Check output directory**:
```bash
ls -la output/
ls -la output/draft_applications/
```

4. **Verify permissions**:
```bash
# Ensure write permissions
chmod -R u+w output/
```

### Incomplete Drafts

**Problem**: Generated drafts are missing sections or incomplete

**Causes**:
- Token limits exceeded
- Missing profile information
- LLM generation issues

**Solutions**:

1. **Increase token limits**:
```json
{
  "writer": {
    "max_tokens_per_section": 2000  // Increase from 1000
  }
}
```

2. **Complete department profile**:
- Add mission statement
- Include organization background
- Provide budget details

3. **Check logs for errors**:
```bash
grep ERROR output/logs/agent_writer.log
```

4. **Regenerate specific sections**:
```bash
python main.py --config config.json --agent writer --section need_statement
```

### File Permission Errors

**Problem**: `PermissionError: [Errno 13] Permission denied`

**Cause**: Insufficient permissions for output directory

**Solution**:
```bash
# Fix permissions
chmod -R u+w output/

# Or specify different output directory
python main.py --config config.json --output ~/grants/output

# Check ownership
ls -la output/
```

## Grant Search Issues

### No Grants Found

**Problem**: GrantScout returns empty results

**Solutions**:

1. **Broaden search criteria**:
```json
{
  "scout": {
    "relevance_threshold": 0.5,  // Lower threshold
    "search_domains": {
      "whitelist": [],  // Remove whitelist restrictions
      "blacklist": []
    }
  }
}
```

2. **Check search queries**:
```bash
# Run with verbose logging
python main.py --config config.json --verbose

# Check generated queries
grep "Search query" output/logs/agent_scout.log
```

3. **Verify department needs**:
- Ensure needs are specific enough
- Add more need categories
- Include location information

4. **Test Search API manually**:
```bash
curl "https://www.googleapis.com/customsearch/v1?key=YOUR_KEY&cx=YOUR_CX&q=fire+department+grants"
```

### Irrelevant Grants Returned

**Problem**: Many results don't match department needs

**Solutions**:

1. **Increase relevance threshold**:
```json
{
  "scout": {
    "relevance_threshold": 0.8  // Increase from 0.6
  }
}
```

2. **Add domain filters**:
```json
{
  "scout": {
    "search_domains": {
      "whitelist": ["*.gov", "*.org"],
      "blacklist": ["example-spam.com"]
    }
  }
}
```

3. **Refine department needs**:
- Be more specific (e.g., "SCBA equipment" vs "equipment")
- Remove generic needs
- Prioritize critical needs

## Validation Issues

### All Grants Marked Ineligible

**Problem**: GrantValidator marks all grants as ineligible

**Solutions**:

1. **Lower eligibility threshold**:
```json
{
  "validator": {
    "eligibility_threshold": 50  // Lower from 70
  }
}
```

2. **Review validation logs**:
```bash
grep "ineligible" output/logs/agent_validator.log
```

3. **Check common rejection reasons**:
- Geographic restrictions
- Department type mismatch
- Budget requirements
- Missing certifications

4. **Update department profile**:
- Ensure all fields are accurate
- Add missing certifications
- Verify location details

### Document Parsing Failures

**Problem**: `ParsingError: Failed to parse document`

**Causes**:
- Password-protected PDFs
- Corrupted files
- Unsupported format
- Network issues

**Solutions**:

1. **Skip problematic documents**:
```json
{
  "validator": {
    "skip_parsing_errors": true
  }
}
```

2. **Increase timeout**:
```json
{
  "validator": {
    "document_timeout_seconds": 120
  }
}
```

3. **Limit PDF pages**:
```json
{
  "validator": {
    "max_pdf_pages": 20  // Reduce from 50
  }
}
```

4. **Check specific URL manually**:
```bash
curl -I https://problematic-url.com/grant.pdf
```

## Writing Issues

### Poor Quality Drafts

**Problem**: Generated drafts are generic or low quality

**Solutions**:

1. **Improve department profile**:
- Add detailed mission statement
- Include specific statistics
- Provide community impact data
- Add success stories

2. **Adjust writing settings**:
```json
{
  "writer": {
    "detail_level": "comprehensive",  // More detail
    "include_examples": true,
    "include_statistics": true,
    "temperature": 0.8  // More creative
  }
}
```

3. **Regenerate with more context**:
- Provide more background information
- Add specific grant requirements
- Include relevant past applications

### Formatting Issues

**Problem**: Generated drafts have formatting problems

**Solutions**:

1. **Convert to different format**:
```bash
# Install pandoc
sudo apt-get install pandoc

# Convert markdown to Word
pandoc draft.md -o draft.docx

# Convert to PDF
pandoc draft.md -o draft.pdf
```

2. **Change output format**:
```json
{
  "writer": {
    "format": "docx"  // Instead of markdown
  }
}
```

## Debugging Tips

### Enable Debug Logging

```bash
# Run with debug output
python main.py --config config.json --log-level DEBUG

# Check debug logs
tail -f output/logs/agent.log
```

### Use Dry Run Mode

```bash
# Test without API calls
python main.py --config config.json --dry-run
```

### Validate Configuration

```bash
# Check configuration before running
python main.py --validate-config config.json
```

### Run Tests

```bash
# Run test suite
pytest

# Run specific tests
pytest tests/test_scout.py -v
```

## Getting Additional Help

If you can't resolve the issue:

1. **Gather information**:
   - Error messages
   - Log files
   - Configuration files
   - Steps to reproduce

2. **Check documentation**:
   - [FAQ](FAQ.md)
   - [Configuration Guide](Configuration.md)
   - [API Reference](API-Reference.md)

3. **Search existing issues**:
   - GitHub Issues
   - GitHub Discussions

4. **Open a new issue**:
   - Use issue template
   - Include all relevant information
   - Attach log files if possible

5. **Contact maintainers**:
   - For urgent or sensitive issues
   - See CONTRIBUTING.md for contact info

## Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| `ConfigurationError` | Invalid config file | Validate JSON syntax |
| `AuthenticationError` | Invalid API key | Check .env file |
| `RateLimitError` | Too many requests | Wait and reduce frequency |
| `TimeoutError` | Request timed out | Check connection, increase timeout |
| `ParsingError` | Document parsing failed | Skip or retry with different settings |
| `ValidationError` | Invalid data | Check input format |
| `MemoryError` | Out of memory | Reduce batch size or limit scope |
| `PermissionError` | File access denied | Fix permissions |

## Performance Tuning

For optimal performance:

```json
{
  "scout": {
    "max_results_per_query": 5,
    "cache_results": true,
    "cache_ttl_hours": 24
  },
  "validator": {
    "eligibility_threshold": 70,
    "document_timeout_seconds": 60,
    "parse_pdfs": true,
    "max_pdf_pages": 20,
    "batch_size": 5,
    "cache_parsed_documents": true
  },
  "writer": {
    "temperature": 0.7,
    "max_tokens_per_section": 1000,
    "detail_level": "standard"
  }
}
```

## Still Having Issues?

Open an issue on GitHub with:
- Description of the problem
- Steps to reproduce
- Error messages and logs
- Configuration (sanitize API keys!)
- System information (OS, Python version)
